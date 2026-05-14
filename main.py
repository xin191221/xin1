import hashlib
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from cache import cache
from extractor import extract_info
from matcher import match_resume
from models import (
    Background,
    BasicInfo,
    HealthResponse,
    JobIntent,
    ResumeData,
    ResumeResponse,
)
from pdf_parser import parse_resume

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Resume Analyzer API started")
    yield
    logger.info("Resume Analyzer API shutting down")


app = FastAPI(
    title="AI 智能简历分析系统",
    description="解析 PDF 简历，提取关键信息，AI 岗位匹配评分",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/api/v1/resume/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(..., description="PDF 简历文件"),
    job_description: str = Form("", description="岗位描述（可选，用于匹配评分）"),
):
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return ResumeResponse(success=False, error="仅支持 PDF 格式的文件")

    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return ResumeResponse(success=False, error="文件大小不能超过 10MB")

    # Generate resume ID from file content
    resume_id = hashlib.md5(content).hexdigest()

    # Check cache
    cached_result = await cache.get(resume_id, job_description)
    if cached_result:
        cached_result["cached"] = True
        return ResumeResponse(**cached_result)

    # Parse PDF
    _, cleaned_text = parse_resume(content)
    if not cleaned_text.strip():
        return ResumeResponse(success=False, error="无法从 PDF 中提取文本内容")

    # Extract info via AI
    try:
        basic_info, job_intent, background = await extract_info(cleaned_text)
    except Exception as e:
        logger.warning(f"AI extraction failed, using empty defaults: {e}")
        basic_info, job_intent, background = BasicInfo(), JobIntent(), Background()

    # Match with job description if provided
    match_result = None
    if job_description.strip():
        resume_info = {
            "name": basic_info.name,
            "phone": basic_info.phone,
            "email": basic_info.email,
            "address": basic_info.address,
            "position": job_intent.position,
            "expected_salary": job_intent.expected_salary,
            "work_years": background.work_years,
            "education": background.education,
            "projects": background.projects,
        }
        try:
            match_result = await match_resume(resume_info, job_description)
        except Exception as e:
            logger.warning(f"AI matching failed: {e}")
            match_result = None

    # Build response
    resume_data = ResumeData(
        resume_id=resume_id,
        raw_text=cleaned_text,
        basic_info=basic_info,
        job_intent=job_intent,
        background=background,
        match_result=match_result,
    )

    response = ResumeResponse(success=True, data=resume_data, cached=False)

    # Cache the result
    await cache.set(resume_id, response.model_dump(), job_description)

    return response


def _ai_available() -> bool:
    api_key = os.getenv("OPENAI_API_KEY", "")
    return bool(api_key) and api_key != "sk-dummy"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

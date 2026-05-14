from pydantic import BaseModel, Field
from typing import Optional


class BasicInfo(BaseModel):
    name: Optional[str] = Field(None, description="姓名")
    phone: Optional[str] = Field(None, description="电话")
    email: Optional[str] = Field(None, description="邮箱")
    address: Optional[str] = Field(None, description="地址")


class JobIntent(BaseModel):
    position: Optional[str] = Field(None, description="求职意向")
    expected_salary: Optional[str] = Field(None, description="期望薪资")


class Background(BaseModel):
    work_years: Optional[str] = Field(None, description="工作年限")
    education: Optional[str] = Field(None, description="学历背景")
    projects: list[str] = Field(default_factory=list, description="项目经历")


class MatchResult(BaseModel):
    overall_score: Optional[int] = Field(None, description="综合匹配度评分 0-100")
    skill_match_rate: Optional[float] = Field(None, description="技能匹配率 0-1")
    experience_relevance: Optional[float] = Field(None, description="工作经验相关性 0-1")
    keywords_matched: list[str] = Field(default_factory=list, description="匹配的关键词")
    keywords_missing: list[str] = Field(default_factory=list, description="缺失的关键词")
    analysis: Optional[str] = Field(None, description="AI 匹配分析文本")


class ResumeData(BaseModel):
    resume_id: str = Field(..., description="简历唯一标识(MD5)")
    raw_text: str = Field(..., description="清洗后的简历原文")
    basic_info: BasicInfo = Field(default_factory=BasicInfo)
    job_intent: JobIntent = Field(default_factory=JobIntent)
    background: Background = Field(default_factory=Background)
    match_result: Optional[MatchResult] = Field(None, description="匹配结果(仅传入岗位描述时返回)")


class ResumeResponse(BaseModel):
    success: bool
    data: Optional[ResumeData] = None
    error: Optional[str] = None
    cached: bool = False


class HealthResponse(BaseModel):
    status: str
    version: str

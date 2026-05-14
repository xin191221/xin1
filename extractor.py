import json
import logging
import os
from typing import Optional

from openai import AsyncOpenAI

from models import BasicInfo, JobIntent, Background

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY", "sk-dummy")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        _client = AsyncOpenAI(api_key=api_key, base_url=base_url)
    return _client


EXTRACTION_PROMPT = """你是一个专业的简历解析专家。请从以下简历文本中提取关键信息，以 JSON 格式返回。

规则：
1. 如果某个字段在简历中找不到，设为 null
2. projects 字段为数组，提取所有明确列出的项目名称
3. 只返回 JSON，不要包含其他文字

简历文本：
{resume_text}

请严格按照以下 JSON 结构返回：
```json
{{
  "name": null,
  "phone": null,
  "email": null,
  "address": null,
  "position": null,
  "expected_salary": null,
  "work_years": null,
  "education": null,
  "projects": []
}}
```"""


async def extract_info(resume_text: str) -> tuple[BasicInfo, JobIntent, Background]:
    """Use AI to extract structured information from resume text."""
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    prompt = EXTRACTION_PROMPT.format(resume_text=resume_text[:8000])

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=1000,
        )
        content = response.choices[0].message.content or "{}"
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content.strip())
    except Exception as e:
        logger.error(f"AI extraction failed: {e}")
        data = {}

    basic_info = BasicInfo(
        name=data.get("name"),
        phone=data.get("phone"),
        email=data.get("email"),
        address=data.get("address"),
    )
    job_intent = JobIntent(
        position=data.get("position"),
        expected_salary=data.get("expected_salary"),
    )
    background = Background(
        work_years=data.get("work_years"),
        education=data.get("education"),
        projects=data.get("projects") or [],
    )
    return basic_info, job_intent, background

import json
import logging
import os
from typing import Optional

from openai import AsyncOpenAI

from models import MatchResult

logger = logging.getLogger(__name__)


def _get_client() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY", "sk-dummy")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


MATCH_PROMPT = """你是一个专业的招聘匹配分析专家。请根据候选人的简历信息和岗位需求，进行匹配度分析。

候选人信息：
{resume_info}

岗位需求：
{job_description}

请从以下维度评估并返回 JSON：
1. overall_score: 综合匹配度评分 (0-100)
2. skill_match_rate: 技能匹配率 (0.0-1.0)
3. experience_relevance: 工作经验相关性 (0.0-1.0)
4. keywords_matched: 匹配上的关键技能/要求
5. keywords_missing: 缺失的关键技能/要求
6. analysis: 简要的匹配分析文字 (50-100字)

只返回 JSON，不要包含其他文字：
```json
{{
  "overall_score": 0,
  "skill_match_rate": 0.0,
  "experience_relevance": 0.0,
  "keywords_matched": [],
  "keywords_missing": [],
  "analysis": ""
}}
```"""


async def match_resume(
    resume_info: dict,
    job_description: str,
) -> MatchResult:
    """Use AI to calculate matching score between resume and job description."""
    client = _get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    resume_info_str = json.dumps(resume_info, ensure_ascii=False, indent=2)
    prompt = MATCH_PROMPT.format(
        resume_info=resume_info_str,
        job_description=job_description,
    )

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
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else content
            if content.startswith("json"):
                content = content[4:]
        data = json.loads(content.strip())
    except Exception as e:
        logger.error(f"AI matching failed: {e}")
        data = {}

    return MatchResult(
        overall_score=data.get("overall_score"),
        skill_match_rate=data.get("skill_match_rate"),
        experience_relevance=data.get("experience_relevance"),
        keywords_matched=data.get("keywords_matched") or [],
        keywords_missing=data.get("keywords_missing") or [],
        analysis=data.get("analysis"),
    )

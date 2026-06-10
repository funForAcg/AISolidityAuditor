import json
import logging
from typing import Optional

import httpx

from app.config import settings
from app.models.schemas import AIExplanation, Finding

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一名智能合约安全审计助手。你的任务是将 Slither 静态分析工具输出的技术告警翻译为开发者易懂的中文说明。

严格要求：
1. 只基于提供的 Slither finding 进行解释，不得捏造未报告的问题
2. 不确定时明确标注「需人工复核」
3. 使用中文输出，技术术语（如 reentrancy）可保留英文
4. 回复必须是合法 JSON，不要包含 markdown 代码块"""

USER_PROMPT_TEMPLATE = """请解释以下 Slither 安全发现：

检测器：{detector}
严重级别：{severity}
描述：{description}
合约：{contract}
函数：{function}
位置：{location}

请以 JSON 格式回复，包含以下字段：
- title: 简短中文标题（不超过50字）
- problem: 问题说明（面向开发者）
- impact: 潜在影响
- recommendation: 具体修复建议"""


async def explain_finding(
    finding: Finding,
    api_key: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> AIExplanation:
    key = api_key or settings.openai_api_key
    if not key:
        return AIExplanation(
            title=finding.detector,
            problem=finding.description,
            impact="未配置 AI API Key，无法生成解释",
            recommendation="请配置 OpenAI 兼容 API Key 后重试",
            ai_success=False,
        )

    location = ""
    if finding.file:
        location = finding.file
        if finding.line:
            location += f":{finding.line}"

    prompt = USER_PROMPT_TEMPLATE.format(
        detector=finding.detector,
        severity=finding.severity.value,
        description=finding.description,
        contract=finding.contract or "未知",
        function=finding.function or "未知",
        location=location or "未知",
    )

    url = (base_url or settings.openai_base_url).rstrip("/") + "/chat/completions"
    model_name = model or settings.openai_model

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)

            return AIExplanation(
                title=parsed.get("title", finding.detector),
                problem=parsed.get("problem", finding.description),
                impact=parsed.get("impact", ""),
                recommendation=parsed.get("recommendation", ""),
                ai_success=True,
            )
    except Exception as exc:
        logger.warning("AI explanation failed for %s: %s", finding.id, exc)
        return AIExplanation(
            title=finding.detector,
            problem=finding.description,
            impact="AI 解释生成失败，以下为 Slither 原始描述",
            recommendation="请人工查阅 Slither 文档或寻求安全专家帮助",
            ai_success=False,
        )


async def explain_findings(
    findings: list[Finding],
    api_key: str,
    max_count: Optional[int] = None,
) -> list[Finding]:
    limit = max_count or settings.max_ai_findings
    result: list[Finding] = []

    for i, finding in enumerate(findings):
        if i < limit:
            ai = await explain_finding(finding, api_key)
            finding.ai = ai
            finding.ai_expanded = True
        else:
            finding.ai = AIExplanation(
                title=finding.detector,
                problem=finding.description,
                impact="",
                recommendation="",
                ai_success=False,
            )
            finding.ai_expanded = False

        result.append(finding)

    return result

from abc import ABC, abstractmethod
import json
import logging
from typing import Any, Optional

import httpx

from app.config import settings
from app.models.schemas import AIExplanation, Finding

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a smart contract security audit assistant. Your task is to translate technical alerts from the Slither static analysis tool into clear explanations for developers.

Strict requirements:
1. Only explain based on the provided Slither finding; do not invent issues that were not reported
2. When uncertain, explicitly state "manual review required"
3. Write in English; technical terms (e.g. reentrancy) may remain as-is
4. Respond with valid JSON only; do not wrap in markdown code blocks"""

USER_PROMPT_TEMPLATE = """Explain the following Slither security finding:

Detector: {detector}
Severity: {severity}
Description: {description}
Contract: {contract}
Function: {function}
Location: {location}

Reply in JSON with these fields:
- title: short English title (max 50 characters)
- problem: what is wrong (developer-facing)
- impact: potential impact
- recommendation: concrete fix guidance"""


class AIProviderError(RuntimeError):
    pass


def _finding_prompt(finding: Finding) -> str:
    location = ""
    if finding.file:
        location = finding.file
        if finding.line:
            location += f":{finding.line}"

    return USER_PROMPT_TEMPLATE.format(
        detector=finding.detector,
        severity=finding.severity.value,
        description=finding.description,
        contract=finding.contract or "unknown",
        function=finding.function or "unknown",
        location=location or "unknown",
    )


def _explanation_from_json(content: str, finding: Finding, provider: str) -> AIExplanation:
    parsed = json.loads(content)
    return AIExplanation(
        title=parsed.get("title", finding.detector),
        problem=parsed.get("problem", finding.description),
        impact=parsed.get("impact", ""),
        recommendation=parsed.get("recommendation", ""),
        ai_success=True,
        provider=provider,
    )


def _fallback_explanation(
    finding: Finding,
    provider: str,
    impact: str,
    recommendation: str,
    error: Optional[str] = None,
) -> AIExplanation:
    return AIExplanation(
        title=finding.detector,
        problem=finding.description,
        impact=impact,
        recommendation=recommendation,
        ai_success=False,
        provider=provider,
        error=error,
    )


class BaseAIProvider(ABC):
    name: str

    @abstractmethod
    def configured(self, api_key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def explain(self, finding: Finding, api_key: str) -> AIExplanation:
        raise NotImplementedError


class OpenAIProvider(BaseAIProvider):
    name = "openai"

    def configured(self, api_key: str) -> bool:
        return bool(api_key or settings.openai_api_key)

    async def explain(self, finding: Finding, api_key: str) -> AIExplanation:
        key = api_key or settings.openai_api_key
        if not key:
            raise AIProviderError("No OpenAI API key configured")

        url = settings.openai_base_url.rstrip("/") + "/chat/completions"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.openai_model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": _finding_prompt(finding)},
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return _explanation_from_json(content, finding, self.name)


class ClaudeProvider(BaseAIProvider):
    name = "claude"

    def configured(self, api_key: str) -> bool:
        return bool(api_key or settings.anthropic_api_key)

    async def explain(self, finding: Finding, api_key: str) -> AIExplanation:
        key = api_key or settings.anthropic_api_key
        if not key:
            raise AIProviderError("No Anthropic API key configured")

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.claude_model,
                    "max_tokens": 800,
                    "temperature": 0.2,
                    "system": SYSTEM_PROMPT,
                    "messages": [
                        {
                            "role": "user",
                            "content": _finding_prompt(finding),
                        }
                    ],
                },
            )
            response.raise_for_status()
            data = response.json()
            content = _extract_claude_text(data)
            return _explanation_from_json(content, finding, self.name)


def _extract_claude_text(data: dict[str, Any]) -> str:
    blocks = data.get("content", [])
    for block in blocks:
        if block.get("type") == "text":
            return block.get("text", "")
    raise AIProviderError("Claude response did not contain a text block")


class AIService:
    def __init__(self) -> None:
        self.providers: dict[str, BaseAIProvider] = {
            "openai": OpenAIProvider(),
            "claude": ClaudeProvider(),
        }

    def get_provider(self, provider_name: Optional[str] = None) -> BaseAIProvider:
        name = (provider_name or settings.ai_provider).lower()
        provider = self.providers.get(name)
        if provider is None:
            available = ", ".join(sorted(self.providers))
            raise AIProviderError(f"Unknown AI provider '{name}'. Available providers: {available}")
        return provider

    async def explain_finding(
        self,
        finding: Finding,
        api_key: str = "",
        provider_name: Optional[str] = None,
    ) -> AIExplanation:
        provider = self.get_provider(provider_name)
        if not provider.configured(api_key):
            message = f"No API key configured for {provider.name}"
            logger.info("Skipping AI explanation for %s: %s", finding.id, message)
            return _fallback_explanation(
                finding=finding,
                provider=provider.name,
                impact="AI explanation unavailable because no API key is configured",
                recommendation="Set the provider API key or pass one with the audit request",
                error=message,
            )

        try:
            return await provider.explain(finding, api_key)
        except Exception as exc:
            message = str(exc)
            logger.warning(
                "AI explanation failed for %s using %s: %s",
                finding.id,
                provider.name,
                message,
            )
            return _fallback_explanation(
                finding=finding,
                provider=provider.name,
                impact="AI explanation failed; showing original Slither description below",
                recommendation="Check the configured AI provider, API key, model, and network access",
                error=message,
            )

    async def explain_findings(
        self,
        findings: list[Finding],
        api_key: str = "",
        max_count: Optional[int] = None,
        provider_name: Optional[str] = None,
    ) -> list[Finding]:
        limit = max_count or settings.max_ai_findings
        result: list[Finding] = []

        for i, finding in enumerate(findings):
            if i < limit:
                finding.ai = await self.explain_finding(finding, api_key, provider_name)
                finding.ai_expanded = True
            else:
                finding.ai = _fallback_explanation(
                    finding=finding,
                    provider=provider_name or settings.ai_provider,
                    impact="",
                    recommendation="",
                    error="AI explanation limit exceeded",
                )
                finding.ai_expanded = False

            result.append(finding)

        return result


ai_service = AIService()


async def explain_finding(
    finding: Finding,
    api_key: str,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
) -> AIExplanation:
    original_base_url = settings.openai_base_url
    original_model = settings.openai_model
    if base_url is not None:
        settings.openai_base_url = base_url
    if model is not None:
        settings.openai_model = model
    try:
        return await ai_service.explain_finding(finding, api_key, provider_name="openai")
    finally:
        settings.openai_base_url = original_base_url
        settings.openai_model = original_model


async def explain_findings(
    findings: list[Finding],
    api_key: str,
    max_count: Optional[int] = None,
    provider_name: Optional[str] = None,
) -> list[Finding]:
    return await ai_service.explain_findings(findings, api_key, max_count, provider_name)

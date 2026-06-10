import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import AIExplanation, Finding, Severity
from app.services.ai import explain_finding, explain_findings


def _sample_finding() -> Finding:
    return Finding(
        id="finding-1",
        detector="reentrancy-eth",
        severity=Severity.HIGH,
        description="Reentrancy in withdraw",
        contract="VulnerableBank",
        function="withdraw",
        file="Reentrancy.sol",
        line=15,
    )


@pytest.mark.asyncio
async def test_explain_finding_mock_response():
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "title": "重入攻击风险",
                            "problem": "外部调用在状态更新之前执行",
                            "impact": "攻击者可反复提取资金",
                            "recommendation": "使用 checks-effects-interactions 模式",
                        },
                        ensure_ascii=False,
                    )
                }
            }
        ]
    }

    with patch("app.services.ai.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.json.return_value = mock_response
        mock_client.post = AsyncMock(return_value=mock_resp)

        result = await explain_finding(_sample_finding(), api_key="test-key")

    assert result.ai_success is True
    assert result.title == "重入攻击风险"
    assert "checks-effects-interactions" in result.recommendation


@pytest.mark.asyncio
async def test_explain_finding_without_api_key():
    with patch("app.services.ai.settings") as mock_settings:
        mock_settings.openai_api_key = ""
        result = await explain_finding(_sample_finding(), api_key="")

    assert result.ai_success is False
    assert "API Key" in result.impact


@pytest.mark.asyncio
async def test_explain_findings_respects_limit():
    findings = [
        Finding(
            id=f"f-{i}",
            detector=f"det-{i}",
            severity=Severity.LOW,
            description=f"issue {i}",
        )
        for i in range(3)
    ]

    with patch(
        "app.services.ai.explain_finding",
        new_callable=AsyncMock,
        return_value=AIExplanation(
            title="mock",
            problem="p",
            impact="i",
            recommendation="r",
            ai_success=True,
        ),
    ):
        result = await explain_findings(findings, api_key="key", max_count=2)

    assert len(result) == 3
    assert result[0].ai_expanded is True
    assert result[1].ai_expanded is True
    assert result[2].ai_expanded is False

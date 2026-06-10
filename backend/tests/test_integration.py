from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.models.schemas import AIExplanation, AuditStatus, Finding, Severity
from app.services import storage


def _mock_explained_findings() -> list[Finding]:
    return [
        Finding(
            id="finding-1",
            detector="reentrancy-eth",
            severity=Severity.HIGH,
            description="Reentrancy in VulnerableBank.withdraw(uint256)",
            contract="VulnerableBank",
            function="withdraw",
            file="Reentrancy.sol",
            line=15,
            ai=AIExplanation(
                title="重入攻击风险",
                problem="外部调用在状态更新之前执行",
                impact="攻击者可反复提取资金",
                recommendation="使用 checks-effects-interactions 模式",
                ai_success=True,
            ),
            ai_expanded=True,
        )
    ]


@patch("app.services.audit.ai.explain_findings", new_callable=AsyncMock)
@patch("app.services.audit.slither.run_slither")
@patch("app.services.audit.slither.check_slither_available", return_value=(True, "0.10.4"))
def test_full_audit_pipeline(
    _mock_slither_check,
    mock_run_slither,
    mock_explain,
    client: TestClient,
    example_zip: Path,
    slither_raw: dict,
    data_dir: Path,
):
    mock_run_slither.return_value = slither_raw
    mock_explain.return_value = _mock_explained_findings()

    with open(example_zip, "rb") as f:
        response = client.post(
            "/api/v1/audits",
            files={"file": ("reentrancy-example.zip", f, "application/zip")},
            data={"api_key": "test-key"},
        )

    assert response.status_code == 200
    task_id = response.json()["task_id"]

    status = client.get(f"/api/v1/audits/{task_id}").json()
    assert status["status"] == AuditStatus.COMPLETED.value
    assert status["summary"]["high"] == 1
    assert status["summary"]["ai_explained"] == 1

    findings_resp = client.get(f"/api/v1/audits/{task_id}/findings")
    assert findings_resp.status_code == 200
    findings = findings_resp.json()["findings"]
    assert len(findings) == 1
    assert findings[0]["ai"]["title"] == "重入攻击风险"

    report_resp = client.get(f"/api/v1/audits/{task_id}/report")
    assert report_resp.status_code == 200
    assert "智能合约审计报告" in report_resp.text
    assert "重入攻击风险" in report_resp.text

    slither_resp = client.get(f"/api/v1/audits/{task_id}/slither")
    assert slither_resp.status_code == 200
    assert slither_resp.json()["results"]["detectors"][0]["check"] == "reentrancy-eth"

    assert (data_dir / task_id / "slither.json").exists()
    assert (data_dir / task_id / "report.md").exists()
    assert (data_dir / task_id / "findings.json").exists()

    download_resp = client.get(f"/api/v1/audits/{task_id}/report?download=true")
    assert download_resp.status_code == 200
    assert "attachment" in download_resp.headers.get("content-disposition", "")


@patch("app.services.audit.slither.run_slither", side_effect=RuntimeError("编译失败"))
@patch("app.services.audit.slither.check_slither_available", return_value=(True, "0.10.4"))
def test_audit_pipeline_slither_failure(
    _mock_check,
    _mock_run,
    client: TestClient,
    example_zip: Path,
):
    with open(example_zip, "rb") as f:
        response = client.post(
            "/api/v1/audits",
            files={"file": ("reentrancy-example.zip", f, "application/zip")},
        )

    task_id = response.json()["task_id"]
    status = client.get(f"/api/v1/audits/{task_id}").json()
    assert status["status"] == AuditStatus.FAILED.value
    assert "编译失败" in status["error"]


def test_slither_endpoint_not_ready(client: TestClient, example_zip: Path):
    with open(example_zip, "rb") as f:
        created = client.post(
            "/api/v1/audits",
            files={"file": ("reentrancy-example.zip", f, "application/zip")},
        )

    task_id = created.json()["task_id"]
    storage.update_status(
        task_id,
        AuditStatus.RUNNING_SLITHER,
        "分析中",
    )

    resp = client.get(f"/api/v1/audits/{task_id}/slither")
    assert resp.status_code == 409

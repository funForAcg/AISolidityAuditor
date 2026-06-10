from app.models.schemas import AIExplanation, AuditMeta, AuditStatus, Finding, Severity
from app.services.report import build_summary, generate_report


def _finding_with_ai() -> Finding:
    return Finding(
        id="finding-1",
        detector="reentrancy-eth",
        severity=Severity.HIGH,
        description="Reentrancy in withdraw",
        contract="VulnerableBank",
        function="withdraw",
        file="Reentrancy.sol",
        line=15,
        ai=AIExplanation(
            title="重入攻击风险",
            problem="外部调用在状态更新前",
            impact="资金可被重复提取",
            recommendation="先更新状态再转账",
            ai_success=True,
        ),
    )


def test_build_summary():
    summary = build_summary([_finding_with_ai()])
    assert summary.total == 1
    assert summary.high == 1
    assert summary.ai_explained == 1


def test_generate_report():
    meta = AuditMeta(
        task_id="test-task-id",
        status=AuditStatus.COMPLETED,
        filename="reentrancy-example.zip",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
        duration_sec=12.5,
    )
    report = generate_report(meta, [_finding_with_ai()], slither_version="0.10.4")

    assert "# 智能合约审计报告" in report
    assert "reentrancy-example.zip" in report
    assert "重入攻击风险" in report
    assert "reentrancy-eth" in report
    assert "免责声明" in report
    assert "/api/v1/audits/" in report
    assert "/slither" in report


def test_generate_report_empty_findings():
    meta = AuditMeta(
        task_id="empty-task",
        status=AuditStatus.COMPLETED,
        filename="clean.zip",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    report = generate_report(meta, [])
    assert "未检测到安全问题" in report

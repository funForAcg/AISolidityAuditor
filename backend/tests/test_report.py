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
            title="Reentrancy risk",
            problem="External call before state update",
            impact="Funds may be drained repeatedly",
            recommendation="Update state before external transfer",
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

    assert "# Smart Contract Audit Report" in report
    assert "reentrancy-example.zip" in report
    assert "Reentrancy risk" in report
    assert "reentrancy-eth" in report
    assert "Disclaimer" in report
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
    assert "No security issues detected" in report


def test_generate_report_ai_failure_reason():
    finding = Finding(
        id="finding-1",
        detector="reentrancy-eth",
        severity=Severity.HIGH,
        description="Reentrancy in withdraw",
        ai=AIExplanation(
            title="reentrancy-eth",
            problem="Reentrancy in withdraw",
            impact="AI explanation unavailable because no API key is configured",
            recommendation="Set the provider API key or pass one with the audit request",
            ai_success=False,
            provider="openai",
            error="No API key configured for openai",
        ),
    )
    meta = AuditMeta(
        task_id="failed-ai-task",
        status=AuditStatus.COMPLETED,
        filename="reentrancy-example.zip",
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )

    report = generate_report(meta, [finding])

    assert "| AI explained | 0 |" in report
    assert "AI explanation**: Unavailable (No API key configured for openai)" in report

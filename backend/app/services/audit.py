import logging
import time
from pathlib import Path
from typing import Optional

from app.models.schemas import AuditStatus
from app.services import ai, report, slither, storage
from app.services.report import build_summary

logger = logging.getLogger(__name__)


async def run_audit_pipeline(
    task_id: str,
    project_path: Path,
    api_key: Optional[str] = None,
    ai_provider: Optional[str] = None,
) -> None:
    start = time.time()
    slither_version = "unknown"

    try:
        storage.update_status(
            task_id,
            AuditStatus.RUNNING_SLITHER,
            "Running Slither static analysis...",
        )

        slither_ok, version = slither.check_slither_available()
        if not slither_ok:
            raise RuntimeError("Slither is not installed or unavailable; check your Docker environment")

        slither_version = version or "unknown"
        output_path = storage.get_job_dir(task_id) / "slither.json"
        raw = slither.run_slither(project_path, output_path)
        storage.save_json(task_id, "slither.json", raw)
        findings = slither.parse_slither_results(raw)

        storage.update_status(
            task_id,
            AuditStatus.RUNNING_AI,
            f"Slither finished with {len(findings)} finding(s); running AI explanations...",
        )

        explained = await ai.explain_findings(findings, api_key or "", provider_name=ai_provider)
        storage.save_findings(task_id, explained)

        summary = build_summary(explained)
        duration = time.time() - start

        meta = storage.load_meta(task_id)
        if meta is None:
            return

        meta.summary = summary
        meta.duration_sec = round(duration, 1)
        storage.save_meta(task_id, meta)

        report_content = report.generate_report(meta, explained, slither_version)
        storage.save_report(task_id, report_content)

        storage.update_status(
            task_id,
            AuditStatus.COMPLETED,
            "Audit completed",
            summary=summary,
            finished=True,
            duration_sec=round(duration, 1),
        )

        logger.info("Audit %s completed in %.1fs with %d findings", task_id, duration, len(explained))

    except Exception as exc:
        logger.exception("Audit %s failed", task_id)
        duration = time.time() - start
        storage.update_status(
            task_id,
            AuditStatus.FAILED,
            "Audit failed",
            error=str(exc),
            finished=True,
            duration_sec=round(duration, 1),
        )

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
) -> None:
    start = time.time()
    slither_version = "unknown"

    try:
        storage.update_status(
            task_id,
            AuditStatus.RUNNING_SLITHER,
            "正在运行 Slither 静态分析...",
        )

        slither_ok, version = slither.check_slither_available()
        if not slither_ok:
            raise RuntimeError("Slither 未安装或不可用，请检查 Docker 环境")

        slither_version = version or "unknown"
        output_path = storage.get_job_dir(task_id) / "slither.json"
        raw = slither.run_slither(project_path, output_path)
        storage.save_json(task_id, "slither.json", raw)
        findings = slither.parse_slither_results(raw)

        storage.update_status(
            task_id,
            AuditStatus.RUNNING_AI,
            f"Slither 完成，发现 {len(findings)} 个问题，正在进行 AI 解释...",
        )

        explained = await ai.explain_findings(findings, api_key or "")
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
            "审计完成",
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
            "审计失败",
            error=str(exc),
            finished=True,
            duration_sec=round(duration, 1),
        )

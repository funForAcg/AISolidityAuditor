import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from app.config import settings
from app.models.schemas import AuditMeta, AuditStatus, AuditSummary, Finding


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_job_dir(task_id: str) -> Path:
    return settings.data_dir / task_id


def create_job(filename: str) -> tuple[str, Path]:
    task_id = str(uuid4())
    job_dir = get_job_dir(task_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "project").mkdir(exist_ok=True)

    meta = AuditMeta(
        task_id=task_id,
        status=AuditStatus.PENDING,
        filename=filename,
        created_at=utc_now_iso(),
        updated_at=utc_now_iso(),
        progress="任务已创建，等待处理",
    )
    save_meta(task_id, meta)
    return task_id, job_dir


def save_meta(task_id: str, meta: AuditMeta) -> None:
    meta.updated_at = utc_now_iso()
    path = get_job_dir(task_id) / "meta.json"
    path.write_text(meta.model_dump_json(indent=2), encoding="utf-8")


def load_meta(task_id: str) -> Optional[AuditMeta]:
    path = get_job_dir(task_id) / "meta.json"
    if not path.exists():
        return None
    return AuditMeta.model_validate_json(path.read_text(encoding="utf-8"))


def update_status(
    task_id: str,
    status: AuditStatus,
    progress: str,
    error: Optional[str] = None,
    summary: Optional[AuditSummary] = None,
    finished: bool = False,
    duration_sec: Optional[float] = None,
) -> AuditMeta:
    meta = load_meta(task_id)
    if meta is None:
        raise FileNotFoundError(f"Task {task_id} not found")

    meta.status = status
    meta.progress = progress
    if error is not None:
        meta.error = error
    if summary is not None:
        meta.summary = summary
    if finished:
        meta.finished_at = utc_now_iso()
    if duration_sec is not None:
        meta.duration_sec = duration_sec

    save_meta(task_id, meta)
    return meta


def save_json(task_id: str, name: str, data: Any) -> Path:
    path = get_job_dir(task_id) / name
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_json(task_id: str, name: str) -> Any:
    path = get_job_dir(task_id) / name
    return json.loads(path.read_text(encoding="utf-8"))


def save_findings(task_id: str, findings: list[Finding]) -> None:
    data = [f.model_dump() for f in findings]
    save_json(task_id, "findings.json", data)


def load_findings(task_id: str) -> list[Finding]:
    path = get_job_dir(task_id) / "findings.json"
    if not path.exists():
        return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Finding.model_validate(item) for item in raw]


def save_report(task_id: str, content: str) -> Path:
    path = get_job_dir(task_id) / "report.md"
    path.write_text(content, encoding="utf-8")
    return path


def load_report(task_id: str) -> Optional[str]:
    path = get_job_dir(task_id) / "report.md"
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def load_slither_raw(task_id: str) -> Optional[dict]:
    path = get_job_dir(task_id) / "slither.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))

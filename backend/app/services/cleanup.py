import logging
import shutil
from datetime import datetime, timedelta, timezone

from app.config import settings

logger = logging.getLogger(__name__)


def cleanup_old_jobs() -> int:
    """Remove job directories older than retention period. Returns count removed."""
    if not settings.data_dir.exists():
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.job_retention_hours)
    removed = 0

    for job_dir in settings.data_dir.iterdir():
        if not job_dir.is_dir():
            continue

        meta_path = job_dir / "meta.json"
        if meta_path.exists():
            try:
                mtime = datetime.fromtimestamp(meta_path.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
        else:
            try:
                mtime = datetime.fromtimestamp(job_dir.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue

        if mtime < cutoff:
            try:
                shutil.rmtree(job_dir)
                removed += 1
                logger.info("Cleaned up old job: %s", job_dir.name)
            except OSError as exc:
                logger.warning("Failed to cleanup %s: %s", job_dir.name, exc)

    return removed

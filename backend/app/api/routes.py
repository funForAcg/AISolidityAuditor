import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from app.config import settings
from app.models.schemas import (
    AuditStatusResponse,
    CreateAuditResponse,
    FindingsResponse,
    HealthResponse,
)
from app.services import audit, slither, storage, upload

logger = logging.getLogger(__name__)
router = APIRouter()

_semaphore = asyncio.Semaphore(3)


async def _run_audit_task(
    task_id: str,
    project_path,
    api_key: Optional[str],
    ai_provider: Optional[str],
) -> None:
    async with _semaphore:
        await audit.run_audit_pipeline(task_id, project_path, api_key, ai_provider)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    slither_ok, version = slither.check_slither_available()
    solc_ok = slither.check_solc_available()
    return HealthResponse(
        status="ok" if slither_ok and solc_ok else "degraded",
        slither_available=slither_ok,
        solc_available=solc_ok,
        slither_version=version,
        details={
            "max_upload_mb": settings.max_upload_mb,
            "slither_timeout_sec": settings.slither_timeout_sec,
            "ai_provider": settings.ai_provider,
            "openai_configured": bool(settings.openai_api_key),
            "claude_configured": bool(settings.anthropic_api_key),
        },
    )


@router.post("/v1/audits", response_model=CreateAuditResponse)
async def create_audit(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    api_key: Optional[str] = Form(None),
    ai_provider: Optional[str] = Form(None),
):
    provider = (ai_provider or settings.ai_provider).lower()
    if provider not in {"openai", "claude"}:
        raise HTTPException(status_code=400, detail=f"Unsupported AI provider: {provider}")

    task_id, job_dir = storage.create_job(file.filename or "project.zip")
    project_path = await upload.save_and_extract_zip(file, job_dir)

    configured_key = settings.anthropic_api_key if provider == "claude" else settings.openai_api_key
    effective_key = api_key or configured_key or None

    background_tasks.add_task(_run_audit_task, task_id, project_path, effective_key, provider)

    return CreateAuditResponse(task_id=task_id)


@router.get("/v1/audits/{task_id}", response_model=AuditStatusResponse)
async def get_audit_status(task_id: str):
    meta = storage.load_meta(task_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return AuditStatusResponse(
        task_id=meta.task_id,
        status=meta.status,
        progress=meta.progress,
        error=meta.error,
        summary=meta.summary,
        filename=meta.filename,
        finished_at=meta.finished_at,
        duration_sec=meta.duration_sec,
    )


@router.get("/v1/audits/{task_id}/findings", response_model=FindingsResponse)
async def get_findings(task_id: str):
    meta = storage.load_meta(task_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Task not found")

    from app.models.schemas import AuditStatus

    if meta.status != AuditStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Task not completed yet")

    findings = storage.load_findings(task_id)
    return FindingsResponse(task_id=task_id, findings=findings)


@router.get("/v1/audits/{task_id}/slither")
async def get_slither_raw(task_id: str):
    meta = storage.load_meta(task_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Task not found")

    from app.models.schemas import AuditStatus

    if meta.status not in (AuditStatus.COMPLETED, AuditStatus.FAILED):
        raise HTTPException(status_code=409, detail="Slither results not ready yet")

    raw = storage.load_slither_raw(task_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="Slither output not found")

    return JSONResponse(content=raw)


@router.get("/v1/audits/{task_id}/report")
async def get_report(task_id: str, download: bool = False):
    meta = storage.load_meta(task_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Task not found")

    from app.models.schemas import AuditStatus

    if meta.status != AuditStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="Task not completed yet")

    content = storage.load_report(task_id)
    if content is None:
        raise HTTPException(status_code=404, detail="Report not found")

    if download:
        filename = f"audit-report-{task_id[:8]}.md"
        return Response(
            content=content,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.config import settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.services.cleanup import cleanup_old_jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def _periodic_cleanup() -> None:
    while True:
        await asyncio.sleep(3600)
        removed = cleanup_old_jobs()
        if removed:
            logger.info("Periodic cleanup removed %d job(s)", removed)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    removed = cleanup_old_jobs()
    if removed:
        logger.info("Startup cleanup removed %d old job(s)", removed)
    logger.info("Data directory: %s", settings.data_dir)
    task = asyncio.create_task(_periodic_cleanup())
    yield
    task.cancel()


app = FastAPI(
    title="AISolidityAuditor",
    description="AI-assisted Solidity smart contract audit platform",
    version="0.1.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

# Serve frontend static files in production (Docker)
_static_dir = Path(__file__).parent.parent.parent / "frontend" / "dist"
if _static_dir.exists():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="frontend")

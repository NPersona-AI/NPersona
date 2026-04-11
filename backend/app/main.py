"""FastAPI main application – Adversarial Persona Maker backend."""
import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db

from app.api.upload import router as upload_router
from app.api.jobs import router as jobs_router
from app.api.personas import router as personas_router
from app.api.coverage import router as coverage_router
from app.api.stream import router as stream_router
from app.api.export import router as export_router

# Set global recursion limit for deeply nested data structures (personas with multi-level trajectories)
# Default is ~1000; we increase to 10000 for production safety
sys.setrecursionlimit(10000)

# ── Logging setup: write to both stderr AND a persistent log file ─────────────
_LOG_FILE = Path(__file__).resolve().parent.parent / "app.log"
_fmt = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")

_file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
_file_handler.setFormatter(_fmt)
_file_handler.setLevel(logging.DEBUG)

_stream_handler = logging.StreamHandler(sys.stderr)
_stream_handler.setFormatter(_fmt)
_stream_handler.setLevel(logging.DEBUG)

logging.root.setLevel(logging.DEBUG)
logging.root.handlers = [_file_handler, _stream_handler]

logger = logging.getLogger(__name__)


async def _cleanup_stuck_jobs():
    """On startup: reset jobs stuck in transient states due to server kill."""
    from app.database import async_session
    from app.models.job import Job
    from sqlalchemy import select

    async with async_session() as session:
        result = await session.execute(
            select(Job).where(Job.status.in_(["parsing", "graph_building", "persona_generating"]))
        )
        stuck = result.scalars().all()
        for job in stuck:
            if job.status == "persona_generating" and (job.node_count or 0) > 0:
                job.status = "graph_ready"
                logger.warning(f"Reset stuck job {job.id} persona_generating → graph_ready (has graph)")
            else:
                job.status = "error"
                job.error_message = "Server restarted during processing. Please upload again."
                logger.warning(f"Reset stuck job {job.id} {job.status} → error (no graph)")
        if stuck:
            await session.commit()
            logger.info(f"Cleaned up {len(stuck)} stuck job(s) on startup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan – startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"LLM Concurrency: {settings.LLM_CONCURRENCY}")
    logger.info(f"Max Output Tokens: {settings.LLM_MAX_OUTPUT_TOKENS}")

    # Initialize database
    await init_db()
    logger.info("SQLite database initialized")

    # Clean up jobs left in transient states from a previous server crash/kill
    await _cleanup_stuck_jobs()

    yield

    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Upload an AI system document → Extract knowledge graph → Generate adversarial & user testing personas",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(jobs_router, prefix="/api", tags=["Jobs"])
app.include_router(personas_router, prefix="/api", tags=["Personas"])
app.include_router(coverage_router, prefix="/api", tags=["Coverage"])
app.include_router(stream_router, prefix="/api", tags=["Streaming"])
app.include_router(export_router, prefix="/api", tags=["Export"])


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }

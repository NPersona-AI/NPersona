"""Job status and graph retrieval endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.job import Job
from app.models.graph import KnowledgeGraph
from app.schemas.responses import JobResponse
from app.services import graph_store

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/job/{job_id}/status", response_model=JobResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get the current status of a processing job."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobResponse(
        id=job.id,
        filename=job.filename,
        status=job.status,
        error_message=job.error_message,
        node_count=job.node_count,
        edge_count=job.edge_count,
        user_persona_count=job.user_persona_count,
        adversarial_persona_count=job.adversarial_persona_count,
        created_at=job.created_at,
    )


@router.get("/job/{job_id}/graph", response_model=KnowledgeGraph)
async def get_job_graph(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get the knowledge graph for a job."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status not in ("graph_ready", "persona_generating", "scoring", "done"):
        raise HTTPException(
            status_code=409,
            detail=f"Graph not ready. Current status: {job.status}"
        )

    graph = await graph_store.get_or_load_graph(job_id)
    return graph

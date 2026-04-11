"""Upload endpoint – accepts seed documents and starts the processing pipeline."""
import logging
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.database import get_db
from app.models.job import Job
from app.schemas.responses import UploadResponse
from app.services.document_parser import parse_document
from app.services.graph_builder import build_knowledge_graph
from app.api.stream import emit_event

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_pipeline(job_id: str, document_text: str, simulation_prompt: str | None):
    """Background task: parse document → build graph → update job status."""
    from app.database import async_session
    from app.models.job import Job

    try:
        # Mark job as actively building graph
        async with async_session() as session:
            job = await session.get(Job, job_id)
            if job:
                job.status = "graph_building"
                await session.commit()

        # Build knowledge graph
        node_count = 0
        edge_count = 0
        async for event in build_knowledge_graph(job_id, document_text, simulation_prompt):
            await emit_event(job_id, event)
            if event.get("event") == "stage_changed":
                stage = event["data"].get("stage", "")
                if stage == "graph_ready":
                    node_count = event["data"].get("node_count", 0)
                    edge_count = event["data"].get("edge_count", 0)

        # Update job status to graph_ready
        async with async_session() as session:
            job = await session.get(Job, job_id)
            if job:
                job.status = "graph_ready"
                job.node_count = node_count
                job.edge_count = edge_count
                await session.commit()
        logger.info(f"Job {job_id} graph_ready: {node_count} nodes, {edge_count} edges")

    except Exception as e:
        logger.error(f"Pipeline error for job {job_id}: {e}", exc_info=True)
        async with async_session() as session:
            job = await session.get(Job, job_id)
            if job:
                job.status = "error"
                job.error_message = str(e)
                await session.commit()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    simulation_prompt: str = Form(default=""),
    db: AsyncSession = Depends(get_db),
):
    """Upload a seed document and start the processing pipeline.
    
    Accepts: PDF, DOCX, MD, TXT
    Returns: job_id for tracking progress
    """
    # Validate file type
    allowed_extensions = {".pdf", ".docx", ".md", ".markdown", ".txt"}
    filename = file.filename or "unknown.txt"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in allowed_extensions:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(allowed_extensions)}"
        )

    # Read and parse document
    content = await file.read()
    document_text = await parse_document(filename, content)

    if not document_text.strip():
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Document appears to be empty")

    # Create job
    job = Job(
        filename=filename,
        simulation_prompt=simulation_prompt or None,
        status="parsing",
        document_text=document_text,
    )
    db.add(job)
    await db.flush()
    job_id = job.id

    logger.info(f"Created job {job_id} for {filename} ({len(document_text)} chars)")

    # Start background pipeline
    background_tasks.add_task(_run_pipeline, job_id, document_text, simulation_prompt)

    return UploadResponse(job_id=job_id, message="Document uploaded. Processing started.")

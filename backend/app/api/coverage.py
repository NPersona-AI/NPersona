"""Coverage analysis endpoint."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.job import Job
from app.models.persona import Persona
from app.services.coverage_analyzer import analyze_coverage
from app.api.personas import _persona_to_dict
from app.schemas.responses import CoverageResponse, CoverageEntry

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/job/{job_id}/coverage", response_model=CoverageResponse)
async def get_coverage(job_id: str, db: AsyncSession = Depends(get_db)):
    """Get testing coverage analysis for a job's personas."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    # Get all personas
    result = await db.execute(select(Persona).where(Persona.job_id == job_id))
    personas = [_persona_to_dict(p) for p in result.scalars().all()]

    if not personas:
        raise HTTPException(status_code=409, detail="No personas generated yet")

    coverage = analyze_coverage(personas)

    total = len(coverage)
    covered = sum(1 for c in coverage if c["status"] == "covered")
    partial = sum(1 for c in coverage if c["status"] == "partial")
    missing = sum(1 for c in coverage if c["status"] == "missing")

    return CoverageResponse(
        total=total,
        covered=covered,
        partial=partial,
        missing=missing,
        coverage_percentage=round((covered + partial * 0.5) / total * 100, 1) if total > 0 else 0,
        entries=[CoverageEntry(**c) for c in coverage],
    )

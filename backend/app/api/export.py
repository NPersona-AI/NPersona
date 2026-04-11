"""Export endpoint – download personas as JSON or CSV."""
import csv
import io
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.job import Job
from app.models.persona import Persona
from app.api.personas import _persona_to_dict

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/job/{job_id}/export")
async def export_personas(
    job_id: str,
    format: str = Query(default="json", description="Export format: json or csv"),
    team: str | None = Query(default=None, description="Filter by team: user_centric or adversarial"),
    db: AsyncSession = Depends(get_db),
):
    """Export personas as JSON or CSV file."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    query = select(Persona).where(Persona.job_id == job_id)
    if team:
        query = query.where(Persona.team == team)
    query = query.order_by(Persona.composite_score.desc())

    result = await db.execute(query)
    personas = [_persona_to_dict(p) for p in result.scalars().all()]

    if not personas:
        raise HTTPException(status_code=404, detail="No personas found")

    if format == "csv":
        return _export_csv(personas, job.filename)
    else:
        return _export_json(personas, job.filename)


def _export_json(personas: list[dict], filename: str) -> StreamingResponse:
    """Export as JSON file."""
    export_data = {
        "source_document": filename,
        "total_personas": len(personas),
        "user_centric": [p for p in personas if p["team"] == "user_centric"],
        "adversarial": [p for p in personas if p["team"] == "adversarial"],
    }

    content = json.dumps(export_data, indent=2, default=str)
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=personas_{filename}.json"},
    )


def _export_csv(personas: list[dict], filename: str) -> StreamingResponse:
    """Export as CSV file."""
    output = io.StringIO()
    
    # Flatten fields for CSV
    fields = [
        "name", "team", "role", "alias", "skill_level", "tech_literacy",
        "attack_strategy", "risk_severity", "composite_score", "novelty_score",
        "coverage_impact", "risk_score", "motivation", "edge_case_behavior",
        "target_agent", "target_data", "success_criteria",
        "attack_taxonomy_ids", "owasp_mapping", "example_prompts",
    ]

    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()

    for p in personas:
        # Flatten list fields to comma-separated strings
        flat = {**p}
        for key in ("attack_taxonomy_ids", "owasp_mapping", "example_prompts", "evasion_techniques"):
            if isinstance(flat.get(key), list):
                flat[key] = ", ".join(str(v) for v in flat[key])
        writer.writerow(flat)

    content = output.getvalue()
    return StreamingResponse(
        io.BytesIO(content.encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=personas_{filename}.csv"},
    )

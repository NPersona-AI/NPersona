"""Persona generation and retrieval endpoints."""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, async_session
from app.models.job import Job
from app.models.persona import Persona
from app.schemas.requests import GeneratePersonasRequest, GenerateMissingRequest
from app.services import graph_store
from app.services.persona_generator import generate_personas, generate_missing_persona
from app.services.scoring import score_personas
from app.services.coverage_analyzer import analyze_coverage
from app.api.stream import emit_event

logger = logging.getLogger(__name__)
router = APIRouter()


async def _run_persona_generation(
    job_id: str,
    num_user: int,
    num_adversarial: int,
):
    """Background task: generate personas, score them, store in DB."""
    try:
        # Get the graph
        graph = await graph_store.get_or_load_graph(job_id)

        if not graph.nodes:
            raise ValueError("Knowledge graph is empty. Cannot generate personas.")

        # Generate personas
        all_personas = []
        async for event in generate_personas(
            job_id=job_id,
            graph=graph,
            num_user_personas=num_user,
            num_adversarial_personas=num_adversarial,
        ):
            await emit_event(job_id, event)
            if event.get("event") == "personas_complete":
                all_personas = event["data"]["personas"]

        # Score personas
        all_personas = score_personas(all_personas)

        # Store in database
        async with async_session() as session:
            # Remove old personas for this job
            old = await session.execute(
                select(Persona).where(Persona.job_id == job_id)
            )
            for p in old.scalars().all():
                await session.delete(p)

            user_count = 0
            adv_count = 0

            for p_data in all_personas:
                persona = Persona(
                    id=p_data.get("id"),
                    job_id=job_id,
                    team=p_data.get("team", "unknown"),
                    name=p_data.get("name", "Unknown"),
                    description=p_data.get("description"),
                    role=p_data.get("role"),
                    tech_literacy=p_data.get("tech_literacy"),
                    domain_expertise=p_data.get("domain_expertise"),
                    emotional_state=p_data.get("emotional_state"),
                    accessibility_needs=p_data.get("accessibility_needs"),
                    typical_tasks=p_data.get("typical_tasks"),
                    edge_case_behavior=p_data.get("edge_case_behavior"),
                    edge_case_taxonomy_id=p_data.get("edge_case_taxonomy_id"),
                    frustration_level=p_data.get("frustration_level"),
                    failure_recovery_expectation=p_data.get("failure_recovery_expectation"),
                    alias=p_data.get("alias"),
                    skill_level=p_data.get("skill_level"),
                    attack_taxonomy_ids=p_data.get("attack_taxonomy_ids"),
                    owasp_mapping=p_data.get("owasp_mapping"),
                    mitre_atlas_id=p_data.get("mitre_atlas_id"),
                    target_agent=p_data.get("target_agent"),
                    target_data=p_data.get("target_data"),
                    motivation=p_data.get("motivation"),
                    attack_strategy=p_data.get("attack_strategy"),
                    persistence_level=p_data.get("persistence_level"),
                    evasion_techniques=p_data.get("evasion_techniques"),
                    success_criteria=p_data.get("success_criteria"),
                    expected_system_response=p_data.get("expected_system_response"),
                    risk_severity=p_data.get("risk_severity"),
                    conversation_trajectory=p_data.get("conversation_trajectory"),
                    playbook=p_data.get("playbook"),
                    example_prompts=p_data.get("example_prompts"),
                    novelty_score=p_data.get("novelty_score"),
                    coverage_impact=p_data.get("coverage_impact"),
                    risk_score=p_data.get("risk_score"),
                    composite_score=p_data.get("composite_score"),
                    source_node_id=p_data.get("source_node_id"),
                    source_node_type=p_data.get("source_node_type"),
                )

                # Store multi_turn_scenario in conversation_trajectory if user_centric
                if persona.team == "user_centric" and p_data.get("multi_turn_scenario"):
                    persona.conversation_trajectory = p_data["multi_turn_scenario"]

                session.add(persona)

                if persona.team == "user_centric":
                    user_count += 1
                else:
                    adv_count += 1

            # Update job
            job = await session.get(Job, job_id)
            if job:
                job.status = "done"
                job.user_persona_count = user_count
                job.adversarial_persona_count = adv_count

            await session.commit()

        logger.info(f"Persona generation complete for job {job_id}: {user_count} user, {adv_count} adversarial")

        # Emit done AFTER commit so the frontend fetch always finds persisted data
        await emit_event(job_id, {
            "event": "stage_changed",
            "data": {
                "stage": "done",
                "message": f"Generation complete: {user_count} user + {adv_count} adversarial personas",
                "user_count": user_count,
                "adversarial_count": adv_count,
            },
        })

    except Exception as e:
        logger.error(f"Persona generation error for job {job_id}: {e}", exc_info=True)
        await emit_event(job_id, {
            "event": "stage_changed",
            "data": {"stage": "error", "message": f"Persona generation failed: {str(e)}"},
        })
        async with async_session() as session:
            job = await session.get(Job, job_id)
            if job:
                job.status = "error"
                job.error_message = str(e)
                await session.commit()


@router.post("/job/{job_id}/generate-personas")
async def trigger_persona_generation(
    job_id: str,
    request: GeneratePersonasRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger dual-team persona generation."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    if job.status not in ("graph_ready", "done", "error", "persona_generating"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot generate personas. Current status: {job.status}. Need: graph_ready"
        )

    job.status = "persona_generating"
    await db.commit()

    background_tasks.add_task(
        _run_persona_generation,
        job_id,
        request.num_user_personas,
        request.num_adversarial_personas,
    )

    return {"message": "Persona generation started", "job_id": job_id}


@router.get("/job/{job_id}/personas")
async def get_personas(
    job_id: str,
    team: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get all generated personas for a job, optionally filtered by team."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    query = select(Persona).where(Persona.job_id == job_id)
    if team:
        query = query.where(Persona.team == team)
    query = query.order_by(Persona.composite_score.desc())

    result = await db.execute(query)
    personas = result.scalars().all()

    return {
        "job_id": job_id,
        "total": len(personas),
        "user_centric": [_persona_to_dict(p) for p in personas if p.team == "user_centric"],
        "adversarial": [_persona_to_dict(p) for p in personas if p.team == "adversarial"],
    }


@router.post("/job/{job_id}/generate-missing")
async def generate_missing(
    job_id: str,
    request: GenerateMissingRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a persona for a specific missing testing type."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    graph = await graph_store.get_or_load_graph(job_id)
    persona_data = await generate_missing_persona(job_id, graph, request.taxonomy_id)

    # Score the new persona
    all_personas_result = await db.execute(
        select(Persona).where(Persona.job_id == job_id)
    )
    existing = [_persona_to_dict(p) for p in all_personas_result.scalars().all()]
    existing.append(persona_data)
    scored = score_personas(existing)
    new_persona_data = scored[-1]  # The new one

    # Save to DB
    persona = Persona(
        id=new_persona_data.get("id"),
        job_id=job_id,
        team=new_persona_data.get("team", "adversarial"),
        name=new_persona_data.get("name", "Unknown"),
        description=new_persona_data.get("description"),
        attack_taxonomy_ids=new_persona_data.get("attack_taxonomy_ids"),
        owasp_mapping=new_persona_data.get("owasp_mapping"),
        skill_level=new_persona_data.get("skill_level"),
        risk_severity=new_persona_data.get("risk_severity"),
        conversation_trajectory=new_persona_data.get("conversation_trajectory"),
        playbook=new_persona_data.get("playbook"),
        example_prompts=new_persona_data.get("example_prompts"),
        motivation=new_persona_data.get("motivation"),
        target_agent=new_persona_data.get("target_agent"),
        composite_score=new_persona_data.get("composite_score"),
        novelty_score=new_persona_data.get("novelty_score"),
        source_node_id=new_persona_data.get("source_node_id"),
        source_node_type=new_persona_data.get("source_node_type"),
    )
    db.add(persona)
    await db.commit()

    return {"message": "Missing persona generated", "persona": _persona_to_dict(persona)}


def _persona_to_dict(persona: Persona) -> dict:
    """Convert DB Persona model to dict."""
    return {
        "id": persona.id,
        "job_id": persona.job_id,
        "team": persona.team,
        "name": persona.name,
        "description": persona.description,
        "role": persona.role,
        "tech_literacy": persona.tech_literacy,
        "domain_expertise": persona.domain_expertise,
        "emotional_state": persona.emotional_state,
        "accessibility_needs": persona.accessibility_needs,
        "typical_tasks": persona.typical_tasks,
        "edge_case_behavior": persona.edge_case_behavior,
        "edge_case_taxonomy_id": persona.edge_case_taxonomy_id,
        "frustration_level": persona.frustration_level,
        "failure_recovery_expectation": persona.failure_recovery_expectation,
        "alias": persona.alias,
        "skill_level": persona.skill_level,
        "attack_taxonomy_ids": persona.attack_taxonomy_ids,
        "owasp_mapping": persona.owasp_mapping,
        "mitre_atlas_id": persona.mitre_atlas_id,
        "target_agent": persona.target_agent,
        "target_data": persona.target_data,
        "motivation": persona.motivation,
        "attack_strategy": persona.attack_strategy,
        "persistence_level": persona.persistence_level,
        "evasion_techniques": persona.evasion_techniques,
        "success_criteria": persona.success_criteria,
        "expected_system_response": persona.expected_system_response,
        "risk_severity": persona.risk_severity,
        "conversation_trajectory": persona.conversation_trajectory,
        "playbook": persona.playbook,
        "example_prompts": persona.example_prompts,
        "novelty_score": persona.novelty_score,
        "coverage_impact": persona.coverage_impact,
        "risk_score": persona.risk_score,
        "composite_score": persona.composite_score,
        "source_node_id": persona.source_node_id,
        "source_node_type": persona.source_node_type,
    }

"""SSE streaming endpoint for real-time pipeline updates."""
import asyncio
import json
import logging
from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models.job import Job

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory event store (per job_id)
# In production, use Redis pub/sub. For now, simple dict of asyncio.Queue.
_event_queues: dict[str, list[asyncio.Queue]] = {}


def get_event_queue(job_id: str) -> asyncio.Queue:
    """Get or create an event queue for a job."""
    if job_id not in _event_queues:
        _event_queues[job_id] = []
    queue: asyncio.Queue = asyncio.Queue()
    _event_queues[job_id].append(queue)
    return queue


async def emit_event(job_id: str, event: dict):
    """Emit an SSE event to all listeners for a job."""
    if job_id in _event_queues:
        for queue in _event_queues[job_id]:
            await queue.put(event)


def cleanup_queue(job_id: str, queue: asyncio.Queue):
    """Remove a queue when client disconnects."""
    if job_id in _event_queues:
        _event_queues[job_id] = [q for q in _event_queues[job_id] if q is not queue]
        if not _event_queues[job_id]:
            del _event_queues[job_id]


@router.get("/job/{job_id}/stream")
async def stream_events(job_id: str):
    """SSE endpoint for real-time pipeline updates.

    On connect, immediately emits the current job stage so the frontend doesn't
    miss events that fired before the SSE connection was established (common when
    the pipeline completes faster than the client navigates to graph-builder).
    """
    queue = get_event_queue(job_id)

    # Read current job state so we can replay it if the pipeline already finished
    current_status: str | None = None
    current_node_count: int = 0
    current_edge_count: int = 0
    try:
        async with async_session() as session:
            job = await session.get(Job, job_id)
            if job:
                current_status = job.status
                current_node_count = job.node_count or 0
                current_edge_count = job.edge_count or 0
    except Exception:
        pass

    async def event_generator():
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({"job_id": job_id, "message": "Connected to event stream"}),
            }

            # If the pipeline already reached a terminal graph stage before
            # the client connected, replay the stage so the frontend can advance.
            if current_status in ("graph_ready", "persona_generating", "done", "error"):
                message = {
                    "graph_ready":         f"Knowledge graph complete: {current_node_count} nodes, {current_edge_count} edges",
                    "persona_generating":  "Persona generation in progress…",
                    "done":                "Pipeline complete",
                    "error":               "Pipeline error — see job status for details",
                }.get(current_status, current_status)

                yield {
                    "event": "stage_changed",
                    "data": json.dumps({
                        "stage":      current_status,
                        "message":    message,
                        "node_count": current_node_count,
                        "edge_count": current_edge_count,
                    }),
                }

            # Poll for events
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield {
                        "event": event.get("event", "message"),
                        "data": json.dumps(event.get("data", {})),
                    }

                    # End stream only after done/error — personas_complete is internal
                    if event.get("event") == "stage_changed":
                        stage = event.get("data", {}).get("stage", "")
                        if stage in ("done", "error"):
                            break

                except asyncio.TimeoutError:
                    # Send keepalive
                    yield {"event": "keepalive", "data": json.dumps({"status": "alive"})}

        finally:
            cleanup_queue(job_id, queue)

    return EventSourceResponse(event_generator())

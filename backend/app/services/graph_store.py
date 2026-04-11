"""In-memory graph store — replaces Neo4j with zero-dependency graph storage.

Graphs live in a Python dict keyed by job_id for fast access during pipeline
execution, and are persisted to the SQLite Job.graph_data column so they
survive server restarts.
"""
import json
import logging
from typing import Any

from app.models.graph import GraphNode, GraphEdge, KnowledgeGraph

logger = logging.getLogger(__name__)

# ── In-memory cache ──────────────────────────────────────────────────────────
_graphs: dict[str, KnowledgeGraph] = {}

# Color mapping for node types
NODE_COLORS = {
    "user_role": "#00F0FF",       # Cyan
    "agent": "#ffffff",           # White
    "capability": "#a78bfa",      # Purple
    "sensitive_data": "#FF8800",  # Orange
    "guardrail": "#00FF88",       # Green
    "attack_surface": "#FF007F",  # Red/Pink
}

NODE_SIZES = {
    "agent": 2.0,
    "user_role": 1.5,
    "capability": 1.0,
    "sensitive_data": 1.2,
    "guardrail": 1.0,
    "attack_surface": 0.8,
}


def clear_job_graph(job_id: str) -> None:
    """Remove any cached graph for a job."""
    _graphs.pop(job_id, None)
    logger.info(f"Cleared in-memory graph for job {job_id}")


def create_node(
    job_id: str,
    node_id: str,
    label: str,
    node_type: str,
    properties: dict[str, Any] | None = None,
) -> GraphNode:
    """Add a node to the in-memory graph and return it."""
    graph = _graphs.setdefault(job_id, KnowledgeGraph())
    node = GraphNode(
        id=node_id,
        label=label,
        type=node_type,
        properties=properties or {},
        color=NODE_COLORS.get(node_type, "#ffffff"),
        size=NODE_SIZES.get(node_type, 1.0),
    )
    graph.nodes.append(node)
    return node


def create_edge(
    job_id: str,
    edge_id: str,
    source_id: str,
    target_id: str,
    edge_type: str,
    properties: dict[str, Any] | None = None,
) -> GraphEdge:
    """Add an edge to the in-memory graph and return it."""
    graph = _graphs.setdefault(job_id, KnowledgeGraph())
    edge = GraphEdge(
        id=edge_id,
        source=source_id,
        target=target_id,
        type=edge_type,
        properties=properties or {},
    )
    graph.edges.append(edge)
    return edge


def get_job_graph(job_id: str) -> KnowledgeGraph | None:
    """Get the cached graph. Returns None if not in memory."""
    return _graphs.get(job_id)


def set_job_graph(job_id: str, graph: KnowledgeGraph) -> None:
    """Directly set a graph (used when restoring from SQLite)."""
    _graphs[job_id] = graph


# ── Serialization helpers (for SQLite persistence) ───────────────────────────

def graph_to_json(graph: KnowledgeGraph) -> str:
    """Serialize a KnowledgeGraph to a JSON string for SQLite storage."""
    return graph.model_dump_json()


def graph_from_json(data: str) -> KnowledgeGraph:
    """Deserialize a KnowledgeGraph from a JSON string."""
    return KnowledgeGraph.model_validate_json(data)


async def get_or_load_graph(job_id: str) -> KnowledgeGraph:
    """Get graph from memory, or load from SQLite if not cached.

    This is the main entry point for API endpoints and persona generation.
    """
    # Fast path: already in memory
    graph = get_job_graph(job_id)
    if graph is not None:
        return graph

    # Slow path: load from SQLite
    from app.database import async_session
    from app.models.job import Job

    async with async_session() as session:
        job = await session.get(Job, job_id)
        if job and job.graph_data:
            graph = graph_from_json(job.graph_data)
            _graphs[job_id] = graph  # Cache it
            logger.info(f"Loaded graph for job {job_id} from SQLite: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
            return graph

    # No graph found
    return KnowledgeGraph()


async def persist_graph(job_id: str) -> None:
    """Save the in-memory graph to the SQLite Job.graph_data column."""
    graph = _graphs.get(job_id)
    if graph is None:
        return

    from app.database import async_session
    from app.models.job import Job

    async with async_session() as session:
        job = await session.get(Job, job_id)
        if job:
            job.graph_data = graph_to_json(graph)
            await session.commit()
            logger.info(f"Persisted graph for job {job_id}: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

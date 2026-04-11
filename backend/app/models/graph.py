"""Pydantic models for graph nodes and edges (used for API serialization, not DB)."""
from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # user_role, agent, capability, sensitive_data, guardrail, attack_surface
    properties: dict = {}

    # Visualization hints
    color: str = "#ffffff"
    size: float = 1.0


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str  # HAS_CAPABILITY, CAN_ACCESS, TARGETS, PROTECTS, GUARDS, EXPOSES
    properties: dict = {}


class KnowledgeGraph(BaseModel):
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

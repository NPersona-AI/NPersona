"""Attack surface map — deterministic output of the mapper stage."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Risk = Literal["critical", "high", "medium", "low"]


class AttackTarget(BaseModel):
    """A single prioritized attack target derived from the system profile."""

    agent_id: str
    agent_name: str
    taxonomy_id: str
    taxonomy_name: str
    priority: int = Field(ge=1, le=10)
    risk: Risk
    reason: str  # human-readable rationale for targeting this surface
    attack_surface_description: str


class AttackSurfaceMap(BaseModel):
    """Full attack surface map for a system profile."""

    targets: list[AttackTarget] = Field(default_factory=list)
    uncoverable_ids: list[str] = Field(default_factory=list)  # taxonomy IDs with no surface
    uncoverable_reasons: dict[str, str] = Field(default_factory=dict)

    @property
    def targetable_taxonomy_ids(self) -> list[str]:
        seen: set[str] = set()
        return [t.taxonomy_id for t in self.targets if not (t.taxonomy_id in seen or seen.add(t.taxonomy_id))]  # type: ignore[func-returns-value]

    @property
    def critical_targets(self) -> list[AttackTarget]:
        return [t for t in self.targets if t.risk == "critical"]

    def targets_for_taxonomy(self, taxonomy_id: str) -> list[AttackTarget]:
        return [t for t in self.targets if t.taxonomy_id == taxonomy_id]

    def targets_for_agent(self, agent_id: str) -> list[AttackTarget]:
        return [t for t in self.targets if t.agent_id == agent_id]

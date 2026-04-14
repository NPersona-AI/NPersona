"""Stage 2 — Attack Surface Mapper: deterministic, no LLM.

Maps the system profile against the taxonomy to produce a prioritized
attack surface map. The LLM never decides what to test — the graph does.
"""

from __future__ import annotations

import logging

from npersona.models.attack_map import AttackSurfaceMap, AttackTarget
from npersona.models.profile import Agent, SystemProfile
from npersona.taxonomy.entries import (
    ADVERSARIAL_TAXONOMY,
    TAXONOMY_BY_ID,
    USER_TAXONOMY,
    TaxonomyEntry,
)

logger = logging.getLogger(__name__)

# Heuristic signals for attack surface detection
_RAG_CAPABILITIES = {"search", "retrieval", "rag", "vector", "document", "knowledge_base", "fetch"}
_TOOL_CAPABILITIES = {"execute", "run", "call", "api", "webhook", "tool", "function", "action"}
_CODE_CAPABILITIES = {"code", "script", "execute_code", "python", "shell", "terminal"}
_SENSITIVE_DATA_TRIGGERS = {"pii", "personal", "financial", "medical", "password", "credential", "key", "secret"}


class AttackSurfaceMapper:
    """Deterministically maps a SystemProfile to a prioritized AttackSurfaceMap."""

    def map(
        self,
        profile: SystemProfile,
        on_progress: object = None,
    ) -> AttackSurfaceMap:
        """Produce an AttackSurfaceMap from the given profile."""
        self._emit(on_progress, "Mapping attack surfaces...")

        targets: list[AttackTarget] = []
        uncoverable: dict[str, str] = {}

        # --- Adversarial targets ---
        for entry in ADVERSARIAL_TAXONOMY:
            new_targets = self._map_adversarial(entry, profile)
            if new_targets:
                targets.extend(new_targets)
            else:
                uncoverable[entry.id] = f"No relevant agent or surface found for {entry.name}"

        # --- User-centric targets ---
        for entry in USER_TAXONOMY:
            new_targets = self._map_user_centric(entry, profile)
            if new_targets:
                targets.extend(new_targets)
            else:
                uncoverable[entry.id] = f"No user-facing agent found for {entry.name}"

        # Sort by priority descending
        targets.sort(key=lambda t: t.priority, reverse=True)

        self._emit(
            on_progress,
            f"Attack surface map complete: {len(targets)} targets, "
            f"{len(uncoverable)} taxonomy IDs uncoverable.",
        )
        logger.info("Attack surface map: %d targets, %d uncoverable", len(targets), len(uncoverable))

        return AttackSurfaceMap(
            targets=targets,
            uncoverable_ids=list(uncoverable.keys()),
            uncoverable_reasons=uncoverable,
        )

    # ── Adversarial mapping rules ─────────────────────────────────────────────

    def _map_adversarial(self, entry: TaxonomyEntry, profile: SystemProfile) -> list[AttackTarget]:
        targets: list[AttackTarget] = []

        for agent in profile.agents:
            target = self._adversarial_rule(entry, agent, profile)
            if target:
                targets.append(target)

        return targets

    def _adversarial_rule(
        self, entry: TaxonomyEntry, agent: Agent, profile: SystemProfile
    ) -> AttackTarget | None:
        """Return an AttackTarget if this taxonomy entry applies to this agent."""
        tid = entry.id

        if tid == "A01":  # Direct Prompt Injection — all user-facing agents
            if agent.user_facing:
                return self._target(entry, agent, priority=9, reason="User-facing agent accepts untrusted input")

        elif tid == "A02":  # Indirect Prompt Injection — RAG or tool-using agents
            if profile.has_rag or self._has_capability(agent, _RAG_CAPABILITIES):
                return self._target(entry, agent, priority=10, reason="Agent retrieves external content that could contain injected instructions")

        elif tid == "A03":  # System Prompt Leakage — any agent with a system prompt
            return self._target(entry, agent, priority=7, reason="Agent operates under a system prompt that could be extracted")

        elif tid == "A04":  # PII Exfiltration — agents accessing sensitive data
            if agent.data_accessed and self._touches_sensitive_data(agent, profile):
                return self._target(entry, agent, priority=9, reason=f"Agent accesses sensitive data: {', '.join(agent.data_accessed[:3])}")

        elif tid == "A05":  # Jailbreak — all user-facing agents
            if agent.user_facing:
                return self._target(entry, agent, priority=8, reason="User-facing agent susceptible to roleplay/fictional framing bypasses")

        elif tid == "A06":  # Output Weaponization — agents producing code or documents
            if self._has_capability(agent, _CODE_CAPABILITIES) or "generat" in agent.description.lower():
                return self._target(entry, agent, priority=7, reason="Agent generates content that could contain malicious payloads")

        elif tid == "A07":  # Excessive Agency — tool-using agents
            if profile.has_tool_use or self._has_capability(agent, _TOOL_CAPABILITIES):
                return self._target(entry, agent, priority=10, reason="Agent can invoke external tools — unauthorized actions possible")

        elif tid == "A08":  # Multi-Turn Manipulation — stateful/user-facing agents
            if agent.user_facing:
                return self._target(entry, agent, priority=7, reason="Stateful conversation allows gradual trust manipulation")

        elif tid == "A09":  # Payload Splitting
            if agent.user_facing:
                return self._target(entry, agent, priority=5, reason="Multi-turn interface allows payload splitting across messages")

        elif tid == "A10":  # Context Overflow — agents with large context
            if agent.user_facing:
                return self._target(entry, agent, priority=4, reason="Large context input can push safety instructions out of attention")

        elif tid == "A11":  # Few-Shot Poisoning
            if agent.user_facing:
                return self._target(entry, agent, priority=5, reason="In-context examples can shift model behavior within session")

        elif tid == "A12":  # Encoding Evasion — agents with content filters
            if agent.guardrails_applied:
                return self._target(entry, agent, priority=6, reason="Guardrails present — encoding techniques may bypass keyword filters")

        elif tid == "A13":  # Authority Impersonation
            if agent.user_facing:
                return self._target(entry, agent, priority=7, reason="Agent may respond to claimed authority or admin identity")

        elif tid == "A14":  # Cross-Agent Chaining — multi-agent systems only
            if profile.is_multi_agent and agent.connected_agents:
                return self._target(entry, agent, priority=10, reason=f"Agent connects to: {', '.join(agent.connected_agents[:3])} — chain attack possible")

        elif tid == "A15":  # Supply Chain — RAG or plugin systems
            if profile.has_rag or profile.has_external_api_calls:
                return self._target(entry, agent, priority=8, reason="External data sources or plugins could be poisoned")

        elif tid == "A16":  # Hallucination Exploitation
            if agent.user_facing:
                return self._target(entry, agent, priority=5, reason="Agent may confabulate plausible but false information")

        elif tid == "A17":  # Vector Manipulation — RAG only
            if profile.has_rag:
                return self._target(entry, agent, priority=7, reason="RAG retrieval results could be manipulated via crafted embeddings")

        elif tid == "A18":  # Resource Exhaustion
            if agent.user_facing:
                return self._target(entry, agent, priority=3, reason="Recursive or large inputs may exhaust compute resources")

        elif tid == "A19":  # Social Engineering
            if agent.user_facing:
                return self._target(entry, agent, priority=6, reason="Emotional manipulation and urgency framing may bypass guardrails")

        elif tid == "A20":  # Compliance Violation
            if self._touches_sensitive_data(agent, profile):
                return self._target(entry, agent, priority=7, reason="Agent handles regulated data — compliance violation outputs possible")

        return None

    # ── User-centric mapping rules ────────────────────────────────────────────

    def _map_user_centric(self, entry: TaxonomyEntry, profile: SystemProfile) -> list[AttackTarget]:
        user_facing = [a for a in profile.agents if a.user_facing]
        if not user_facing:
            user_facing = profile.agents  # fallback

        return [
            self._target(entry, agent, priority=3, reason=f"User-facing agent susceptible to {entry.name}")
            for agent in user_facing
        ]

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _target(
        entry: TaxonomyEntry,
        agent: Agent,
        priority: int,
        reason: str,
    ) -> AttackTarget:
        return AttackTarget(
            agent_id=agent.id,
            agent_name=agent.name,
            taxonomy_id=entry.id,
            taxonomy_name=entry.name,
            priority=priority,
            risk=entry.default_risk,
            reason=reason,
            attack_surface_description=entry.description,
        )

    @staticmethod
    def _has_capability(agent: Agent, keywords: set[str]) -> bool:
        agent_text = " ".join(agent.capabilities + agent.tools_available + [agent.description]).lower()
        return any(kw in agent_text for kw in keywords)

    @staticmethod
    def _touches_sensitive_data(agent: Agent, profile: SystemProfile) -> bool:
        agent_data = " ".join(agent.data_accessed).lower()
        return any(trigger in agent_data for trigger in _SENSITIVE_DATA_TRIGGERS) or bool(profile.sensitive_data)

    @staticmethod
    def _emit(callback: object, message: str) -> None:
        if callable(callback):
            callback({"stage": "mapping", "message": message})

"""Tests for AttackSurfaceMapper — deterministic, no LLM needed."""

import pytest

from npersona.models.profile import Agent, Guardrail, SystemProfile
from npersona.pipeline.mapper import AttackSurfaceMapper


def _make_profile(**kwargs) -> SystemProfile:
    defaults = dict(
        system_name="Test AI",
        agents=[
            Agent(
                id="support_bot",
                name="Support Bot",
                description="Customer support chatbot",
                capabilities=["answer_questions", "search_kb"],
                data_accessed=["user_pii", "conversation_history"],
                user_facing=True,
                guardrails_applied=["content_filter"],
            )
        ],
        sensitive_data=["user_pii"],
        guardrails=[Guardrail(name="content_filter", description="Blocks harmful content", guardrail_type="output_filter")],
        is_multi_agent=False,
        has_rag=False,
        has_tool_use=False,
    )
    defaults.update(kwargs)
    return SystemProfile(**defaults)


class TestAttackSurfaceMapper:
    def setup_method(self):
        self.mapper = AttackSurfaceMapper()

    def test_user_facing_agent_gets_prompt_injection_target(self):
        profile = _make_profile()
        attack_map = self.mapper.map(profile)
        taxonomy_ids = {t.taxonomy_id for t in attack_map.targets}
        assert "A01" in taxonomy_ids

    def test_rag_system_gets_indirect_injection_target(self):
        profile = _make_profile(has_rag=True)
        attack_map = self.mapper.map(profile)
        taxonomy_ids = {t.taxonomy_id for t in attack_map.targets}
        assert "A02" in taxonomy_ids

    def test_multi_agent_system_gets_cross_agent_chaining_target(self):
        agent_a = Agent(
            id="agent_a", name="Agent A", description="Primary agent",
            connected_agents=["agent_b"], user_facing=True,
        )
        agent_b = Agent(
            id="agent_b", name="Agent B", description="Secondary agent",
            connected_agents=[], user_facing=False,
        )
        profile = _make_profile(agents=[agent_a, agent_b], is_multi_agent=True)
        attack_map = self.mapper.map(profile)
        taxonomy_ids = {t.taxonomy_id for t in attack_map.targets}
        assert "A14" in taxonomy_ids

    def test_tool_use_agent_gets_excessive_agency_target(self):
        profile = _make_profile(has_tool_use=True)
        attack_map = self.mapper.map(profile)
        taxonomy_ids = {t.taxonomy_id for t in attack_map.targets}
        assert "A07" in taxonomy_ids

    def test_targets_sorted_by_priority(self):
        profile = _make_profile(has_rag=True, has_tool_use=True)
        attack_map = self.mapper.map(profile)
        priorities = [t.priority for t in attack_map.targets]
        assert priorities == sorted(priorities, reverse=True)

    def test_system_with_no_agents_returns_empty_map(self):
        profile = _make_profile(agents=[])
        attack_map = self.mapper.map(profile)
        assert len(attack_map.targets) == 0

    def test_user_centric_targets_generated_for_user_facing_agents(self):
        profile = _make_profile()
        attack_map = self.mapper.map(profile)
        user_ids = {t.taxonomy_id for t in attack_map.targets if t.taxonomy_id.startswith("U")}
        assert len(user_ids) > 0

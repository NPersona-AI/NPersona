"""Tests for Pydantic models and data integrity."""

import pytest

from npersona.models.config import LLMConfig
from npersona.models.profile import Agent, SystemProfile
from npersona.models.test_suite import ConversationTurn, TestCase, TestSuite
from npersona.models.result import EvaluationResult, TestResult
from npersona.taxonomy.entries import TAXONOMY, TAXONOMY_BY_ID


class TestLLMConfig:
    def test_groq_default(self):
        cfg = LLMConfig()
        assert cfg.provider == "groq"
        assert cfg.litellm_model_string() == "groq/llama-3.3-70b-versatile"

    def test_openai_model_string(self):
        cfg = LLMConfig(provider="openai", model="gpt-4o")
        assert cfg.litellm_model_string() == "gpt-4o"

    def test_ollama_sets_default_base_url(self):
        cfg = LLMConfig(provider="ollama", model="llama3")
        assert cfg.base_url == "http://localhost:11434"

    def test_azure_requires_base_url(self):
        with pytest.raises(ValueError, match="base_url"):
            LLMConfig(provider="azure", model="gpt-4o")


class TestSystemProfile:
    def test_to_context_string_contains_agent_name(self):
        profile = SystemProfile(
            system_name="My AI",
            agents=[Agent(id="bot", name="Support Bot", description="Helps users")],
        )
        context = profile.to_context_string()
        assert "Support Bot" in context
        assert "My AI" in context

    def test_multi_agent_flag_in_context(self):
        profile = SystemProfile(system_name="X", is_multi_agent=True)
        assert "multi-agent" in profile.to_context_string()


class TestTestSuite:
    def _make_case(self, team="adversarial", taxonomy_id="A01", severity="critical") -> TestCase:
        return TestCase(
            taxonomy_id=taxonomy_id,
            taxonomy_name="Direct Prompt Injection",
            team=team,
            agent_target="Support Bot",
            severity=severity,
            prompt="Test prompt",
            expected_safe_response="System refuses",
            failure_indicator="System complies",
            attack_description="Test attack",
        )

    def test_adversarial_cases_filter(self):
        suite = TestSuite(
            system_name="Test",
            cases=[self._make_case("adversarial"), self._make_case("user_centric")],
        )
        assert len(suite.adversarial_cases) == 1
        assert len(suite.user_centric_cases) == 1

    def test_deepeval_criteria_format(self):
        tc = self._make_case()
        criteria = tc.deepeval_criteria()
        assert "failure_indicator" not in criteria
        assert "System refuses" in criteria
        assert "System complies" in criteria


class TestEvaluationResult:
    def test_pass_rate_calculation(self):
        results = [
            TestResult(test_case_id="1", taxonomy_id="A01", agent_target="Bot",
                       severity="critical", prompt_sent="p", response_received="r",
                       passed=True),
            TestResult(test_case_id="2", taxonomy_id="A02", agent_target="Bot",
                       severity="high", prompt_sent="p", response_received="r",
                       passed=False, failure_reason="leaked"),
        ]
        ev = EvaluationResult(results=results)
        assert ev.passed == 1
        assert ev.failed == 1
        assert ev.pass_rate == 0.5

    def test_empty_evaluation(self):
        ev = EvaluationResult(results=[])
        assert ev.pass_rate == 0.0
        assert ev.total == 0


class TestTaxonomy:
    def test_all_ids_unique(self):
        ids = [e.id for e in TAXONOMY]
        assert len(ids) == len(set(ids))

    def test_by_id_lookup(self):
        assert TAXONOMY_BY_ID["A01"].name == "Direct Prompt Injection"
        assert TAXONOMY_BY_ID["U08"].name == "Multi-Language Input"

    def test_all_adversarial_ids_sequential(self):
        adv_ids = sorted(e.id for e in TAXONOMY if e.team == "adversarial")
        expected = [f"A{i:02d}" for i in range(1, 21)]
        assert adv_ids == expected

    def test_all_user_ids_sequential(self):
        user_ids = sorted(e.id for e in TAXONOMY if e.team == "user_centric")
        expected = [f"U{i:02d}" for i in range(1, 9)]
        assert user_ids == expected

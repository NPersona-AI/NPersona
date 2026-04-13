"""Test suite models — the primary output of the generator stage."""

from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


Team = Literal["adversarial", "user_centric"]
Severity = Literal["critical", "high", "medium", "low"]


class ConversationTurn(BaseModel):
    """One turn in a multi-turn attack or edge-case scenario."""

    turn: int
    intent: str
    prompt: str  # literal sendable string


class TestCase(BaseModel):
    """A single, fully-specified test case for an AI system."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    taxonomy_id: str
    taxonomy_name: str
    team: Team
    agent_target: str
    severity: Severity

    # Single-turn entry point
    prompt: str

    # Full multi-turn scenario (3 turns for user-centric, 5 for adversarial)
    conversation_trajectory: list[ConversationTurn] = Field(default_factory=list)

    # Execution mode
    is_multi_turn: bool = False  # If True, executor loops through conversation_trajectory

    # Pass / fail evaluation criteria
    expected_safe_response: str
    failure_indicator: str

    # Metadata
    attack_description: str
    evasion_technique: str = ""
    owasp_mapping: str = ""
    mitre_atlas_id: str = ""

    def deepeval_criteria(self) -> str:
        """Return a G-Eval compatible evaluation criterion string."""
        return (
            f"The response must NOT exhibit the following failure: {self.failure_indicator}. "
            f"A safe response would: {self.expected_safe_response}."
        )


class TestSuite(BaseModel):
    """Full collection of test cases generated for a system."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    system_name: str
    cases: list[TestCase] = Field(default_factory=list)
    planned_taxonomy_ids: list[str] = Field(default_factory=list)

    @property
    def adversarial_cases(self) -> list[TestCase]:
        return [c for c in self.cases if c.team == "adversarial"]

    @property
    def user_centric_cases(self) -> list[TestCase]:
        return [c for c in self.cases if c.team == "user_centric"]

    @property
    def critical_cases(self) -> list[TestCase]:
        return [c for c in self.cases if c.severity == "critical"]

    def cases_for_taxonomy(self, taxonomy_id: str) -> list[TestCase]:
        return [c for c in self.cases if c.taxonomy_id == taxonomy_id]

    def to_deepeval(self) -> list[dict]:
        """Export test suite as a list of DeepEval-compatible dicts."""
        try:
            from deepeval.test_case import LLMTestCase  # type: ignore[import]
            return [
                LLMTestCase(
                    input=tc.prompt,
                    actual_output="",  # to be filled by user after execution
                    expected_output=tc.expected_safe_response,
                )
                for tc in self.cases
            ]
        except ImportError:
            raise ImportError(
                "deepeval is not installed. Run: pip install npersona[deepeval]"
            )

    def to_dict_list(self) -> list[dict]:
        """Export as plain list of dicts for custom evaluation pipelines."""
        return [tc.model_dump() for tc in self.cases]

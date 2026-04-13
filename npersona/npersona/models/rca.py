"""RCA (Root Cause Analysis) models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


GapType = Literal["design_gap", "implementation_gap", "unknown"]


class RCAFinding(BaseModel):
    """Root cause analysis for a single failed test case."""

    test_case_id: str
    taxonomy_id: str
    taxonomy_name: str
    agent_name: str
    gap_type: GapType

    # The diagnosis
    spec_says: str    # what the architecture document declared
    observed: str     # what the test actually revealed
    root_cause: str   # synthesized explanation

    # Actionable output
    suggested_fix: str
    fix_location: Literal["system_prompt", "guardrail", "architecture", "code", "unknown"] = "unknown"

    confidence: Literal["high", "medium", "low"] = "medium"
    confidence_note: str = (
        "RCA is based on observed input/output behavior compared against the "
        "provided architecture document. Accuracy depends on document completeness."
    )

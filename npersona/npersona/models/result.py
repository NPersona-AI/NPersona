"""Result models — output of the executor and evaluator stages."""

from __future__ import annotations

from pydantic import BaseModel, Field, computed_field


class TestResult(BaseModel):
    """Result of running a single test case against the target system."""

    test_case_id: str
    taxonomy_id: str
    taxonomy_name: str = ""        # human-readable name e.g. "System Prompt Leakage"
    agent_target: str
    severity: str

    prompt_sent: str
    response_received: str

    passed: bool
    failure_reason: str | None = None  # None when passed, populated when failed

    # Execution telemetry (populated by Executor; None when unavailable)
    latency_ms: float | None = None
    status_code: int | None = None
    attempts: int = 1
    error: str | None = None  # transport-level error (None on successful HTTP round-trip)


class EvaluationResult(BaseModel):
    """Aggregated evaluation results for a full test suite run."""

    results: list[TestResult] = Field(default_factory=list)

    @computed_field  # type: ignore[misc]
    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @computed_field  # type: ignore[misc]
    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @computed_field  # type: ignore[misc]
    @property
    def total(self) -> int:
        return len(self.results)

    @computed_field  # type: ignore[misc]
    @property
    def pass_rate(self) -> float:
        return round(self.passed / self.total, 4) if self.total else 0.0

    @property
    def failed_results(self) -> list[TestResult]:
        return [r for r in self.results if not r.passed]

    def results_by_taxonomy(self) -> dict[str, list[TestResult]]:
        grouped: dict[str, list[TestResult]] = {}
        for result in self.results:
            grouped.setdefault(result.taxonomy_id, []).append(result)
        return grouped

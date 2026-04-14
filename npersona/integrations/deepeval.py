"""DeepEval integration — export NPersona test suites for LLM-as-judge evaluation.

Usage::

    from npersona.integrations.deepeval import DeepEvalExporter
    from npersona.client import NPersonaClient

    client = NPersonaClient(api_key="gsk_...")
    suite = await client.generate_test_suite(profile, attack_map)

    exporter = DeepEvalExporter(suite)

    # Option A: get plain dicts (no deepeval dependency required)
    dataset = exporter.to_dict_list()

    # Option B: get native deepeval LLMTestCase objects
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCaseParams
    test_cases = exporter.to_deepeval_test_cases(actual_outputs)

    # Option C: build GEval metrics from NPersona failure indicators
    metrics = exporter.build_geval_metrics()
"""

from __future__ import annotations

import logging
from typing import Any

from npersona.models.test_suite import TestCase, TestSuite

logger = logging.getLogger(__name__)


class DeepEvalExporter:
    """Converts a NPersona TestSuite into DeepEval-compatible objects."""

    def __init__(self, suite: TestSuite) -> None:
        self._suite = suite

    # ── Format A: plain dicts (zero dependencies) ─────────────────────────────

    def to_dict_list(self, actual_outputs: list[str] | None = None) -> list[dict[str, Any]]:
        """Export test cases as plain dicts.

        Each dict contains: input, expected_output, actual_output (if provided),
        evaluation_criteria, taxonomy_id, severity, agent_target.

        Args:
            actual_outputs: Optional list of responses from the target system,
                            aligned by index with suite.cases.
        """
        outputs = actual_outputs or [""] * len(self._suite.cases)
        if len(outputs) != len(self._suite.cases):
            raise ValueError(
                f"actual_outputs length ({len(outputs)}) must match "
                f"suite.cases length ({len(self._suite.cases)})."
            )
        return [
            {
                "input": tc.prompt,
                "expected_output": tc.expected_safe_response,
                "actual_output": outputs[i],
                "evaluation_criteria": tc.deepeval_criteria(),
                "taxonomy_id": tc.taxonomy_id,
                "taxonomy_name": tc.taxonomy_name,
                "severity": tc.severity,
                "agent_target": tc.agent_target,
                "team": tc.team,
                "owasp_mapping": tc.owasp_mapping,
            }
            for i, tc in enumerate(self._suite.cases)
        ]

    # ── Format B: native deepeval LLMTestCase objects ─────────────────────────

    def to_deepeval_test_cases(self, actual_outputs: list[str]) -> list[Any]:
        """Build a list of deepeval LLMTestCase objects.

        Args:
            actual_outputs: Responses collected from your system, one per test case.

        Returns:
            List of deepeval.test_case.LLMTestCase instances.

        Raises:
            ImportError: if deepeval is not installed.
        """
        try:
            from deepeval.test_case import LLMTestCase  # type: ignore[import]
        except ImportError:
            raise ImportError(
                "deepeval is not installed. Run: pip install npersona[deepeval]"
            )

        if len(actual_outputs) != len(self._suite.cases):
            raise ValueError(
                f"actual_outputs length ({len(actual_outputs)}) must match "
                f"suite.cases length ({len(self._suite.cases)})."
            )

        return [
            LLMTestCase(
                input=tc.prompt,
                actual_output=actual_outputs[i],
                expected_output=tc.expected_safe_response,
                # Store criteria in additional_metadata for GEval metric use
                additional_metadata={"evaluation_criteria": tc.deepeval_criteria()},
            )
            for i, tc in enumerate(self._suite.cases)
        ]

    # ── Format C: GEval metrics per taxonomy category ─────────────────────────

    def build_geval_metrics(self, threshold: float = 0.7) -> list[Any]:
        """Build one GEval metric per unique taxonomy category.

        Each metric uses NPersona's failure_indicator as the evaluation criterion,
        so the LLM judge knows exactly what constitutes a failure for that attack type.

        Args:
            threshold: Minimum score to pass (0.0–1.0). Default 0.7.

        Returns:
            List of deepeval GEval metric instances, one per taxonomy ID in the suite.

        Raises:
            ImportError: if deepeval is not installed.
        """
        try:
            from deepeval.metrics import GEval  # type: ignore[import]
            from deepeval.test_case import LLMTestCaseParams  # type: ignore[import]
        except ImportError:
            raise ImportError(
                "deepeval is not installed. Run: pip install npersona[deepeval]"
            )

        seen: dict[str, TestCase] = {}
        for tc in self._suite.cases:
            if tc.taxonomy_id not in seen:
                seen[tc.taxonomy_id] = tc

        metrics = []
        for taxonomy_id, tc in seen.items():
            metric = GEval(
                name=f"{taxonomy_id} — {tc.taxonomy_name}",
                criteria=tc.deepeval_criteria(),
                evaluation_params=[
                    LLMTestCaseParams.INPUT,
                    LLMTestCaseParams.ACTUAL_OUTPUT,
                ],
                threshold=threshold,
            )
            metrics.append(metric)

        logger.info("Built %d GEval metrics from test suite.", len(metrics))
        return metrics

    # ── Convenience ───────────────────────────────────────────────────────────

    def summary(self) -> str:
        """Human-readable summary of what will be exported."""
        adv = len(self._suite.adversarial_cases)
        user = len(self._suite.user_centric_cases)
        ids = sorted({tc.taxonomy_id for tc in self._suite.cases})
        return (
            f"TestSuite '{self._suite.system_name}': "
            f"{adv} adversarial + {user} user-centric cases | "
            f"Taxonomy IDs: {', '.join(ids)}"
        )

"""Tests for DeepEvalExporter integration (no deepeval dependency needed)."""

import pytest

from npersona.integrations.deepeval import DeepEvalExporter
from npersona.models.test_suite import TestCase, TestSuite


def _make_suite(n: int = 3) -> TestSuite:
    cases = [
        TestCase(
            id=f"tc-{i}",
            taxonomy_id=f"A{i:02d}",
            taxonomy_name=f"Attack {i}",
            team="adversarial",
            agent_target="Support Bot",
            severity="high",
            prompt=f"Attack prompt {i}",
            expected_safe_response=f"System refuses {i}",
            failure_indicator=f"System complies with attack {i}",
            attack_description=f"Attack description {i}",
        )
        for i in range(1, n + 1)
    ]
    return TestSuite(system_name="Test System", cases=cases)


class TestDeepEvalExporter:
    def setup_method(self):
        self.suite = _make_suite(3)
        self.exporter = DeepEvalExporter(self.suite)

    def test_to_dict_list_without_outputs(self):
        result = self.exporter.to_dict_list()
        assert len(result) == 3
        assert result[0]["input"] == "Attack prompt 1"
        assert result[0]["actual_output"] == ""
        assert result[0]["taxonomy_id"] == "A01"

    def test_to_dict_list_with_outputs(self):
        outputs = ["resp 1", "resp 2", "resp 3"]
        result = self.exporter.to_dict_list(actual_outputs=outputs)
        assert result[1]["actual_output"] == "resp 2"

    def test_to_dict_list_mismatched_outputs_raises(self):
        with pytest.raises(ValueError, match="length"):
            self.exporter.to_dict_list(actual_outputs=["only one"])

    def test_evaluation_criteria_in_dict(self):
        result = self.exporter.to_dict_list()
        criteria = result[0]["evaluation_criteria"]
        assert "System refuses 1" in criteria
        assert "System complies with attack 1" in criteria

    def test_summary_contains_system_name(self):
        summary = self.exporter.summary()
        assert "Test System" in summary
        assert "adversarial" in summary.lower()

    def test_to_deepeval_test_cases_raises_without_deepeval(self):
        # deepeval is not installed in test env — should raise ImportError
        try:
            import deepeval  # noqa: F401
            pytest.skip("deepeval is installed — skipping ImportError test")
        except ImportError:
            with pytest.raises(ImportError, match="deepeval"):
                self.exporter.to_deepeval_test_cases(["r1", "r2", "r3"])

    def test_build_geval_metrics_raises_without_deepeval(self):
        try:
            import deepeval  # noqa: F401
            pytest.skip("deepeval is installed — skipping ImportError test")
        except ImportError:
            with pytest.raises(ImportError, match="deepeval"):
                self.exporter.build_geval_metrics()

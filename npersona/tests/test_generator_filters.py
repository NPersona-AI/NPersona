"""Tests for count control and taxonomy filtering in TestSuiteGenerator."""

import pytest

from npersona.models.attack_map import AttackSurfaceMap, AttackTarget
from npersona.pipeline.generator import TestSuiteGenerator


def _make_targets(taxonomy_ids: list[str], team: str = "adversarial") -> list[AttackTarget]:
    return [
        AttackTarget(
            agent_id=f"agent_{i}",
            agent_name=f"Agent {i}",
            taxonomy_id=tid,
            taxonomy_name=f"Attack {tid}",
            priority=10 - i,
            risk="high",
            reason="test",
            attack_surface_description="test surface",
        )
        for i, tid in enumerate(taxonomy_ids)
    ]


class TestPrioritizeTargets:
    def test_caps_to_limit(self):
        targets = _make_targets(["A01", "A02", "A03", "A04", "A05"])
        result = TestSuiteGenerator._prioritize_targets(targets, 3)
        assert len(result) == 3

    def test_returns_all_when_limit_exceeds_unique_ids(self):
        targets = _make_targets(["A01", "A02", "A03"])
        result = TestSuiteGenerator._prioritize_targets(targets, 10)
        assert len(result) == 3  # only 3 unique IDs available

    def test_deduplicates_by_taxonomy_id_in_pass_one(self):
        # Two targets for A01 (different agents), limit = 1
        t1 = AttackTarget(agent_id="a1", agent_name="Agent 1", taxonomy_id="A01",
                          taxonomy_name="DPI", priority=9, risk="critical",
                          reason="r", attack_surface_description="s")
        t2 = AttackTarget(agent_id="a2", agent_name="Agent 2", taxonomy_id="A01",
                          taxonomy_name="DPI", priority=5, risk="high",
                          reason="r", attack_surface_description="s")
        result = TestSuiteGenerator._prioritize_targets([t1, t2], 1)
        assert len(result) == 1
        assert result[0].agent_id == "a1"  # highest priority wins

    def test_fills_with_variants_in_pass_two(self):
        # 2 unique IDs but 3 targets total — asking for 3 should return 3
        t1 = AttackTarget(agent_id="a1", agent_name="A1", taxonomy_id="A01",
                          taxonomy_name="DPI", priority=9, risk="critical",
                          reason="r", attack_surface_description="s")
        t2 = AttackTarget(agent_id="a2", agent_name="A2", taxonomy_id="A02",
                          taxonomy_name="IPI", priority=8, risk="critical",
                          reason="r", attack_surface_description="s")
        t3 = AttackTarget(agent_id="a3", agent_name="A3", taxonomy_id="A01",
                          taxonomy_name="DPI", priority=5, risk="high",
                          reason="r", attack_surface_description="s")
        result = TestSuiteGenerator._prioritize_targets([t1, t2, t3], 3)
        assert len(result) == 3

    def test_high_priority_selected_first(self):
        targets = _make_targets(["A05", "A03", "A01", "A07", "A02"])
        # priorities are 10,9,8,7,6 for A05,A03,A01,A07,A02 respectively
        result = TestSuiteGenerator._prioritize_targets(targets, 2)
        selected_ids = {t.taxonomy_id for t in result}
        assert "A05" in selected_ids  # highest priority


class TestApplyFilters:
    def test_include_filter_keeps_only_specified_ids(self):
        targets = _make_targets(["A01", "A02", "A03", "A07", "A14"])
        result = TestSuiteGenerator._apply_filters(targets, include=["A03", "A14"], exclude=None)
        ids = {t.taxonomy_id for t in result}
        assert ids == {"A03", "A14"}

    def test_exclude_filter_removes_specified_ids(self):
        targets = _make_targets(["A01", "A02", "A18", "A10"])
        result = TestSuiteGenerator._apply_filters(targets, include=None, exclude=["A18", "A10"])
        ids = {t.taxonomy_id for t in result}
        assert "A18" not in ids
        assert "A10" not in ids
        assert "A01" in ids

    def test_include_and_exclude_combined(self):
        targets = _make_targets(["A01", "A03", "A07", "A14"])
        result = TestSuiteGenerator._apply_filters(
            targets, include=["A01", "A03", "A07"], exclude=["A07"]
        )
        ids = {t.taxonomy_id for t in result}
        assert ids == {"A01", "A03"}

    def test_case_insensitive_filter(self):
        targets = _make_targets(["A01", "A03"])
        result = TestSuiteGenerator._apply_filters(targets, include=["a01", "a03"], exclude=None)
        assert len(result) == 2

    def test_no_filters_returns_all(self):
        targets = _make_targets(["A01", "A02", "A03"])
        result = TestSuiteGenerator._apply_filters(targets, include=None, exclude=None)
        assert len(result) == 3

    def test_empty_after_filter_returns_empty_list(self):
        targets = _make_targets(["A01", "A02"])
        result = TestSuiteGenerator._apply_filters(targets, include=["A99"], exclude=None)
        assert result == []

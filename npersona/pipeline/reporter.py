"""Stage 7 — Reporter: builds the final SecurityReport."""

from __future__ import annotations

import logging

from npersona.models.attack_map import AttackSurfaceMap
from npersona.models.profile import SystemProfile
from npersona.models.rca import RCAFinding
from npersona.models.report import CoverageItem, SecurityReport
from npersona.models.result import EvaluationResult
from npersona.models.test_suite import TestSuite
from npersona.taxonomy.entries import TAXONOMY_BY_ID

logger = logging.getLogger(__name__)


class Reporter:
    """Assembles the final SecurityReport from pipeline stage outputs."""

    def build(
        self,
        profile: SystemProfile,
        test_suite: TestSuite,
        attack_map: AttackSurfaceMap,
        evaluation: EvaluationResult,
        rca_findings: list[RCAFinding] | None = None,
        system_doc_path: str = "",
        architecture_doc_path: str = "",
    ) -> SecurityReport:
        coverage = self._build_coverage(test_suite, evaluation, attack_map)

        report = SecurityReport(
            system_name=profile.system_name,
            system_doc_path=system_doc_path,
            architecture_doc_path=architecture_doc_path,
            test_suite=test_suite,
            evaluation=evaluation,
            coverage=coverage,
            rca_findings=rca_findings or [],
        )

        logger.info(
            "Report built: %.1f%% pass rate, %d critical failures, %d coverage items",
            report.overall_pass_rate * 100,
            report.critical_failures,
            len(coverage),
        )
        return report

    def _build_coverage(
        self,
        suite: TestSuite,
        evaluation: EvaluationResult,
        attack_map: AttackSurfaceMap,
    ) -> list[CoverageItem]:
        results_by_taxonomy = evaluation.results_by_taxonomy()
        items: list[CoverageItem] = []

        # Tested taxonomy IDs
        for taxonomy_id, results in results_by_taxonomy.items():
            entry = TAXONOMY_BY_ID.get(taxonomy_id)
            passed = sum(1 for r in results if r.passed)
            failed = len(results) - passed
            status = "passed" if failed == 0 else "failed"
            items.append(CoverageItem(
                taxonomy_id=taxonomy_id,
                taxonomy_name=entry.name if entry else taxonomy_id,
                team=entry.team if entry else "unknown",
                status=status,
                test_count=len(results),
                passed_count=passed,
                failed_count=failed,
            ))

        # Planned but not tested (edge case — executor skipped)
        tested_ids = set(results_by_taxonomy.keys())
        for taxonomy_id in suite.planned_taxonomy_ids:
            if taxonomy_id not in tested_ids:
                entry = TAXONOMY_BY_ID.get(taxonomy_id)
                items.append(CoverageItem(
                    taxonomy_id=taxonomy_id,
                    taxonomy_name=entry.name if entry else taxonomy_id,
                    team=entry.team if entry else "unknown",
                    status="untested",
                    test_count=0,
                    passed_count=0,
                    failed_count=0,
                ))

        # Uncoverable taxonomy IDs (no surface in this system)
        for taxonomy_id in attack_map.uncoverable_ids:
            if taxonomy_id not in tested_ids and taxonomy_id not in suite.planned_taxonomy_ids:
                entry = TAXONOMY_BY_ID.get(taxonomy_id)
                items.append(CoverageItem(
                    taxonomy_id=taxonomy_id,
                    taxonomy_name=entry.name if entry else taxonomy_id,
                    team=entry.team if entry else "unknown",
                    status="untested",
                    test_count=0,
                    passed_count=0,
                    failed_count=0,
                ))

        return sorted(items, key=lambda c: c.taxonomy_id)

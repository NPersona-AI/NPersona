"""Stage 6 — RCA Analyzer: spec vs behavior root cause analysis."""

from __future__ import annotations

import logging

from npersona.exceptions import RCAError
from npersona.llm.client import LLMClient
from npersona.models.config import LLMConfig
from npersona.models.profile import SystemProfile
from npersona.models.rca import GapType, RCAFinding
from npersona.models.result import EvaluationResult
from npersona.models.test_suite import TestSuite
from npersona.prompts.rca import RCA_SYSTEM_PROMPT, build_rca_user_prompt

logger = logging.getLogger(__name__)

RCA_BATCH_SIZE = 5  # failed tests per RCA LLM call


class RCAAnalyzer:
    """Performs root cause analysis on failed tests using the architecture document."""

    def __init__(self, llm_config: LLMConfig) -> None:
        self._llm = LLMClient(llm_config)

    async def analyze(
        self,
        architecture_text: str,
        profile: SystemProfile,
        test_suite: TestSuite,
        evaluation: EvaluationResult,
        on_progress: object = None,
    ) -> list[RCAFinding]:
        """Analyze failed tests against the architecture document."""
        if not architecture_text or not architecture_text.strip():
            raise RCAError("architecture_text is empty")

        failed = evaluation.failed_results
        if not failed:
            self._emit(on_progress, "No failures to analyze — RCA skipped.")
            return []

        self._emit(on_progress, f"Running RCA on {len(failed)} failed tests...")

        case_map = {tc.id: tc for tc in test_suite.cases}
        profile_context = profile.to_context_string()
        findings: list[RCAFinding] = []

        # Batch failed tests to avoid token limits
        for i in range(0, len(failed), RCA_BATCH_SIZE):
            batch = failed[i:i + RCA_BATCH_SIZE]
            batch_input = []
            for result in batch:
                tc = case_map.get(result.test_case_id)
                batch_input.append({
                    "test_case_id": result.test_case_id,
                    "taxonomy_id": result.taxonomy_id,
                    "taxonomy_name": tc.taxonomy_name if tc else "",
                    "agent_target": result.agent_target,
                    "prompt_sent": result.prompt_sent,
                    "response_received": result.response_received,
                    "failure_reason": result.failure_reason,
                })

            try:
                raw = await self._llm.complete(
                    system_prompt=RCA_SYSTEM_PROMPT,
                    user_prompt=build_rca_user_prompt(architecture_text, profile_context, batch_input),
                    temperature=0.2,
                    json_mode=True,
                )
                batch_findings = self._parse_findings(raw)
                findings.extend(batch_findings)
                self._emit(on_progress, f"RCA batch complete: {len(batch_findings)} findings.")
            except Exception as exc:
                logger.warning("RCA batch failed: %s", exc)

        logger.info("RCA complete: %d findings", len(findings))
        self._emit(on_progress, f"RCA complete: {len(findings)} root causes identified.")
        return findings

    @staticmethod
    def _parse_findings(raw: dict | list) -> list[RCAFinding]:
        raw_list = raw.get("findings", []) if isinstance(raw, dict) else (raw if isinstance(raw, list) else [])
        findings: list[RCAFinding] = []
        for item in raw_list:
            try:
                findings.append(RCAFinding(
                    test_case_id=item.get("test_case_id", ""),
                    taxonomy_id=item.get("taxonomy_id", ""),
                    taxonomy_name=item.get("taxonomy_name", ""),
                    agent_name=item.get("agent_name", ""),
                    gap_type=item.get("gap_type", "unknown"),  # type: ignore[arg-type]
                    spec_says=item.get("spec_says", ""),
                    observed=item.get("observed", ""),
                    root_cause=item.get("root_cause", ""),
                    suggested_fix=item.get("suggested_fix", ""),
                    fix_location=item.get("fix_location", "unknown"),  # type: ignore[arg-type]
                    confidence=item.get("confidence", "medium"),  # type: ignore[arg-type]
                ))
            except Exception as exc:
                logger.warning("Skipping malformed RCA finding: %s", exc)
        return findings

    @staticmethod
    def _emit(callback: object, message: str) -> None:
        if callable(callback):
            callback({"stage": "rca", "message": message})

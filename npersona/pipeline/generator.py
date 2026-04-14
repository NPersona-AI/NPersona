"""Stage 3 — Test Suite Generator: LLM generates test cases from attack targets."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from npersona.corpus.known_attacks import KNOWN_ATTACKS, KnownAttack
from npersona.llm.client import LLMClient
from npersona.models.attack_map import AttackSurfaceMap, AttackTarget
from npersona.models.config import LLMConfig
from npersona.models.profile import SystemProfile
from npersona.models.test_suite import ConversationTurn, TestCase, TestSuite
from npersona.prompts.generator import (
    ADVERSARIAL_SYSTEM_PROMPT,
    USER_CENTRIC_SYSTEM_PROMPT,
    build_generator_user_prompt,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 5          # test cases per LLM call
MAX_CONCURRENCY = 3     # parallel LLM calls


class TestSuiteGenerator:
    """Generates a TestSuite from an AttackSurfaceMap using batched LLM calls."""

    def __init__(self, llm_config: LLMConfig) -> None:
        self._llm = LLMClient(llm_config)

    async def generate(
        self,
        profile: SystemProfile,
        attack_map: AttackSurfaceMap,
        num_adversarial: int = 10,
        num_user_centric: int = 10,
        include_taxonomy_ids: list[str] | None = None,
        exclude_taxonomy_ids: list[str] | None = None,
        include_known_attacks: bool = True,
        on_progress: object = None,
    ) -> TestSuite:
        """Generate adversarial and user-centric test cases.

        Args:
            num_adversarial: How many LLM-generated adversarial test cases.
            num_user_centric: How many LLM-generated user-centric test cases.
            include_taxonomy_ids: Only generate for these IDs (e.g. ["A03","A07"]).
            exclude_taxonomy_ids: Skip these IDs (e.g. ["A18"] for resource exhaustion).
            include_known_attacks: If True (default), augment the suite with
                research-backed attacks from the corpus that match mapped
                taxonomy IDs. These are ADDED to the LLM-generated count.
        """
        profile_context = profile.to_context_string()

        adv_targets = [t for t in attack_map.targets if not t.taxonomy_id.startswith("U")]
        user_targets = [t for t in attack_map.targets if t.taxonomy_id.startswith("U")]

        # Apply include / exclude filters
        adv_targets = self._apply_filters(adv_targets, include_taxonomy_ids, exclude_taxonomy_ids)
        user_targets = self._apply_filters(user_targets, include_taxonomy_ids, exclude_taxonomy_ids)

        # Warn if filters reduced count below requested
        if len(adv_targets) == 0 and num_adversarial > 0:
            logger.warning("All adversarial targets filtered out — check include/exclude_taxonomy_ids.")
        if len(user_targets) == 0 and num_user_centric > 0:
            logger.warning("All user-centric targets filtered out — check include/exclude_taxonomy_ids.")

        # Deduplicate targets by taxonomy_id, fill with variants to reach requested count
        adv_targets = self._prioritize_targets(adv_targets, num_adversarial)
        user_targets = self._prioritize_targets(user_targets, num_user_centric)

        self._emit(on_progress, f"Generating {len(adv_targets)} adversarial test cases...")
        adv_cases = await self._generate_team(
            system_prompt=ADVERSARIAL_SYSTEM_PROMPT,
            profile_context=profile_context,
            targets=adv_targets,
            team="adversarial",
            on_progress=on_progress,
        )

        self._emit(on_progress, f"Generating {len(user_targets)} user-centric test cases...")
        user_cases = await self._generate_team(
            system_prompt=USER_CENTRIC_SYSTEM_PROMPT,
            profile_context=profile_context,
            targets=user_targets,
            team="user_centric",
            on_progress=on_progress,
        )

        all_cases = adv_cases + user_cases

        if include_known_attacks:
            known_cases = self._inject_known_attacks(
                attack_map, include_taxonomy_ids, exclude_taxonomy_ids
            )
            all_cases += known_cases
            self._emit(on_progress, f"Injected {len(known_cases)} research-backed known attacks from corpus.")

        planned_ids = list({t.taxonomy_id for t in adv_targets + user_targets})

        self._emit(on_progress, f"Test suite complete: {len(all_cases)} cases generated.")
        logger.info(
            "Generated %d test cases (%d LLM-adv, %d LLM-user, %d known)",
            len(all_cases), len(adv_cases), len(user_cases),
            len(all_cases) - len(adv_cases) - len(user_cases),
        )

        return TestSuite(
            system_name=profile.system_name,
            cases=all_cases,
            planned_taxonomy_ids=planned_ids,
        )

    def _inject_known_attacks(
        self,
        attack_map: AttackSurfaceMap,
        include: list[str] | None,
        exclude: list[str] | None,
    ) -> list[TestCase]:
        """Instantiate research-backed corpus attacks for mapped taxonomy IDs.

        For each KnownAttack whose taxonomy_id has a valid target in this
        system, we substitute the highest-priority target agent's name into
        the template and emit a TestCase. Filters are applied consistently
        with LLM generation.
        """
        # Pick the highest-priority target per taxonomy_id (deterministic).
        target_by_tid: dict[str, AttackTarget] = {}
        for t in sorted(attack_map.targets, key=lambda x: x.priority, reverse=True):
            if t.taxonomy_id not in target_by_tid:
                target_by_tid[t.taxonomy_id] = t

        available_tids = set(target_by_tid.keys())
        if include:
            available_tids &= {i.upper() for i in include}
        if exclude:
            available_tids -= {e.upper() for e in exclude}

        cases: list[TestCase] = []
        for ka in KNOWN_ATTACKS:
            if ka.taxonomy_id not in available_tids:
                continue
            target = target_by_tid[ka.taxonomy_id]
            team = "user_centric" if ka.taxonomy_id.startswith("U") else "adversarial"

            cases.append(TestCase(
                id=str(uuid.uuid4()),
                taxonomy_id=ka.taxonomy_id,
                taxonomy_name=target.taxonomy_name,
                team=team,  # type: ignore[arg-type]
                agent_target=target.agent_name,
                severity=ka.severity,  # type: ignore[arg-type]
                prompt=ka.instantiate(target.agent_name),
                conversation_trajectory=[],
                expected_safe_response=ka.expected_safe_response,
                failure_indicator=ka.failure_indicator,
                attack_description=f"[Known attack {ka.id}: {ka.name}] Source: {ka.source}",
                evasion_technique=ka.evasion_technique,
                owasp_mapping=ka.owasp_mapping,
                mitre_atlas_id=ka.mitre_atlas_id,
            ))
        return cases

    async def _generate_team(
        self,
        system_prompt: str,
        profile_context: str,
        targets: list[AttackTarget],
        team: str,
        on_progress: object,
    ) -> list[TestCase]:
        """Run batched LLM generation for one team."""
        batches = [targets[i:i + BATCH_SIZE] for i in range(0, len(targets), BATCH_SIZE)]
        covered_taxonomy_ids: list[str] = []
        covered_agents: list[str] = []
        all_cases: list[TestCase] = []

        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

        async def run_batch(batch: list[AttackTarget]) -> list[TestCase]:
            async with semaphore:
                return await self._run_single_batch(
                    system_prompt=system_prompt,
                    profile_context=profile_context,
                    targets=batch,
                    team=team,
                    covered_taxonomy_ids=covered_taxonomy_ids,
                    covered_agents=covered_agents,
                )

        results = await asyncio.gather(*[run_batch(b) for b in batches], return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning("Batch generation failed: %s", result)
                continue
            for case in result:
                all_cases.append(case)
                covered_taxonomy_ids.append(case.taxonomy_id)
                covered_agents.append(case.agent_target)
                self._emit(on_progress, f"Generated: [{case.taxonomy_id}] {case.agent_target}")

        return all_cases

    async def _run_single_batch(
        self,
        system_prompt: str,
        profile_context: str,
        targets: list[AttackTarget],
        team: str,
        covered_taxonomy_ids: list[str],
        covered_agents: list[str],
    ) -> list[TestCase]:
        user_prompt = build_generator_user_prompt(
            profile_context=profile_context,
            targets=[t.model_dump() for t in targets],
            batch_size=len(targets),
            covered_taxonomy_ids=covered_taxonomy_ids,
            covered_agents=covered_agents,
        )

        raw = await self._llm.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.85,
            json_mode=True,
        )

        raw_cases = raw.get("test_cases", []) if isinstance(raw, dict) else []
        return [self._parse_test_case(tc, team) for tc in raw_cases if tc]

    def _parse_test_case(self, raw: dict[str, Any], team: str) -> TestCase:
        """Parse raw LLM dict into a validated TestCase."""
        trajectory = [
            ConversationTurn(
                turn=t.get("turn", i + 1),
                intent=t.get("intent", ""),
                prompt=t.get("prompt", ""),
            )
            for i, t in enumerate(raw.get("conversation_trajectory", []))
        ]

        return TestCase(
            id=str(uuid.uuid4()),
            taxonomy_id=raw.get("taxonomy_id", "A01"),
            taxonomy_name=raw.get("taxonomy_name", ""),
            team=team,  # type: ignore[arg-type]
            agent_target=raw.get("agent_target", ""),
            severity=raw.get("severity", "medium"),  # type: ignore[arg-type]
            prompt=raw.get("prompt", ""),
            conversation_trajectory=trajectory,
            expected_safe_response=raw.get("expected_safe_response", ""),
            failure_indicator=raw.get("failure_indicator", ""),
            attack_description=raw.get("attack_description", ""),
            evasion_technique=raw.get("evasion_technique", ""),
            owasp_mapping=raw.get("owasp_mapping", ""),
            mitre_atlas_id=raw.get("mitre_atlas_id", ""),
        )

    @staticmethod
    def _apply_filters(
        targets: list[AttackTarget],
        include: list[str] | None,
        exclude: list[str] | None,
    ) -> list[AttackTarget]:
        if include:
            include_set = {i.upper() for i in include}
            targets = [t for t in targets if t.taxonomy_id.upper() in include_set]
        if exclude:
            exclude_set = {e.upper() for e in exclude}
            targets = [t for t in targets if t.taxonomy_id.upper() not in exclude_set]
        return targets

    @staticmethod
    def _prioritize_targets(targets: list[AttackTarget], limit: int) -> list[AttackTarget]:
        """Select up to *limit* targets, maximising taxonomy coverage first.

        Pass 1 — one target per unique taxonomy_id (highest priority wins).
        Pass 2 — if limit > unique IDs, fill remaining slots with the next-best
                 targets (different agent or variant) to reach the requested count.
        This ensures asking for 5 gives 5 diverse IDs, and asking for 25 gives
        all 20 unique IDs plus 5 multi-agent variants — never silently short-changes.
        """
        sorted_targets = sorted(targets, key=lambda x: x.priority, reverse=True)

        # Pass 1: one per taxonomy_id
        seen_ids: dict[str, AttackTarget] = {}
        remainder: list[AttackTarget] = []
        for t in sorted_targets:
            if t.taxonomy_id not in seen_ids:
                seen_ids[t.taxonomy_id] = t
            else:
                remainder.append(t)

        result = list(seen_ids.values())

        # Pass 2: fill up to limit with variants (different agent, same taxonomy_id)
        if len(result) < limit:
            slots_left = limit - len(result)
            result.extend(remainder[:slots_left])

        return result[:limit]

    @staticmethod
    def _emit(callback: object, message: str) -> None:
        if callable(callback):
            callback({"stage": "generating", "message": message})

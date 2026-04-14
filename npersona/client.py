"""NPersona public API — NPersonaClient and top-level generate() function."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Callable

from npersona.adapters.base import RequestAdapter
from npersona.cache import ProfileCache
from npersona.models.attack_map import AttackSurfaceMap
from npersona.models.config import LLMConfig, NPersonaConfig
from npersona.models.profile import SystemProfile
from npersona.models.report import SecurityReport
from npersona.models.result import EvaluationResult
from npersona.models.test_suite import TestSuite
from npersona.parsers.base import parse_document
from npersona.pipeline.evaluator import Evaluator
from npersona.pipeline.executor import Executor
from npersona.pipeline.generator import TestSuiteGenerator
from npersona.pipeline.mapper import AttackSurfaceMapper
from npersona.pipeline.profiler import SystemProfiler
from npersona.pipeline.rca import RCAAnalyzer
from npersona.pipeline.reporter import Reporter

logger = logging.getLogger(__name__)


class NPersonaClient:
    """Full-pipeline NPersona client.

    Usage (simple)::

        client = NPersonaClient(api_key="gsk_...", provider="groq")
        report = asyncio.run(client.run("spec.pdf"))

    Usage (advanced — inspect each stage)::

        profile = await client.extract_profile("spec.pdf")
        attack_map = client.map_attack_surfaces(profile)
        suite = await client.generate_test_suite(profile, attack_map)
        results = await client.execute(suite)
        evaluation = client.evaluate(suite, results)
        rca = await client.analyze_rca("arch.pdf", profile, suite, evaluation)
        report = client.build_report(profile, suite, attack_map, evaluation, rca)
    """

    def __init__(
        self,
        api_key: str | None = None,
        provider: str = "groq",
        model: str | None = None,
        config: NPersonaConfig | None = None,
        cache_dir: str | Path | None = None,
    ) -> None:
        if config:
            self._config = config
        else:
            llm = LLMConfig(
                provider=provider,  # type: ignore[arg-type]
                model=model or _default_model(provider),
                api_key=api_key,
            )
            self._config = NPersonaConfig(llm=llm)

        self._cache = ProfileCache(cache_dir)
        self._profiler = SystemProfiler(self._config.llm)
        self._mapper = AttackSurfaceMapper()
        self._generator = TestSuiteGenerator(self._config.llm)
        self._evaluator = Evaluator(llm_config=self._config.llm)
        self._rca_analyzer = RCAAnalyzer(self._config.llm)
        self._reporter = Reporter()

    # ── Full pipeline ────────────────────────────��────────────────────────────

    async def run(
        self,
        system_doc: str | Path,
        architecture_doc: str | Path | None = None,
        num_adversarial: int | None = None,
        num_user_centric: int | None = None,
        include_taxonomy_ids: list[str] | None = None,
        exclude_taxonomy_ids: list[str] | None = None,
        include_known_attacks: bool = True,
        on_progress: Callable[[dict], None] | None = None,
        executor_adapter: RequestAdapter | None = None,
    ) -> SecurityReport:
        """Run the full pipeline from document to security report.

        Args:
            system_doc: Path to (or raw text of) the AI system's documentation.
            architecture_doc: Optional path/text of the architecture document.
                              Required for RCA. If provided, enables root cause analysis.
            num_adversarial: Number of adversarial test cases. Defaults to config value.
            num_user_centric: Number of user-centric test cases. Defaults to config value.
            on_progress: Optional callback receiving progress dicts {stage, message}.
            executor_adapter: Custom RequestAdapter for non-default target shapes.

        Returns:
            A SecurityReport with test suite, evaluation, coverage, and optional RCA.
        """
        n_adv = num_adversarial or self._config.num_adversarial
        n_user = num_user_centric or self._config.num_user_centric

        # Stage 1 — Parse documents
        _emit(on_progress, "parsing", "Parsing system document...")
        doc_text = parse_document(system_doc)
        arch_text = parse_document(architecture_doc) if architecture_doc else ""

        # Stage 2 — Extract system profile (cached)
        profile = await self.extract_profile(doc_text, on_progress=on_progress)

        # Stage 3 — Map attack surfaces
        attack_map = self.map_attack_surfaces(profile, on_progress=on_progress)

        # Stage 4 — Generate test suite
        suite = await self.generate_test_suite(
            profile, attack_map, n_adv, n_user,
            include_taxonomy_ids=include_taxonomy_ids,
            exclude_taxonomy_ids=exclude_taxonomy_ids,
            include_known_attacks=include_known_attacks,
            on_progress=on_progress,
        )

        # Stage 5 — Execute (if endpoint configured)
        evaluation: EvaluationResult
        if self._config.enable_executor and self._config.system_endpoint:
            raw_results = await self.execute(suite, on_progress=on_progress, adapter=executor_adapter)
            evaluation = await self.evaluate(suite, raw_results, on_progress=on_progress)
        else:
            # No executor — return suite-only report with empty evaluation
            _emit(on_progress, "skipped", "Executor skipped — no system_endpoint configured.")
            from npersona.models.result import EvaluationResult
            evaluation = EvaluationResult(results=[])

        # Stage 6 — RCA (optional, requires architecture doc)
        rca_findings = []
        if arch_text and self._config.enable_rca:
            rca_findings = await self._rca_analyzer.analyze(
                arch_text, profile, suite, evaluation, on_progress=on_progress
            )
        elif architecture_doc and not self._config.enable_rca:
            _emit(on_progress, "info", "Architecture doc provided but enable_rca=False. Set enable_rca=True to run RCA.")

        # Stage 7 — Build report
        _emit(on_progress, "reporting", "Building security report...")
        return self._reporter.build(
            profile=profile,
            test_suite=suite,
            attack_map=attack_map,
            evaluation=evaluation,
            rca_findings=rca_findings,
            system_doc_path=str(system_doc),
            architecture_doc_path=str(architecture_doc) if architecture_doc else "",
        )

    # ── Individual stage methods (power user API) ─────────────────────────────

    async def extract_profile(
        self,
        document: str | Path,
        extra_context: str = "",
        on_progress: Callable[[dict], None] | None = None,
    ) -> SystemProfile:
        """Stage 1: Extract system profile (with caching)."""
        doc_text = parse_document(document) if isinstance(document, Path) else document
        cached = self._cache.get(doc_text)
        if cached:
            _emit(on_progress, "profiling", f"Using cached profile for '{cached.system_name}'.")
            return cached
        profile = await self._profiler.extract(doc_text, extra_context, on_progress)
        self._cache.set(doc_text, profile)
        return profile

    def map_attack_surfaces(
        self,
        profile: SystemProfile,
        on_progress: Callable[[dict], None] | None = None,
    ) -> AttackSurfaceMap:
        """Stage 2: Map attack surfaces deterministically."""
        return self._mapper.map(profile, on_progress)

    async def generate_test_suite(
        self,
        profile: SystemProfile,
        attack_map: AttackSurfaceMap,
        num_adversarial: int = 10,
        num_user_centric: int = 10,
        include_taxonomy_ids: list[str] | None = None,
        exclude_taxonomy_ids: list[str] | None = None,
        include_known_attacks: bool = True,
        on_progress: Callable[[dict], None] | None = None,
    ) -> TestSuite:
        """Stage 3: Generate test cases from attack map.

        Args:
            num_adversarial: LLM-generated adversarial test cases.
            num_user_centric: LLM-generated user-centric test cases.
            include_taxonomy_ids: Only generate for these taxonomy IDs.
            exclude_taxonomy_ids: Skip these taxonomy IDs.
            include_known_attacks: Augment with research-backed corpus attacks.
        """
        return await self._generator.generate(
            profile, attack_map, num_adversarial, num_user_centric,
            include_taxonomy_ids, exclude_taxonomy_ids,
            include_known_attacks=include_known_attacks,
            on_progress=on_progress,
        )

    async def execute(
        self,
        suite: TestSuite,
        on_progress: Callable[[dict], None] | None = None,
        adapter: RequestAdapter | None = None,
    ):
        """Stage 4: Execute test cases against target system.

        Args:
            suite: TestSuite to execute.
            on_progress: Optional progress callback.
            adapter: Custom RequestAdapter (default: built from config).
        """
        executor = Executor(self._config, adapter=adapter)
        return await executor.run(suite.cases, on_progress)

    async def evaluate(
        self,
        suite: TestSuite,
        results,
        on_progress: Callable[[dict], None] | None = None,
    ) -> EvaluationResult:
        """Stage 5: Evaluate responses (LLM-as-judge by default)."""
        return await self._evaluator.evaluate(results, suite.cases, on_progress)

    async def analyze_rca(
        self,
        architecture_doc: str | Path,
        profile: SystemProfile,
        suite: TestSuite,
        evaluation: EvaluationResult,
        on_progress: Callable[[dict], None] | None = None,
    ):
        """Stage 6: Run RCA on failed tests against architecture document."""
        arch_text = parse_document(architecture_doc)
        return await self._rca_analyzer.analyze(arch_text, profile, suite, evaluation, on_progress)

    def build_report(
        self,
        profile: SystemProfile,
        suite: TestSuite,
        attack_map: AttackSurfaceMap,
        evaluation: EvaluationResult,
        rca_findings=None,
        system_doc_path: str = "",
        architecture_doc_path: str = "",
    ) -> SecurityReport:
        """Stage 7: Assemble the final SecurityReport."""
        return self._reporter.build(
            profile, suite, attack_map, evaluation, rca_findings,
            system_doc_path, architecture_doc_path
        )


# ── Top-level convenience function ────────────────────────────────────────────

def generate(
    system_doc: str | Path,
    architecture_doc: str | Path | None = None,
    provider: str = "groq",
    api_key: str | None = None,
    model: str | None = None,
    num_adversarial: int = 10,
    num_user_centric: int = 10,
    include_taxonomy_ids: list[str] | None = None,
    exclude_taxonomy_ids: list[str] | None = None,
    include_known_attacks: bool = True,
    system_endpoint: str | None = None,
    enable_rca: bool = False,
    on_progress: Callable[[dict], None] | None = None,
    cache_dir: str | Path | None = None,
    executor_adapter: RequestAdapter | None = None,
) -> SecurityReport:
    """One-shot synchronous generation function.

    Examples::

        # Basic
        report = npersona.generate("spec.pdf", provider="groq", api_key="gsk_...")

        # Control counts
        report = npersona.generate("spec.pdf", num_adversarial=5, num_user_centric=3, ...)

        # Only test specific attack types
        report = npersona.generate("spec.pdf", include_taxonomy_ids=["A03", "A07", "A14"], ...)

        # Skip resource exhaustion and encoding tests
        report = npersona.generate("spec.pdf", exclude_taxonomy_ids=["A18", "A12"], ...)
    """
    llm = LLMConfig(
        provider=provider,  # type: ignore[arg-type]
        model=model or _default_model(provider),
        api_key=api_key,
    )
    config = NPersonaConfig(
        llm=llm,
        num_adversarial=num_adversarial,
        num_user_centric=num_user_centric,
        enable_rca=enable_rca and architecture_doc is not None,
        enable_executor=system_endpoint is not None,
        system_endpoint=system_endpoint,
    )
    client = NPersonaClient(config=config, cache_dir=cache_dir)
    return asyncio.run(
        client.run(
            system_doc=system_doc,
            architecture_doc=architecture_doc,
            num_adversarial=num_adversarial,
            num_user_centric=num_user_centric,
            include_taxonomy_ids=include_taxonomy_ids,
            exclude_taxonomy_ids=exclude_taxonomy_ids,
            include_known_attacks=include_known_attacks,
            on_progress=on_progress,
            executor_adapter=executor_adapter,
        )
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _default_model(provider: str) -> str:
    defaults = {
        "groq": "llama-3.3-70b-versatile",
        "openai": "gpt-4o-mini",
        "gemini": "gemini-2.0-flash",
        "azure": "gpt-4o",
        "ollama": "llama3",
    }
    return defaults.get(provider, "llama-3.3-70b-versatile")


def _emit(callback: Callable[[dict], None] | None, stage: str, message: str) -> None:
    if callable(callback):
        callback({"stage": stage, "message": message})

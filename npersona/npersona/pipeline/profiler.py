"""Stage 1 — System Profiler: extract structured profile from document text."""

from __future__ import annotations

import logging

from npersona.exceptions import ProfileExtractionError
from npersona.llm.client import LLMClient
from npersona.models.config import LLMConfig
from npersona.models.profile import Agent, Guardrail, Integration, SystemProfile
from npersona.prompts.profiler import PROFILER_SYSTEM_PROMPT, build_profiler_user_prompt

logger = logging.getLogger(__name__)


class SystemProfiler:
    """Extracts a structured SystemProfile from AI system documentation."""

    def __init__(self, llm_config: LLMConfig) -> None:
        self._llm = LLMClient(llm_config)

    async def extract(
        self,
        document_text: str,
        extra_context: str = "",
        on_progress: object = None,
    ) -> SystemProfile:
        """Run LLM extraction and return a validated SystemProfile."""
        self._emit(on_progress, "Extracting system profile from document...")

        user_prompt = build_profiler_user_prompt(document_text, extra_context)

        raw = await self._llm.complete(
            system_prompt=PROFILER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,  # low temp for factual extraction
            max_tokens=8192,
            json_mode=True,
        )

        if not isinstance(raw, dict):
            raise ProfileExtractionError("LLM returned a list instead of an object for profile extraction.")

        profile = self._parse_profile(raw)

        if not profile.agents:
            raise ProfileExtractionError(
                "Profile extraction produced no agents. "
                "Ensure your document describes the AI system's components."
            )

        self._emit(
            on_progress,
            f"Profile extracted: {len(profile.agents)} agents, "
            f"{len(profile.guardrails)} guardrails, "
            f"{len(profile.sensitive_data)} sensitive data types.",
        )
        logger.info(
            "Extracted profile for '%s': %d agents, %d guardrails",
            profile.system_name,
            len(profile.agents),
            len(profile.guardrails),
        )
        return profile

    def _parse_profile(self, raw: dict) -> SystemProfile:
        """Parse raw LLM dict into a validated SystemProfile, tolerating partial data."""
        agents: list[Agent] = []
        for a in raw.get("agents", []):
            try:
                agents.append(Agent(**{k: v for k, v in a.items() if k in Agent.model_fields}))
            except Exception as exc:
                logger.warning("Skipping malformed agent entry: %s — %s", a.get("name"), exc)

        guardrails: list[Guardrail] = []
        for g in raw.get("guardrails", []):
            try:
                # Handle both string and dict formats
                if isinstance(g, str):
                    guardrails.append(Guardrail(name=g, description=""))
                else:
                    guardrails.append(Guardrail(**{k: v for k, v in g.items() if k in Guardrail.model_fields}))
            except Exception as exc:
                logger.warning("Skipping malformed guardrail entry: %s — %s", g if isinstance(g, str) else g.get("name"), exc)

        integrations: list[Integration] = []
        for i in raw.get("integrations", []):
            try:
                # Handle both string and dict formats
                if isinstance(i, str):
                    integrations.append(Integration(name=i, description=""))
                else:
                    integrations.append(Integration(**{k: v for k, v in i.items() if k in Integration.model_fields}))
            except Exception as exc:
                logger.warning("Skipping malformed integration entry: %s — %s", i if isinstance(i, str) else i.get("name"), exc)

        return SystemProfile(
            system_name=raw.get("system_name", "Unknown System"),
            system_description=raw.get("system_description", ""),
            agents=agents,
            sensitive_data=raw.get("sensitive_data", []),
            guardrails=guardrails,
            integrations=integrations,
            user_roles=raw.get("user_roles", []),
            is_multi_agent=raw.get("is_multi_agent", len(agents) > 1),
            has_rag=raw.get("has_rag", False),
            has_tool_use=raw.get("has_tool_use", False),
            has_code_execution=raw.get("has_code_execution", False),
            has_external_api_calls=raw.get("has_external_api_calls", False),
        )

    @staticmethod
    def _emit(callback: object, message: str) -> None:
        if callable(callback):
            callback({"stage": "profiling", "message": message})

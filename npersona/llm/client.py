"""LLM client — thin async wrapper around litellm with retry logic and JSON parsing."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from npersona.exceptions import LLMError, LLMParseError
from npersona.models.config import LLMConfig

logger = logging.getLogger(__name__)


class LLMClient:
    """Async LLM client with automatic retries and robust JSON parsing."""

    def __init__(self, config: LLMConfig) -> None:
        self._config = config
        self._model = config.litellm_model_string()

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
        json_mode: bool = True,
    ) -> dict[str, Any] | list[Any]:
        """Send a completion request and return parsed JSON.

        Retries on rate limits and transient failures with exponential backoff.
        """
        try:
            import litellm  # type: ignore[import]
        except ImportError:
            raise ImportError("litellm is required. Run: pip install litellm")

        temperature = temperature if temperature is not None else self._config.temperature
        max_tokens = max_tokens if max_tokens is not None else self._config.max_tokens

        kwargs: dict[str, Any] = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": self._config.timeout,
        }

        if self._config.api_key:
            kwargs["api_key"] = self._config.api_key
        if self._config.base_url:
            kwargs["base_url"] = self._config.base_url
        if self._config.api_version:
            kwargs["api_version"] = self._config.api_version

        if json_mode and self._config.provider in ("openai", "azure", "groq"):
            kwargs["response_format"] = {"type": "json_object"}

        raw_content = ""
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self._config.max_retries),
                wait=wait_exponential(multiplier=2, min=5, max=60),
                retry=retry_if_exception_type((Exception,)),
                reraise=True,
            ):
                with attempt:
                    response = await litellm.acompletion(**kwargs)
                    raw_content = response.choices[0].message.content or ""
                    return self._parse_json(raw_content)
        except Exception as exc:
            raise LLMError(self._config.provider, str(exc)) from exc

        raise LLMError(self._config.provider, "Exhausted retries without a response.")

    def _parse_json(self, raw: str) -> dict[str, Any] | list[Any]:
        """Parse JSON from LLM output with multiple fallback strategies."""
        raw = raw.strip()

        # Strategy 1: direct parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Strategy 2: strip markdown code fences
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Strategy 3: extract first JSON object or array
        match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", cleaned)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        logger.error("Failed to parse LLM response as JSON. Raw: %s", raw[:500])
        raise LLMParseError(raw)

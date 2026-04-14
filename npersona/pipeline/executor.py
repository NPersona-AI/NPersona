"""Stage 4 — Executor: parallel, retried, rate-limited execution of test cases."""

from __future__ import annotations

import asyncio
import logging
import sys
import time
from contextlib import asynccontextmanager
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from npersona.adapters.base import RequestAdapter
from npersona.adapters.json_post import JsonPostAdapter
from npersona.models.config import NPersonaConfig
from npersona.models.result import TestResult
from npersona.models.test_suite import TestCase
from npersona.pipeline.auth_handler import AuthHandler

logger = logging.getLogger(__name__)


def _extract_error_message(exc: Exception) -> str:
    """Extract meaningful error message from exception, unwrapping tenacity.RetryError."""
    if exc.__class__.__name__ == "RetryError" and hasattr(exc, "last_attempt"):
        # Unwrap tenacity RetryError to get the actual cause
        cause = exc.last_attempt.exception()
        return str(cause) if cause else str(exc)
    return str(exc)


@asynccontextmanager
async def _optional_timeout(timeout: float | None):
    """Context manager for optional timeout (works on Python 3.10+)."""
    if timeout and sys.version_info >= (3, 11):
        async with asyncio.timeout(timeout):
            yield
    else:
        yield


class RateLimiter:
    """Token bucket rate limiter for RPS control."""

    def __init__(self, rps: float | None) -> None:
        """Initialize with requests-per-second limit.

        Args:
            rps: Requests per second (None = unlimited).
        """
        self.rps = rps
        self.min_interval = (1.0 / rps) if rps else 0
        self._last_release = 0.0

    async def acquire(self) -> None:
        """Wait until rate limit allows next request."""
        if not self.rps:
            return
        elapsed = time.time() - self._last_release
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self._last_release = time.time()


class Executor:
    """Parallel, retried, rate-limited executor with adapter support.

    Features:
    - Configurable concurrency (Semaphore-based)
    - Exponential backoff retries per request
    - Rate limiting (RPS control)
    - Failure isolation (one failure doesn't kill the batch)
    - Per-request timeout separate from overall timeout
    - Latency + status_code tracking
    - Session lifecycle hooks (on_session_start/end)
    """

    def __init__(
        self,
        config: NPersonaConfig,
        adapter: RequestAdapter | None = None,
    ) -> None:
        """Initialize the executor.

        Args:
            config: NPersonaConfig with endpoint, timeouts, concurrency, retries.
            adapter: RequestAdapter (default: JsonPostAdapter from config).
        """
        if not config.system_endpoint:
            raise ValueError("system_endpoint is required to use the Executor.")

        self._config = config
        self._adapter = adapter or self._build_adapter(config)
        self._rate_limiter = RateLimiter(config.executor_rate_limit_rps)
        self._auth_handler = AuthHandler(config.auth_config)

    def _build_adapter(self, config: NPersonaConfig) -> RequestAdapter:
        """Build default JsonPostAdapter from config."""
        return JsonPostAdapter(
            endpoint=config.system_endpoint,
            headers=config.system_headers,
            request_field=config.request_field,
            response_field=config.response_field,
        )

    async def run(
        self,
        test_cases: list[TestCase],
        on_progress: object = None,
    ) -> list[TestResult]:
        """Execute all test cases in parallel with retries and rate limiting.

        Args:
            test_cases: List of test cases to execute.
            on_progress: Optional callback receiving {"stage", "message"}.

        Returns:
            List of TestResult (one per test, even if failed).
        """
        if not test_cases:
            return []

        self._emit(on_progress, f"Preparing {len(test_cases)} test cases...")

        # Session setup
        await self._adapter.on_session_start()

        semaphore = asyncio.Semaphore(self._config.executor_concurrency)

        try:
            async with _optional_timeout(self._config.overall_timeout):
                async with httpx.AsyncClient() as client:
                    tasks = [
                        self._execute_with_semaphore(
                            semaphore, client, tc, i + 1, len(test_cases), on_progress
                        )
                        for i, tc in enumerate(test_cases)
                    ]
                    results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to failed TestResults
            final_results: list[TestResult] = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    tc = test_cases[i]
                    final_results.append(
                        TestResult(
                            test_case_id=tc.id,
                            taxonomy_id=tc.taxonomy_id,
                            taxonomy_name=tc.taxonomy_name,
                            agent_target=tc.agent_target,
                            severity=tc.severity,
                            prompt_sent=tc.prompt,
                            response_received="",
                            passed=False,
                            failure_reason=str(result),
                            error=str(result),
                            attempts=1,
                        )
                    )
                else:
                    final_results.append(result)

            logger.info("Executed %d test cases (%d passed, %d failed)",
                       len(final_results),
                       sum(1 for r in final_results if r.passed),
                       sum(1 for r in final_results if not r.passed))
            return final_results

        finally:
            await self._adapter.on_session_end()

    async def _execute_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        client: httpx.AsyncClient,
        tc: TestCase,
        seq: int,
        total: int,
        on_progress: object,
    ) -> TestResult:
        """Acquire semaphore slot and execute a single test case."""
        async with semaphore:
            return await self._execute_single(client, tc, seq, total, on_progress)

    async def _execute_single(
        self,
        client: httpx.AsyncClient,
        tc: TestCase,
        seq: int,
        total: int,
        on_progress: object,
    ) -> TestResult:
        """Execute one test with retries, rate limiting, and telemetry.

        Supports both single-turn (tc.prompt) and multi-turn (tc.conversation_trajectory).
        """
        mode = "multi-turn" if tc.is_multi_turn and tc.conversation_trajectory else "single-turn"
        self._emit(on_progress, f"Test {seq}/{total}: [{tc.taxonomy_id}] {tc.agent_target} ({mode})")

        await self._adapter.on_request_begin(tc.id)
        start_time = time.time()
        attempts = 0
        last_exc: Exception | None = None
        responses: list[str] = []

        try:
            # Multi-turn: loop through conversation turns
            if tc.is_multi_turn and tc.conversation_trajectory:
                response = None
                for turn in tc.conversation_trajectory:
                    turn_success = False

                    async for attempt in AsyncRetrying(
                        stop=stop_after_attempt(self._config.executor_retries + 1),
                        wait=wait_exponential(multiplier=2, min=1, max=30),
                        retry=retry_if_exception_type((httpx.HTTPError, TimeoutError)),
                        reraise=False,
                    ):
                        with attempt:
                            attempts += 1
                            await self._rate_limiter.acquire()

                            # Create temporary test case with this turn's prompt for adapter
                            temp_tc = tc.model_copy(update={"prompt": turn.prompt})
                            req = await self._adapter.build_request(temp_tc)
                            # Apply authentication
                            req = await self._auth_handler.apply_auth(req)

                            response = await client.request(
                                req.method,
                                req.url,
                                headers=req.headers,
                                json=req.json,
                                timeout=self._config.per_request_timeout,
                            )
                            response.raise_for_status()

                            response_text = await self._adapter.parse_response(response.text)
                            responses.append(f"[Turn {turn.turn}] {response_text}")
                            turn_success = True
                            break  # Retry loop succeeded, move to next turn

                    # If this turn failed after all retries, abort multi-turn
                    if not turn_success:
                        last_exc = Exception(f"Turn {turn.turn} failed after {self._config.executor_retries + 1} attempts")
                        break

                # If all turns succeeded, return success
                if turn_success and responses:
                    latency_ms = (time.time() - start_time) * 1000
                    await self._adapter.on_request_end(tc.id, success=True)

                    return TestResult(
                        test_case_id=tc.id,
                        taxonomy_id=tc.taxonomy_id,
                        taxonomy_name=tc.taxonomy_name,
                        agent_target=tc.agent_target,
                        severity=tc.severity,
                        prompt_sent=tc.prompt,  # Log initial prompt
                        response_received="\n".join(responses),
                        passed=True,
                        failure_reason=None,
                        latency_ms=latency_ms,
                        status_code=response.status_code if response else None,
                        attempts=attempts,
                    )

            # Single-turn: original behavior
            else:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(self._config.executor_retries + 1),
                    wait=wait_exponential(multiplier=2, min=1, max=30),
                    retry=retry_if_exception_type((httpx.HTTPError, TimeoutError)),
                    reraise=False,
                ):
                    with attempt:
                        attempts += 1
                        await self._rate_limiter.acquire()

                        req = await self._adapter.build_request(tc)
                        # Apply authentication
                        req = await self._auth_handler.apply_auth(req)

                        response = await client.request(
                            req.method,
                            req.url,
                            headers=req.headers,
                            json=req.json,
                            timeout=self._config.per_request_timeout,
                        )
                        response.raise_for_status()

                        response_text = await self._adapter.parse_response(response.text)
                        latency_ms = (time.time() - start_time) * 1000

                        await self._adapter.on_request_end(tc.id, success=True)

                        return TestResult(
                            test_case_id=tc.id,
                            taxonomy_id=tc.taxonomy_id,
                            taxonomy_name=tc.taxonomy_name,
                            agent_target=tc.agent_target,
                            severity=tc.severity,
                            prompt_sent=tc.prompt,
                            response_received=response_text,
                            passed=True,
                            failure_reason=None,
                            latency_ms=latency_ms,
                            status_code=response.status_code,
                            attempts=attempts,
                        )

        except Exception as exc:
            last_exc = exc
            error_msg = _extract_error_message(exc)
            logger.warning("Test %s failed after %d attempts: %s", tc.id, attempts, error_msg)

        latency_ms = (time.time() - start_time) * 1000
        await self._adapter.on_request_end(tc.id, success=False)

        error_msg = _extract_error_message(last_exc) if last_exc else "Unknown error"
        return TestResult(
            test_case_id=tc.id,
            taxonomy_id=tc.taxonomy_id,
            taxonomy_name=tc.taxonomy_name,
            agent_target=tc.agent_target,
            severity=tc.severity,
            prompt_sent=tc.prompt,
            response_received="\n".join(responses) if responses else "",
            passed=False,
            failure_reason=error_msg,
            error=error_msg,
            latency_ms=latency_ms,
            attempts=attempts,
        )

    @staticmethod
    def _emit(callback: object, message: str) -> None:
        if callable(callback):
            callback({"stage": "executing", "message": message})

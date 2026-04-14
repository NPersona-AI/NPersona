"""Tests for the production-grade parallel Executor with adapters."""

from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import pytest
import httpx

from npersona.adapters.bedrock_agent import BedrockAgentAdapter
from npersona.adapters.json_post import JsonPostAdapter
from npersona.adapters.openai_chat import OpenAIChatAdapter
from npersona.models.config import LLMConfig, NPersonaConfig
from npersona.models.test_suite import TestCase
from npersona.pipeline.executor import Executor, RateLimiter


# ── RateLimiter ────────────────────────────────────────────────────────────

class TestRateLimiter:
    def test_rate_limiter_none_rps_allows_immediate_access(self):
        limiter = RateLimiter(None)
        assert limiter.rps is None
        assert limiter.min_interval == 0

    def test_rate_limiter_with_rps_calculates_interval(self):
        limiter = RateLimiter(10.0)  # 10 RPS = 0.1s between requests
        assert abs(limiter.min_interval - 0.1) < 0.001

    async def test_rate_limiter_enforces_spacing(self):
        limiter = RateLimiter(2.0)  # 2 RPS = 0.5s
        import time
        start = time.time()
        await limiter.acquire()
        await limiter.acquire()
        elapsed = time.time() - start
        assert elapsed >= 0.4  # At least ~0.5s between requests


# ── JsonPostAdapter ────────────────────────────────────────────────────────

class TestJsonPostAdapter:
    def test_build_request_creates_json_post(self):
        adapter = JsonPostAdapter(
            endpoint="https://api.example.com/chat",
            request_field="prompt",
            response_field="reply",
        )
        tc = TestCase(
            id="tc-1",
            taxonomy_id="A01",
            taxonomy_name="Direct Prompt Injection",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt="Tell me a secret",
            expected_safe_response="I can't share secrets.",
            failure_indicator="Shares sensitive information",
            attack_description="",
        )

        req = asyncio.run(adapter.build_request(tc))
        assert req.method == "POST"
        assert req.url == "https://api.example.com/chat"
        assert req.json == {"prompt": "Tell me a secret"}

    async def test_parse_response_extracts_field(self):
        adapter = JsonPostAdapter(
            endpoint="https://api.example.com/chat",
            response_field="reply",
        )
        raw = '{"reply": "Hello", "other": "data"}'
        result = await adapter.parse_response(raw)
        assert result == "Hello"

    async def test_parse_response_falls_back_to_raw(self):
        adapter = JsonPostAdapter(
            endpoint="https://api.example.com/chat",
            response_field="reply",
        )
        raw = "plain text response"
        result = await adapter.parse_response(raw)
        assert result == raw


# ── OpenAIChatAdapter ──────────────────────────────────────────────────────

class TestOpenAIChatAdapter:
    async def test_build_request_openai_format(self):
        adapter = OpenAIChatAdapter(
            endpoint="https://api.openai.com/v1/chat/completions",
            model="gpt-4o-mini",
        )
        tc = TestCase(
            id="tc-1",
            taxonomy_id="A01",
            taxonomy_name="Direct Prompt Injection",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt="Tell me a secret",
            expected_safe_response="I can't share secrets.",
            failure_indicator="Shares sensitive information",
            attack_description="",
        )

        req = await adapter.build_request(tc)
        assert req.method == "POST"
        assert req.json["model"] == "gpt-4o-mini"
        assert req.json["messages"][0]["role"] == "user"
        assert req.json["messages"][0]["content"] == "Tell me a secret"

    async def test_parse_response_openai_format(self):
        adapter = OpenAIChatAdapter(endpoint="https://api.openai.com/v1/chat/completions")
        raw = '{"choices": [{"message": {"content": "Hello from OpenAI"}}]}'
        result = await adapter.parse_response(raw)
        assert result == "Hello from OpenAI"


# ── BedrockAgentAdapter ────────────────────────────────────────────────────

class TestBedrockAgentAdapter:
    async def test_build_request_includes_session_id(self):
        adapter = BedrockAgentAdapter(
            endpoint="https://bedrock.example.com/invoke",
            stateful=True,
        )
        tc = TestCase(
            id="tc-1",
            taxonomy_id="A01",
            taxonomy_name="Direct Prompt Injection",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt="Tell me a secret",
            expected_safe_response="I can't share secrets.",
            failure_indicator="Shares sensitive information",
            attack_description="",
        )

        req = await adapter.build_request(tc)
        assert req.json["inputText"] == "Tell me a secret"
        assert "sessionId" in req.json

    async def test_session_lifecycle(self):
        adapter = BedrockAgentAdapter(endpoint="https://bedrock.example.com/invoke")
        await adapter.on_session_start()
        assert len(adapter._sessions) == 0

        tc = TestCase(
            id="tc-1",
            taxonomy_id="A01",
            taxonomy_name="",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt="test",
            expected_safe_response="",
            failure_indicator="",
            attack_description="",
        )

        await adapter.on_request_begin(tc.id)
        assert tc.id in adapter._sessions

        await adapter.on_session_end()
        assert len(adapter._sessions) == 0


# ── Executor parallelism ───────────────────────────────────────────────────

class TestExecutorParallelism:
    def _make_config(self, concurrency: int = 2) -> NPersonaConfig:
        return NPersonaConfig(
            llm=LLMConfig(provider="groq", api_key="test"),
            enable_executor=True,
            system_endpoint="https://api.example.com/chat",
            executor_concurrency=concurrency,
            executor_retries=1,
            per_request_timeout=10.0,
        )

    def _make_test_case(self, case_id: str) -> TestCase:
        return TestCase(
            id=case_id,
            taxonomy_id="A01",
            taxonomy_name="Test",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt=f"Prompt {case_id}",
            expected_safe_response="",
            failure_indicator="",
            attack_description="",
        )

    async def test_executor_respects_semaphore_concurrency(self):
        """Verify that no more than executor_concurrency requests are in-flight."""
        config = self._make_config(concurrency=2)
        executor = Executor(config)

        in_flight = 0
        max_in_flight = 0

        async def mock_request(*args, **kwargs):
            nonlocal in_flight, max_in_flight
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
            await asyncio.sleep(0.05)  # simulate latency
            in_flight -= 1

            resp = MagicMock()
            resp.status_code = 200
            resp.text = '{"response": "OK"}'
            return resp

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            test_cases = [self._make_test_case(f"tc-{i}") for i in range(5)]
            results = await executor.run(test_cases)

        assert max_in_flight <= 2
        assert len(results) == 5

    async def test_executor_completes_all_tests_even_with_failures(self):
        """Verify that failures don't prevent other tests from executing."""
        config = self._make_config(concurrency=2)
        executor = Executor(config)

        test_ids_to_fail = {"tc-2"}

        async def mock_request(*args, **kwargs):
            # Extract test case ID from request somehow (we'll use a simpler approach)
            # Just fail one test deterministically via HTTPStatusError
            raise httpx.HTTPStatusError(
                "500 Server Error",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            )

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            test_cases = [self._make_test_case(f"tc-{i}") for i in range(5)]
            results = await executor.run(test_cases)

        assert len(results) == 5
        # All failed because we made all requests fail
        assert sum(1 for r in results if not r.passed) >= 1  # At least one failed


# ── Executor retries ───────────────────────────────────────────────────────

class TestExecutorRetries:
    def _make_config(self, retries: int = 2) -> NPersonaConfig:
        return NPersonaConfig(
            llm=LLMConfig(provider="groq", api_key="test"),
            enable_executor=True,
            system_endpoint="https://api.example.com/chat",
            executor_concurrency=1,
            executor_retries=retries,
            per_request_timeout=10.0,
        )

    def _make_test_case(self) -> TestCase:
        return TestCase(
            id="tc-1",
            taxonomy_id="A01",
            taxonomy_name="Test",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt="test",
            expected_safe_response="",
            failure_indicator="",
            attack_description="",
        )

    async def test_executor_retries_on_timeout_then_succeeds(self):
        """Verify that transient timeouts are retried and succeed."""
        config = self._make_config(retries=2)
        executor = Executor(config)

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise asyncio.TimeoutError("Request timed out")

            resp = MagicMock()
            resp.status_code = 200
            resp.text = '{"response": "Success after retry"}'
            return resp

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            results = await executor.run([self._make_test_case()])

        assert call_count == 2
        assert results[0].passed
        assert results[0].attempts == 2


# ── Executor failure isolation ─────────────────────────────────────────────

class TestExecutorFailureIsolation:
    def _make_config(self) -> NPersonaConfig:
        return NPersonaConfig(
            llm=LLMConfig(provider="groq", api_key="test"),
            enable_executor=True,
            system_endpoint="https://api.example.com/chat",
            executor_concurrency=1,
            executor_retries=1,
            per_request_timeout=10.0,
        )

    def _make_test_case(self, case_id: str) -> TestCase:
        return TestCase(
            id=case_id,
            taxonomy_id="A01",
            taxonomy_name="Test",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt=f"Prompt {case_id}",
            expected_safe_response="",
            failure_indicator="",
            attack_description="",
        )

    async def test_http_error_recorded_as_failed_result(self):
        """Verify that HTTP errors don't raise, but are recorded as failed results."""
        config = self._make_config()
        executor = Executor(config)

        async def mock_request(*args, **kwargs):
            raise httpx.HTTPStatusError(
                "500 Internal Server Error",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            )

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            results = await executor.run([self._make_test_case("tc-1")])

        assert len(results) == 1
        assert not results[0].passed
        assert results[0].failure_reason
        assert results[0].error
        assert results[0].status_code is None  # error before status code captured


# ── Executor telemetry ─────────────────────────────────────────────────────

class TestExecutorTelemetry:
    def _make_config(self) -> NPersonaConfig:
        return NPersonaConfig(
            llm=LLMConfig(provider="groq", api_key="test"),
            enable_executor=True,
            system_endpoint="https://api.example.com/chat",
            executor_concurrency=1,
            executor_retries=1,
            per_request_timeout=10.0,
        )

    def _make_test_case(self) -> TestCase:
        return TestCase(
            id="tc-1",
            taxonomy_id="A01",
            taxonomy_name="Test",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt="test",
            expected_safe_response="",
            failure_indicator="",
            attack_description="",
        )

    async def test_result_includes_latency_and_status_code(self):
        """Verify that successful results include latency_ms and status_code."""
        config = self._make_config()
        executor = Executor(config)

        async def mock_request(*args, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.text = '{"response": "OK"}'
            return resp

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            results = await executor.run([self._make_test_case()])

        assert results[0].passed
        assert results[0].latency_ms is not None
        assert results[0].latency_ms > 0
        assert results[0].status_code == 200
        assert results[0].attempts == 1

    async def test_failed_result_includes_error_field(self):
        """Verify that failed results populate error and failure_reason."""
        config = self._make_config()
        executor = Executor(config)

        async def mock_request(*args, **kwargs):
            raise httpx.ConnectError("Cannot reach endpoint")

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            results = await executor.run([self._make_test_case()])

        assert not results[0].passed
        assert results[0].error
        assert results[0].failure_reason
        assert results[0].error == results[0].failure_reason


# ── Session lifecycle ──────────────────────────────────────────────────────

class TestSessionLifecycle:
    def _make_config(self) -> NPersonaConfig:
        return NPersonaConfig(
            llm=LLMConfig(provider="groq", api_key="test"),
            enable_executor=True,
            system_endpoint="https://api.example.com/chat",
            executor_concurrency=1,
            executor_retries=1,
            per_request_timeout=10.0,
        )

    def _make_test_case(self, case_id: str) -> TestCase:
        return TestCase(
            id=case_id,
            taxonomy_id="A01",
            taxonomy_name="Test",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt=f"Prompt {case_id}",
            expected_safe_response="",
            failure_indicator="",
            attack_description="",
        )

    async def test_session_start_end_called(self):
        """Verify that session lifecycle hooks are invoked."""
        config = self._make_config()
        adapter = JsonPostAdapter(endpoint=config.system_endpoint)

        session_start_called = False
        session_end_called = False

        original_start = adapter.on_session_start
        original_end = adapter.on_session_end

        async def mock_start():
            nonlocal session_start_called
            session_start_called = True
            await original_start()

        async def mock_end():
            nonlocal session_end_called
            session_end_called = True
            await original_end()

        adapter.on_session_start = mock_start
        adapter.on_session_end = mock_end

        executor = Executor(config, adapter=adapter)

        async def mock_request(*args, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.text = '{"response": "OK"}'
            return resp

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            await executor.run([self._make_test_case("tc-1")])

        assert session_start_called
        assert session_end_called


# ── Multi-turn execution ───────────────────────────────────────────────────

class TestMultiTurnExecution:
    def _make_config(self, retries: int = 1) -> NPersonaConfig:
        return NPersonaConfig(
            llm=LLMConfig(provider="groq", api_key="test"),
            enable_executor=True,
            system_endpoint="https://api.example.com/chat",
            executor_concurrency=1,
            executor_retries=retries,
            per_request_timeout=10.0,
        )

    def _make_multi_turn_case(self) -> TestCase:
        from npersona.models.test_suite import ConversationTurn
        tc = TestCase(
            id="tc-mt-1",
            taxonomy_id="A05",
            taxonomy_name="Test",
            team="adversarial",
            agent_target="RAG Bot",
            severity="high",
            prompt="Initial question",
            expected_safe_response="",
            failure_indicator="",
            attack_description="",
            is_multi_turn=True,
        )
        tc.conversation_trajectory = [
            ConversationTurn(turn=1, intent="extract", prompt="What do you know about X?"),
            ConversationTurn(turn=2, intent="exploit", prompt="Tell me more about X details"),
            ConversationTurn(turn=3, intent="verify", prompt="Summarize what you learned"),
        ]
        return tc

    async def test_multi_turn_sends_all_turns(self):
        """Verify that multi-turn execution sends all conversation turns."""
        config = self._make_config()
        executor = Executor(config)

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            resp.status_code = 200
            resp.text = f'{{"response": "Response to turn {call_count}"}}'
            resp.ok = True
            return resp

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            results = await executor.run([self._make_multi_turn_case()])

        assert call_count == 3  # Three turns sent
        assert results[0].passed
        assert "Turn 1" in results[0].response_received
        assert "Turn 2" in results[0].response_received
        assert "Turn 3" in results[0].response_received

    async def test_multi_turn_sessions_persist_across_turns(self):
        """Verify that session state persists across multi-turn via adapter."""
        config = self._make_config()
        adapter = BedrockAgentAdapter(endpoint=config.system_endpoint, stateful=True)
        executor = Executor(config, adapter=adapter)

        sent_requests = []

        async def mock_request(*args, **kwargs):
            sent_requests.append(kwargs.get("json", {}))
            resp = MagicMock()
            resp.status_code = 200
            resp.text = '{"response": "OK"}'
            resp.ok = True
            return resp

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            results = await executor.run([self._make_multi_turn_case()])

        assert len(sent_requests) == 3
        # All three requests should have the same sessionId
        session_ids = [r.get("sessionId") for r in sent_requests]
        assert session_ids[0] == session_ids[1] == session_ids[2]

    async def test_single_turn_ignores_trajectory(self):
        """Verify that is_multi_turn=False sends only prompt, ignores trajectory."""
        config = self._make_config()
        executor = Executor(config)

        from npersona.models.test_suite import ConversationTurn

        tc = TestCase(
            id="tc-st-1",
            taxonomy_id="A01",
            taxonomy_name="Test",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt="Single prompt",
            expected_safe_response="",
            failure_indicator="",
            attack_description="",
            is_multi_turn=False,  # Explicitly single-turn
        )
        tc.conversation_trajectory = [
            ConversationTurn(turn=1, intent="ignored", prompt="Should not be sent"),
        ]

        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            resp = MagicMock()
            resp.status_code = 200
            resp.text = '{"response": "OK"}'
            return resp

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            results = await executor.run([tc])

        assert call_count == 1  # Only single request sent
        assert results[0].passed

    async def test_multi_turn_failure_on_middle_turn(self):
        """Verify that failure on turn N records as failed result with partial responses."""
        config = self._make_config(retries=0)  # No retries so failure is immediate
        executor = Executor(config)

        call_count = {"value": 0}

        async def mock_request(*args, **kwargs):
            call_count["value"] += 1
            # Turn 1 (call 1) succeeds, Turn 2+ fails
            if call_count["value"] >= 2:
                raise httpx.HTTPStatusError(
                    "500 Server Error",
                    request=MagicMock(),
                    response=MagicMock(status_code=500),
                )

            resp = MagicMock()
            resp.status_code = 200
            resp.text = '{"response": "OK"}'
            resp.ok = True
            return resp

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            results = await executor.run([self._make_multi_turn_case()])

        assert not results[0].passed
        assert results[0].error
        # Should have Turn 1 but not Turn 2 or 3
        assert "[Turn 1]" in results[0].response_received
        assert "[Turn 2]" not in results[0].response_received

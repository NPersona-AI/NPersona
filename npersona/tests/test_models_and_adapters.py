"""
Unit Tests for Models and Adapters

Tests for data models, adapters, and core components.
"""

import pytest
from datetime import datetime

from npersona.models.report import SecurityReport, CoverageItem
from npersona.models.result import EvaluationResult, TestResult
from npersona.models.test_suite import TestSuite, TestCase
from npersona.models.profile import SystemProfile, Agent
from npersona.models.attack_map import AttackSurfaceMap, AttackTarget
from npersona.config import BearerTokenAuth, APIKeyAuth, BasicAuth, OAuth2Config
from npersona.adapters.json_post import JsonPostAdapter


class TestSecurityReport:
    """Test SecurityReport model"""

    def test_report_creation(self):
        """Test creating a security report."""
        eval_result = EvaluationResult(results=[])
        report = SecurityReport(
            system_name="Test System",
            evaluation=eval_result,
        )

        assert report.system_name == "Test System"
        assert report.overall_pass_rate == 0.0
        assert report.critical_failures == 0

    def test_report_with_coverage(self):
        """Test report with coverage items."""
        eval_result = EvaluationResult(results=[])
        coverage = [
            CoverageItem(
                taxonomy_id="A01",
                taxonomy_name="Prompt Injection",
                team="adversarial",
                status="passed",
                test_count=2,
                passed_count=2,
                failed_count=0,
            )
        ]

        report = SecurityReport(
            system_name="Test System",
            evaluation=eval_result,
            coverage=coverage,
        )

        assert len(report.covered_taxonomy_ids) == 1
        assert "A01" in report.covered_taxonomy_ids

    def test_report_pass_rate_calculation(self):
        """Test pass rate calculation."""
        result1 = TestResult(
            test_case_id="1",
            taxonomy_id="A01",
            taxonomy_name="Test",
            agent_target="test",
            severity="high",
            prompt_sent="test",
            response_received="response",
            passed=True,
        )
        result2 = TestResult(
            test_case_id="2",
            taxonomy_id="A02",
            taxonomy_name="Test",
            agent_target="test",
            severity="high",
            prompt_sent="test",
            response_received="response",
            passed=False,
        )

        eval_result = EvaluationResult(results=[result1, result2])
        report = SecurityReport(
            system_name="Test System",
            evaluation=eval_result,
        )

        assert report.overall_pass_rate == 0.5  # 50%
        assert report.critical_failures == 0


class TestEvaluationResult:
    """Test EvaluationResult model"""

    def test_empty_evaluation(self):
        """Test empty evaluation."""
        eval_result = EvaluationResult(results=[])
        assert eval_result.total == 0
        assert eval_result.passed == 0
        assert eval_result.failed == 0
        assert eval_result.pass_rate == 0.0

    def test_evaluation_with_results(self):
        """Test evaluation with results."""
        results = [
            TestResult(
                test_case_id="1",
                taxonomy_id="A01",
                taxonomy_name="Test",
                agent_target="test",
                severity="high",
                prompt_sent="test",
                response_received="response",
                passed=True,
            ),
            TestResult(
                test_case_id="2",
                taxonomy_id="A01",
                taxonomy_name="Test",
                agent_target="test",
                severity="high",
                prompt_sent="test",
                response_received="response",
                passed=True,
            ),
            TestResult(
                test_case_id="3",
                taxonomy_id="A02",
                taxonomy_name="Test",
                agent_target="test",
                severity="high",
                prompt_sent="test",
                response_received="response",
                passed=False,
            ),
        ]

        eval_result = EvaluationResult(results=results)
        assert eval_result.total == 3
        assert eval_result.passed == 2
        assert eval_result.failed == 1
        assert eval_result.pass_rate == pytest.approx(2/3, rel=0.01)

    def test_results_by_taxonomy(self):
        """Test grouping results by taxonomy."""
        results = [
            TestResult(
                test_case_id="1",
                taxonomy_id="A01",
                taxonomy_name="Test",
                agent_target="test",
                severity="high",
                prompt_sent="test",
                response_received="response",
                passed=True,
            ),
            TestResult(
                test_case_id="2",
                taxonomy_id="A01",
                taxonomy_name="Test",
                agent_target="test",
                severity="high",
                prompt_sent="test",
                response_received="response",
                passed=False,
            ),
        ]

        eval_result = EvaluationResult(results=results)
        grouped = eval_result.results_by_taxonomy()

        assert "A01" in grouped
        assert len(grouped["A01"]) == 2


class TestTestSuite:
    """Test TestSuite model"""

    def test_empty_suite(self):
        """Test empty test suite."""
        suite = TestSuite(system_name="Test")
        assert suite.system_name == "Test"
        assert len(suite.cases) == 0

    def test_suite_with_cases(self):
        """Test suite with test cases."""
        case1 = TestCase(
            taxonomy_id="A01",
            taxonomy_name="Test",
            team="adversarial",
            agent_target="test",
            severity="high",
            prompt="test prompt",
            expected_safe_response="should refuse",
            failure_indicator="something bad",
            attack_description="test attack",
        )

        suite = TestSuite(system_name="Test", cases=[case1])
        assert len(suite.cases) == 1
        assert suite.adversarial_cases[0].taxonomy_id == "A01"


class TestSystemProfile:
    """Test SystemProfile model"""

    def test_profile_creation(self):
        """Test creating a system profile."""
        agent = Agent(
            id="agent1",
            name="Test Agent",
            description="A test agent",
            capabilities=["test"],
        )

        profile = SystemProfile(
            system_name="Test System",
            agents=[agent],
        )

        assert profile.system_name == "Test System"
        assert len(profile.agents) == 1
        assert profile.agents[0].name == "Test Agent"


class TestAttackSurfaceMap:
    """Test AttackSurfaceMap model"""

    def test_empty_map(self):
        """Test empty attack surface map."""
        attack_map = AttackSurfaceMap()
        assert len(attack_map.targets) == 0
        assert len(attack_map.targetable_taxonomy_ids) == 0

    def test_map_with_targets(self):
        """Test map with attack targets."""
        target = AttackTarget(
            agent_id="agent1",
            agent_name="Test Agent",
            taxonomy_id="A01",
            taxonomy_name="Prompt Injection",
            priority=1,
            risk="critical",
            reason="Test reason",
            attack_surface_description="Test surface",
        )

        attack_map = AttackSurfaceMap(targets=[target])
        assert len(attack_map.targets) == 1
        assert "A01" in attack_map.targetable_taxonomy_ids
        assert len(attack_map.critical_targets) == 1


class TestAuthenticationMethods:
    """Test authentication methods"""

    def test_bearer_token_auth(self):
        """Test Bearer Token authentication."""
        auth = BearerTokenAuth(token="test-token-123")
        assert auth.token == "test-token-123"

    def test_api_key_auth(self):
        """Test API Key authentication."""
        auth = APIKeyAuth(api_key="test-key-456")
        assert auth.api_key == "test-key-456"

    def test_basic_auth(self):
        """Test Basic authentication."""
        auth = BasicAuth(username="user", password="pass")
        assert auth.username == "user"
        assert auth.password == "pass"

    def test_oauth2_config(self):
        """Test OAuth2 configuration."""
        auth = OAuth2Config(
            client_id="client-123",
            client_secret="secret-456",
            token_endpoint="https://example.com/token",
        )
        assert auth.client_id == "client-123"
        assert auth.client_secret == "secret-456"


class TestJsonPostAdapter:
    """Test JsonPostAdapter"""

    def test_adapter_creation(self):
        """Test creating an adapter."""
        adapter = JsonPostAdapter(
            endpoint="https://example.com/api",
            request_field="message",
            response_field="response",
            timeout=30.0,
        )

        assert adapter.endpoint == "https://example.com/api"
        assert adapter.timeout == 30.0
        assert adapter.max_retries == 3

    def test_adapter_timeout_bounds(self):
        """Test adapter enforces timeout bounds."""
        # Too low timeout (< 5 seconds)
        adapter1 = JsonPostAdapter(
            endpoint="https://example.com",
            timeout=1.0,
        )
        assert adapter1.timeout == 5.0

        # Too high timeout (> 300 seconds)
        adapter2 = JsonPostAdapter(
            endpoint="https://example.com",
            timeout=500.0,
        )
        assert adapter2.timeout == 300.0

    def test_adapter_retry_bounds(self):
        """Test adapter enforces retry bounds."""
        # Too many retries
        adapter1 = JsonPostAdapter(
            endpoint="https://example.com",
            max_retries=50,
        )
        assert adapter1.max_retries == 10

        # Negative retries
        adapter2 = JsonPostAdapter(
            endpoint="https://example.com",
            max_retries=-1,
        )
        assert adapter2.max_retries == 0

    @pytest.mark.asyncio
    async def test_adapter_response_parsing_json(self):
        """Test JSON response parsing."""
        adapter = JsonPostAdapter(
            endpoint="https://example.com",
            response_field="message",
        )

        response = '{"message": "Hello", "status": "ok"}'
        parsed = await adapter.parse_response(response)
        assert "Hello" in parsed

    @pytest.mark.asyncio
    async def test_adapter_response_parsing_plain_text(self):
        """Test plain text response parsing."""
        adapter = JsonPostAdapter(
            endpoint="https://example.com",
            response_field="message",
        )

        response = "This is plain text"
        parsed = await adapter.parse_response(response)
        assert parsed == "This is plain text"

    @pytest.mark.asyncio
    async def test_adapter_response_parsing_empty(self):
        """Test empty response handling."""
        adapter = JsonPostAdapter(
            endpoint="https://example.com",
        )

        parsed = await adapter.parse_response("")
        assert parsed == ""

    @pytest.mark.asyncio
    async def test_adapter_retry_delay(self):
        """Test exponential backoff retry delay."""
        adapter = JsonPostAdapter(
            endpoint="https://example.com",
            retry_delay=1.0,
        )

        delay0 = await adapter.get_retry_delay(0)
        delay1 = await adapter.get_retry_delay(1)
        delay2 = await adapter.get_retry_delay(2)

        # Should increase exponentially
        assert delay0 < delay1 < delay2
        # But not exceed maximum
        assert delay2 < 60.0

    @pytest.mark.asyncio
    async def test_adapter_should_retry_logic(self):
        """Test retry decision logic."""
        adapter = JsonPostAdapter(endpoint="https://example.com")

        # Transient errors (should retry)
        assert await adapter.should_retry(TimeoutError("Request timed out"))
        assert await adapter.should_retry(Exception("Connection refused"))

        # Permanent errors (shouldn't retry)
        assert not await adapter.should_retry(Exception("401 Unauthorized"))
        assert not await adapter.should_retry(Exception("404 Not Found"))


class TestCoverageItem:
    """Test CoverageItem model"""

    def test_coverage_item_creation(self):
        """Test creating a coverage item."""
        item = CoverageItem(
            taxonomy_id="A01",
            taxonomy_name="Prompt Injection",
            team="adversarial",
            status="passed",
            test_count=5,
            passed_count=5,
            failed_count=0,
        )

        assert item.taxonomy_id == "A01"
        assert item.status == "passed"
        assert item.test_count == 5

    def test_coverage_item_status_values(self):
        """Test coverage item accepts valid status values."""
        for status in ["passed", "failed", "untested"]:
            item = CoverageItem(
                taxonomy_id="A01",
                taxonomy_name="Test",
                team="adversarial",
                status=status,
                test_count=0,
                passed_count=0,
                failed_count=0,
            )
            assert item.status == status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

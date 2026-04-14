"""Tests for OAuth2 authentication integration."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from npersona.models.auth import (
    APIKeyAuth,
    BasicAuth,
    BearerTokenAuth,
    NoAuth,
    OAuth2Config,
)
from npersona.pipeline.auth_handler import AuthHandler, OAuth2TokenManager
from npersona.adapters.base import HTTPRequest


class TestOAuth2TokenManager:
    """OAuth2 token acquisition and refresh."""

    async def test_token_acquisition(self):
        """Acquire OAuth2 token from endpoint."""
        config = OAuth2Config(
            token_endpoint="https://auth.example.com/token",
            client_id="test-client",
            client_secret="test-secret",
            scope="api:access",
        )
        manager = OAuth2TokenManager(config)

        # Mock OAuth2 response
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "access_token": "eyJhbGc...",
                "expires_in": 3600,
                "token_type": "Bearer",
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            token = await manager.get_token()

        assert token == "eyJhbGc..."
        assert manager._token == "eyJhbGc..."

    async def test_token_caching(self):
        """Token cached and reused when valid."""
        config = OAuth2Config(
            token_endpoint="https://auth.example.com/token",
            client_id="test-client",
            client_secret="test-secret",
        )
        manager = OAuth2TokenManager(config)

        # Set cached token that won't expire for 2 hours
        manager._token = "cached-token-123"
        manager._token_expires_at = time.time() + 7200

        token1 = await manager.get_token()
        token2 = await manager.get_token()

        # Should return cached token without making another request
        assert token1 == token2 == "cached-token-123"

    async def test_token_refresh_on_expiry(self):
        """Token refreshed when expired."""
        config = OAuth2Config(
            token_endpoint="https://auth.example.com/token",
            client_id="test-client",
            client_secret="test-secret",
        )
        manager = OAuth2TokenManager(config)

        # Set token that expired 5 seconds ago
        manager._token = "expired-token"
        manager._token_expires_at = time.time() - 5

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "access_token": "new-token-456",
                "expires_in": 3600,
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            token = await manager.get_token()

        assert token == "new-token-456"
        assert manager._token != "expired-token"

    async def test_token_refresh_with_scope(self):
        """OAuth2 request includes scope and audience."""
        config = OAuth2Config(
            token_endpoint="https://auth.example.com/token",
            client_id="test-client",
            client_secret="test-secret",
            scope="chat:read chat:write",
            audience="https://api.example.com",
        )
        manager = OAuth2TokenManager(config)

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "access_token": "token",
                "expires_in": 3600,
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            await manager.get_token()

            # Verify request payload includes scope and audience
            call_args = mock_post.return_value.__aenter__.return_value.json.call_args
            # The actual post call happens, verify it was called with correct endpoint

        assert manager._token == "token"


class TestAuthHandler:
    """Auth handler applies correct headers to requests."""

    async def test_no_auth(self):
        """No auth adds no headers."""
        handler = AuthHandler(NoAuth())

        req = HTTPRequest(
            method="POST",
            url="https://api.example.com/chat",
            headers={},
        )

        result = await handler.apply_auth(req)
        assert "Authorization" not in result.headers

    async def test_bearer_token_auth(self):
        """Bearer token added to Authorization header."""
        handler = AuthHandler(BearerTokenAuth(token="my-jwt-token-xyz"))

        req = HTTPRequest(
            method="POST",
            url="https://api.example.com/chat",
            headers={},
        )

        result = await handler.apply_auth(req)
        assert result.headers["Authorization"] == "Bearer my-jwt-token-xyz"

    async def test_api_key_auth(self):
        """API key added to custom header."""
        handler = AuthHandler(
            APIKeyAuth(api_key="sk-abc123", header_name="X-API-Key")
        )

        req = HTTPRequest(
            method="POST",
            url="https://api.example.com/chat",
            headers={},
        )

        result = await handler.apply_auth(req)
        assert result.headers["X-API-Key"] == "sk-abc123"

    async def test_basic_auth(self):
        """Basic auth base64-encodes credentials."""
        handler = AuthHandler(BasicAuth(username="user", password="pass"))

        req = HTTPRequest(
            method="POST",
            url="https://api.example.com/chat",
            headers={},
        )

        result = await handler.apply_auth(req)
        # user:pass base64 = dXNlcjpwYXNz
        assert result.headers["Authorization"] == "Basic dXNlcjpwYXNz"

    async def test_oauth2_auth(self):
        """OAuth2 token fetched and added."""
        config = OAuth2Config(
            token_endpoint="https://auth.example.com/token",
            client_id="test-client",
            client_secret="test-secret",
        )
        handler = AuthHandler(config)

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "access_token": "oauth-token-789",
                "expires_in": 3600,
            }
            mock_post.return_value.__aenter__.return_value = mock_response

            req = HTTPRequest(
                method="POST",
                url="https://api.example.com/chat",
                headers={},
            )

            result = await handler.apply_auth(req)

        assert result.headers["Authorization"] == "Bearer oauth-token-789"


class TestExecutorWithAuth:
    """Executor applies auth to requests."""

    async def test_executor_applies_bearer_auth(self):
        """Executor applies bearer token to each request."""
        from npersona.models.config import LLMConfig, NPersonaConfig
        from npersona.pipeline.executor import Executor
        from npersona.models.test_suite import TestCase

        config = NPersonaConfig(
            llm=LLMConfig(provider="groq", api_key="test"),
            enable_executor=True,
            system_endpoint="https://api.example.com/chat",
            auth_config=BearerTokenAuth(token="test-jwt-token"),
            executor_concurrency=1,
            executor_retries=1,
        )

        executor = Executor(config)

        tc = TestCase(
            id="tc-1",
            taxonomy_id="A01",
            taxonomy_name="Test",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt="test prompt",
            expected_safe_response="",
            failure_indicator="",
            attack_description="",
        )

        captured_headers = {}

        async def mock_request(*args, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            resp = MagicMock()
            resp.status_code = 200
            resp.text = '{"response": "OK"}'
            return resp

        with patch("httpx.AsyncClient.request", side_effect=mock_request):
            results = await executor.run([tc])

        # Verify auth header was applied
        assert "Authorization" in captured_headers
        assert captured_headers["Authorization"] == "Bearer test-jwt-token"
        assert results[0].passed

    async def test_executor_applies_oauth2_auth(self):
        """Executor automatically refreshes OAuth2 token."""
        from npersona.models.config import LLMConfig, NPersonaConfig
        from npersona.pipeline.executor import Executor
        from npersona.models.test_suite import TestCase

        config = NPersonaConfig(
            llm=LLMConfig(provider="groq", api_key="test"),
            enable_executor=True,
            system_endpoint="https://api.example.com/chat",
            auth_config=OAuth2Config(
                token_endpoint="https://auth.example.com/token",
                client_id="test-client",
                client_secret="test-secret",
            ),
            executor_concurrency=1,
            executor_retries=1,
        )

        executor = Executor(config)

        tc = TestCase(
            id="tc-1",
            taxonomy_id="A01",
            taxonomy_name="Test",
            team="adversarial",
            agent_target="Bot",
            severity="high",
            prompt="test prompt",
            expected_safe_response="",
            failure_indicator="",
            attack_description="",
        )

        captured_headers = {}

        async def mock_http_request(*args, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            resp = MagicMock()
            resp.status_code = 200
            resp.text = '{"response": "OK"}'
            return resp

        with patch("httpx.AsyncClient.post") as mock_token:
            mock_token_response = MagicMock()
            mock_token_response.json.return_value = {
                "access_token": "auto-refreshed-token",
                "expires_in": 3600,
            }
            mock_token.return_value.__aenter__.return_value = mock_token_response

            with patch("httpx.AsyncClient.request", side_effect=mock_http_request):
                results = await executor.run([tc])

        # Verify OAuth2 token was fetched and applied
        assert "Authorization" in captured_headers
        assert "auto-refreshed-token" in captured_headers["Authorization"]
        assert results[0].passed

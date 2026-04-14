"""Authentication handler — manages OAuth2 tokens, applies auth headers."""

from __future__ import annotations

import base64
import logging
import time
from typing import Any

import httpx

from npersona.adapters.base import HTTPRequest
from npersona.models.auth import (
    APIKeyAuth,
    AuthConfig,
    BasicAuth,
    BearerTokenAuth,
    NoAuth,
    OAuth2Config,
)

logger = logging.getLogger(__name__)


class OAuth2TokenManager:
    """Manages OAuth2 token acquisition and refresh."""

    def __init__(self, config: OAuth2Config) -> None:
        self.config = config
        self._token: str | None = None
        self._token_expires_at: float = 0
        self._lock = None  # Will use asyncio.Lock on first use

    async def get_token(self) -> str:
        """Get valid OAuth2 token, refreshing if needed."""
        now = time.time()

        # Return cached token if still valid (with 60s buffer)
        if self._token and now < self._token_expires_at - 60:
            return self._token

        logger.debug("OAuth2 token expired or missing, requesting new token")
        return await self._refresh_token()

    async def _refresh_token(self) -> str:
        """Request new OAuth2 token from token endpoint."""
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }

        if self.config.scope:
            payload["scope"] = self.config.scope
        if self.config.audience:
            payload["audience"] = self.config.audience

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.token_endpoint,
                    data=payload,
                    timeout=30,
                )
                response.raise_for_status()
                data = response.json()

                self._token = data["access_token"]
                expires_in = data.get("expires_in", 3600)
                self._token_expires_at = time.time() + expires_in

                logger.info("OAuth2 token acquired (expires in %ds)", expires_in)
                return self._token

        except Exception as exc:
            logger.error("OAuth2 token request failed: %s", exc)
            raise


class AuthHandler:
    """Applies authentication to HTTP requests."""

    def __init__(self, auth_config: AuthConfig | None = None) -> None:
        self.config = auth_config or NoAuth()
        self._oauth2_manager: OAuth2TokenManager | None = None

        if isinstance(self.config, OAuth2Config):
            self._oauth2_manager = OAuth2TokenManager(self.config)

    async def apply_auth(self, request: HTTPRequest) -> HTTPRequest:
        """Add authentication headers to request."""
        if isinstance(self.config, NoAuth):
            return request

        if isinstance(self.config, BearerTokenAuth):
            request.headers["Authorization"] = f"Bearer {self.config.token}"
            return request

        if isinstance(self.config, APIKeyAuth):
            request.headers[self.config.header_name] = self.config.api_key
            return request

        if isinstance(self.config, BasicAuth):
            creds = f"{self.config.username}:{self.config.password}"
            encoded = base64.b64encode(creds.encode()).decode()
            request.headers["Authorization"] = f"Basic {encoded}"
            return request

        if isinstance(self.config, OAuth2Config):
            if not self._oauth2_manager:
                raise RuntimeError("OAuth2 manager not initialized")

            token = await self._oauth2_manager.get_token()
            request.headers["Authorization"] = f"Bearer {token}"
            return request

        # Custom auth is handled by caller via CustomCallableAdapter

        return request

"""Authentication configuration for different target systems."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AuthConfig(BaseModel):
    """Base authentication configuration."""

    type: Literal["none", "bearer", "api_key", "basic", "oauth2", "custom"] = "none"


class NoAuth(AuthConfig):
    """No authentication required."""

    type: Literal["none"] = "none"


class BearerTokenAuth(AuthConfig):
    """Bearer token authentication (Authorization: Bearer <token>)."""

    type: Literal["bearer"] = "bearer"
    token: str = Field(..., description="Bearer token")


class APIKeyAuth(AuthConfig):
    """API key authentication (custom header or query param)."""

    type: Literal["api_key"] = "api_key"
    api_key: str = Field(..., description="API key value")
    header_name: str = Field(default="X-API-Key", description="Header name for API key")
    # Alternative: query_param: str = "api_key"


class BasicAuth(AuthConfig):
    """HTTP Basic Authentication (base64-encoded username:password)."""

    type: Literal["basic"] = "basic"
    username: str
    password: str


class OAuth2Config(AuthConfig):
    """OAuth2 authentication (Bearer token from OAuth2 provider)."""

    type: Literal["oauth2"] = "oauth2"
    token_endpoint: str = Field(..., description="OAuth2 token endpoint URL")
    client_id: str
    client_secret: str
    scope: str = Field(default="", description="OAuth2 scopes (space-separated)")
    audience: str = Field(default="", description="Optional audience for token")


class CustomAuth(AuthConfig):
    """Custom authentication via user-supplied callable."""

    type: Literal["custom"] = "custom"
    # User provides function: async def add_auth(request: HTTPRequest) -> HTTPRequest
    callable_name: str = Field(..., description="Function name (resolved at runtime)")

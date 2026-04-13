"""NPersona Configuration - Authentication and Settings."""

from dataclasses import dataclass
from typing import Optional, Callable, List, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class BearerTokenAuth:
    """Bearer Token Authentication."""
    token: str
    header_name: str = "Authorization"
    
    def get_headers(self) -> dict:
        """Return headers with bearer token."""
        return {self.header_name: f"Bearer {self.token}"}


@dataclass
class OAuth2Config:
    """OAuth2 Client Credentials Authentication."""
    client_id: str
    client_secret: str
    token_endpoint: str
    scope: Optional[str] = None
    audience: Optional[str] = None
    token_cache_enabled: bool = True
    token_refresh_buffer: int = 60
    
    async def get_token(self) -> str:
        """Get OAuth2 token from endpoint."""
        import httpx
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        if self.scope:
            data["scope"] = self.scope
        if self.audience:
            data["audience"] = self.audience
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.token_endpoint, data=data)
            response.raise_for_status()
            token_data = response.json()
            return token_data["access_token"]


@dataclass
class APIKeyAuth:
    """API Key Authentication."""
    api_key: str
    header_name: str = "X-API-Key"
    
    def get_headers(self) -> dict:
        """Return headers with API key."""
        return {self.header_name: self.api_key}


@dataclass
class BasicAuth:
    """Basic Authentication (username:password)."""
    username: str
    password: str
    
    def get_headers(self) -> dict:
        """Return headers with basic auth."""
        import base64
        credentials = base64.b64encode(
            f"{self.username}:{self.password}".encode()
        ).decode()
        return {"Authorization": f"Basic {credentials}"}


@dataclass
class CustomAdapter:
    """Custom Authentication Handler."""
    handler: Callable
    
    async def get_headers(self) -> dict:
        """Return headers from custom handler."""
        return await self.handler()


@dataclass
class Config:
    """NPersona Configuration."""
    
    # API Configuration
    target_url: str
    auth: Any  # BearerTokenAuth, OAuth2Config, APIKeyAuth, BasicAuth, or CustomAdapter
    
    # Execution Settings
    concurrency_limit: int = 5
    rate_limit_rps: float = 10.0
    request_timeout: float = 30.0
    max_retries: int = 3
    retry_backoff_factor: float = 2.0
    
    # LLM Configuration
    llm_provider: str = "azure-openai"
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 8192
    
    # Test Configuration
    num_tests: int = 43
    attack_categories: Any = "all"  # "all" or list of categories
    include_corpus_attacks: bool = True
    
    # Output Configuration
    output_format: str = "json"  # json, html, markdown
    output_dir: str = "./reports"
    save_html: bool = True
    save_json: bool = True
    save_markdown: bool = False
    
    # Advanced Settings
    log_level: str = "INFO"
    verbose: bool = False
    enable_cache: bool = True
    cache_dir: str = "./.npersona_cache"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.target_url:
            raise ValueError("target_url is required")
        if not self.auth:
            raise ValueError("auth configuration is required")
        if self.concurrency_limit < 1:
            raise ValueError("concurrency_limit must be >= 1")
        if self.rate_limit_rps < 0.1:
            raise ValueError("rate_limit_rps must be >= 0.1")
        if self.request_timeout < 1:
            raise ValueError("request_timeout must be >= 1")


def load_config_from_env() -> Config:
    """Load configuration from environment variables."""
    target_url = os.getenv("NPERSONA_TARGET_URL")
    token = os.getenv("NPERSONA_TOKEN")
    
    if not target_url or not token:
        raise ValueError(
            "Set NPERSONA_TARGET_URL and NPERSONA_TOKEN environment variables"
        )
    
    return Config(
        target_url=target_url,
        auth=BearerTokenAuth(token=token),
        llm_provider=os.getenv("LLM_PROVIDER", "azure-openai"),
        llm_model=os.getenv("LLM_MODEL", "gpt-4o"),
        num_tests=int(os.getenv("NUM_TESTS", "43")),
    )

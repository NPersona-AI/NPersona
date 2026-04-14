"""Configuration models for LLM providers and NPersona pipeline."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


Provider = Literal["groq", "openai", "gemini", "azure", "ollama"]


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: Provider = "groq"
    model: str = "llama-3.3-70b-versatile"
    api_key: str | None = None
    base_url: str | None = None  # required for ollama and azure
    api_version: str | None = None  # azure only
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=8192, ge=256, le=131072)
    timeout: int = Field(default=60, ge=10, le=300)
    max_retries: int = Field(default=3, ge=1, le=10)

    @model_validator(mode="after")
    def validate_provider_config(self) -> "LLMConfig":
        if self.provider == "ollama" and self.base_url is None:
            self.base_url = "http://localhost:11434"
        if self.provider == "azure" and self.base_url is None:
            raise ValueError("base_url (Azure endpoint) is required for azure provider.")
        return self

    def litellm_model_string(self) -> str:
        """Return the litellm-compatible model string."""
        mapping = {
            "groq": f"groq/{self.model}",
            "openai": self.model,
            "gemini": f"gemini/{self.model}",
            "azure": f"azure/{self.model}",
            "ollama": f"ollama/{self.model}",
        }
        return mapping[self.provider]


class NPersonaConfig(BaseModel):
    """Top-level configuration for the NPersona pipeline."""

    llm: LLMConfig = Field(default_factory=LLMConfig)

    # Generation controls
    num_adversarial: int = Field(default=10, ge=1, le=100)
    num_user_centric: int = Field(default=10, ge=1, le=100)

    # Pipeline feature flags
    enable_rca: bool = False          # requires architecture_doc
    enable_executor: bool = False     # requires system_endpoint
    enable_coverage_report: bool = True

    # Executor settings (used when enable_executor=True)
    system_endpoint: str | None = None
    system_headers: dict[str, str] = Field(default_factory=dict)
    request_field: str = "message"   # JSON field name for the prompt
    response_field: str = "response" # JSON field name for the reply

    # Executor tuning — applies to pipeline/executor.Executor
    executor_adapter: Literal["json-post", "openai-chat", "bedrock-agent", "custom"] = "json-post"
    executor_concurrency: int = Field(default=4, ge=1, le=64)
    executor_retries: int = Field(default=3, ge=0, le=10)
    executor_rate_limit_rps: float | None = Field(default=None, ge=0.01)
    per_request_timeout: float = Field(default=30.0, ge=1.0, le=600.0)
    overall_timeout: float | None = Field(default=None, ge=1.0)
    stateful_session: bool = False  # Bedrock/LangGraph-style session reuse across turns

    # Authentication — applies to all HTTP requests
    auth_config: object | None = Field(default=None, exclude=True)  # AuthConfig object

    # Output
    progress_callback: object | None = Field(default=None, exclude=True)

    model_config = {"arbitrary_types_allowed": True}

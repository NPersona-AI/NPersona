# NPersona API Reference

Complete API documentation for the NPersona Security Testing Framework.

---

## Table of Contents

1. [Core Client](#core-client)
2. [Configuration](#configuration)
3. [Data Models](#data-models)
4. [Adapters](#adapters)
5. [Authentication](#authentication)
6. [Report Generation](#report-generation)
7. [Error Handling](#error-handling)
8. [Examples](#examples)

---

## Core Client

### NPersonaClient

The main entry point for NPersona security testing.

#### Constructor

```python
NPersonaClient(
    api_key: str | None = None,
    provider: str = "groq",
    model: str | None = None,
    config: NPersonaConfig | None = None,
    cache_dir: str | Path | None = None,
) -> None
```

**Parameters:**
- `api_key`: API key for the LLM provider (optional if using config)
- `provider`: LLM provider ("groq", "openai", "azure", "gemini", "ollama")
- `model`: Model name for the provider
- `config`: Complete NPersonaConfig object (overrides api_key/provider/model)
- `cache_dir`: Directory for caching profiles

**Example:**
```python
from npersona import NPersonaClient
from npersona.models.config import NPersonaConfig, LLMConfig

# Option 1: Simple initialization
client = NPersonaClient(
    api_key="sk-...",
    provider="openai",
    model="gpt-4"
)

# Option 2: Advanced configuration
config = NPersonaConfig(
    llm=LLMConfig(
        provider="azure",
        api_key="...",
        model="gpt-4o",
        base_url="https://...",
        api_version="2025-01-01-preview",
    ),
    num_adversarial=10,
    num_user_centric=5,
)
client = NPersonaClient(config=config)
```

#### Methods

##### `run()`

Run the complete security testing pipeline.

```python
async def run(
    system_doc: str | Path,
    architecture_doc: str | Path | None = None,
    num_adversarial: int | None = None,
    num_user_centric: int | None = None,
    include_taxonomy_ids: list[str] | None = None,
    exclude_taxonomy_ids: list[str] | None = None,
    include_known_attacks: bool = True,
    on_progress: Callable[[dict], None] | None = None,
    executor_adapter: RequestAdapter | None = None,
) -> SecurityReport
```

**Parameters:**
- `system_doc`: Path to or content of system documentation
- `architecture_doc`: Optional architecture documentation for RCA
- `num_adversarial`: Number of adversarial tests (default: config value)
- `num_user_centric`: Number of user-centric tests (default: config value)
- `include_taxonomy_ids`: Test only specific attack categories
- `exclude_taxonomy_ids`: Skip specific attack categories
- `include_known_attacks`: Include known vulnerability patterns
- `on_progress`: Callback receiving progress updates
- `executor_adapter`: Custom adapter for non-standard endpoints

**Returns:** `SecurityReport` with complete security assessment

---

## Configuration

### NPersonaConfig

Top-level configuration for the pipeline.

```python
NPersonaConfig(
    llm: LLMConfig = Field(default_factory=LLMConfig),
    num_adversarial: int = 10,
    num_user_centric: int = 10,
    executor_concurrency: int = 4,
    executor_retries: int = 3,
    per_request_timeout: float = 30.0,
)
```

### LLMConfig

LLM provider configuration.

```python
LLMConfig(
    provider: str = "groq",
    model: str = "llama-3.3-70b-versatile",
    api_key: str | None = None,
    base_url: str | None = None,
    api_version: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    timeout: int = 60,
)
```

---

## Data Models

### SecurityReport

Complete security report output.

```python
report.export_json("report.json")
report.export_markdown("report.md")
report.export_html("report.html")
```

### EvaluationResult

Aggregated test evaluation results.

- `passed: int` - Number of passed tests
- `failed: int` - Number of failed tests
- `total: int` - Total tests
- `pass_rate: float` - Pass rate (0.0-1.0)

### TestResult

Individual test execution result with timing and status.

### SystemProfile

Extracted system profile from documentation.

### TestSuite

Collection of generated test cases.

---

## Adapters

### JsonPostAdapter

Default adapter for JSON POST endpoints.

```python
from npersona.adapters.json_post import JsonPostAdapter

adapter = JsonPostAdapter(
    endpoint="https://api.example.com/chat",
    headers={"Authorization": "Bearer token"},
    request_field="message",
    response_field="response",
    timeout=30.0,
    max_retries=3,
    retry_delay=1.0,
)
```

---

## Authentication

### BearerTokenAuth

```python
from npersona.config import BearerTokenAuth

auth = BearerTokenAuth(token="your-token")
```

### APIKeyAuth

```python
from npersona.config import APIKeyAuth

auth = APIKeyAuth(api_key="your-key")
```

### BasicAuth

```python
from npersona.config import BasicAuth

auth = BasicAuth(username="user", password="pass")
```

### OAuth2Config

```python
from npersona.config import OAuth2Config

auth = OAuth2Config(
    client_id="client-id",
    client_secret="secret",
    token_endpoint="https://example.com/token",
)
```

---

## Report Generation

### Export Formats

```python
# JSON - Machine-readable
report.export_json("report.json")

# Markdown - Human-readable
report.export_markdown("report.md")

# HTML - Interactive dashboard
report.export_html("report.html")
```

---

## Error Handling

The library automatically handles:

- Timeout errors (configurable per request)
- Network failures (automatic retry with exponential backoff)
- Malformed responses (graceful fallback to raw text)
- Rate limiting (429 errors trigger retry)
- Service unavailable (503 errors trigger retry)

---

## Complete Example

```python
import asyncio
from npersona import NPersonaClient
from npersona.models.config import NPersonaConfig, LLMConfig
from npersona.adapters.json_post import JsonPostAdapter

async def main():
    config = NPersonaConfig(
        llm=LLMConfig(
            provider="azure",
            api_key="your-api-key",
            model="gpt-4o",
            base_url="https://your.openai.azure.com/",
            api_version="2025-01-01-preview",
        ),
        num_adversarial=10,
        num_user_centric=5,
    )

    client = NPersonaClient(config=config)

    adapter = JsonPostAdapter(
        endpoint="https://your-api.example.com/chat",
        headers={"Authorization": "Bearer token"},
    )

    report = await client.run(
        system_doc="system_spec.pdf",
        executor_adapter=adapter,
    )

    report.export_json("report.json")
    report.export_markdown("report.md")
    report.export_html("report.html")

    print(f"Pass Rate: {report.overall_pass_rate:.1%}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Support

For issues, see:
- [README.md](README.md)
- [GitHub Issues](https://github.com/NPersona-AI/NPersona/issues)

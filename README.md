# NPersona: AI Security Testing Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests Passing](https://img.shields.io/badge/tests-115%2F115%20passing-brightgreen)](https://github.com/NPersona-AI/npersona/actions)

A comprehensive, production-ready framework for adversarial security testing of AI systems. NPersona automates the discovery of vulnerabilities in large language models and AI agents through intelligent test generation, execution, and evaluation.

## 🎯 Key Features

- **7-Stage Security Pipeline**: Profile extraction → Attack mapping → Test generation → Execution → Evaluation → RCA → Reporting
- **Comprehensive Attack Coverage**: 28-category attack taxonomy (OWASP AI Security) + 40 research-backed known attacks
- **Multi-Auth Support**: Bearer token, API key, OAuth2, Basic Auth, and custom authentication
- **Real API Testing**: Full support for live endpoint testing with rate limiting and retry logic
- **LLM-Agnostic**: Works with OpenAI, Groq, Azure OpenAI, Gemini, and Ollama
- **Adapter Pattern**: Extensible architecture for custom HTTP target shapes (JSON POST, OpenAI Chat, Bedrock, custom)
- **Parallel Execution**: Concurrent test execution with configurable concurrency and rate limiting
- **Multi-Turn Conversations**: Support for stateful session-based attacks and multi-turn conversation testing
- **Detailed Telemetry**: Latency tracking, status codes, retry counts, and failure analysis
- **Production-Ready**: 115+ comprehensive tests, error isolation, graceful degradation

## 📊 What NPersona Tests

### Attack Categories (28 Total)
- **A01-A20**: Adversarial/prompt injection attacks
- **U01-U08**: User-centric safety scenarios
- **Corpus Attacks**: 40+ research-backed known vulnerabilities

### Vulnerability Types
- Prompt injection & jailbreaks
- Indirect injection via data fields
- Information disclosure (constraint/instruction leakage)
- Training data extraction
- Harmful content generation
- Misinformation & false advice
- Privacy pattern leakage
- Behavioral override attacks
- And 20+ more categories

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/NPersona-AI/npersona.git
cd npersona

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Basic Usage

```python
from npersona.client import NPersonaClient
from npersona.models.auth import BearerTokenAuth

# 1. Configure your LLM provider
client = NPersonaClient(
    provider="groq",
    api_key="gsk_YOUR_KEY",
    cache_dir="./cache"
)

# 2. Define your system
system_spec = """
A fitness coaching AI that:
- Provides personalized workout routines
- Gives evidence-based nutrition advice
- Never recommends harmful practices
"""

# 3. Run full security pipeline
report = client.run(
    system_doc=system_spec,
    system_endpoint="https://your-api.example.com/chat",
    auth_config=BearerTokenAuth(token="your-bearer-token"),
    num_adversarial=10,
    num_user_centric=5,
)

# 4. Review results
print(f"Tests passed: {report.evaluation.passed_count}")
print(f"Vulnerabilities found: {len(report.evaluation.failed_results)}")
print(f"Coverage: {report.attack_map.coverage_percentage}%")

# 5. Export report
report.export_markdown("security_report.md")
report.export_json("results.json")
```

### Advanced Configuration

```python
from npersona.models.config import NPersonaConfig, LLMConfig
from npersona.models.auth import OAuth2Config
from npersona.adapters.openai_chat import OpenAIChatAdapter

# Configure Azure OpenAI + OAuth2 + Custom adapter
config = NPersonaConfig(
    llm=LLMConfig(
        provider="azure",
        api_key="your-key",
        base_url="https://your-resource.openai.azure.com/",
        model="gpt-4o",
    ),
    system_endpoint="https://your-target.example.com/v1/chat/completions",
    auth_config=OAuth2Config(
        token_endpoint="https://auth.example.com/oauth/token",
        client_id="your-client-id",
        client_secret="your-client-secret",
        scope="api:access",
    ),
    enable_executor=True,
    executor_concurrency=4,
    executor_retries=3,
    executor_rate_limit_rps=10.0,
    per_request_timeout=30.0,
    num_adversarial=15,
    num_user_centric=8,
)

client = NPersonaClient(config=config)
report = client.run("system_spec.pdf")
```

## 🔧 Core Components

### 1. Profiler (Stage 1)
Extracts system characteristics from documentation
```python
profile = await client.extract_profile("system_spec.pdf")
# Returns: SystemProfile with agents, guardrails, integrations, data types
```

### 2. Attack Surface Mapper (Stage 2)
Maps 28 attack categories to system components
```python
attack_map = client.map_attack_surfaces(profile)
# Returns: AttackSurfaceMap with coverage analysis
```

### 3. Test Generator (Stage 3)
Generates adversarial and user-centric test cases using LLM
```python
suite = await client.generate_test_suite(profile, attack_map)
# Returns: TestSuite with 40+ test cases
```

### 4. Executor (Stage 4)
Executes tests against live API with auth, retries, rate limiting
```python
results = await client.execute(suite)
# Returns: List[TestResult] with telemetry
```

### 5. Evaluator (Stage 5)
LLM-as-judge evaluation with keyword fallback
```python
evaluation = await client.evaluate(suite, results)
# Returns: EvaluationResult with pass/fail analysis
```

### 6. RCA Analyzer (Stage 6 - Optional)
Root cause analysis using architecture documentation
```python
rca_findings = await client.analyze_rca("arch.pdf", profile, suite, evaluation)
# Returns: List[RCAFinding]
```

### 7. Reporter (Stage 7)
Generates comprehensive security report
```python
report = client.build_report(profile, suite, attack_map, evaluation, rca_findings)
# Returns: SecurityReport in JSON/Markdown/HTML
```

## 🔐 Authentication Support

### Bearer Token
```python
from npersona.models.auth import BearerTokenAuth

auth = BearerTokenAuth(token="eyJhbGc...")
```

### OAuth2 (Client Credentials)
```python
from npersona.models.auth import OAuth2Config

auth = OAuth2Config(
    token_endpoint="https://auth.example.com/token",
    client_id="your-client-id",
    client_secret="your-client-secret",
    scope="api:read api:write",
    audience="https://api.example.com",
)
```

### API Key
```python
from npersona.models.auth import APIKeyAuth

auth = APIKeyAuth(
    api_key="sk-abc123",
    header_name="X-API-Key",  # Custom header
)
```

### Basic Auth
```python
from npersona.models.auth import BasicAuth

auth = BasicAuth(
    username="user@example.com",
    password="secure_password",
)
```

### Custom Auth
```python
from npersona.adapters.custom import CustomCallableAdapter

async def my_auth_handler(test_case):
    # Your custom auth logic
    req.headers["Authorization"] = f"Bearer {custom_token}"
    return req

adapter = CustomCallableAdapter(
    build_request=my_auth_handler,
    parse_response=lambda resp: resp.get("data"),
)
results = await client.execute(suite, adapter=adapter)
```

## 🎯 Target System Adapters

NPersona supports multiple HTTP target shapes:

### JSON POST (Default)
```python
# Automatically selected for: {"message": "..."} → {"response": "..."}
config.executor_adapter = "json-post"
```

### OpenAI Chat Format
```python
# For OpenAI-compatible APIs
config.executor_adapter = "openai-chat"
```

### AWS Bedrock Agent
```python
# For Bedrock agents with stateful sessions
config.executor_adapter = "bedrock-agent"
config.stateful_session = True
```

### Custom Adapter
```python
from npersona.adapters.custom import CustomCallableAdapter

adapter = CustomCallableAdapter(
    build_request=my_build_request_fn,
    parse_response=my_parse_response_fn,
)
```

## 📈 Configuration Options

```python
NPersonaConfig(
    # LLM Configuration
    llm=LLMConfig(
        provider="groq|openai|azure|gemini|ollama",
        model="llama-3.3-70b-versatile",
        api_key="...",
        temperature=0.7,
        max_tokens=8192,
        timeout=60,
    ),
    
    # Test Generation
    num_adversarial=10,          # LLM-generated adversarial tests
    num_user_centric=10,         # LLM-generated user-centric tests
    
    # Executor Configuration
    enable_executor=True,
    system_endpoint="https://...",
    auth_config=BearerTokenAuth(...),
    executor_adapter="json-post",
    executor_concurrency=4,       # Parallel requests
    executor_retries=3,           # Exponential backoff
    executor_rate_limit_rps=10.0, # Rate limiting
    per_request_timeout=30.0,
    overall_timeout=3600.0,
    
    # Pipeline Features
    enable_rca=True,              # Requires architecture_doc
    enable_coverage_report=True,
    
    # System Configuration
    system_headers={"User-Agent": "..."},
    request_field="message",      # JSON field name for prompt
    response_field="response",    # JSON field name for response
)
```

## 📊 Output Formats

### Security Report
```python
report = client.run("spec.pdf")

# JSON Export
report.export_json("report.json")
# {
#   "system_name": "Fitness Bot",
#   "test_results": [...],
#   "vulnerabilities": [...],
#   "recommendations": [...],
#   "coverage": "87.5%",
#   "timestamp": "2026-04-12T20:30:00Z"
# }

# Markdown Export
report.export_markdown("report.md")
# Formatted with tables, code blocks, vulnerability details

# HTML Export
report.export_html("report.html")
# Interactive dashboard with charts and findings
```

## 🧪 Testing Against Real APIs

### Example: Testing with Real Endpoint

```python
import asyncio
from npersona.client import NPersonaClient
from npersona.models.auth import BearerTokenAuth

async def test_real_api():
    client = NPersonaClient(
        provider="groq",
        api_key="gsk_YOUR_KEY",
    )
    
    report = await client.run(
        system_doc="My AI system specification",
        system_endpoint="https://api.example.com/chat",
        auth_config=BearerTokenAuth(token="bearer-token"),
        num_adversarial=20,
        num_user_centric=10,
    )
    
    print(f"Pass rate: {report.evaluation.pass_rate}%")
    print(f"Critical issues: {len(report.critical_vulnerabilities)}")
    
    # Export results
    report.export_markdown("security_findings.md")

asyncio.run(test_real_api())
```

### Cost Estimation

| LLM Provider | Cost per Run | Speed | Best For |
|---|---|---|---|
| Groq | ~$0.01 | 10-30s | Development, frequent testing |
| OpenAI GPT-4o | ~$0.10 | 30-60s | Quality assurance |
| Claude 3 Opus | ~$0.30 | 30-60s | Deep analysis |
| Azure OpenAI | ~$0.05-0.15 | 30-60s | Enterprise deployments |

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: AI Security Tests

on: [push, pull_request]

jobs:
  security-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install npersona
      
      - name: Run NPersona security tests
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          TARGET_ENDPOINT: ${{ secrets.STAGING_ENDPOINT }}
          AUTH_TOKEN: ${{ secrets.STAGING_TOKEN }}
        run: |
          python -m npersona.cli \
            --spec system_spec.pdf \
            --endpoint $TARGET_ENDPOINT \
            --auth-bearer $AUTH_TOKEN \
            --output report.json
      
      - name: Check for critical issues
        run: |
          python -c "
          import json
          with open('report.json') as f:
              report = json.load(f)
          critical = len(report['critical_vulnerabilities'])
          if critical > 0:
              print(f'FAIL: {critical} critical issues found')
              exit(1)
          print('PASS: No critical issues')
          "
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: report.json
```

## 📚 Documentation

- **[Installation Guide](./docs/INSTALLATION.md)** - Detailed setup instructions
- **[User Guide](./docs/USER_GUIDE.md)** - Comprehensive usage documentation
- **[API Reference](./npersona/API_REFERENCE.md)** - Complete API documentation
- **[Troubleshooting Guide](./npersona/TROUBLESHOOTING.md)** - Common issues and solutions (new!)
- **[Performance Guide](./npersona/PERFORMANCE.md)** - Benchmarks and scaling recommendations (new!)
- **[Examples](./examples/)** - Real-world usage examples
- **[Architecture](./docs/ARCHITECTURE.md)** - System design and internals
- **[Testing Guide](./docs/TESTING_WITH_REAL_APIS.md)** - Real API testing procedures

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  NPersona Pipeline                   │
├─────────────────────────────────────────────────────┤
│ 1. Profiler        → Extract system characteristics   │
│ 2. Mapper          → Map attack surfaces             │
│ 3. Generator       → Generate test cases (LLM)       │
│ 4. Executor        → Execute tests (live API)        │
│ 5. Evaluator       → Evaluate results (LLM-judge)    │
│ 6. RCA Analyzer    → Root cause analysis             │
│ 7. Reporter        → Generate security report        │
├─────────────────────────────────────────────────────┤
│ Supporting Systems:                                  │
│ • AuthHandler      → Multi-auth support              │
│ • RequestAdapter   → HTTP shape abstraction          │
│ • RateLimiter      → Token bucket rate limiting      │
│ • TestCache        → Profile caching                 │
└─────────────────────────────────────────────────────┘
```

## 🧬 Extensibility

### Custom Request Adapter

```python
from npersona.adapters.base import RequestAdapter, HTTPRequest

class MyCustomAdapter(RequestAdapter):
    async def build_request(self, test_case):
        # Build custom HTTP request
        return HTTPRequest(
            method="POST",
            url=f"{self.endpoint}/chat",
            headers={"Authorization": "..."},
            json={"prompt": test_case.prompt, "context": "..."},
        )
    
    async def parse_response(self, response_text):
        # Parse response
        import json
        data = json.loads(response_text)
        return data.get("output", "")
    
    async def on_session_start(self):
        # Setup (e.g., open connections)
        pass
    
    async def on_session_end(self):
        # Cleanup (e.g., close connections)
        pass
```

### Custom Evaluation Criteria

```python
from npersona.pipeline.evaluator import Evaluator

class CustomEvaluator(Evaluator):
    async def evaluate(self, result, test_case):
        # Custom pass/fail logic
        if "harmful" in result.response_received.lower():
            return False
        return True

evaluator = CustomEvaluator(self.config.llm)
evaluation = await evaluator.evaluate(results, suite.cases)
```

## 📊 Test Results Example

```
Tests Executed: 43
Tests Passed: 35 (81.4%)
Tests Failed: 8 (18.6%)

Vulnerabilities Found:
  🔴 CRITICAL: 2
     - Debug mode information disclosure
     - Constraint enumeration

  🟠 HIGH: 3
     - Prompt injection (50% failure rate)
     - Training data extraction (33% failure rate)
     - Behavioral override (50% failure rate)

  🟡 MEDIUM: 3
     - Indirect injection (20% failure rate)
     - Harmful content generation
     - Privacy pattern leakage

Attack Coverage:
  ✓ A01: Prompt Injection          50% (2/4 pass)
  ✓ A03: Output Handling          100% (4/4 pass)
  ✓ A04: Code Execution           100% (3/3 pass)
  ...

Recommendations:
  1. Remove debug mode response (< 1 hour)
  2. Block constraint queries (< 2 hours)
  3. Validate roleplay contexts (4-6 hours)
  4. Enhanced jailbreak detection (8-12 hours)
```

## 🤝 Contributing

Contributions are welcome! Please follow our [Contributing Guidelines](./CONTRIBUTING.md).

### Development Setup

```bash
# Clone and install in development mode
git clone https://github.com/NPersona-AI/npersona.git
cd npersona
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
black .
flake8 .
mypy npersona/

# Build docs
cd docs && make html
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built with [LiteLLM](https://litellm.ai/) for unified LLM provider support
- Authentication patterns inspired by industry security standards
- Attack taxonomy based on [OWASP AI Security](https://owasp.org/www-project-ai-security/)
- Evaluation methodology influenced by academic security research

## 📞 Support

- **Documentation**: [docs/](./docs/)
- **Issues**: [GitHub Issues](https://github.com/NPersona-AI/npersona/issues)
- **Discussions**: [GitHub Discussions](https://github.com/NPersona-AI/npersona/discussions)
- **Security**: See [SECURITY.md](./SECURITY.md) for responsible disclosure

## 🗺️ Roadmap

- [ ] Web dashboard for result visualization
- [ ] Multi-model evaluation consensus
- [ ] Custom taxonomy support
- [ ] Continuous monitoring integration
- [ ] ML-based vulnerability prediction
- [ ] Automated remediation suggestions
- [ ] Enterprise deployment guides

## Citation

```bibtex
@software{npersona2026,
  title={NPersona: AI Security Testing Framework},
  author={NPersona-AI},
  year={2026},
  url={https://github.com/NPersona-AI/npersona}
}
```

---

**NPersona** - Making AI systems safer, one test at a time.

*Built by [NPersona-AI](https://github.com/NPersona-AI)*

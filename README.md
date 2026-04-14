# 🛡️ NPersona: AI Security Testing Framework

> **Making AI Systems Safer, One Test at a Time**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests Passing](https://img.shields.io/badge/tests-115%2F115%20passing-brightgreen)](https://github.com/NPersona-AI/NPersona)
[![PyPI Version](https://img.shields.io/badge/pypi-v1.0.4-blue)](https://pypi.org/project/npersona/)

---

## 🎯 What is NPersona?

**NPersona** is a comprehensive, production-ready framework for **adversarial security testing of AI systems**. It automates the discovery of vulnerabilities in large language models and AI agents through intelligent test generation, execution, and evaluation.

Think of it as a **professional penetration testing tool specifically designed for AI systems**. Just like security researchers stress-test web applications to find vulnerabilities, NPersona stress-tests AI systems to discover security flaws before they reach production.

### Why NPersona?

- **🚀 Production Ready**: 115+ comprehensive tests, enterprise-grade architecture
- **🎯 Comprehensive**: 28 attack categories + 40+ research-backed vulnerabilities
- **⚡ Fast**: Test your AI system in 2-10 minutes
- **🔧 Flexible**: Works with any AI API (OpenAI, Azure, Groq, Ollama, etc.)
- **📊 Professional Reports**: JSON, HTML, Markdown with detailed analysis
- **🔐 Secure**: Multiple authentication methods, rate limiting, retry logic
- **🧪 Real Testing**: Test against actual APIs with production data

---

## ✨ Key Features

### 🏗️ **7-Stage Security Pipeline**
```
Profile → AttackMap → Generate → Execute → Evaluate → Analyze → Report
```

Each stage is optimized for discovering different classes of AI vulnerabilities.

### 📋 **Comprehensive Attack Coverage**
- **28 Attack Categories**: OWASP AI Security taxonomy
- **40+ Known Vulnerabilities**: Research-backed attack patterns  
- **Adversarial Tests**: A01-A20 (prompt injection, jailbreaks, etc.)
- **User-Centric Tests**: U01-U08 (usability, accessibility attacks)

### 🔑 **Multi-Authentication Support**
- Bearer Token
- OAuth2 (with auto-refresh)
- API Key (custom headers)
- Basic Authentication
- Custom callable adapters

### 🌐 **LLM Agnostic**
Works seamlessly with:
- **OpenAI** (GPT-4, GPT-4o)
- **Azure OpenAI** (Enterprise)
- **Groq** (Fast & affordable)
- **Google Gemini**
- **Anthropic Claude**
- **Ollama** (Local/private)

### 🔌 **HTTP Adapter Pattern**
- JSON POST (default)
- OpenAI Chat format
- AWS Bedrock Agent
- Custom callable adapters

### ⚙️ **Enterprise Features**
- Parallel test execution with configurable concurrency
- Token bucket rate limiting
- Exponential backoff retry logic
- Per-request timeouts
- Session-based multi-turn testing
- Detailed telemetry & analytics

---

## 🚀 Quick Start (5 minutes)

### Installation

```bash
pip install npersona
```

Or from source:
```bash
git clone https://github.com/NPersona-AI/NPersona.git
cd NPersona
pip install -e .
```

### Your First Security Assessment

```python
import asyncio
from npersona import NPersonaClient
from npersona.models.auth import BearerTokenAuth

async def test_my_ai():
    # 1. Create client with any LLM provider
    client = NPersonaClient(
        provider="groq",  # or openai, azure, gemini, ollama
        api_key="gsk_YOUR_KEY"
    )
    
    # 2. Define your AI system
    system_doc = """
    A customer support chatbot that:
    - Answers product questions
    - Processes refund requests
    - Never shares internal policies
    """
    
    # 3. Run security assessment
    report = await client.run(
        system_doc=system_doc,
        system_endpoint="https://your-api.example.com/chat",
        auth_config=BearerTokenAuth(token="your-token"),
        num_adversarial=20,  # LLM-generated adversarial tests
        num_user_centric=10  # User behavior tests
    )
    
    # 4. Get results
    print(f"✅ Tests Passed: {report.evaluation.passed_count}")
    print(f"❌ Tests Failed: {report.evaluation.failed_count}")
    print(f"📊 Pass Rate: {report.evaluation.pass_rate}%")
    print(f"🔴 Critical Issues: {len(report.critical_vulnerabilities)}")
    
    # 5. Save reports
    report.export_json("security_report.json")
    report.export_html("security_report.html")

asyncio.run(test_my_ai())
```

Output:
```
✅ Tests Passed: 35
❌ Tests Failed: 8
📊 Pass Rate: 81.4%
🔴 Critical Issues: 3
Reports saved!
```

---

## 📊 What Gets Tested

### Prompt Injection Attacks
- Direct prompt injection
- Indirect injection via data fields
- Constraint enumeration
- System instruction leakage

### Information Disclosure
- Debug mode exploitation
- Sensitive data leakage
- Training data extraction
- Privacy pattern leakage

### Harmful Content Generation
- Jailbreak attempts
- Roleplay exploitation
- Behavioral override
- Multi-turn manipulation

### And 18+ More Categories...
See [Attack Patterns Catalog](./ATTACK_PATTERNS_CATALOG.md) for complete taxonomy.

---

## 🎯 Real-World Example

### Test a Fitness Coaching AI

```python
system_doc = """
A fitness AI that:
- Generates workout routines
- Provides nutrition advice
- Never recommends dangerous practices
"""

report = await client.run(
    system_doc=system_doc,
    system_endpoint="https://gym-api.example.com/chat",
    num_adversarial=25,
    num_user_centric=15
)
```

### Example Results

```
Test Results Summary
════════════════════════════════════
Tests Executed: 40
Tests Passed: 32 (80%)
Tests Failed: 8 (20%)

Vulnerabilities Found:

🔴 CRITICAL (Immediate action required)
  • Debug Mode Information Disclosure
    Fix time: < 1 hour
  
  • Constraint Enumeration Attack
    Fix time: < 2 hours

🟠 HIGH (Address within 1 week)
  • Prompt Injection via Roleplay
    Severity: High
    
  • Training Data Extraction
    Severity: High

🟡 MEDIUM (Address within 1 month)
  • Indirect Injection via JSON
    Severity: Medium

Remediation Timeline:
  After CRITICAL fixes: 95% pass rate
  After HIGH fixes: 99%+ pass rate
```

---

## 🔐 Authentication Examples

### Bearer Token (Simplest)
```python
auth = BearerTokenAuth(token="your_token_here")
```

### OAuth2 (Enterprise)
```python
auth = OAuth2Config(
    client_id="your_id",
    client_secret="your_secret",
    token_endpoint="https://auth.example.com/token",
    scope="api:read api:write"
)
```

### API Key (Custom Header)
```python
auth = APIKeyAuth(
    api_key="sk_abc123",
    header_name="X-API-Key"
)
```

See [SECURITY.md](./SECURITY.md) for more authentication options.

---

## 📈 Advanced Usage

### Configure Everything

```python
from npersona.models.config import NPersonaConfig, LLMConfig

config = NPersonaConfig(
    # Use Azure OpenAI with GPT-4o
    llm=LLMConfig(
        provider="azure",
        model="gpt-4o",
        api_key="your_key",
        base_url="https://your-resource.openai.azure.com/",
        temperature=0.7,
        max_tokens=8192
    ),
    
    # Execution settings
    executor_concurrency=5,        # Parallel requests
    executor_retries=3,            # Retry logic
    executor_rate_limit_rps=10.0,  # Rate limiting
    per_request_timeout=30.0,      # Timeouts
    
    # Test generation
    num_adversarial=30,
    num_user_centric=15
)

client = NPersonaClient(config=config)
```

### Custom HTTP Adapters

```python
from npersona.adapters.custom import CustomCallableAdapter

async def my_adapter(test_case):
    # Your custom logic
    return {
        "url": "https://api.example.com/v1/chat",
        "method": "POST",
        "json": {"message": test_case.prompt},
        "headers": {"Authorization": "Bearer ..."}
    }

adapter = CustomCallableAdapter(handler=my_adapter)
report = await client.run(..., adapter=adapter)
```

See [USER_GUIDE.md](./USER_GUIDE.md) for more advanced examples.

---

## 💰 Cost Estimation

| LLM Provider | Cost per Run | Speed | Best For |
|---|---|---|---|
| **Groq** (Recommended) | ~$0.01 | 10-30s | Development |
| **OpenAI GPT-4o** | ~$0.10 | 30-60s | Production |
| **Azure OpenAI** | ~$0.05-0.15 | 30-60s | Enterprise |
| **Ollama** (Local) | FREE | Varies | Privacy-first |

Run an assessment for the cost of a coffee ☕

---

## 🧪 CI/CD Integration

### GitHub Actions

```yaml
name: AI Security Tests

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run NPersona assessment
        env:
          GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
          TARGET_API: ${{ secrets.STAGING_API }}
          AUTH_TOKEN: ${{ secrets.AUTH_TOKEN }}
        run: |
          pip install npersona
          python assess_security.py
      
      - name: Check for critical issues
        run: |
          python check_results.py --fail-on-critical
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[INSTALLATION_GUIDE.md](./INSTALLATION_GUIDE.md)** | Setup & configuration |
| **[QUICK_START_TUTORIAL.md](./QUICK_START_TUTORIAL.md)** | 10-minute tutorial |
| **[USER_GUIDE.md](./USER_GUIDE.md)** | Complete reference |
| **[CONTRIBUTING.md](./CONTRIBUTING.md)** | Contribute code |
| **[SECURITY.md](./SECURITY.md)** | Security policy |
| **[CHANGELOG.md](./CHANGELOG.md)** | Release notes |

---

## 🏗️ Architecture

```
NPersona Pipeline (7 Stages)
════════════════════════════════════════════════

Stage 1: PROFILER
  Input: System documentation
  Output: SystemProfile (agents, guardrails, capabilities)
  
Stage 2: MAPPER
  Input: SystemProfile
  Output: AttackSurfaceMap (attack categories coverage)
  
Stage 3: GENERATOR
  Input: Profile + AttackMap
  Output: TestSuite (40+ test cases)
  
Stage 4: EXECUTOR
  Input: TestSuite
  Output: TestResults (API responses, latency, errors)
  
Stage 5: EVALUATOR
  Input: TestResults
  Output: EvaluationResult (pass/fail analysis)
  
Stage 6: RCA ANALYZER
  Input: Failures + Architecture
  Output: RCAFindings (root causes)
  
Stage 7: REPORTER
  Input: Everything
  Output: SecurityReport (JSON/HTML/Markdown)
```

---

## 🧬 Extensibility

### Custom Evaluation Criteria

```python
class MyEvaluator(Evaluator):
    async def evaluate(self, result, test_case):
        # Your custom logic
        if "forbidden_word" in result.response:
            return False
        return True
```

### Custom Request Adapter

```python
class MyAdapter(RequestAdapter):
    async def build_request(self, test_case):
        return HTTPRequest(
            method="POST",
            url="https://api.example.com/test",
            json={"input": test_case.prompt}
        )
    
    async def parse_response(self, response):
        return response.get("output")
```

See [docs/](./docs/) for more examples.

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

```bash
# Development setup
git clone https://github.com/NPersona-AI/NPersona.git
cd NPersona
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Code quality
black . && flake8 . && mypy npersona/
```

---

## 📜 License

MIT License - See [LICENSE](./LICENSE) for details

---

## 🙏 Acknowledgments

- Attack taxonomy based on [OWASP AI Security](https://owasp.org/www-project-ai-security/)
- LLM integration via [LiteLLM](https://litellm.ai/)
- Authentication patterns inspired by industry standards
- Evaluation methodology from academic security research

---

## 📞 Support & Contact

- **Email**: npersona.ai@gmail.com
- **Issues**: [GitHub Issues](https://github.com/NPersona-AI/NPersona/issues)
- **Discussions**: [GitHub Discussions](https://github.com/NPersona-AI/NPersona/discussions)
- **Security**: See [SECURITY.md](./SECURITY.md) for responsible disclosure

---

## 🗺️ Roadmap

- [ ] Web dashboard for visualization
- [ ] Multi-model evaluation consensus
- [ ] Custom attack taxonomy
- [ ] Continuous monitoring service
- [ ] ML-based vulnerability prediction
- [ ] Automated remediation
- [ ] Enterprise support

---

## 📊 Project Stats

- **Framework Version**: 1.0.0
- **Python Support**: 3.9+
- **Test Coverage**: 115+ tests
- **LLM Providers**: 5+ (OpenAI, Azure, Groq, Gemini, Ollama)
- **Attack Categories**: 28
- **Known Vulnerabilities**: 40+
- **Lines of Code**: 5000+
- **Documentation**: 100+ pages

---

## 🌟 Getting Help

**New to NPersona?**
→ Start with [QUICK_START_TUTORIAL.md](./QUICK_START_TUTORIAL.md)

**Need detailed info?**
→ Read [USER_GUIDE.md](./USER_GUIDE.md)

**Want to contribute?**
→ See [CONTRIBUTING.md](./CONTRIBUTING.md)

**Found a security issue?**
→ Email npersona.ai@gmail.com

---

## 🎉 Made with ❤️ by [NPersona-AI](https://github.com/NPersona-AI)

**NPersona** - Making AI Systems Safer, One Test at a Time.

```
 ╔═══════════════════════════════════════════════╗
 ║                                               ║
 ║   🛡️  Security Testing for AI Systems  🛡️    ║
 ║                                               ║
 ║   Production-Ready • Comprehensive • Fast    ║
 ║                                               ║
 ╚═══════════════════════════════════════════════╝
```

---

**Latest Release**: v1.0.0 (April 13, 2026)

[![Star us on GitHub](https://img.shields.io/github/stars/NPersona-AI/NPersona?style=social)](https://github.com/NPersona-AI/NPersona)

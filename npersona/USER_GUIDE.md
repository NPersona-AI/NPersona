# NPersona User Guide - Complete Reference

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running Assessments](#running-assessments)
5. [Understanding Results](#understanding-results)
6. [Report Generation](#report-generation)
7. [Best Practices](#best-practices)
8. [Frequently Asked Questions](#faq)

---

## Overview

### What is NPersona?

NPersona is a **7-stage AI security testing framework** that evaluates AI systems for vulnerabilities and security issues through automated adversarial testing.

### How It Works

```
1. PROFILE        → Analyze your AI system
2. MAPPER         → Identify attack surface
3. GENERATOR      → Create test cases
4. EXECUTOR       → Run against API
5. EVALUATOR      → Judge results
6. RCA            → Analyze root causes
7. REPORTER       → Generate reports
```

### What Can It Test?

✅ **Prompt Injection Attacks** - Trying to override system instructions  
✅ **Constraint Extraction** - Discovering hidden guidelines  
✅ **Harmful Content Generation** - Testing safety boundaries  
✅ **Information Disclosure** - Sensitive data leakage  
✅ **Privilege Escalation** - Unauthorized access attempts  
✅ **Training Data Extraction** - Privacy concerns  
✅ **And 22+ more attack categories**

### Output

- **Pass Rate** - Percentage of security tests passed
- **Vulnerabilities Found** - Detailed list with severity
- **Remediation Recommendations** - Steps to fix issues
- **Professional Reports** - JSON, HTML, Markdown formats

---

## Installation

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- Internet connection (for API calls)

### Install from PyPI (Recommended)

```bash
# Simple install
pip install npersona

# With extras
pip install npersona[dev,test]
```

### Install from GitHub

```bash
git clone https://github.com/NPersona-AI/npersona.git
cd npersona
pip install -e ".[dev,test]"
```

### Verify Installation

```bash
python -c "import npersona; print(npersona.__version__)"
```

---

## Configuration

### Environment Setup

Create a `.env` file:

```ini
# Required: Your API endpoint
NPERSONA_TARGET_URL=https://your-api.example.com/chat

# Required: Authentication token
NPERSONA_TOKEN=your-bearer-token

# Required: LLM API key
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-azure.openai.azure.com/

# Optional: Fine-tuning
NPERSONA_CONCURRENCY=5
NPERSONA_RATE_LIMIT=10
NPERSONA_TIMEOUT=30
```

### Python Configuration

```python
from npersona.config import Config, BearerTokenAuth

config = Config(
    # API Setup
    target_url="https://your-api.example.com/chat",
    auth=BearerTokenAuth(token="your-token"),
    
    # Performance
    concurrency_limit=5,           # Parallel requests
    rate_limit_rps=10,             # Requests per second
    request_timeout=30,            # Seconds
    max_retries=3,                 # Retry attempts
    
    # Testing
    num_tests=43,                  # Total tests
    attack_categories="all",       # Or list specific
    include_corpus_attacks=True,   # Research-backed attacks
    
    # Output
    output_format="json",
    save_reports=True,
    report_dir="./reports"
)
```

---

## Running Assessments

### Basic Assessment

```python
import asyncio
from npersona import NPersonaClient
from npersona.config import BearerTokenAuth

async def run_assessment():
    auth = BearerTokenAuth(token="your-token")
    
    client = NPersonaClient(
        target_url="https://your-api.example.com/chat",
        auth=auth
    )
    
    # Run full assessment
    report = await client.run_assessment()
    
    return report

# Execute
report = asyncio.run(run_assessment())
```

### Assessment with Options

```python
# Full options
report = await client.run_assessment(
    # Test selection
    num_tests=50,                              # Number of tests
    attack_categories=["A01", "A05", "A12"],  # Specific categories
    include_corpus_attacks=True,               # Research-backed
    
    # Behavior
    enable_sessions=True,                      # Multi-turn support
    session_timeout=300,                       # Session duration
    
    # Execution
    concurrency_limit=5,
    rate_limit_rps=10,
    
    # Output
    save_html=True,
    save_json=True,
    save_markdown=True
)
```

### Different Authentication Methods

```python
# Bearer Token
from npersona.config import BearerTokenAuth
auth = BearerTokenAuth(token="your-token")

# OAuth2
from npersona.config import OAuth2Config
auth = OAuth2Config(
    client_id="id",
    client_secret="secret",
    token_endpoint="https://auth.example.com/token"
)

# API Key
from npersona.config import APIKeyAuth
auth = APIKeyAuth(api_key="key", header_name="X-API-Key")

# Basic Auth
from npersona.config import BasicAuth
auth = BasicAuth(username="user", password="pass")

# Custom
from npersona.config import CustomAdapter
adapter = CustomAdapter(handler=your_custom_function)
```

---

## Understanding Results

### Report Structure

```python
report = await client.run_assessment()

# Overall metrics
report.tests_passed      # Number of tests passed
report.tests_failed      # Number of tests failed
report.pass_rate         # Percentage (0-100)

# Issue breakdown
report.critical_count    # Critical severity
report.high_count        # High severity
report.medium_count      # Medium severity
report.low_count         # Low severity

# Execution details
report.execution_time    # Total time
report.tests_executed    # Number of tests run
report.errors            # Any errors encountered

# Details
report.vulnerabilities   # List of issues found
report.recommendations   # Suggested fixes
```

### Interpreting Pass Rates

```
✅ 95%+ SECURE
   - System is well-protected
   - Minor issues only
   - Ready for production

⚠️  80-95% GOOD
   - Adequate protection
   - Some issues to address
   - Recommended fixes before production

🔴 <80% NEEDS WORK
   - Critical vulnerabilities found
   - Requires immediate fixes
   - Not production-ready
```

### Issue Severity

```
🔴 CRITICAL
   - Complete system compromise
   - Immediate action required
   - Security threat

🟠 HIGH
   - Significant vulnerability
   - Should fix within 1 week
   - Security risk

🟡 MEDIUM
   - Notable issue
   - Should fix within 1 month
   - Quality concern

🟢 LOW
   - Minor issue
   - Can be addressed later
   - Documentation/improvement
```

### Example Results

```python
report = await assessment()

print(f"Pass Rate: {report.pass_rate:.1f}%")  # 81.4%
print(f"Critical: {report.critical_count}")    # 3
print(f"High: {report.high_count}")            # 4
print(f"Time: {report.execution_time:.1f}s")   # 45.2s

# View vulnerabilities
for vuln in report.vulnerabilities:
    print(f"\n{vuln.title}")
    print(f"  Severity: {vuln.severity}")
    print(f"  Category: {vuln.category}")
    print(f"  Description: {vuln.description}")
    print(f"  Fix: {vuln.remediation}")
```

---

## Report Generation

### Save Reports

```python
# JSON format
report.save_json("report.json")

# HTML (interactive)
report.save_html("report.html")

# Markdown
report.save_markdown("report.md")

# All formats
report.save_json("results/report.json")
report.save_html("results/report.html")
report.save_markdown("results/report.md")
```

### Custom Report Processing

```python
# Get as dictionary
data = report.to_dict()

# Access specific elements
failures = [t for t in report.tests if not t.passed]
critical = [v for v in report.vulnerabilities if v.severity == "CRITICAL"]

# Generate summary
summary = f"""
Security Assessment Summary
============================
Pass Rate: {report.pass_rate:.1f}%
Tests: {report.tests_executed}
Critical Issues: {report.critical_count}
High Issues: {report.high_count}
"""

# Create custom report
with open("custom_report.txt", "w") as f:
    f.write(summary)
    for vuln in report.vulnerabilities:
        f.write(f"\n{vuln.title}: {vuln.description}")
```

### Report Formats

**JSON** - Machine-readable, for integration  
**HTML** - Beautiful, interactive, shareable  
**Markdown** - Documentation-friendly

---

## Best Practices

### 1. Test in Staging First

```python
# Test against staging API first
async def test_staging():
    auth = BearerTokenAuth(token="staging-token")
    
    client = NPersonaClient(
        target_url="https://staging-api.example.com/chat",
        auth=auth
    )
    
    report = await client.run_assessment()
    return report
```

### 2. Use Appropriate Rate Limits

```python
# Don't overwhelm API
config = Config(
    target_url="...",
    auth=auth,
    rate_limit_rps=5,          # Conservative
    concurrency_limit=2        # Low concurrency
)

# After confirming API can handle it:
config = Config(
    target_url="...",
    auth=auth,
    rate_limit_rps=20,         # Higher if stable
    concurrency_limit=5        # More parallel
)
```

### 3. Monitor Progress

```python
# Use progress callback
def on_progress(current, total, status):
    print(f"[{current}/{total}] {status}")

report = await client.run_assessment(
    progress_callback=on_progress,
    verbose=True
)
```

### 4. Handle Errors Gracefully

```python
try:
    report = await client.run_assessment()
except TimeoutError:
    print("Request timeout - increase timeout value")
    config.request_timeout = 60
except Exception as e:
    print(f"Error: {e}")
    # Fall back to conservative settings
    config.rate_limit_rps = 5
    config.concurrency_limit = 1
```

### 5. Schedule Regular Testing

```bash
# Run weekly assessment
0 0 * * 0 python /path/to/run_assessment.py

# Run on every deployment
# Add to CI/CD pipeline
```

### 6. Store Results for Comparison

```python
import json
from datetime import datetime

# Save with timestamp
timestamp = datetime.now().isoformat()
filename = f"reports/assessment_{timestamp}.json"

report.save_json(filename)

# Compare over time
import glob
reports = sorted(glob.glob("reports/assessment_*.json"))
for r in reports:
    with open(r) as f:
        data = json.load(f)
        print(f"{r}: {data['pass_rate']:.1f}%")
```

---

## Frequently Asked Questions

### Q: How long does an assessment take?

A: Typically 2-10 minutes depending on:
- Number of tests (43 is default)
- API response time
- Rate limiting
- Network latency

Example: 43 tests with 10 RPS = ~4-5 minutes

### Q: What if my API is not public?

A: Use authentication:
- Bearer token
- OAuth2
- API key
- Basic auth
- Custom authentication

### Q: Can I test multiple APIs?

A: Yes, run assessments separately:

```python
async def test_multiple():
    for api_url in ["api1", "api2", "api3"]:
        report = await client.run_assessment(
            target_url=api_url
        )
        report.save_json(f"{api_url}.json")
```

### Q: How do I fix vulnerabilities?

A: Each report includes:
- Detailed explanation
- Root cause
- Specific remediation steps
- Estimated effort

Follow the remediation checklist in the report.

### Q: Can I use a different LLM?

A: Yes, configure LLM provider:

```python
config = Config(
    target_url="...",
    auth=auth,
    llm_provider="groq",      # or azure-openai, openai, etc.
    llm_model="llama-3.3-70b"
)
```

### Q: How does pricing work?

A: Framework is open source and free.

Costs are only for:
- Your target API (if it charges)
- LLM API calls (Azure, Groq, etc.)

You can minimize LLM costs by:
- Reducing number of tests
- Using cheaper models
- Caching results

### Q: Is my data secure?

A: Yes:
- No data stored externally
- Tokens kept in memory only
- Reports saved locally
- SSL/TLS for all API calls
- No telemetry or tracking

### Q: Can I customize tests?

A: Yes, several ways:

```python
# Select specific categories
report = await client.run_assessment(
    attack_categories=["A01", "A05"]
)

# Use custom prompts
# Create custom adapter
# Add your own test logic
```

### Q: How do I integrate with CI/CD?

A: Add to pipeline:

```yaml
# GitHub Actions example
- name: Run NPersona Assessment
  run: |
    pip install npersona
    python run_assessment.py
    
- name: Check Results
  run: |
    python check_pass_rate.py --min 80
```

### Q: What if assessment fails?

A: Debug with:

```bash
# Verbose mode
python run_assessment.py --verbose --debug

# Check authentication
python -c "from npersona.config import BearerTokenAuth; auth = BearerTokenAuth('token'); print(auth.validate())"

# Test API connectivity
curl -H "Authorization: Bearer token" https://your-api.example.com/chat
```

---

## Performance Tuning

### Optimize for Speed

```python
config = Config(
    target_url="...",
    auth=auth,
    concurrency_limit=10,    # Higher
    rate_limit_rps=50,       # Higher
    request_timeout=60,      # More time
    num_tests=20             # Fewer tests
)
```

### Optimize for Accuracy

```python
config = Config(
    target_url="...",
    auth=auth,
    concurrency_limit=2,     # Lower
    rate_limit_rps=5,        # Lower
    request_timeout=30,      # Standard
    num_tests=100,           # More tests
    include_corpus_attacks=True
)
```

### Optimize for Cost

```python
config = Config(
    target_url="...",
    auth=auth,
    num_tests=20,                    # Fewer
    llm_provider="groq",             # Cheaper
    llm_model="llama-3.3-70b",       # Budget model
    cache_evaluations=True           # Reuse results
)
```

---

## Summary

### Quick Reference

| Task | Code |
|------|------|
| Install | `pip install npersona` |
| Setup | Create `.env` with credentials |
| Run | `python run_assessment.py` |
| Save | `report.save_json()` |
| Check | `report.pass_rate` |
| Analyze | View report.json or .html |

### Resources

- 📖 [Full Documentation](README.md)
- 🚀 [Quick Start](QUICK_START_TUTORIAL.md)
- 📋 [Installation Guide](INSTALLATION_GUIDE.md)
- 🔧 [Configuration Guide](docs/CONFIGURATION.md)
- 📊 [Professional Report](NPersona_Security_Report.pdf)

---

**Version:** 1.0.0  
**Last Updated:** April 13, 2026  
**Questions?** npersona.ai@gmail.com

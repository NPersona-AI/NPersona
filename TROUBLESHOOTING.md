# NPersona Troubleshooting Guide

Common issues, solutions, and debugging techniques.

---

## Quick Diagnosis

### Is it working at all?

```bash
# Test basic import
python -c "from npersona import NPersonaClient; print('OK')"

# If this fails: Check installation
pip install npersona
```

### Check your configuration

```python
from npersona.models.config import NPersonaConfig, LLMConfig

# Validate config loads without errors
config = NPersonaConfig(
    llm=LLMConfig(
        provider="your-provider",
        api_key="your-key",
    )
)
print("Config OK")
```

---

## Common Issues & Solutions

### 1. Authentication Errors

#### Error: `401 Unauthorized`

**Cause**: Invalid or missing API key

**Solutions**:
```python
# Check your API key is correct
import os
api_key = os.getenv('AZURE_OPENAI_API_KEY')
print(f"Key length: {len(api_key) if api_key else 'NOT SET'}")

# For Azure OpenAI:
# 1. Verify key in Azure portal
# 2. Check it's not expired
# 3. Ensure it has the right permissions

# For OpenAI:
# 1. Log in to platform.openai.com
# 2. Go to API keys
# 3. Copy exact key (no extra spaces)

# Test connection:
from npersona import NPersonaClient
client = NPersonaClient(
    api_key="your-key",
    provider="openai",
    model="gpt-4"
)
# If this works, auth is OK
```

**For Azure OpenAI specifically**:
```python
from npersona.models.config import NPersonaConfig, LLMConfig

config = NPersonaConfig(
    llm=LLMConfig(
        provider="azure",
        api_key="your-actual-key",
        model="gpt-4o",
        base_url="https://your-instance.openai.azure.com/",
        api_version="2025-01-01-preview",
    )
)

# Check all fields are correct
print(f"Provider: {config.llm.provider}")
print(f"Model: {config.llm.model}")
print(f"Base URL: {config.llm.base_url}")
print(f"API Version: {config.llm.api_version}")
```

#### Error: `403 Forbidden`

**Cause**: API key exists but lacks permissions

**Solutions**:
- Check API key has the right role (e.g., "Cognitive Services OpenAI Contributor" for Azure)
- Check quota/credits haven't been exceeded
- Try with a different API key to rule out per-key issues

---

### 2. Timeout Errors

#### Error: `TimeoutError: Request timed out`

**Cause**: LLM taking too long to respond, or endpoint unreachable

**Solutions**:

```python
# Increase timeout (default is 30 seconds)
from npersona.models.config import NPersonaConfig, LLMConfig

config = NPersonaConfig(
    llm=LLMConfig(
        provider="openai",
        api_key="...",
        timeout=60,  # Increased from default 30
    ),
    per_request_timeout=45.0,  # For executor requests
)
```

**If timeout persists**:
1. Check network connectivity
2. Try a different LLM provider
3. Check if your API endpoint is responding (curl test)

```bash
# Test endpoint connectivity
curl -v https://your-api.example.com/chat \
  -H "Authorization: Bearer your-token" \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

---

### 3. Network & Connection Errors

#### Error: `ConnectionError` or `Connection refused`

**Cause**: Cannot reach endpoint or LLM service

**Solutions**:

```python
# Check network connectivity
import httpx
import asyncio

async def test_endpoint():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://your-endpoint.com/health")
            print(f"Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_endpoint())
```

**Troubleshooting steps**:
1. Check internet connection: `ping 8.8.8.8`
2. Check endpoint is up: `curl https://your-endpoint.com/health`
3. Check firewall isn't blocking: Contact your IT team
4. Check API service status page (Azure, OpenAI, etc.)

#### Error: `429 Too Many Requests` (Rate Limited)

**Cause**: Exceeded API rate limit

**Solutions**:

```python
# Reduce concurrency
from npersona.models.config import NPersonaConfig

config = NPersonaConfig(
    executor_concurrency=1,  # Run tests sequentially
    executor_rate_limit_rps=0.5,  # 1 request every 2 seconds
)
```

**Also consider**:
- Reduce number of tests: `num_adversarial=5, num_user_centric=2`
- Wait before retrying (library does this automatically)
- Check rate limit quotas with your API provider

---

### 4. Invalid Documentation Errors

#### Error: `Failed to parse system documentation`

**Cause**: Documentation format not supported or missing

**Solutions**:

```python
from npersona import NPersonaClient

# Supported formats:
# 1. Plain text string
system_doc_text = """
Your AI system description here.
Explain capabilities, constraints, etc.
"""

# 2. Path to text file
system_doc_path = "path/to/spec.txt"

# 3. Path to PDF file
system_doc_pdf = "path/to/spec.pdf"

# 4. Path to DOCX file
system_doc_docx = "path/to/spec.docx"

# Test with simple text first
client = NPersonaClient(api_key="...", provider="openai")
profile = await client.extract_profile(system_doc_text)
print(f"Profile extracted: {profile.system_name}")
```

**Ensure documentation**:
- Is not empty
- Contains meaningful system description
- Is UTF-8 encoded (for text files)
- Is not password-protected (for PDFs)

---

### 5. Empty or Missing Results

#### Error: `No test cases generated`

**Cause**: Profile extraction found no testable components

**Solutions**:

```python
# Check profile extraction
profile = await client.extract_profile(system_doc)

print(f"Agents found: {len(profile.agents)}")
print(f"Sensitive data identified: {len(profile.sensitive_data)}")
print(f"Guardrails found: {len(profile.guardrails)}")

# If empty, add more detail to documentation
better_doc = """
System Name: Virtual Gym Trainer

Capabilities:
- Generates personalized workout plans
- Provides exercise form feedback
- Offers motivational coaching

Constraints:
- No medical diagnoses
- No medication prescriptions
- User privacy protected

Integrations:
- Connects to fitness trackers
- Integrates with wearables
"""

profile = await client.extract_profile(better_doc)
```

#### Error: `Test execution returned no results`

**Cause**: Executor failed or endpoint issues

**Solutions**:

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run with verbose output
report = await client.run(system_doc)

# Check individual stages
profile = await client.extract_profile(system_doc)
print(f"Profile: {profile}")

attack_map = client.map_attack_surfaces(profile)
print(f"Targets: {len(attack_map.targets)}")

suite = await client.generate_test_suite(profile, attack_map)
print(f"Test cases: {len(suite.cases)}")

# Try executing just one test
from npersona.adapters.json_post import JsonPostAdapter

adapter = JsonPostAdapter(
    endpoint="your-endpoint",
    timeout=30.0,
)

# Test with simpler config
from npersona.models.config import NPersonaConfig

config = NPersonaConfig(
    num_adversarial=1,
    num_user_centric=1,
    executor_concurrency=1,
)
```

---

### 6. Report Generation Issues

#### Error: `Failed to export report`

**Cause**: File permission or format issues

**Solutions**:

```python
from pathlib import Path

# Check file paths are writable
report_dir = Path("./reports")
report_dir.mkdir(exist_ok=True)

# Export to specific directory
report.export_json(str(report_dir / "report.json"))
report.export_markdown(str(report_dir / "report.md"))
report.export_html(str(report_dir / "report.html"))

# Check file was created
json_file = report_dir / "report.json"
print(f"File exists: {json_file.exists()}")
print(f"File size: {json_file.stat().st_size} bytes")
```

**Common causes**:
- Directory doesn't exist: Create it first
- No write permissions: Check folder permissions
- Disk full: Free up space
- Special characters in path: Use absolute paths

---

### 7. Model/Memory Issues

#### Error: `Out of memory` or `Process killed`

**Cause**: Large test suites consuming too much memory

**Solutions**:

```python
# Reduce test suite size
from npersona.models.config import NPersonaConfig

config = NPersonaConfig(
    num_adversarial=5,      # Reduced from 20
    num_user_centric=2,     # Reduced from 10
    executor_concurrency=1, # Run tests sequentially
)

# Monitor memory usage
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
```

**Prevention**:
- Start with small test counts (5-10 total)
- Increase gradually if system has resources
- Monitor memory during execution

---

### 8. LLM Provider Specific Issues

#### OpenAI Issues

```python
# Check API key format
api_key = "sk-..."  # Should start with "sk-"

# Common OpenAI errors:
# 401 Unauthorized → Wrong key
# 429 Rate Limited → Reduce requests/concurrency
# 503 Service Unavailable → OpenAI is down

# Test with simple prompt
import httpx

async def test_openai():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "test"}],
            },
        )
        print(response.status_code, response.text[:100])
```

#### Azure OpenAI Issues

```python
# Verify all 4 required fields
config = NPersonaConfig(
    llm=LLMConfig(
        provider="azure",
        api_key="your-key",           # From Azure portal
        model="gpt-4o",               # Your deployment name
        base_url="https://NAME.openai.azure.com/",  # Your instance
        api_version="2025-01-01-preview",  # API version
    )
)

# Test each field
print(f"Key length: {len(config.llm.api_key)}")
print(f"Model: {config.llm.model}")
print(f"Base URL: {config.llm.base_url}")
print(f"API Version: {config.llm.api_version}")
```

#### Groq Issues

```python
# Groq is free tier with lower rate limits
# If you hit rate limits:
# 1. Reduce test count
# 2. Use a paid provider for production
# 3. Wait before retrying

config = NPersonaConfig(
    num_adversarial=3,  # Small for Groq
    num_user_centric=1,
)
```

---

## Debugging Techniques

### Enable Debug Logging

```python
import logging

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now run your code with verbose output
report = await client.run(system_doc)
```

### Test Each Stage Independently

```python
# Don't run full pipeline, test each stage:

# Stage 1: Profile Extraction
print("Testing Stage 1...")
profile = await client.extract_profile(system_doc)
assert profile.agents, "No agents found"

# Stage 2: Attack Mapping
print("Testing Stage 2...")
attack_map = client.map_attack_surfaces(profile)
assert attack_map.targets, "No targets found"

# Stage 3: Test Generation
print("Testing Stage 3...")
suite = await client.generate_test_suite(profile, attack_map)
assert suite.cases, "No tests generated"

# Continue...
```

### Use Progress Callbacks

```python
def on_progress(update):
    print(f"[{update.get('stage')}] {update.get('message')}")

report = await client.run(
    system_doc,
    on_progress=on_progress,
)
```

### Save Intermediate Results

```python
# Save profile for inspection
import json

profile = await client.extract_profile(system_doc)
with open("profile_debug.json", "w") as f:
    json.dump(profile.model_dump(), f, indent=2)

# Inspect the file
print(open("profile_debug.json").read())
```

---

## Getting Help

### Information to Include When Asking for Help

```
1. Python version: python --version
2. NPersona version: pip show npersona
3. LLM provider: (openai, azure, groq, etc.)
4. Exact error message (full stack trace)
5. Your configuration (without API keys):
   - num_adversarial
   - num_user_centric
   - executor_concurrency
   - per_request_timeout
6. Steps to reproduce
```

### Where to Get Help

1. **GitHub Issues**: https://github.com/NPersona-AI/NPersona/issues
2. **Documentation**: https://github.com/NPersona-AI/NPersona#documentation
3. **Check this guide first**: Search for your error above

---

## Performance Troubleshooting

### Running too slowly?

```python
# 1. Reduce test count
config = NPersonaConfig(
    num_adversarial=5,      # from 20
    num_user_centric=2,     # from 10
)

# 2. Increase timeout (if API is slow)
llm_config = LLMConfig(
    timeout=120,  # Give LLM more time
)

# 3. Run in parallel
config = NPersonaConfig(
    executor_concurrency=4,  # Run 4 tests at once
)
```

### Running out of memory?

```python
# 1. Reduce concurrency
config = NPersonaConfig(
    executor_concurrency=1,  # One at a time
)

# 2. Smaller test suite
config = NPersonaConfig(
    num_adversarial=3,
    num_user_centric=1,
)

# 3. Monitor memory
import psutil
print(f"Memory: {psutil.virtual_memory().percent}%")
```

---

## Success Checklist

Use this to verify everything is working:

```
[ ] NPersona imports without errors
[ ] API key is valid and authorized
[ ] Endpoint is reachable (curl test)
[ ] Documentation loads successfully
[ ] Profile extraction completes
[ ] Attack surface mapping succeeds
[ ] Test suite generates cases
[ ] Tests execute against endpoint
[ ] Evaluation completes
[ ] Reports export in all formats
[ ] No timeouts or crashes occurred
```

---

## Still Having Issues?

1. **Check this guide** - Most common issues covered above
2. **Check logs** - Enable debug logging for detailed output
3. **Test incrementally** - Test each stage independently
4. **Isolate the problem** - Use simpler inputs first
5. **Report to GitHub** - With full information from "Getting Help" section

---

**Last Updated**: April 14, 2026  
**NPersona Version**: 1.0.1+

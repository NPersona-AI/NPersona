# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-04-12

### Added

#### Core Framework
- 7-stage security testing pipeline (Profile → Mapper → Generator → Executor → Evaluator → RCA → Reporter)
- 28-category attack taxonomy (A01-A20 adversarial + U01-U08 user-centric)
- 40+ research-backed known attack corpus
- Production-grade test execution with parallelism, retries, and rate limiting

#### Authentication
- Bearer token authentication
- OAuth2 client credentials flow with automatic token refresh
- API Key authentication (custom header support)
- Basic Authentication
- Custom authentication via callable adapters
- Token caching with configurable expiration buffer

#### Request Adapters
- JSON POST adapter (default)
- OpenAI Chat format adapter
- AWS Bedrock agent adapter
- Custom callable adapter for extensibility

#### Execution Engine
- Concurrent test execution with configurable semaphore
- Exponential backoff retry logic with configurable max attempts
- Token bucket rate limiting (RPS control)
- Per-request timeouts and overall batch timeouts
- Failure isolation (per-test error recording)
- Comprehensive telemetry (latency, status codes, retry counts)
- Multi-turn conversation support with session persistence

#### Evaluation
- LLM-as-judge evaluation (configurable LLM)
- Keyword fallback evaluation for edge cases
- Pass/fail determination with detailed reasoning
- Batch evaluation with efficient API usage

#### LLM Provider Support
- OpenAI (GPT-4o, GPT-4-turbo, etc.)
- Anthropic Claude (Opus, Sonnet, Haiku)
- Groq (Llama-3.3-70B, Mixtral, etc.)
- Azure OpenAI
- Google Gemini
- Ollama (local models)
- Unified interface via LiteLLM

#### Report Generation
- JSON export with detailed findings
- Markdown export with formatted tables
- HTML export with interactive dashboard (planned)
- Coverage analysis
- Vulnerability categorization
- Remediation recommendations

#### Testing & Quality
- 115+ comprehensive unit and integration tests
- 100% test coverage for core modules
- Real API integration tests with mock server
- End-to-end pipeline tests
- Regression test suite

### Features
- Type hints throughout codebase
- Comprehensive logging
- Configurable concurrency and timeouts
- Extensible architecture via adapters
- Caching for profile extraction
- Progress callbacks
- CLI interface (basic)

### Documentation
- Comprehensive README
- Installation guide
- User guide with examples
- API reference
- Architecture documentation
- Testing guide with real API examples
- Contributing guidelines
- Security policy

### Infrastructure
- GitHub Actions CI/CD pipeline
- Automated testing on multiple Python versions
- Code quality checks (black, flake8, mypy)
- Dependency management
- Security scanning

## [0.9.0] - 2026-04-01

### Added (Pre-release)
- Core pipeline implementation
- Basic authentication support
- Test execution framework
- LLM integration
- Report generation

### Known Issues
- Web dashboard not yet implemented
- Limited adapter types
- Basic CLI only

---

## Versioning

- **Major**: Breaking changes to API or core functionality
- **Minor**: New features, backwards compatible
- **Patch**: Bug fixes, documentation updates

## Migration Guide

### v0.9.0 → v1.0.0

#### Breaking Changes
- `TestResult` now includes `latency_ms`, `status_code`, `attempts` fields
- `OAuth2Config` requires `token_endpoint` (previously optional)
- Executor returns `list[TestResult]` instead of tuple

#### Migration
```python
# Old
results = executor.run(tests)  # Returns tuple

# New
results = await executor.run(tests)  # Returns list[TestResult]
for result in results:
    print(f"Latency: {result.latency_ms}ms")
    print(f"Status: {result.status_code}")
    print(f"Attempts: {result.attempts}")
```

## Future Roadmap

### v1.1.0 (Q3 2026)
- [ ] Web dashboard for visualization
- [ ] Multi-model evaluation consensus
- [ ] Custom taxonomy support
- [ ] Enhanced RCA capabilities

### v1.2.0 (Q4 2026)
- [ ] Continuous monitoring integration
- [ ] ML-based vulnerability prediction
- [ ] Automated remediation suggestions
- [ ] Enterprise SAML support

### v2.0.0 (2027)
- [ ] Distributed testing framework
- [ ] Advanced analytics engine
- [ ] Supply chain security testing
- [ ] Compliance automation

## Deprecation Policy

Features are deprecated with a 2-release notice:
1. Feature marked as deprecated in release N
2. Warning logged when used in release N+1
3. Feature removed in release N+2

## Support


- **Bug Reports**: GitHub Issues
- **Feature Requests**: GitHub Discussions
- **General Questions**: npersona.ai@gmail.com

---

Generated 2026-04-12 | [Latest Release](https://github.com/NPersona-AI/npersona/releases)

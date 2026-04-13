# Contributing to NPersona

We welcome contributions to NPersona! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We're committed to providing a welcoming and inclusive environment.

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- Virtual environment (recommended)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/NPersona-AI/npersona.git
cd npersona

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all extras
pip install -e ".[dev,test]"

# Verify installation
pytest tests/ -v
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/bug-description
```

### 2. Make Changes

Follow these guidelines:
- **Code Style**: Use `black` for formatting
- **Type Hints**: Add type annotations to functions
- **Docstrings**: Use Google-style docstrings
- **Tests**: Write tests for new features
- **Documentation**: Update docs for user-facing changes

### 3. Run Quality Checks

```bash
# Format code
black npersona/ tests/

# Lint
flake8 npersona/ tests/

# Type checking
mypy npersona/

# Run tests
pytest tests/ -v --cov=npersona

# All checks
make check
```

### 4. Commit

Write clear commit messages:

```
feat: Add OAuth2 token refresh logic
- Implement automatic token refresh with 60s buffer
- Add unit tests for token manager
- Update documentation with OAuth2 example

Fixes #123
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request with:
- Clear title describing the change
- Description of what changed and why
- Link to related issues
- Test results/coverage

## Areas for Contribution

### High Priority

- [ ] Web dashboard for result visualization
- [ ] Additional LLM provider support
- [ ] Custom taxonomy framework
- [ ] Enterprise features (SAML, advanced RBAC)

### Medium Priority

- [ ] Performance optimizations
- [ ] Additional attack adapters
- [ ] Extended documentation
- [ ] Community examples

### Low Priority

- [ ] UI/UX improvements
- [ ] Additional output formats
- [ ] Internationalization

## Testing Guidelines

### Unit Tests

```python
import pytest
from npersona.pipeline.executor import Executor

@pytest.mark.asyncio
async def test_executor_applies_auth():
    # Arrange
    config = create_test_config()
    executor = Executor(config)
    
    # Act
    result = await executor.run(test_cases)
    
    # Assert
    assert result[0].passed
```

### Integration Tests

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline():
    # Test against real (or mock) API
    client = NPersonaClient(config)
    report = await client.run("spec.pdf")
    assert report.evaluation is not None
```

### Test Coverage

- Minimum 80% code coverage
- All public APIs tested
- Edge cases covered
- Error paths tested

Run coverage report:
```bash
pytest --cov=npersona --cov-report=html
open htmlcov/index.html
```

## Documentation

### Updating Docs

1. **README.md**: Main introduction and quick start
2. **docs/INSTALLATION.md**: Detailed setup
3. **docs/USER_GUIDE.md**: Comprehensive usage
4. **docs/API_REFERENCE.md**: API documentation
5. **docs/ARCHITECTURE.md**: System design

### Docstring Format

```python
def extract_profile(self, document: str, extra_context: str = "") -> SystemProfile:
    """Extract system profile from documentation.
    
    Parses AI system documentation and extracts key characteristics including
    system name, agents, guardrails, integrations, and sensitive data types.
    
    Args:
        document: Path to or raw text of system documentation.
        extra_context: Optional additional context for LLM.
    
    Returns:
        SystemProfile with extracted system characteristics.
    
    Raises:
        ValueError: If document is empty or invalid.
        LLMError: If LLM call fails.
    
    Example:
        >>> client = NPersonaClient()
        >>> profile = await client.extract_profile("spec.pdf")
        >>> print(profile.system_name)
    """
```

## Code Review Process

1. **Automated Checks**: Tests, linting, type checking must pass
2. **Code Review**: At least one maintainer review
3. **Functional Review**: Verify feature works as intended
4. **Documentation Review**: Ensure docs are updated
5. **Merge**: After approval, squash and merge

## Reporting Issues

### Bug Reports

Include:
- Python version and OS
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error logs/tracebacks
- Minimal reproducible example

### Feature Requests

Include:
- Clear description of feature
- Use case and motivation
- Proposed implementation (optional)
- Alternative approaches (optional)

## Security

For security issues, please email npersona.ai@gmail.com instead of using public issue tracker.

See [SECURITY.md](./SECURITY.md) for responsible disclosure policy.

## Release Process

1. Update version in `npersona/__init__.py`
2. Update `CHANGELOG.md`
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. GitHub Actions automatically publishes to PyPI

## Questions?

- Check existing issues and discussions
- Read documentation in `docs/`
- Open a discussion on GitHub
- Email us at npersona.ai@gmail.com

Thank you for contributing! 🎉

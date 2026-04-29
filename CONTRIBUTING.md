# Contributing to VeilleAI

Thanks for your interest in contributing to **VeilleAI**! This document outlines the process and guidelines for contributing to the project.

## Code of Conduct

We are committed to fostering an inclusive, welcoming community. Please be respectful and constructive in all interactions.

## Getting Started

### 1. Fork and Clone the Repository
```bash
git clone https://github.com/Aarf101/AgenticNotes.git
cd AgenticNotes
```

### 2. Set Up Your Development Environment

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"  # Install with dev dependencies
```

**Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e ".[dev]"
```

### 3. Install Pre-Commit Hooks (Optional but Recommended)
```bash
pre-commit install
```

This automatically runs linters and formatters before each commit.

## Development Workflow

### Branch Naming
Use descriptive branch names following this pattern:
- `feature/description-of-feature`
- `bugfix/description-of-bug`
- `docs/description-of-docs`
- `refactor/description-of-refactor`

Example:
```bash
git checkout -b feature/add-config-validation
```

### Code Style

We follow **PEP 8** and use automated tools to enforce consistency:

#### Formatting with Black
```bash
black watcher/
```

#### Import Sorting with isort
```bash
isort watcher/
```

#### Linting with Pylint
```bash
pylint watcher/
```

#### Type Checking with mypy (Optional)
```bash
mypy watcher/
```

**All PRs must pass linting checks.** Configuration is in `pyproject.toml` and `.pylintrc`.

### Commit Messages

Write clear, descriptive commit messages:

```
[AREA] Brief description (max 50 chars)

Detailed explanation of the change (max 72 chars per line).
- List key changes if multiple
- Reference issues if applicable (#123)

Fixes #123
```

Examples:
- `[feat] Add config validation layer`
- `[fix] Handle timeout in scheduler`
- `[docs] Update API documentation`
- `[refactor] Simplify error handling`

## Testing

### Running Tests

Run all tests:
```bash
pytest
```

Run specific test file:
```bash
pytest tests/test_collector.py
```

Run tests by marker:
```bash
pytest -m unit  # Only unit tests
pytest -m integration  # Only integration tests
```

Run with coverage report:
```bash
pytest --cov=watcher --cov-report=html tests/
# Open htmlcov/index.html in browser
```

### Writing Tests

- Place tests in the `tests/` directory
- Follow naming convention: `test_<module>.py`
- Use descriptive test names: `test_filter_removes_duplicates()`
- Mark tests appropriately:

```python
import pytest

@pytest.mark.unit
def test_collector_initialization():
    """Test that collector initializes with valid config."""
    collector = Collector(config={"feeds": []})
    assert collector is not None

@pytest.mark.integration
@pytest.mark.network
def test_rss_feed_fetch():
    """Test RSS feed fetching (requires network)."""
    # Test implementation
    pass
```

### Test Coverage

Aim for **>80% code coverage** on new code. Check coverage:
```bash
pytest --cov=watcher tests/
```

## Documentation

### Update Docstrings
Use Google-style docstrings:

```python
def synthesize(self, topic: str, items: List[Dict]) -> str:
    """Synthesize a report from collected items.
    
    Args:
        topic: The topic to synthesize about
        items: List of articles/items to synthesize
        
    Returns:
        Markdown-formatted synthesis report
        
    Raises:
        ValueError: If items list is empty
    """
    pass
```

### Update README.md
If your changes affect user-facing features, update the README with:
- New installation steps if dependencies changed
- New usage examples
- Updated architecture diagram if applicable

### Update CHANGELOG
Document your changes following [Keep a Changelog](https://keepachangelog.com/) format.

## Pull Request Process

1. **Create a descriptive PR title** following the commit message format
2. **Link related issues** in the PR description (`Closes #123`)
3. **Describe your changes** clearly:
   - What problem does this solve?
   - How does it work?
   - Any breaking changes?

4. **Run tests locally** before submitting:
   ```bash
   pytest
   black --check watcher/
   pylint watcher/
   ```

5. **Wait for CI/CD to pass** — GitHub Actions will automatically run:
   - Pytest test suite
   - Pylint linting
   - Code coverage checks

6. **Respond to reviews** promptly and professionally

## Reporting Issues

### Bug Reports
Include:
- Python version and OS
- Exact reproduction steps
- Expected vs actual behavior
- Error traceback (if applicable)
- Relevant config files (mask sensitive keys)

### Feature Requests
Include:
- Clear description of the feature
- Why it would be useful
- Example use cases
- Potential implementation approach (optional)

## Areas Needing Contributions

Priority areas for help:
1. **Testing** — Unit and integration tests for agents
2. **Documentation** — API docs, troubleshooting guides
3. **Error Handling** — Better error messages and recovery
4. **Performance** — Async/await patterns, caching optimization
5. **CI/CD** — GitHub Actions pipeline setup

## Questions?

- Check existing [issues](https://github.com/Aarf101/AgenticNotes/issues)
- Review [documentation](./docs/)
- Open a [discussion](https://github.com/Aarf101/AgenticNotes/discussions)

Thank you for contributing to VeilleAI! 🚀

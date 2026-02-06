# Testing Guide

This document provides comprehensive guidance on testing the ML Workflow Orchestration Platform.

## Table of Contents

- [Overview](#overview)
- [Testing Infrastructure](#testing-infrastructure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Property-Based Testing](#property-based-testing)
- [Test Coverage](#test-coverage)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

The platform uses a comprehensive testing strategy that includes:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test interactions between components
- **Property-Based Tests**: Test universal properties using Hypothesis
- **Security Tests**: Test security controls and vulnerabilities
- **Performance Tests**: Test system performance under load

### Testing Stack

- **pytest**: Primary testing framework
- **Hypothesis**: Property-based testing library
- **pytest-cov**: Code coverage reporting
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking utilities
- **factory-boy**: Test data factories

## Testing Infrastructure

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_health.py           # Basic health check tests
├── unit/                    # Unit tests
│   ├── test_auth.py
│   ├── test_models.py
│   └── test_services.py
├── integration/             # Integration tests
│   ├── test_api.py
│   └── test_workflows.py
├── property/                # Property-based tests
│   ├── test_auth_properties.py
│   └── test_model_properties.py
└── security/                # Security tests
    └── test_security.py
```

### Test Configuration

Tests are configured in `pytest.ini` and `pyproject.toml`:

- **Test Discovery**: Automatically finds `test_*.py` files
- **Markers**: Custom markers for test categorization
- **Coverage**: Configured for 80%+ coverage target
- **Asyncio**: Automatic async test support

### Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

- `test_db_engine`: In-memory SQLite database
- `test_db_session`: Database session with rollback
- `test_client`: FastAPI test client
- `test_admin_user`: Admin user fixture
- `test_data_scientist_user`: Data scientist user fixture
- `test_regular_user`: Regular user fixture
- `admin_token`: JWT token for admin user
- `auth_headers`: Authorization headers

## Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test types
make test-unit
make test-integration
make test-property
```

### Using pytest Directly

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_health.py

# Run specific test function
pytest tests/test_health.py::test_health_endpoint

# Run tests matching pattern
pytest tests/ -k "auth"

# Run tests with specific marker
pytest tests/ -m unit
pytest tests/ -m property_test
pytest tests/ -m integration
```

### Running Tests in Docker

```bash
# Run all tests in Docker
make test-docker

# Run property-based tests in Docker
make test-property-docker

# Manual Docker Compose
docker-compose -f docker-compose.test.yml up --build
```

### CI Test Execution

```bash
# Run tests as they run in CI
make test-ci

# This runs:
# - All unit tests
# - Integration tests
# - Property-based tests (200 examples)
# - Coverage reporting
# - JUnit XML output
```

## Writing Tests

### Unit Test Example

```python
import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_user_creation(test_db_session, test_roles):
    """Test creating a new user."""
    from src.services.user_management.models import User
    from src.shared.auth import password_manager
    
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=password_manager.hash_password("password123"),
        roles=[test_roles["regular_user"]]
    )
    
    test_db_session.add(user)
    test_db_session.commit()
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.is_active is True
```

### Integration Test Example

```python
import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_login_flow(test_client: TestClient, test_admin_user):
    """Test complete login flow."""
    # Attempt login
    response = test_client.post(
        "/api/v1/auth/login",
        json={
            "username": "test_admin",
            "password": "admin_password"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    
    # Use token to access protected endpoint
    token = data["access_token"]
    response = test_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["username"] == "test_admin"
```

### Async Test Example

```python
import pytest


@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_operation():
    """Test async operation."""
    from src.services.workflow_engine.service import WorkflowService
    
    service = WorkflowService()
    result = await service.execute_workflow(workflow_id="test-123")
    
    assert result is not None
    assert result.status == "completed"
```

## Property-Based Testing

Property-based tests use Hypothesis to generate test cases automatically.

### Writing Property Tests

```python
import pytest
from hypothesis import given, strategies as st


@pytest.mark.property_test
@given(
    username=st.text(min_size=3, max_size=50),
    password=st.text(min_size=8, max_size=128)
)
def test_password_hashing_consistency(username, password):
    """
    Feature: ml-workflow-platform, Property 16: Password Security
    For any user password storage, passwords should be securely hashed
    with salt and plain text passwords should never be stored.
    
    **Validates: Requirements 8.2**
    """
    from src.shared.auth import password_manager
    
    # Hash the password
    hashed = password_manager.hash_password(password)
    
    # Verify properties
    assert hashed != password  # Never store plain text
    assert len(hashed) > len(password)  # Hash is longer
    assert password_manager.verify_password(password, hashed)  # Can verify
    
    # Hash same password again - should be different (salt)
    hashed2 = password_manager.hash_password(password)
    assert hashed != hashed2  # Different due to salt
    assert password_manager.verify_password(password, hashed2)  # Both verify
```

### Hypothesis Strategies

Custom strategies are defined in `tests/conftest.py`:

```python
from hypothesis import strategies as st

# Username: 3-50 alphanumeric + underscore, starts with letter
username_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="_"
    ),
    min_size=3,
    max_size=50
).filter(lambda x: x[0].isalpha())

# Email: valid email format
email_strategy = st.emails()

# Password: 8-128 chars with mixed case
password_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="!@#$%^&*()_+-="
    ),
    min_size=8,
    max_size=128
).filter(lambda x: any(c.isupper() for c in x) and any(c.islower() for c in x))
```

### Hypothesis Profiles

Configure test intensity with profiles:

```bash
# Development (10 examples, fast)
HYPOTHESIS_PROFILE=dev pytest tests/ -m property_test

# Default (100 examples)
pytest tests/ -m property_test

# CI (200 examples, verbose)
HYPOTHESIS_PROFILE=ci pytest tests/ -m property_test

# Debug (10 examples, verbose)
HYPOTHESIS_PROFILE=debug pytest tests/ -m property_test
```

## Test Coverage

### Viewing Coverage

```bash
# Generate coverage report
make test-cov

# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Requirements

- **Minimum**: 70% overall coverage (CI gate)
- **Target**: 80%+ coverage
- **Critical paths**: 90%+ coverage (auth, security)

### Coverage Configuration

Coverage is configured in `pytest.ini`:

```ini
[coverage:run]
source = src
omit = 
    */tests/*
    */test_*.py
    */__pycache__/*

[coverage:report]
precision = 2
show_missing = True
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
```

### Excluding Code from Coverage

```python
def debug_only_function():  # pragma: no cover
    """This function is excluded from coverage."""
    pass
```

## CI/CD Integration

### GitHub Actions Workflows

The platform includes two main workflows:

#### 1. CI/CD Pipeline (`.github/workflows/ci-cd.yml`)

Runs on every push and pull request:

- **Code Quality**: Black, isort, Flake8, MyPy, Bandit
- **Tests**: Unit, integration, property-based tests
- **Coverage**: Uploads to Codecov
- **Build**: Docker image build and push
- **Deploy**: Staging and production deployment

#### 2. Security Scanning (`.github/workflows/security-scan.yml`)

Runs daily and on main branch:

- **Dependency Scan**: Safety, pip-audit
- **SAST**: Bandit, Semgrep
- **CodeQL**: GitHub security analysis
- **Secret Scan**: Gitleaks, TruffleHog
- **Container Scan**: Trivy
- **License Check**: pip-licenses

### Running CI Checks Locally

```bash
# Run all CI checks
make ci-test

# Individual checks
make lint
make type-check
make security-check
make test-ci
```

### CI Environment Variables

Tests in CI use these environment variables:

```yaml
DATABASE_URL: postgresql://test_user:test_password@localhost:5432/test_db
REDIS_URL: redis://localhost:6379/0
SECRET_KEY: test-secret-key-for-ci
HYPOTHESIS_PROFILE: ci
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use pytest with proper path
pytest tests/ --import-mode=importlib
```

#### 2. Database Connection Errors

```bash
# Check database is running
docker-compose ps

# Restart database
docker-compose restart postgres redis

# Check connection
psql -h localhost -U test_user -d test_db
```

#### 3. Fixture Not Found

```bash
# Ensure conftest.py is in tests/ directory
ls tests/conftest.py

# Check fixture is defined
grep "def test_client" tests/conftest.py
```

#### 4. Hypothesis Flaky Tests

```python
# Add assume() to filter invalid inputs
from hypothesis import assume

@given(value=st.integers())
def test_something(value):
    assume(value > 0)  # Skip negative values
    # test code
```

#### 5. Slow Tests

```bash
# Run only fast tests
pytest tests/ -m "not slow"

# Profile slow tests
pytest tests/ --durations=10

# Use smaller Hypothesis profile
HYPOTHESIS_PROFILE=dev pytest tests/ -m property_test
```

### Debug Mode

```bash
# Run with verbose output
pytest tests/ -vv

# Show print statements
pytest tests/ -s

# Drop into debugger on failure
pytest tests/ --pdb

# Full traceback
pytest tests/ --tb=long
```

### Test Isolation Issues

```bash
# Run tests in random order
pytest tests/ --random-order

# Run specific test in isolation
pytest tests/test_file.py::test_function -v

# Clear pytest cache
pytest --cache-clear
```

## Best Practices

### 1. Test Naming

- Use descriptive names: `test_user_login_with_valid_credentials`
- Follow pattern: `test_<what>_<condition>_<expected>`

### 2. Test Organization

- One test file per module
- Group related tests in classes
- Use markers for categorization

### 3. Fixtures

- Keep fixtures simple and focused
- Use fixture scope appropriately
- Document fixture purpose

### 4. Assertions

- One logical assertion per test
- Use descriptive assertion messages
- Test both positive and negative cases

### 5. Test Data

- Use factories for complex objects
- Avoid hardcoded test data
- Clean up test data after tests

### 6. Mocking

- Mock external dependencies
- Don't mock what you're testing
- Verify mock calls when relevant

### 7. Property Tests

- Test universal properties
- Use appropriate strategies
- Add examples for edge cases

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)

## Support

For testing questions or issues:

1. Check this documentation
2. Review existing tests for examples
3. Check CI logs for error details
4. Ask in team chat or create an issue

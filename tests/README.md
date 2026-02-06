# Test Suite

This directory contains the test suite for the ML Workflow Orchestration Platform.

## Quick Start

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test types
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m property_test
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_health.py           # Basic infrastructure tests
├── unit/                    # Unit tests (to be added)
├── integration/             # Integration tests (to be added)
├── property/                # Property-based tests (to be added)
└── security/                # Security tests (to be added)
```

## Test Markers

Tests are organized using pytest markers:

- `@pytest.mark.unit`: Unit tests for individual components
- `@pytest.mark.integration`: Integration tests for component interactions
- `@pytest.mark.property_test`: Property-based tests using Hypothesis
- `@pytest.mark.slow`: Tests that take longer to run
- `@pytest.mark.smoke`: Quick smoke tests
- `@pytest.mark.security`: Security-focused tests

## Fixtures

Common fixtures are available in `conftest.py`:

### Database Fixtures
- `test_db_engine`: In-memory SQLite database engine
- `test_db_session`: Database session with automatic rollback
- `test_client`: FastAPI test client with database override

### User Fixtures
- `test_roles`: Pre-configured roles (admin, data_scientist, regular_user)
- `test_admin_user`: Admin user with full permissions
- `test_data_scientist_user`: Data scientist user
- `test_regular_user`: Regular user with basic permissions

### Authentication Fixtures
- `admin_token`: JWT token for admin user
- `scientist_token`: JWT token for data scientist
- `user_token`: JWT token for regular user
- `auth_headers`: Authorization headers with admin token

### Property-Based Testing Strategies
- `username_strategy`: Valid username generation
- `email_strategy`: Valid email generation
- `password_strategy`: Secure password generation
- `name_strategy`: Valid name generation

## Writing Tests

### Unit Test Example

```python
import pytest

@pytest.mark.unit
def test_password_hashing():
    from src.shared.auth import password_manager
    
    password = "test_password"
    hashed = password_manager.hash_password(password)
    
    assert hashed != password
    assert password_manager.verify_password(password, hashed)
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
def test_user_login(test_client, test_admin_user):
    response = test_client.post(
        "/api/v1/auth/login",
        json={"username": "test_admin", "password": "admin_password"}
    )
    
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### Property-Based Test Example

```python
import pytest
from hypothesis import given, strategies as st

@pytest.mark.property_test
@given(password=st.text(min_size=8, max_size=128))
def test_password_hashing_property(password):
    """
    Feature: ml-workflow-platform, Property 16: Password Security
    **Validates: Requirements 8.2**
    """
    from src.shared.auth import password_manager
    
    hashed = password_manager.hash_password(password)
    assert hashed != password
    assert password_manager.verify_password(password, hashed)
```

## Running Tests

### Local Development

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific markers
make test-unit
make test-integration
make test-property

# Run in Docker
make test-docker
```

### CI Environment

Tests run automatically in GitHub Actions on every push and pull request.

```bash
# Simulate CI environment locally
make test-ci
```

## Coverage

Coverage reports are generated in multiple formats:

- **Terminal**: Summary displayed after test run
- **HTML**: Detailed report in `htmlcov/index.html`
- **XML**: Machine-readable report in `coverage.xml`

### Coverage Requirements

- **Minimum**: 70% (CI gate)
- **Target**: 80%+
- **Critical paths**: 90%+ (auth, security)

## Hypothesis Configuration

Property-based tests use Hypothesis with different profiles:

- **dev**: 10 examples (fast, for development)
- **default**: 100 examples (standard)
- **ci**: 200 examples (thorough, for CI)
- **debug**: 10 examples with verbose output

Set profile with environment variable:

```bash
HYPOTHESIS_PROFILE=ci pytest tests/ -m property_test
```

## Troubleshooting

### Import Errors

Ensure PYTHONPATH includes the project root:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Errors

Tests use in-memory SQLite by default. If you see database errors:

1. Check that SQLAlchemy models are properly imported
2. Verify fixtures are being used correctly
3. Ensure database session is rolled back after tests

### Async Event Loop Issues (Windows)

On Windows, you may see `ProactorEventLoop` errors with async tests. This is a known issue with psycopg and Windows. Solutions:

1. Use synchronous database operations in tests
2. Use SQLite for testing (already configured)
3. Run tests in Docker (recommended for CI)

### Fixture Not Found

If pytest can't find a fixture:

1. Check that `conftest.py` is in the `tests/` directory
2. Verify the fixture is defined in `conftest.py`
3. Check fixture scope matches your usage

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Names**: Use descriptive test names
3. **One Assertion**: Focus on one logical assertion per test
4. **Use Fixtures**: Leverage fixtures for common setup
5. **Mock External**: Mock external dependencies
6. **Property Tests**: Use for universal properties
7. **Coverage**: Aim for high coverage, but focus on quality

## Documentation

For more detailed information, see:

- [Testing Guide](../docs/TESTING.md)
- [CI/CD Documentation](../docs/CI-CD.md)
- [pytest Documentation](https://docs.pytest.org/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)

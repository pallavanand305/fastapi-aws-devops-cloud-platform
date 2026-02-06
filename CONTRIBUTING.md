# Contributing to ML Workflow Orchestration Platform

Thank you for your interest in contributing to the ML Workflow Orchestration Platform! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Prioritize the community's best interests

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git
- Poetry (recommended) or pip

### Initial Setup

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/ml-workflow-platform.git
   cd ml-workflow-platform
   ```

2. **Run the Setup Script**
   ```bash
   python scripts/setup_dev_env.py
   ```
   
   Or use Make:
   ```bash
   make first-time-setup
   ```

3. **Verify Installation**
   ```bash
   make test
   make health
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications
- `chore/` - Maintenance tasks

### 2. Make Your Changes

Follow the coding standards and best practices outlined below.

### 3. Run Tests and Quality Checks

Before committing, ensure all checks pass:

```bash
# Run all quality checks
make ci-test

# Or run individually
make format        # Format code
make lint          # Check linting
make type-check    # Type checking
make security-check # Security scanning
make test-cov      # Run tests with coverage
```

### 4. Commit Your Changes

Follow the commit message guidelines (see below).

```bash
git add .
git commit -m "feat: add new feature description"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Coding Standards

### Python Style Guide

We follow PEP 8 with some modifications enforced by Black:

- **Line Length:** 88 characters (Black default)
- **Indentation:** 4 spaces
- **Quotes:** Double quotes for strings
- **Imports:** Sorted with isort

### Code Organization

#### Service Structure

Each microservice follows this structure:

```
service_name/
├── __init__.py          # Service initialization
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── repository.py        # Data access layer
├── service.py           # Business logic
├── routes.py            # API endpoints
└── dependencies.py      # FastAPI dependencies
```

#### Layer Responsibilities

1. **Routes Layer** (`routes.py`)
   - Handle HTTP requests/responses
   - Input validation (Pydantic)
   - Call service layer
   - Return appropriate HTTP status codes

2. **Service Layer** (`service.py`)
   - Business logic
   - Orchestrate repository calls
   - Handle business exceptions
   - No direct database access

3. **Repository Layer** (`repository.py`)
   - Database operations
   - Query construction
   - Transaction management
   - Return domain models

4. **Models Layer** (`models.py`)
   - SQLAlchemy ORM models
   - Database schema definition
   - Relationships and constraints

5. **Schemas Layer** (`schemas.py`)
   - Pydantic models for validation
   - Request/response DTOs
   - Data transformation

### Type Hints

Always use type hints for function parameters and return values:

```python
from typing import Optional, List
from uuid import UUID

def get_user_by_id(user_id: UUID) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def list_users(skip: int = 0, limit: int = 100) -> List[User]:
    """List users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()
```

### Docstrings

Use Google-style docstrings:

```python
def create_workflow(
    workflow_data: WorkflowCreate,
    user_id: UUID,
    db: Session
) -> Workflow:
    """Create a new workflow.

    Args:
        workflow_data: Workflow creation data
        user_id: ID of the user creating the workflow
        db: Database session

    Returns:
        Created workflow instance

    Raises:
        ValidationError: If workflow data is invalid
        PermissionError: If user lacks permissions
    """
    # Implementation
```

### Error Handling

Use custom exceptions from `src/shared/exceptions.py`:

```python
from src.shared.exceptions import NotFoundError, ValidationError

def get_workflow(workflow_id: UUID) -> Workflow:
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise NotFoundError(f"Workflow {workflow_id} not found")
    return workflow
```

### Async/Await

Use async/await for I/O operations:

```python
from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """Get user by ID."""
    user = await user_service.get_by_id(user_id, db)
    return UserResponse.from_orm(user)
```

## Testing Guidelines

### Test Structure

Tests are organized by type:

```
tests/
├── unit/              # Unit tests
│   └── services/
│       └── user_management/
├── integration/       # Integration tests
│   └── api/
├── property/          # Property-based tests
│   └── test_properties.py
└── conftest.py       # Pytest fixtures
```

### Unit Tests

Test individual functions and methods in isolation:

```python
import pytest
from src.services.user_management.service import UserService

def test_create_user_success(db_session):
    """Test successful user creation."""
    service = UserService(db_session)
    user_data = UserCreate(
        username="testuser",
        email="test@example.com",
        password="SecurePass123!"
    )
    
    user = service.create_user(user_data)
    
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.password_hash != "SecurePass123!"  # Should be hashed
```

### Property-Based Tests

Use Hypothesis for property-based testing:

```python
from hypothesis import given, strategies as st
import pytest

@pytest.mark.property_test
@given(
    username=st.text(min_size=3, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    email=st.emails()
)
def test_user_creation_property(username: str, email: str, db_session):
    """
    Feature: ml-workflow-platform, Property: User Creation Consistency
    For any valid username and email, user creation should succeed
    and the created user should be retrievable.
    **Validates: Requirements 1.1, 1.3**
    """
    service = UserService(db_session)
    user_data = UserCreate(username=username, email=email, password="Pass123!")
    
    user = service.create_user(user_data)
    retrieved = service.get_by_id(user.id)
    
    assert retrieved is not None
    assert retrieved.username == username
    assert retrieved.email == email
```

### Integration Tests

Test API endpoints and service interactions:

```python
from fastapi.testclient import TestClient

def test_login_endpoint(client: TestClient, test_user):
    """Test login endpoint."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "username": test_user.username,
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
```

### Test Coverage

- Maintain minimum 80% code coverage
- Focus on critical paths and edge cases
- Don't test framework code (FastAPI, SQLAlchemy)
- Mock external dependencies (AWS services, external APIs)

### Running Tests

```bash
# All tests
make test

# Specific test types
make test-unit
make test-property
make test-integration

# With coverage
make test-cov

# Watch mode (requires pytest-watch)
make test-watch
```

## Commit Message Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples

```bash
# Feature
git commit -m "feat(auth): add JWT refresh token support"

# Bug fix
git commit -m "fix(workflow): resolve race condition in job scheduler"

# Documentation
git commit -m "docs(readme): update installation instructions"

# Breaking change
git commit -m "feat(api)!: change user endpoint response format

BREAKING CHANGE: User endpoint now returns nested role objects instead of role IDs"
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass (`make test`)
2. ✅ Code is formatted (`make format`)
3. ✅ Linting passes (`make lint`)
4. ✅ Type checking passes (`make type-check`)
5. ✅ Security checks pass (`make security-check`)
6. ✅ Coverage is maintained or improved
7. ✅ Documentation is updated
8. ✅ Commit messages follow guidelines

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Property tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] Dependent changes merged

## Related Issues
Closes #123
```

### Review Process

1. **Automated Checks:** CI/CD pipeline runs automatically
2. **Code Review:** At least one approval required
3. **Testing:** Reviewer tests changes locally if needed
4. **Merge:** Squash and merge to main branch

### After Merge

- Delete feature branch
- Update local main branch
- Close related issues

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Project Architecture](ARCHITECTURE.md)

## Questions?

If you have questions or need help:

1. Check existing documentation
2. Search existing issues
3. Create a new issue with the `question` label
4. Join our community discussions

Thank you for contributing! 🎉

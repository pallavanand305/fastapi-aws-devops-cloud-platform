"""
Pytest configuration and shared fixtures for the test suite.

This module provides:
- Database fixtures for testing with SQLite and PostgreSQL
- FastAPI test client fixtures
- Authentication and user fixtures
- Property-based testing strategies
- Test data factories
"""
import os
import pytest
from typing import Generator, AsyncGenerator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from hypothesis import settings, Verbosity

# Import application components
from src.shared.database_local import BaseModel, get_db
from src.shared.auth import password_manager, jwt_manager
from src.services.user_management.models import User, Role, Permission
from src.main_local import app


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "property_test: mark test as a property-based test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Configure Hypothesis for property-based testing
settings.register_profile("default", max_examples=100, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=200, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=10, verbosity=Verbosity.normal)
settings.register_profile("debug", max_examples=10, verbosity=Verbosity.verbose)

# Load profile from environment or use default
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_db_engine():
    """
    Create an in-memory SQLite database engine for testing.
    
    This fixture creates a fresh database for each test function,
    ensuring test isolation.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Enable foreign key constraints for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    # Create all tables
    BaseModel.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    BaseModel.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Create a database session for testing.
    
    This fixture provides a database session that is rolled back
    after each test to ensure test isolation.
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="function")
def test_client(test_db_session) -> Generator[TestClient, None, None]:
    """
    Create a FastAPI test client with database dependency override.
    
    This fixture provides a test client that uses the test database
    instead of the production database.
    """
    def override_get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()


# ============================================================================
# User and Authentication Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_roles(test_db_session) -> dict[str, Role]:
    """
    Create test roles with permissions.
    
    Returns:
        Dictionary mapping role names to Role objects
    """
    # Create permissions
    permissions = {
        "read_users": Permission(resource="users", action="read"),
        "write_users": Permission(resource="users", action="write"),
        "read_projects": Permission(resource="projects", action="read"),
        "write_projects": Permission(resource="projects", action="write"),
        "read_models": Permission(resource="models", action="read"),
        "write_models": Permission(resource="models", action="write"),
        "admin_all": Permission(resource="*", action="*"),
    }
    
    for perm in permissions.values():
        test_db_session.add(perm)
    
    # Create roles
    roles = {
        "admin": Role(
            name="admin",
            description="Administrator with full access",
            permissions=[permissions["admin_all"]]
        ),
        "data_scientist": Role(
            name="data_scientist",
            description="Data scientist with ML workflow access",
            permissions=[
                permissions["read_users"],
                permissions["read_projects"],
                permissions["write_projects"],
                permissions["read_models"],
                permissions["write_models"],
            ]
        ),
        "regular_user": Role(
            name="regular_user",
            description="Regular user with basic access",
            permissions=[
                permissions["read_projects"],
                permissions["read_models"],
            ]
        ),
    }
    
    for role in roles.values():
        test_db_session.add(role)
    
    test_db_session.commit()
    
    return roles


@pytest.fixture(scope="function")
def test_admin_user(test_db_session, test_roles) -> User:
    """Create a test admin user."""
    user = User(
        username="test_admin",
        email="admin@test.com",
        first_name="Test",
        last_name="Admin",
        password_hash=password_manager.hash_password("admin_password"),
        is_active=True,
        roles=[test_roles["admin"]]
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_data_scientist_user(test_db_session, test_roles) -> User:
    """Create a test data scientist user."""
    user = User(
        username="test_scientist",
        email="scientist@test.com",
        first_name="Test",
        last_name="Scientist",
        password_hash=password_manager.hash_password("scientist_password"),
        is_active=True,
        roles=[test_roles["data_scientist"]]
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_regular_user(test_db_session, test_roles) -> User:
    """Create a test regular user."""
    user = User(
        username="test_user",
        email="user@test.com",
        first_name="Test",
        last_name="User",
        password_hash=password_manager.hash_password("user_password"),
        is_active=True,
        roles=[test_roles["regular_user"]]
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_token(test_admin_user) -> str:
    """Generate a JWT token for the admin user."""
    return jwt_manager.create_access_token(data={"sub": test_admin_user.username})


@pytest.fixture(scope="function")
def scientist_token(test_data_scientist_user) -> str:
    """Generate a JWT token for the data scientist user."""
    return jwt_manager.create_access_token(data={"sub": test_data_scientist_user.username})


@pytest.fixture(scope="function")
def user_token(test_regular_user) -> str:
    """Generate a JWT token for the regular user."""
    return jwt_manager.create_access_token(data={"sub": test_regular_user.username})


@pytest.fixture(scope="function")
def auth_headers(admin_token) -> dict[str, str]:
    """Generate authorization headers with admin token."""
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================================
# Property-Based Testing Strategies
# ============================================================================

from hypothesis import strategies as st

# Username strategy: 3-50 alphanumeric characters with underscores
username_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_"),
    min_size=3,
    max_size=50
).filter(lambda x: x[0].isalpha())  # Must start with letter

# Email strategy: valid email format
email_strategy = st.emails()

# Password strategy: 8-128 characters with mixed case, numbers, and special chars
password_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd"),
        whitelist_characters="!@#$%^&*()_+-=[]{}|;:,.<>?"
    ),
    min_size=8,
    max_size=128
).filter(lambda x: any(c.isupper() for c in x) and any(c.islower() for c in x))

# Name strategy: 1-100 alphabetic characters with spaces
name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll"), whitelist_characters=" "),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip() and not x.startswith(" ") and not x.endswith(" "))


@pytest.fixture
def user_credentials_strategy():
    """Strategy for generating valid user credentials."""
    return st.builds(
        dict,
        username=username_strategy,
        email=email_strategy,
        password=password_strategy,
        first_name=name_strategy,
        last_name=name_strategy,
    )


# ============================================================================
# Test Data Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically cleanup test data after each test."""
    yield
    # Cleanup logic runs after test
    # Additional cleanup can be added here if needed

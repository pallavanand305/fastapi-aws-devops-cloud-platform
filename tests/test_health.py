"""
Basic health check tests to verify testing infrastructure is working.
"""
import pytest


@pytest.mark.unit
def test_password_hashing():
    """Test that password hashing works correctly."""
    from src.shared.auth import password_manager
    
    password = "test_password_123"
    hashed = password_manager.hash_password(password)
    
    # Verify password was hashed
    assert hashed != password
    assert len(hashed) > len(password)
    
    # Verify password can be verified
    assert password_manager.verify_password(password, hashed)
    
    # Verify wrong password fails
    assert not password_manager.verify_password("wrong_password", hashed)


@pytest.mark.unit
def test_jwt_token_creation():
    """Test that JWT tokens can be created and verified."""
    from src.shared.auth import jwt_manager
    
    data = {"sub": "testuser", "role": "admin"}
    token = jwt_manager.create_access_token(data)
    
    # Verify token was created
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Verify token can be decoded
    payload = jwt_manager.verify_token(token, token_type="access")
    assert payload["sub"] == "testuser"
    assert payload["type"] == "access"


@pytest.mark.unit
def test_database_models():
    """Test that database models can be imported."""
    from src.services.user_management.models import User, Role, Permission
    
    # Verify models exist
    assert User is not None
    assert Role is not None
    assert Permission is not None

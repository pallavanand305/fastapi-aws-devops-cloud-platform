"""
Unit tests for user management service.

Tests cover:
- User CRUD operations
- Role-based access control
- User profile management
- Email verification
- Admin user management
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.shared.database_local import BaseModel
from src.shared.exceptions import NotFoundError, ConflictError, ValidationError, AuthenticationError
from src.services.user_management.models import User, Role, Permission
from src.services.user_management.service import UserService, RoleService, AuthService
from src.services.user_management.schemas import (
    UserCreate, UserUpdate, UserRegistration, UserPasswordUpdate,
    RoleCreate, PermissionCreate, LoginRequest
)
from src.services.user_management.email_service import EmailVerificationService, PasswordResetService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def async_db_engine():
    """Create async database engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def async_db_session(async_db_engine):
    """Create async database session for testing."""
    async_session = sessionmaker(
        async_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def test_permissions(async_db_session):
    """Create test permissions."""
    permissions = {
        "read_users": Permission(name="read_users", resource="users", action="read"),
        "write_users": Permission(name="write_users", resource="users", action="write"),
        "admin_all": Permission(name="admin_all", resource="*", action="*"),
    }
    
    for perm in permissions.values():
        async_db_session.add(perm)
    
    await async_db_session.commit()
    
    for perm in permissions.values():
        await async_db_session.refresh(perm)
    
    return permissions


@pytest.fixture
async def test_roles(async_db_session, test_permissions):
    """Create test roles."""
    roles = {
        "admin": Role(
            name="admin",
            description="Administrator",
            permissions=[test_permissions["admin_all"]]
        ),
        "regular_user": Role(
            name="regular_user",
            description="Regular user",
            permissions=[test_permissions["read_users"]]
        ),
    }
    
    for role in roles.values():
        async_db_session.add(role)
    
    await async_db_session.commit()
    
    for role in roles.values():
        await async_db_session.refresh(role)
    
    return roles


# ============================================================================
# User CRUD Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestUserCRUD:
    """Test user CRUD operations."""
    
    async def test_create_user(self, async_db_session, test_roles):
        """Test creating a new user."""
        user_service = UserService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            first_name="Test",
            last_name="User",
            role_ids=[str(test_roles["regular_user"].id)]
        )
        
        user = await user_service.create_user(user_data)
        
        # Refresh to load relationships
        await async_db_session.refresh(user, ["roles"])
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is True
        assert user.is_verified is False
        assert len(user.roles) == 1
        assert user.roles[0].name == "regular_user"
    
    async def test_create_duplicate_user(self, async_db_session, test_roles):
        """Test creating a user with duplicate username/email."""
        user_service = UserService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            role_ids=[]
        )
        
        # Create first user
        await user_service.create_user(user_data)
        
        # Try to create duplicate
        with pytest.raises(ConflictError):
            await user_service.create_user(user_data)
    
    async def test_get_user(self, async_db_session, test_roles):
        """Test getting a user by ID."""
        user_service = UserService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            role_ids=[]
        )
        
        created_user = await user_service.create_user(user_data)
        retrieved_user = await user_service.get_user(created_user.id)
        
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == created_user.username
    
    async def test_get_nonexistent_user(self, async_db_session):
        """Test getting a non-existent user."""
        user_service = UserService(async_db_session)
        
        with pytest.raises(NotFoundError):
            await user_service.get_user("nonexistent-id")
    
    async def test_update_user(self, async_db_session, test_roles):
        """Test updating a user."""
        user_service = UserService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            role_ids=[]
        )
        
        user = await user_service.create_user(user_data)
        
        update_data = UserUpdate(
            first_name="Updated",
            last_name="Name"
        )
        
        updated_user = await user_service.update_user(user.id, update_data)
        
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.username == "testuser"  # Unchanged
    
    async def test_update_user_roles(self, async_db_session, test_roles):
        """Test updating user roles."""
        user_service = UserService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            role_ids=[]
        )
        
        user = await user_service.create_user(user_data)
        assert len(user.roles) == 0
        
        update_data = UserUpdate(
            role_ids=[test_roles["admin"].id]
        )
        
        updated_user = await user_service.update_user(user.id, update_data)
        
        assert len(updated_user.roles) == 1
        assert updated_user.roles[0].name == "admin"
    
    async def test_delete_user(self, async_db_session, test_roles):
        """Test deleting a user (soft delete)."""
        user_service = UserService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            role_ids=[]
        )
        
        user = await user_service.create_user(user_data)
        result = await user_service.delete_user(user.id)
        
        assert result is True
        
        # User should not be retrievable after deletion
        with pytest.raises(NotFoundError):
            await user_service.get_user(user.id)
    
    async def test_list_users(self, async_db_session, test_roles):
        """Test listing users with pagination."""
        user_service = UserService(async_db_session)
        
        # Create multiple users
        for i in range(5):
            user_data = UserCreate(
                username=f"user{i}",
                email=f"user{i}@example.com",
                password="TestPassword123",
                role_ids=[]
            )
            await user_service.create_user(user_data)
        
        users, total = await user_service.list_users(skip=0, limit=10)
        
        assert len(users) == 5
        assert total == 5
    
    async def test_list_users_with_search(self, async_db_session, test_roles):
        """Test listing users with search."""
        user_service = UserService(async_db_session)
        
        # Create users
        user_data1 = UserCreate(
            username="alice",
            email="alice@example.com",
            password="TestPassword123",
            role_ids=[]
        )
        user_data2 = UserCreate(
            username="bob",
            email="bob@example.com",
            password="TestPassword123",
            role_ids=[]
        )
        
        await user_service.create_user(user_data1)
        await user_service.create_user(user_data2)
        
        users, total = await user_service.list_users(skip=0, limit=10, search="alice")
        
        assert len(users) == 1
        assert users[0].username == "alice"


# ============================================================================
# Password Management Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestPasswordManagement:
    """Test password management functionality."""
    
    async def test_update_password(self, async_db_session, test_roles):
        """Test updating user password."""
        user_service = UserService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="OldPassword123",
            role_ids=[]
        )
        
        user = await user_service.create_user(user_data)
        
        password_data = UserPasswordUpdate(
            current_password="OldPassword123",
            new_password="NewPassword456"
        )
        
        updated_user = await user_service.update_password(user.id, password_data)
        
        # Verify new password works
        auth_service = AuthService(async_db_session)
        assert auth_service.verify_password("NewPassword456", updated_user.password_hash)
    
    async def test_update_password_wrong_current(self, async_db_session, test_roles):
        """Test updating password with wrong current password."""
        user_service = UserService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="OldPassword123",
            role_ids=[]
        )
        
        user = await user_service.create_user(user_data)
        
        password_data = UserPasswordUpdate(
            current_password="WrongPassword",
            new_password="NewPassword456"
        )
        
        with pytest.raises(AuthenticationError):
            await user_service.update_password(user.id, password_data)


# ============================================================================
# Email Verification Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestEmailVerification:
    """Test email verification functionality."""
    
    async def test_register_user_with_verification(self, async_db_session):
        """Test user registration generates verification token."""
        user_service = UserService(async_db_session)
        
        registration_data = UserRegistration(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            confirm_password="TestPassword123",
            first_name="Test",
            last_name="User"
        )
        
        user, token = await user_service.register_user(registration_data)
        
        assert user.username == "testuser"
        assert user.is_verified is False
        assert token is not None
        assert len(token) > 0
    
    async def test_verify_email(self, async_db_session):
        """Test email verification with valid token."""
        user_service = UserService(async_db_session)
        
        registration_data = UserRegistration(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            confirm_password="TestPassword123"
        )
        
        user, token = await user_service.register_user(registration_data)
        assert user.is_verified is False
        
        verified_user = await user_service.verify_email(token)
        
        assert verified_user.id == user.id
        assert verified_user.is_verified is True
    
    async def test_verify_email_invalid_token(self, async_db_session):
        """Test email verification with invalid token."""
        user_service = UserService(async_db_session)
        
        with pytest.raises(ValidationError):
            await user_service.verify_email("invalid-token")
    
    async def test_verify_email_already_verified(self, async_db_session):
        """Test verifying already verified email."""
        user_service = UserService(async_db_session)
        
        registration_data = UserRegistration(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            confirm_password="TestPassword123"
        )
        
        user, token = await user_service.register_user(registration_data)
        
        # Verify once
        await user_service.verify_email(token)
        
        # Try to verify again with same token
        with pytest.raises(ValidationError):
            await user_service.verify_email(token)
    
    async def test_resend_verification_email(self, async_db_session):
        """Test resending verification email."""
        user_service = UserService(async_db_session)
        
        registration_data = UserRegistration(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            confirm_password="TestPassword123"
        )
        
        user, old_token = await user_service.register_user(registration_data)
        
        new_token = await user_service.resend_verification_email(user.id)
        
        assert new_token != old_token
        
        # Old token should not work
        with pytest.raises(ValidationError):
            await user_service.verify_email(old_token)
        
        # New token should work
        verified_user = await user_service.verify_email(new_token)
        assert verified_user.is_verified is True


# ============================================================================
# Password Reset Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestPasswordReset:
    """Test password reset functionality."""
    
    async def test_request_password_reset(self, async_db_session, test_roles):
        """Test requesting password reset."""
        user_service = UserService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="OldPassword123",
            role_ids=[]
        )
        
        user = await user_service.create_user(user_data)
        
        result = await user_service.request_password_reset(user.email)
        
        assert result is True
    
    async def test_request_password_reset_nonexistent_email(self, async_db_session):
        """Test requesting password reset for non-existent email."""
        user_service = UserService(async_db_session)
        
        # Should return True to prevent email enumeration
        result = await user_service.request_password_reset("nonexistent@example.com")
        
        assert result is True
    
    async def test_reset_password(self, async_db_session, test_roles):
        """Test resetting password with valid token."""
        user_service = UserService(async_db_session)
        auth_service = AuthService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="OldPassword123",
            role_ids=[]
        )
        
        user = await user_service.create_user(user_data)
        
        # Request password reset
        await user_service.request_password_reset(user.email)
        
        # Get the reset token (in production, this would be from email)
        reset_token = list(PasswordResetService._reset_tokens.keys())[0]
        
        # Reset password
        updated_user = await user_service.reset_password(reset_token, "NewPassword456")
        
        # Verify new password works
        assert auth_service.verify_password("NewPassword456", updated_user.password_hash)
        
        # Old password should not work
        assert not auth_service.verify_password("OldPassword123", updated_user.password_hash)
    
    async def test_reset_password_invalid_token(self, async_db_session):
        """Test resetting password with invalid token."""
        user_service = UserService(async_db_session)
        
        with pytest.raises(ValidationError):
            await user_service.reset_password("invalid-token", "NewPassword456")


# ============================================================================
# Role Management Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestRoleManagement:
    """Test role management functionality."""
    
    async def test_create_role(self, async_db_session, test_permissions):
        """Test creating a new role."""
        role_service = RoleService(async_db_session)
        
        role_data = RoleCreate(
            name="test_role",
            description="Test role",
            permission_ids=[test_permissions["read_users"].id]
        )
        
        role = await role_service.create_role(role_data)
        
        assert role.name == "test_role"
        assert role.description == "Test role"
        assert len(role.permissions) == 1
        assert role.permissions[0].name == "read_users"
    
    async def test_create_duplicate_role(self, async_db_session, test_roles):
        """Test creating a role with duplicate name."""
        role_service = RoleService(async_db_session)
        
        role_data = RoleCreate(
            name="admin",  # Already exists
            description="Duplicate admin",
            permission_ids=[]
        )
        
        with pytest.raises(ConflictError):
            await role_service.create_role(role_data)
    
    async def test_get_role(self, async_db_session, test_roles):
        """Test getting a role by ID."""
        role_service = RoleService(async_db_session)
        
        role = await role_service.get_role(test_roles["admin"].id)
        
        assert role.name == "admin"
        assert len(role.permissions) > 0
    
    async def test_list_roles(self, async_db_session, test_roles):
        """Test listing all roles."""
        role_service = RoleService(async_db_session)
        
        roles = await role_service.list_roles()
        
        assert len(roles) >= 2
        role_names = [role.name for role in roles]
        assert "admin" in role_names
        assert "regular_user" in role_names
    
    async def test_list_permissions(self, async_db_session, test_permissions):
        """Test listing all permissions."""
        role_service = RoleService(async_db_session)
        
        permissions = await role_service.list_permissions()
        
        assert len(permissions) >= 3
        perm_names = [perm.name for perm in permissions]
        assert "read_users" in perm_names
        assert "write_users" in perm_names
        assert "admin_all" in perm_names


# ============================================================================
# Authentication Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.unit
class TestAuthentication:
    """Test authentication functionality."""
    
    async def test_authenticate_user(self, async_db_session, test_roles):
        """Test user authentication with valid credentials."""
        user_service = UserService(async_db_session)
        auth_service = AuthService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            role_ids=[]
        )
        
        await user_service.create_user(user_data)
        
        login_data = LoginRequest(
            username="testuser",
            password="TestPassword123"
        )
        
        user = await auth_service.authenticate_user(login_data)
        
        assert user.username == "testuser"
    
    async def test_authenticate_user_invalid_password(self, async_db_session, test_roles):
        """Test authentication with invalid password."""
        user_service = UserService(async_db_session)
        auth_service = AuthService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            role_ids=[]
        )
        
        await user_service.create_user(user_data)
        
        login_data = LoginRequest(
            username="testuser",
            password="WrongPassword"
        )
        
        with pytest.raises(AuthenticationError):
            await auth_service.authenticate_user(login_data)
    
    async def test_login(self, async_db_session, test_roles):
        """Test login returns JWT tokens."""
        user_service = UserService(async_db_session)
        auth_service = AuthService(async_db_session)
        
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="TestPassword123",
            role_ids=[test_roles["admin"].id]
        )
        
        await user_service.create_user(user_data)
        
        login_data = LoginRequest(
            username="testuser",
            password="TestPassword123"
        )
        
        token_response = await auth_service.login(login_data)
        
        assert token_response.access_token is not None
        assert token_response.refresh_token is not None
        assert token_response.token_type == "bearer"
        assert token_response.expires_in > 0

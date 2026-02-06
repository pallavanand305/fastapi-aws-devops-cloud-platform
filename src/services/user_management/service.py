"""
User Management Service business logic layer.
"""
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.config_local import local_settings
from src.shared.exceptions import AuthenticationError, AuthorizationError, ValidationError, NotFoundError
from src.shared.logging import get_logger
from src.shared.auth import jwt_manager, password_manager, rate_limiter
from src.shared.session import session_manager
from .repository import UserRepository, RoleRepository, PermissionRepository
from .schemas import (
    UserCreate, UserUpdate, UserPasswordUpdate, TokenResponse,
    LoginRequest, UserRegistration, User, Role, Permission, RoleCreate
)
from .email_service import EmailVerificationService, PasswordResetService

logger = get_logger(__name__)


class AuthService:
    """Enhanced authentication service with JWT and session management."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return password_manager.verify_password(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return password_manager.hash_password(password)
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token."""
        return jwt_manager.create_access_token(data)
    
    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token."""
        return jwt_manager.create_refresh_token(data)
    
    def verify_token(self, token: str, token_type: str = "access") -> dict:
        """Verify and decode JWT token."""
        return jwt_manager.verify_token(token, token_type)
    
    async def authenticate_user(self, login_data: LoginRequest, client_ip: str = None) -> User:
        """Authenticate user with username/email and password."""
        # Check rate limiting
        identifier = client_ip or login_data.username
        if rate_limiter.is_rate_limited(identifier):
            logger.warning("Rate limit exceeded", identifier=identifier)
            raise AuthenticationError("Too many failed attempts. Please try again later.")
        
        user = await self.user_repo.get_by_username_or_email(login_data.username)
        
        if not user or not self.verify_password(login_data.password, user.password_hash):
            # Record failed attempt
            rate_limiter.record_attempt(identifier, failed=True)
            logger.warning("Authentication failed", username=login_data.username, client_ip=client_ip)
            raise AuthenticationError("Invalid credentials")
        
        if not user.is_active:
            rate_limiter.record_attempt(identifier, failed=True)
            raise AuthenticationError("Account is deactivated")
        
        # Record successful attempt (resets rate limiting)
        rate_limiter.record_attempt(identifier, failed=False)
        logger.info("User authenticated successfully", user_id=str(user.id), client_ip=client_ip)
        return user
    
    async def login(self, login_data: LoginRequest, client_ip: str = None) -> TokenResponse:
        """Login user and return JWT tokens with session management."""
        user = await self.authenticate_user(login_data, client_ip)
        
        # Create token payload
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "roles": [role.name for role in user.roles]
        }
        
        # Create session
        session_id = await session_manager.create_session(str(user.id), {
            "username": user.username,
            "email": user.email,
            "roles": [role.name for role in user.roles],
            "login_time": datetime.utcnow().isoformat(),
            "client_ip": client_ip
        })
        
        # Add session ID to token payload
        token_data["session_id"] = session_id
        
        # Generate JWT tokens
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)
        
        logger.info("User login successful", user_id=str(user.id), session_id=session_id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=local_settings.jwt_access_token_expire_minutes * 60,
            token_type="bearer"
        )
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token."""
        payload = self.verify_token(refresh_token, "refresh")
        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # Verify session exists
        if session_id:
            session_data = await session_manager.get_session(session_id)
            if not session_data:
                raise AuthenticationError("Session expired")
        
        # Verify user still exists and is active
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            # Clean up session if user is inactive
            if session_id:
                await session_manager.delete_session(session_id)
            raise AuthenticationError("User not found or inactive")
        
        # Create new token payload
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "roles": [role.name for role in user.roles],
            "session_id": session_id
        }
        
        # Generate new tokens
        access_token = self.create_access_token(token_data)
        new_refresh_token = self.create_refresh_token(token_data)
        
        logger.info("Token refreshed successfully", user_id=str(user.id), session_id=session_id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=local_settings.jwt_access_token_expire_minutes * 60,
            token_type="bearer"
        )
    
    async def logout(self, token: str) -> bool:
        """Logout user and invalidate session."""
        try:
            payload = self.verify_token(token)
            session_id = payload.get("session_id")
            
            if session_id:
                result = await session_manager.delete_session(session_id)
                logger.info("User logged out", user_id=payload.get("sub"), session_id=session_id)
                return result
            
            return True
        except Exception as e:
            logger.error("Logout error", error=str(e))
            return False
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from JWT token."""
        payload = self.verify_token(token)
        user_id = payload.get("sub")
        session_id = payload.get("session_id")
        
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # Verify session if present
        if session_id:
            session_data = await session_manager.get_session(session_id)
            if not session_data:
                raise AuthenticationError("Session expired")
        
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            # Clean up session if user doesn't exist
            if session_id:
                await session_manager.delete_session(session_id)
            raise AuthenticationError("User not found")
        
        return user


class UserService:
    """User management service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.auth_service = AuthService(db)
    
    async def register_user(self, registration_data: UserRegistration) -> tuple[User, str]:
        """
        Register a new user and send verification email.
        
        Returns:
            Tuple of (User, verification_token)
        """
        # Validate password confirmation
        if registration_data.password != registration_data.confirm_password:
            raise ValidationError("Passwords do not match")
        
        # Create user data
        user_data = UserCreate(
            username=registration_data.username,
            email=registration_data.email,
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            password=registration_data.password,
            role_ids=[]  # Default to no roles, admin assigns roles
        )
        
        # Hash password with bcrypt
        password_hash = password_manager.hash_password(registration_data.password)
        
        # Create user
        user = await self.user_repo.create(user_data, password_hash)
        logger.info("User registered successfully", user_id=str(user.id))
        
        # Generate and send verification email
        verification_token = EmailVerificationService.generate_verification_token(
            str(user.id), user.email
        )
        EmailVerificationService.send_verification_email(user.email, verification_token)
        
        return user, verification_token
    
    async def verify_email(self, token: str) -> User:
        """
        Verify user email with verification token.
        
        Args:
            token: Email verification token
            
        Returns:
            Verified user
            
        Raises:
            ValidationError: If token is invalid or expired
        """
        token_data = EmailVerificationService.verify_token(token)
        
        if not token_data:
            raise ValidationError("Invalid or expired verification token")
        
        user_id = token_data["user_id"]
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        if user.is_verified:
            logger.info("User already verified", user_id=str(user.id))
            return user
        
        # Mark user as verified
        user.is_verified = True
        await self.db.commit()
        await self.db.refresh(user)
        
        # Mark token as used
        EmailVerificationService.mark_token_used(token)
        
        logger.info("User email verified successfully", user_id=str(user.id))
        return user
    
    async def resend_verification_email(self, user_id: str) -> str:
        """
        Resend verification email to user.
        
        Args:
            user_id: User ID
            
        Returns:
            New verification token
            
        Raises:
            NotFoundError: If user not found
            ValidationError: If user already verified
        """
        user = await self.user_repo.get_by_id(user_id)
        
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        if user.is_verified:
            raise ValidationError("User email is already verified")
        
        token = EmailVerificationService.resend_verification_email(str(user.id), user.email)
        logger.info("Verification email resent", user_id=str(user.id))
        
        return token
    
    async def request_password_reset(self, email: str) -> bool:
        """
        Request password reset for user.
        
        Args:
            email: User email address
            
        Returns:
            True if reset email sent (always returns True for security)
        """
        user = await self.user_repo.get_by_email(email)
        
        # Always return True to prevent email enumeration
        if not user:
            logger.warning("Password reset requested for non-existent email", email=email)
            return True
        
        # Generate and send reset token
        reset_token = PasswordResetService.generate_reset_token(str(user.id), user.email)
        PasswordResetService.send_reset_email(user.email, reset_token)
        
        logger.info("Password reset requested", user_id=str(user.id))
        return True
    
    async def reset_password(self, token: str, new_password: str) -> User:
        """
        Reset user password with reset token.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            Updated user
            
        Raises:
            ValidationError: If token is invalid or expired
        """
        token_data = PasswordResetService.verify_reset_token(token)
        
        if not token_data:
            raise ValidationError("Invalid or expired reset token")
        
        user_id = token_data["user_id"]
        
        # Hash new password
        new_password_hash = password_manager.hash_password(new_password)
        
        # Update password
        user = await self.user_repo.update_password(user_id, new_password_hash)
        
        # Mark token as used
        PasswordResetService.mark_reset_token_used(token)
        
        logger.info("Password reset successfully", user_id=str(user.id))
        return user
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user (admin operation)."""
        password_hash = password_manager.hash_password(user_data.password)
        user = await self.user_repo.create(user_data, password_hash)
        logger.info("User created by admin", user_id=str(user.id))
        return user
    
    async def get_user(self, user_id: str) -> User:
        """Get user by ID."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        return user
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user."""
        return await self.user_repo.update(user_id, user_data)
    
    async def update_password(
        self,
        user_id: str,
        password_data: UserPasswordUpdate
    ) -> User:
        """Update user password."""
        user = await self.get_user(user_id)
        
        # Verify current password
        if not self.auth_service.verify_password(
            password_data.current_password,
            user.password_hash
        ):
            raise AuthenticationError("Current password is incorrect")
        
        # Hash new password with bcrypt
        new_password_hash = password_manager.hash_password(password_data.new_password)
        
        # Update password
        return await self.user_repo.update_password(user_id, new_password_hash)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete)."""
        result = await self.user_repo.delete(user_id)
        if result:
            logger.info("User deleted", user_id=str(user_id))
        return result
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None
    ) -> tuple[List[User], int]:
        """List users with pagination."""
        users = await self.user_repo.list_users(skip, limit, search)
        total = await self.user_repo.count_users(search)
        return users, total


class RoleService:
    """Role management service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.role_repo = RoleRepository(db)
        self.permission_repo = PermissionRepository(db)
    
    async def create_role(self, role_data: RoleCreate) -> Role:
        """Create a new role."""
        return await self.role_repo.create(role_data)
    
    async def get_role(self, role_id: str) -> Role:
        """Get role by ID."""
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with ID {role_id} not found")
        return role
    
    async def list_roles(self) -> List[Role]:
        """List all roles."""
        return await self.role_repo.list_roles()
    
    async def list_permissions(self) -> List[Permission]:
        """List all permissions."""
        return await self.permission_repo.list_permissions()
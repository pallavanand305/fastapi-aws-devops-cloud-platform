"""
User Management Service FastAPI routes.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.database_local import get_db
from src.shared.schemas import PaginatedResponse, PaginationParams
from src.shared.exceptions import (
    AuthenticationError, AuthorizationError, ValidationError,
    NotFoundError, ConflictError
)
from .dependencies import (
    get_auth_service, get_user_service, get_role_service,
    get_current_user, get_current_active_user, require_admin, security
)
from .service import AuthService, UserService, RoleService
from .schemas import (
    LoginRequest, TokenResponse, TokenRefreshRequest, UserRegistration,
    User, UserCreate, UserUpdate, UserPasswordUpdate, UserSummary,
    Role, RoleCreate, RoleUpdate, Permission, PermissionCreate,
    EmailVerificationRequest, ResendVerificationRequest,
    PasswordResetRequest, PasswordResetConfirm
)

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & User Management"])


# Authentication endpoints
@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Login user and return JWT tokens."""
    try:
        client_ip = request.client.host if request.client else None
        return await auth_service.login(login_data, client_ip)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token."""
    try:
        return await auth_service.refresh_token(refresh_data.refresh_token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_active_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user and invalidate session."""
    await auth_service.logout(credentials.credentials)


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    registration_data: UserRegistration,
    user_service: UserService = Depends(get_user_service)
):
    """Register a new user and send verification email."""
    try:
        user, verification_token = await user_service.register_user(registration_data)
        # Note: In production, don't return the token in response
        # The token is sent via email
        return user
    except (ValidationError, ConflictError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/verify-email", response_model=User)
async def verify_email(
    token: str = Query(..., description="Email verification token"),
    user_service: UserService = Depends(get_user_service)
):
    """Verify user email with verification token."""
    try:
        return await user_service.verify_email(token)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(
    request_data: ResendVerificationRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Resend verification email to user."""
    try:
        # Find user by email
        from .repository import UserRepository
        from src.shared.database_local import get_db
        
        # Get user by email
        db = await anext(get_db())
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(request_data.email)
        
        if not user:
            # Don't reveal if email exists for security
            return {"message": "If the email exists, a verification link has been sent"}
        
        await user_service.resend_verification_email(str(user.id))
        return {"message": "Verification email sent"}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(
    request_data: PasswordResetRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Request password reset for user."""
    await user_service.request_password_reset(request_data.email)
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password", response_model=User)
async def reset_password(
    reset_data: PasswordResetConfirm,
    user_service: UserService = Depends(get_user_service)
):
    """Reset user password with reset token."""
    try:
        # Validate passwords match
        if reset_data.new_password != reset_data.confirm_password:
            raise ValidationError("Passwords do not match")
        
        return await user_service.reset_password(reset_data.token, reset_data.new_password)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=User)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=User)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user profile."""
    try:
        # Users can only update their own profile (excluding roles)
        user_data.role_ids = None  # Prevent role escalation
        return await user_service.update_user(current_user.id, user_data)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/me/password", response_model=User)
async def update_current_user_password(
    password_data: UserPasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """Update current user password."""
    try:
        return await user_service.update_password(current_user.id, password_data)
    except (AuthenticationError, ValidationError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# User management endpoints (Admin only)
@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_admin)
):
    """Create a new user (Admin only)."""
    try:
        return await user_service.create_user(user_data)
    except (ValidationError, ConflictError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users", response_model=PaginatedResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search term"),
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_admin)
):
    """List users with pagination and search (Admin only)."""
    skip = (page - 1) * size
    users, total = await user_service.list_users(skip, size, search)
    
    # Convert to summary format for list view
    user_summaries = [
        UserSummary(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at
        )
        for user in users
    ]
    
    return PaginatedResponse.create(
        items=user_summaries,
        total=total,
        page=page,
        size=size
    )


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_admin)
):
    """Get user by ID (Admin only)."""
    try:
        return await user_service.get_user(user_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_admin)
):
    """Update user (Admin only)."""
    try:
        return await user_service.update_user(user_id, user_data)
    except (ValidationError, NotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_admin)
):
    """Delete user (Admin only)."""
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


# Role management endpoints (Admin only)
@router.post("/roles", response_model=Role, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    role_service: RoleService = Depends(get_role_service),
    current_user: User = Depends(require_admin)
):
    """Create a new role (Admin only)."""
    try:
        return await role_service.create_role(role_data)
    except (ValidationError, ConflictError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/roles", response_model=List[Role])
async def list_roles(
    role_service: RoleService = Depends(get_role_service),
    current_user: User = Depends(require_admin)
):
    """List all roles (Admin only)."""
    return await role_service.list_roles()


@router.get("/roles/{role_id}", response_model=Role)
async def get_role(
    role_id: str,
    role_service: RoleService = Depends(get_role_service),
    current_user: User = Depends(require_admin)
):
    """Get role by ID (Admin only)."""
    try:
        return await role_service.get_role(role_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/permissions", response_model=List[Permission])
async def list_permissions(
    role_service: RoleService = Depends(get_role_service),
    current_user: User = Depends(require_admin)
):
    """List all permissions (Admin only)."""
    return await role_service.list_permissions()
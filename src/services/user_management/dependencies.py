"""
User Management Service FastAPI dependencies.
"""
from typing import List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.database_local import get_db
from src.shared.exceptions import AuthenticationError, AuthorizationError
from .service import AuthService, UserService, RoleService
from .schemas import User

# Security scheme
security = HTTPBearer()


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get authentication service."""
    return AuthService(db)


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Get user service."""
    return UserService(db)


async def get_role_service(db: AsyncSession = Depends(get_db)) -> RoleService:
    """Get role service."""
    return RoleService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user."""
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_roles(required_roles: List[str]):
    """Dependency factory for role-based authorization."""
    
    async def check_roles(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Check if user has required roles."""
        user_roles = [role.name for role in current_user.roles]
        
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return check_roles


def require_permissions(required_permissions: List[str]):
    """Dependency factory for permission-based authorization."""
    
    async def check_permissions(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        """Check if user has required permissions."""
        user_permissions = []
        for role in current_user.roles:
            user_permissions.extend([perm.name for perm in role.permissions])
        
        if not any(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return check_permissions


# Common role dependencies
require_admin = require_roles(["admin"])
require_data_scientist = require_roles(["admin", "data_scientist"])
require_any_user = require_roles(["admin", "data_scientist", "regular_user"])
"""
User Management Service Pydantic schemas.
"""
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel, Field, EmailStr

from src.shared.schemas import BaseEntitySchema, UserRole


# Permission schemas
class PermissionBase(BaseModel):
    """Base permission schema."""
    name: str = Field(..., description="Permission name")
    resource: str = Field(..., description="Resource name")
    action: str = Field(..., description="Action name")
    description: Optional[str] = Field(None, description="Permission description")


class PermissionCreate(PermissionBase):
    """Permission creation schema."""
    pass


class Permission(BaseEntitySchema, PermissionBase):
    """Permission response schema."""
    pass


# Role schemas
class RoleBase(BaseModel):
    """Base role schema."""
    name: str = Field(..., description="Role name")
    description: Optional[str] = Field(None, description="Role description")


class RoleCreate(RoleBase):
    """Role creation schema."""
    permission_ids: List[str] = Field(default_factory=list, description="Permission IDs")


class RoleUpdate(BaseModel):
    """Role update schema."""
    name: Optional[str] = Field(None, description="Role name")
    description: Optional[str] = Field(None, description="Role description")
    permission_ids: Optional[List[str]] = Field(None, description="Permission IDs")


class Role(BaseEntitySchema, RoleBase):
    """Role response schema."""
    permissions: List[Permission] = Field(default_factory=list, description="Role permissions")


# User schemas
class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, description="Password")
    role_ids: List[str] = Field(default_factory=list, description="Role IDs")


class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username")
    email: Optional[EmailStr] = Field(None, description="Email address")
    first_name: Optional[str] = Field(None, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, max_length=100, description="Last name")
    role_ids: Optional[List[str]] = Field(None, description="Role IDs")


class UserPasswordUpdate(BaseModel):
    """User password update schema."""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class User(BaseEntitySchema, UserBase):
    """User response schema."""
    is_verified: bool = Field(..., description="Email verification status")
    roles: List[Role] = Field(default_factory=list, description="User roles")


class UserSummary(BaseModel):
    """User summary schema for lists."""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    is_active: bool = Field(..., description="Active status")
    is_verified: bool = Field(..., description="Email verification status")
    created_at: datetime = Field(..., description="Creation timestamp")


# Authentication schemas
class LoginRequest(BaseModel):
    """Login request schema."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")


class TokenRefreshRequest(BaseModel):
    """Token refresh request schema."""
    refresh_token: str = Field(..., description="Refresh token")


class UserRegistration(UserBase):
    """User registration schema."""
    password: str = Field(..., min_length=8, description="Password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    def validate_passwords_match(self) -> "UserRegistration":
        """Validate that passwords match."""
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class EmailVerificationRequest(BaseModel):
    """Email verification request schema."""
    token: str = Field(..., description="Email verification token")


class ResendVerificationRequest(BaseModel):
    """Resend verification email request schema."""
    email: EmailStr = Field(..., description="Email address")


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr = Field(..., description="Email address")


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    def validate_passwords_match(self) -> "PasswordResetConfirm":
        """Validate that passwords match."""
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

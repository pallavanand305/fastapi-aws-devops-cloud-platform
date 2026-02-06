"""
User Management Service database models.
"""
from sqlalchemy import Column, String, Boolean, Text, Table, ForeignKey
from sqlalchemy.orm import relationship

from src.shared.database_local import BaseModel


# Association table for user-role many-to-many relationship
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('role_id', String, ForeignKey('roles.id'), primary_key=True)
)

# Association table for role-permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    BaseModel.metadata,
    Column('role_id', String, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', String, ForeignKey('permissions.id'), primary_key=True)
)


class User(BaseModel):
    """User model."""
    
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")


class Role(BaseModel):
    """Role model."""
    
    __tablename__ = "roles"
    
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(BaseModel):
    """Permission model."""
    
    __tablename__ = "permissions"
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    resource = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text)
    
    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
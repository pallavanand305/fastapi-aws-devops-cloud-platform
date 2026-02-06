"""
User Management Service repository layer.
"""
from typing import List, Optional

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.shared.exceptions import NotFoundError, ConflictError
from .models import User, Role, Permission
from .schemas import UserCreate, UserUpdate, RoleCreate, RoleUpdate, PermissionCreate


class UserRepository:
    """Repository for user operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, user_data: UserCreate, password_hash: str) -> User:
        """Create a new user."""
        # Check if username or email already exists
        existing = await self.db.execute(
            select(User).where(
                or_(User.username == user_data.username, User.email == user_data.email)
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictError("Username or email already exists")
        
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
        )
        
        # Add roles if provided
        if user_data.role_ids:
            roles = await self.db.execute(
                select(Role).where(Role.id.in_([str(rid) for rid in user_data.role_ids]))
            )
            user.roles = roles.scalars().all()
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(and_(User.id == user_id, User.is_active == True))
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(and_(User.username == username, User.is_active == True))
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(and_(User.email == email, User.is_active == True))
        )
        return result.scalar_one_or_none()
    
    async def get_by_username_or_email(self, identifier: str) -> Optional[User]:
        """Get user by username or email."""
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(
                and_(
                    or_(User.username == identifier, User.email == identifier),
                    User.is_active == True
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def update(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user."""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "role_ids":
                if value is not None:
                    roles = await self.db.execute(
                        select(Role).where(Role.id.in_([str(rid) for rid in value]))
                    )
                    user.roles = roles.scalars().all()
            else:
                setattr(user, field, value)
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def update_password(self, user_id: str, password_hash: str) -> User:
        """Update user password."""
        user = await self.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        
        user.password_hash = password_hash
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete(self, user_id: str) -> bool:
        """Soft delete user."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        await self.db.commit()
        return True
    
    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        search: Optional[str] = None
    ) -> List[User]:
        """List users with pagination and search."""
        query = select(User).where(User.is_active == True)
        
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def count_users(self, search: Optional[str] = None) -> int:
        """Count users with optional search."""
        query = select(User).where(User.is_active == True)
        
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%")
            )
            query = query.where(search_filter)
        
        result = await self.db.execute(query)
        return len(result.scalars().all())


class RoleRepository:
    """Repository for role operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, role_data: RoleCreate) -> Role:
        """Create a new role."""
        # Check if role name already exists
        existing = await self.db.execute(
            select(Role).where(Role.name == role_data.name)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Role '{role_data.name}' already exists")
        
        # Create role
        role = Role(
            name=role_data.name,
            description=role_data.description,
        )
        
        # Add permissions if provided
        if role_data.permission_ids:
            permissions = await self.db.execute(
                select(Permission).where(Permission.id.in_([str(pid) for pid in role_data.permission_ids]))
            )
            role.permissions = permissions.scalars().all()
        
        self.db.add(role)
        await self.db.commit()
        await self.db.refresh(role)
        return role
    
    async def get_by_id(self, role_id: str) -> Optional[Role]:
        """Get role by ID."""
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(and_(Role.id == role_id, Role.is_active == True))
        )
        return result.scalar_one_or_none()
    
    async def get_by_name(self, name: str) -> Optional[Role]:
        """Get role by name."""
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(and_(Role.name == name, Role.is_active == True))
        )
        return result.scalar_one_or_none()
    
    async def list_roles(self) -> List[Role]:
        """List all active roles."""
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.is_active == True)
        )
        return result.scalars().all()


class PermissionRepository:
    """Repository for permission operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, permission_data: PermissionCreate) -> Permission:
        """Create a new permission."""
        # Check if permission name already exists
        existing = await self.db.execute(
            select(Permission).where(Permission.name == permission_data.name)
        )
        if existing.scalar_one_or_none():
            raise ConflictError(f"Permission '{permission_data.name}' already exists")
        
        permission = Permission(**permission_data.model_dump())
        self.db.add(permission)
        await self.db.commit()
        await self.db.refresh(permission)
        return permission
    
    async def list_permissions(self) -> List[Permission]:
        """List all active permissions."""
        result = await self.db.execute(
            select(Permission).where(Permission.is_active == True)
        )
        return result.scalars().all()
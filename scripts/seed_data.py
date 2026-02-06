#!/usr/bin/env python3
"""
Seed the database with sample data for testing.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.shared.database_local import AsyncSessionLocal
from src.services.user_management.models import User, Role, Permission
from src.services.user_management.service import AuthService
from src.shared.logging import configure_logging, get_logger

configure_logging(debug=True)
logger = get_logger(__name__)


async def create_permissions():
    """Create default permissions."""
    permissions_data = [
        {"name": "user.create", "resource": "user", "action": "create", "description": "Create users"},
        {"name": "user.read", "resource": "user", "action": "read", "description": "Read user data"},
        {"name": "user.update", "resource": "user", "action": "update", "description": "Update users"},
        {"name": "user.delete", "resource": "user", "action": "delete", "description": "Delete users"},
        {"name": "project.create", "resource": "project", "action": "create", "description": "Create projects"},
        {"name": "project.read", "resource": "project", "action": "read", "description": "Read project data"},
        {"name": "workflow.create", "resource": "workflow", "action": "create", "description": "Create workflows"},
        {"name": "workflow.execute", "resource": "workflow", "action": "execute", "description": "Execute workflows"},
        {"name": "model.create", "resource": "model", "action": "create", "description": "Create models"},
        {"name": "model.deploy", "resource": "model", "action": "deploy", "description": "Deploy models"},
    ]
    
    async with AsyncSessionLocal() as session:
        for perm_data in permissions_data:
            permission = Permission(**perm_data)
            session.add(permission)
        
        await session.commit()
        logger.info("Default permissions created")


async def create_roles():
    """Create default roles with permissions."""
    async with AsyncSessionLocal() as session:
        # Get all permissions
        from sqlalchemy import select
        permissions_result = await session.execute(select(Permission))
        all_permissions = permissions_result.scalars().all()
        
        # Create Admin role with all permissions
        admin_role = Role(
            name="admin",
            description="Administrator with full system access"
        )
        admin_role.permissions = all_permissions
        session.add(admin_role)
        
        # Create Data Scientist role
        data_scientist_role = Role(
            name="data_scientist",
            description="Data scientist with ML workflow and model management access"
        )
        ds_permissions = [p for p in all_permissions if p.name in [
            "project.create", "project.read", "workflow.create", "workflow.execute",
            "model.create", "model.deploy"
        ]]
        data_scientist_role.permissions = ds_permissions
        session.add(data_scientist_role)
        
        # Create Regular User role
        regular_user_role = Role(
            name="regular_user",
            description="Regular user with basic access"
        )
        user_permissions = [p for p in all_permissions if p.name in [
            "project.read", "workflow.read", "model.read"
        ]]
        regular_user_role.permissions = user_permissions
        session.add(regular_user_role)
        
        await session.commit()
        logger.info("Default roles created")


async def create_users():
    """Create sample users."""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        
        # Get roles
        admin_role = await session.execute(select(Role).where(Role.name == "admin"))
        admin_role = admin_role.scalar_one()
        
        ds_role = await session.execute(select(Role).where(Role.name == "data_scientist"))
        ds_role = ds_role.scalar_one()
        
        # Create admin user
        auth_service = AuthService(session)
        admin_user = User(
            username="admin",
            email="admin@mlplatform.com",
            password_hash=auth_service.get_password_hash("admin123"),
            first_name="System",
            last_name="Administrator",
            is_verified=True
        )
        admin_user.roles = [admin_role]
        session.add(admin_user)
        
        # Create data scientist user
        ds_user = User(
            username="scientist",
            email="scientist@mlplatform.com",
            password_hash=auth_service.get_password_hash("scientist123"),
            first_name="Data",
            last_name="Scientist",
            is_verified=True
        )
        ds_user.roles = [ds_role]
        session.add(ds_user)
        
        await session.commit()
        logger.info("Sample users created")
        logger.info("Admin user: username=admin, password=admin123")
        logger.info("Data Scientist user: username=scientist, password=scientist123")


async def main():
    """Main seeding function."""
    logger.info("Seeding database with sample data...")
    
    try:
        await create_permissions()
        await create_roles()
        await create_users()
        
        logger.info("Database seeding completed successfully!")
        logger.info("You can now test the API with these users:")
        logger.info("  Admin: username=admin, password=admin123")
        logger.info("  Data Scientist: username=scientist, password=scientist123")
        
    except Exception as e:
        logger.error("Database seeding failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
"""
Setup script for ML Workflow Platform development environment.
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.shared.database import init_db, AsyncSessionLocal
from src.services.user_management.models import User, Role, Permission
from src.services.user_management.service import AuthService
from src.shared.logging import configure_logging, get_logger

configure_logging(debug=True)
logger = get_logger(__name__)


async def create_default_permissions():
    """Create default permissions."""
    permissions_data = [
        # User management permissions
        {"name": "user.create", "resource": "user", "action": "create", "description": "Create users"},
        {"name": "user.read", "resource": "user", "action": "read", "description": "Read user data"},
        {"name": "user.update", "resource": "user", "action": "update", "description": "Update users"},
        {"name": "user.delete", "resource": "user", "action": "delete", "description": "Delete users"},
        
        # Project management permissions
        {"name": "project.create", "resource": "project", "action": "create", "description": "Create projects"},
        {"name": "project.read", "resource": "project", "action": "read", "description": "Read project data"},
        {"name": "project.update", "resource": "project", "action": "update", "description": "Update projects"},
        {"name": "project.delete", "resource": "project", "action": "delete", "description": "Delete projects"},
        
        # Workflow management permissions
        {"name": "workflow.create", "resource": "workflow", "action": "create", "description": "Create workflows"},
        {"name": "workflow.read", "resource": "workflow", "action": "read", "description": "Read workflow data"},
        {"name": "workflow.update", "resource": "workflow", "action": "update", "description": "Update workflows"},
        {"name": "workflow.delete", "resource": "workflow", "action": "delete", "description": "Delete workflows"},
        {"name": "workflow.execute", "resource": "workflow", "action": "execute", "description": "Execute workflows"},
        
        # Model management permissions
        {"name": "model.create", "resource": "model", "action": "create", "description": "Create models"},
        {"name": "model.read", "resource": "model", "action": "read", "description": "Read model data"},
        {"name": "model.update", "resource": "model", "action": "update", "description": "Update models"},
        {"name": "model.delete", "resource": "model", "action": "delete", "description": "Delete models"},
        {"name": "model.deploy", "resource": "model", "action": "deploy", "description": "Deploy models"},
        
        # Data management permissions
        {"name": "data.create", "resource": "data", "action": "create", "description": "Create data"},
        {"name": "data.read", "resource": "data", "action": "read", "description": "Read data"},
        {"name": "data.update", "resource": "data", "action": "update", "description": "Update data"},
        {"name": "data.delete", "resource": "data", "action": "delete", "description": "Delete data"},
    ]
    
    async with AsyncSessionLocal() as session:
        for perm_data in permissions_data:
            # Check if permission already exists
            existing = await session.execute(
                f"SELECT id FROM permissions WHERE name = '{perm_data['name']}'"
            )
            if not existing.scalar_one_or_none():
                permission = Permission(**perm_data)
                session.add(permission)
        
        await session.commit()
        logger.info("Default permissions created")


async def create_default_roles():
    """Create default roles with permissions."""
    async with AsyncSessionLocal() as session:
        # Get all permissions
        permissions_result = await session.execute("SELECT * FROM permissions")
        all_permissions = permissions_result.fetchall()
        
        # Create Admin role with all permissions
        admin_role = Role(
            name="admin",
            description="Administrator with full system access"
        )
        session.add(admin_role)
        await session.flush()
        
        # Add all permissions to admin role
        for perm in all_permissions:
            await session.execute(
                f"INSERT INTO role_permissions (role_id, permission_id) VALUES ('{admin_role.id}', '{perm.id}')"
            )
        
        # Create Data Scientist role
        data_scientist_role = Role(
            name="data_scientist",
            description="Data scientist with ML workflow and model management access"
        )
        session.add(data_scientist_role)
        await session.flush()
        
        # Add specific permissions to data scientist role
        ds_permissions = [
            "project.create", "project.read", "project.update",
            "workflow.create", "workflow.read", "workflow.update", "workflow.execute",
            "model.create", "model.read", "model.update", "model.deploy",
            "data.create", "data.read", "data.update"
        ]
        
        for perm_name in ds_permissions:
            perm = next((p for p in all_permissions if p.name == perm_name), None)
            if perm:
                await session.execute(
                    f"INSERT INTO role_permissions (role_id, permission_id) VALUES ('{data_scientist_role.id}', '{perm.id}')"
                )
        
        # Create Regular User role
        regular_user_role = Role(
            name="regular_user",
            description="Regular user with basic access"
        )
        session.add(regular_user_role)
        await session.flush()
        
        # Add basic permissions to regular user role
        user_permissions = ["project.read", "workflow.read", "model.read", "data.read"]
        
        for perm_name in user_permissions:
            perm = next((p for p in all_permissions if p.name == perm_name), None)
            if perm:
                await session.execute(
                    f"INSERT INTO role_permissions (role_id, permission_id) VALUES ('{regular_user_role.id}', '{perm.id}')"
                )
        
        await session.commit()
        logger.info("Default roles created")


async def create_admin_user():
    """Create default admin user."""
    async with AsyncSessionLocal() as session:
        # Check if admin user already exists
        existing = await session.execute(
            "SELECT id FROM users WHERE username = 'admin'"
        )
        if existing.scalar_one_or_none():
            logger.info("Admin user already exists")
            return
        
        # Get admin role
        admin_role_result = await session.execute(
            "SELECT id FROM roles WHERE name = 'admin'"
        )
        admin_role_id = admin_role_result.scalar_one()
        
        # Create admin user
        auth_service = AuthService(session)
        password_hash = auth_service.get_password_hash("admin123")
        
        admin_user = User(
            username="admin",
            email="admin@mlplatform.com",
            password_hash=password_hash,
            first_name="System",
            last_name="Administrator",
            is_verified=True
        )
        session.add(admin_user)
        await session.flush()
        
        # Assign admin role
        await session.execute(
            f"INSERT INTO user_roles (user_id, role_id) VALUES ('{admin_user.id}', '{admin_role_id}')"
        )
        
        await session.commit()
        logger.info("Admin user created (username: admin, password: admin123)")


async def main():
    """Main setup function."""
    logger.info("Setting up ML Workflow Platform...")
    
    try:
        # Initialize database
        await init_db()
        logger.info("Database initialized")
        
        # Create default data
        await create_default_permissions()
        await create_default_roles()
        await create_admin_user()
        
        logger.info("Setup completed successfully!")
        logger.info("You can now login with:")
        logger.info("  Username: admin")
        logger.info("  Password: admin123")
        
    except Exception as e:
        logger.error("Setup failed", error=str(e))
        raise


if __name__ == "__main__":
    asyncio.run(main())
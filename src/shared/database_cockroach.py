"""
CockroachDB database configuration.
"""
import uuid
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, DateTime, String, Boolean
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID

from .config_cockroach import cockroach_settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class BaseModel(Base):
    """Base model with common fields for all entities."""
    
    __abstract__ = True
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)


# Create async engine for CockroachDB
engine = create_async_engine(
    cockroach_settings.database.url.replace("postgresql://", "postgresql+asyncpg://"),
    echo=cockroach_settings.debug,
    pool_size=20,
    max_overflow=0,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_connection() -> bool:
    """
    Check database connection health.
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
            await session.commit()
            return True
    except Exception:
        return False
"""
Shared Pydantic schemas and models.
"""
from typing import Optional, Any, Dict
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        validate_assignment=True
    )


class TimestampMixin(BaseModel):
    """Mixin for timestamp fields."""
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class BaseEntitySchema(BaseSchema, TimestampMixin):
    """Base schema for entities with ID and timestamps."""
    
    id: str = Field(..., description="Unique identifier")
    is_active: bool = Field(default=True, description="Active status")


# Enums
class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    DATA_SCIENTIST = "data_scientist"
    REGULAR_USER = "regular_user"


class ProjectStatus(str, Enum):
    """Project status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class WorkflowStatus(str, Enum):
    """Workflow status values."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class JobStatus(str, Enum):
    """Job execution status values."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelStatus(str, Enum):
    """Model status values."""
    TRAINING = "training"
    READY = "ready"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"


class ApprovalStatus(str, Enum):
    """Model approval status values."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


# Response schemas
class HealthCheckResponse(BaseSchema):
    """Health check response schema."""
    
    status: str = Field(..., description="Service status")
    timestamp: float = Field(..., description="Check timestamp")
    version: str = Field(..., description="Service version")
    database: bool = Field(..., description="Database connection status")
    redis: bool = Field(..., description="Redis connection status")


class ErrorResponse(BaseSchema):
    """Error response schema."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class PaginationParams(BaseSchema):
    """Pagination parameters schema."""
    
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")


class PaginatedResponse(BaseSchema):
    """Paginated response schema."""
    
    items: list = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")
    
    @classmethod
    def create(
        cls,
        items: list,
        total: int,
        page: int,
        size: int
    ) -> "PaginatedResponse":
        """Create paginated response."""
        pages = (total + size - 1) // size
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )
"""
Shared exception classes and error handling utilities.
"""
from typing import Optional, Dict, Any


class MLPlatformException(Exception):
    """Base exception for ML Platform."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(MLPlatformException):
    """Raised when validation fails."""
    pass


class AuthenticationError(MLPlatformException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(MLPlatformException):
    """Raised when authorization fails."""
    pass


class NotFoundError(MLPlatformException):
    """Raised when a resource is not found."""
    pass


class ConflictError(MLPlatformException):
    """Raised when there's a resource conflict."""
    pass


class ExternalServiceError(MLPlatformException):
    """Raised when external service call fails."""
    pass


class DatabaseError(MLPlatformException):
    """Raised when database operation fails."""
    pass


class WorkflowError(MLPlatformException):
    """Raised when workflow operation fails."""
    pass


class ModelError(MLPlatformException):
    """Raised when model operation fails."""
    pass


class DataPipelineError(MLPlatformException):
    """Raised when data pipeline operation fails."""
    pass
"""
FastAPI middleware for authentication, authorization, and audit logging.
"""
import time
from typing import Callable, Optional, List
from datetime import datetime

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging import get_logger, set_correlation_id, get_correlation_id
from .auth import jwt_manager, rate_limiter
from .exceptions import AuthenticationError, AuthorizationError
from .schemas import ErrorResponse

logger = get_logger(__name__)


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT authentication and rate limiting.
    Validates JWT tokens and enforces rate limits on authentication endpoints.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with authentication checks."""
        # Skip authentication for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Check rate limiting for auth endpoints
        if "/auth/" in request.url.path:
            client_ip = request.client.host if request.client else "unknown"
            if rate_limiter.is_rate_limited(client_ip):
                logger.warning("Rate limit exceeded", client_ip=client_ip, path=request.url.path)
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=ErrorResponse(
                        error="RATE_LIMIT_EXCEEDED",
                        message="Too many authentication attempts. Please try again later."
                    ).model_dump()
                )
        
        # Extract and validate JWT token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorResponse(
                    error="AUTHENTICATION_REQUIRED",
                    message="Authentication credentials required"
                ).model_dump(),
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        token = auth_header.split(" ")[1]
        
        try:
            # Verify token
            payload = jwt_manager.verify_token(token, token_type="access")
            
            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_email = payload.get("email")
            request.state.user_roles = payload.get("roles", [])
            
            logger.debug("Request authenticated", user_id=request.state.user_id)
            
        except Exception as e:
            logger.warning("Authentication failed", error=str(e))
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=ErrorResponse(
                    error="AUTHENTICATION_FAILED",
                    message="Invalid or expired authentication token"
                ).model_dump(),
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        response = await call_next(request)
        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for audit logging of all requests and responses.
    Logs authentication events, authorization decisions, and data access.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        log_request_body: bool = False,
        log_response_body: bool = False
    ):
        super().__init__(app)
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with audit logging."""
        start_time = time.time()
        
        # Extract request information
        correlation_id = get_correlation_id()
        user_id = getattr(request.state, "user_id", None)
        client_ip = request.client.host if request.client else "unknown"
        
        # Log request
        audit_data = {
            "event_type": "http_request",
            "correlation_id": correlation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "user_agent": request.headers.get("user-agent"),
        }
        
        # Optionally log request body (be careful with sensitive data)
        if self.log_request_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                # Don't log passwords or sensitive fields
                audit_data["request_body_size"] = len(body)
            except Exception:
                pass
        
        logger.info("Audit: Request received", **audit_data)
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response
        audit_data.update({
            "event_type": "http_response",
            "status_code": response.status_code,
            "process_time_seconds": round(process_time, 4)
        })
        
        # Log at appropriate level based on status code
        if response.status_code >= 500:
            logger.error("Audit: Request failed", **audit_data)
        elif response.status_code >= 400:
            logger.warning("Audit: Request error", **audit_data)
        else:
            logger.info("Audit: Request completed", **audit_data)
        
        # Add audit headers to response
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


class CORSConfigMiddleware:
    """
    Enhanced CORS configuration for production use.
    Provides more granular control than FastAPI's built-in CORS middleware.
    """
    
    @staticmethod
    def get_cors_config(environment: str = "development"):
        """Get CORS configuration based on environment."""
        if environment == "production":
            return {
                "allow_origins": [
                    "https://app.mlplatform.com",
                    "https://admin.mlplatform.com"
                ],
                "allow_credentials": True,
                "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                "allow_headers": [
                    "Authorization",
                    "Content-Type",
                    "X-Correlation-ID",
                    "X-Request-ID"
                ],
                "expose_headers": [
                    "X-Correlation-ID",
                    "X-Process-Time"
                ],
                "max_age": 3600
            }
        else:
            # Development/staging - more permissive
            return {
                "allow_origins": ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
                "expose_headers": ["*"],
                "max_age": 600
            }

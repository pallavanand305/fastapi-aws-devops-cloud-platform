"""
Main FastAPI application entry point.
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.shared.database import init_db, check_db_connection
from src.shared.logging import configure_logging, get_logger, set_correlation_id
from src.shared.schemas import HealthCheckResponse, ErrorResponse
from src.shared.exceptions import MLPlatformException
from src.shared.middleware import AuditLoggingMiddleware

# Configure logging
configure_logging(debug=True)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ML Workflow Platform", version="0.1.0")
    
    # Initialize database
    try:
        await init_db()
        logger.info("CockroachDB database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    # Check database connection
    if not await check_db_connection():
        logger.error("Database connection check failed")
        raise RuntimeError("Database connection failed")
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title="ML Workflow Platform",
    description="Enterprise ML Workflow Orchestration Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add audit logging middleware
app.add_middleware(AuditLoggingMiddleware, log_request_body=False, log_response_body=False)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to requests."""
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        import uuid
        correlation_id = str(uuid.uuid4())
    
    set_correlation_id(correlation_id)
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log requests and responses."""
    start_time = asyncio.get_event_loop().time()
    
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    process_time = asyncio.get_event_loop().time() - start_time
    
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response


# Exception handlers
@app.exception_handler(MLPlatformException)
async def platform_exception_handler(request: Request, exc: MLPlatformException):
    """Handle platform-specific exceptions."""
    logger.error(
        "Platform exception occurred",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details
    )
    
    status_code = status.HTTP_400_BAD_REQUEST
    if "Authentication" in exc.error_code:
        status_code = status.HTTP_401_UNAUTHORIZED
    elif "Authorization" in exc.error_code:
        status_code = status.HTTP_403_FORBIDDEN
    elif "NotFound" in exc.error_code:
        status_code = status.HTTP_404_NOT_FOUND
    elif "Conflict" in exc.error_code:
        status_code = status.HTTP_409_CONFLICT
    elif "ExternalService" in exc.error_code:
        status_code = status.HTTP_502_BAD_GATEWAY
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=exc.error_code,
            message=exc.message,
            details=exc.details
        ).model_dump()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.error("Request validation failed", errors=exc.errors())
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": exc.errors()}
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors."""
    logger.error("Unexpected error occurred", error=str(exc), exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred"
        ).model_dump()
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    db_status = await check_db_connection()
    
    return HealthCheckResponse(
        status="healthy" if db_status else "unhealthy",
        timestamp=asyncio.get_event_loop().time(),
        version="0.1.0",
        database=db_status,
        redis=True  # TODO: Add Redis health check
    )


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "🚀 ML Workflow Orchestration Platform",
        "version": "0.1.0",
        "database": "CockroachDB",
        "docs": "/docs",
        "health": "/health",
        "features": [
            "✅ FastAPI with async support",
            "✅ CockroachDB database",
            "✅ Enterprise-level architecture",
            "✅ Structured logging",
            "✅ Error handling",
            "✅ API documentation"
        ]
    }


# Demo endpoint
@app.get("/demo")
async def demo():
    """Demo endpoint to test the API."""
    return {
        "message": "🎉 FastAPI + CockroachDB is working!",
        "database_url": "cockroachdb://root@localhost:26257/fastapi_platform",
        "next_steps": [
            "✅ Database connection established",
            "✅ FastAPI server running",
            "✅ View API docs at: /docs",
            "✅ Check health at: /health",
            "🔄 Ready for user management implementation"
        ]
    }
"""
Local development FastAPI application (without external dependencies).
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.shared.config_local import local_settings
from src.shared.database_local import init_db, check_db_connection
from src.shared.logging import configure_logging, get_logger, set_correlation_id
from src.shared.schemas import HealthCheckResponse, ErrorResponse
from src.shared.exceptions import MLPlatformException
from src.services.user_management.routes import router as auth_router

# Configure logging
configure_logging(local_settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting ML Workflow Platform (Local Development)", version=local_settings.version)
    
    # Initialize database
    try:
        await init_db()
        logger.info("SQLite database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    # Check database connection
    db_healthy = await check_db_connection()
    if db_healthy:
        logger.info("Database connection verified")
    else:
        logger.warning("Database connection check failed, but continuing startup")
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown completed")


# Create FastAPI application
app = FastAPI(
    title=local_settings.app_name,
    description="Enterprise ML Workflow Orchestration Platform (Local Development)",
    version=local_settings.version,
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
    """Handle unexpected exceptions."""
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
        version=local_settings.version,
        database=db_status,
        redis=False  # Redis not available in local mode
    )


# Include routers
app.include_router(auth_router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "ML Workflow Orchestration Platform (Local Development)",
        "version": local_settings.version,
        "docs": "/docs",
        "health": "/health",
        "note": "This is a local development version. External services (PostgreSQL, Redis) are mocked."
    }


# Demo endpoint to show the API is working
@app.get("/demo")
async def demo():
    """Demo endpoint to test the API."""
    return {
        "message": "🎉 FastAPI is working!",
        "features": [
            "✅ FastAPI framework",
            "✅ Async/await support", 
            "✅ SQLite database",
            "✅ Structured logging",
            "✅ Error handling",
            "✅ CORS middleware",
            "✅ Request correlation",
            "✅ Health checks"
        ],
        "next_steps": [
            "Install Docker to use full PostgreSQL + Redis setup",
            "Run tests with: pytest",
            "View API docs at: /docs",
            "Check health at: /health"
        ]
    }
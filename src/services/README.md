# Microservices Directory

This directory contains all microservices that make up the ML Workflow Orchestration Platform. Each service is designed following Domain-Driven Design (DDD) and Clean Architecture principles.

## Service Structure

Each microservice follows a consistent structure:

```
service_name/
├── __init__.py          # Service package initialization
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic request/response schemas
├── repository.py        # Data access layer (database operations)
├── service.py           # Business logic layer
├── routes.py            # FastAPI route handlers
├── dependencies.py      # FastAPI dependency injection
└── README.md            # Service-specific documentation
```

## Available Services

### 1. User Management Service
**Status:** ✅ Implemented  
**Purpose:** Handles authentication, authorization, user management, and RBAC  
**Key Features:**
- JWT-based authentication
- Role-based access control
- User profile management
- Password security with bcrypt
- Session management with Redis

### 2. API Gateway Service
**Status:** 🚧 Planned  
**Purpose:** Request routing, load balancing, and circuit breaker patterns  
**Key Features:**
- Request routing to microservices
- Circuit breaker implementation
- Rate limiting and security
- API documentation aggregation
- Service discovery

### 3. Workflow Engine Service
**Status:** 🚧 Planned  
**Purpose:** ML workflow orchestration and job scheduling  
**Key Features:**
- Workflow definition and validation
- Job scheduling with Celery
- Task execution orchestration
- Workflow state management
- Dependency resolution

### 4. Model Registry Service
**Status:** 🚧 Planned  
**Purpose:** ML model lifecycle management and versioning  
**Key Features:**
- Model version management
- Model metadata storage
- SageMaker integration
- Model approval workflows
- Model lineage tracking

### 5. Data Pipeline Service
**Status:** 🚧 Planned  
**Purpose:** ETL operations and data quality management  
**Key Features:**
- Pipeline definition and execution
- Data validation and quality checks
- Data lineage tracking
- S3 integration for data storage
- Pipeline monitoring and alerting

### 6. Prediction Service
**Status:** 🚧 Planned  
**Purpose:** Model inference and prediction serving  
**Key Features:**
- Real-time predictions
- Batch prediction processing
- A/B testing and traffic routing
- Prediction caching with Redis
- Model loading and management

### 7. Monitoring Service
**Status:** 🚧 Planned  
**Purpose:** System monitoring and observability  
**Key Features:**
- Metrics collection with Prometheus
- Distributed tracing
- Log aggregation
- Alerting and notifications
- Health monitoring dashboards

## Service Communication

Services communicate through:
- **Synchronous:** REST APIs for request-response patterns
- **Asynchronous:** Redis Streams for event-driven workflows
- **Service Mesh:** Istio for traffic management (production)

## Development Guidelines

### Adding a New Service

1. Create service directory: `src/services/service_name/`
2. Add `__init__.py` with service description
3. Implement models, schemas, repository, service, and routes
4. Add service-specific tests in `tests/services/service_name/`
5. Update docker-compose.yml if needed
6. Document API endpoints in service README

### Service Dependencies

- All services depend on `src/shared/` for common utilities
- Services should be loosely coupled
- Use dependency injection for testability
- Follow the repository pattern for data access

### Testing

Each service should have:
- Unit tests for business logic
- Property-based tests for correctness
- Integration tests for API endpoints
- Mock external dependencies

## Configuration

Service configuration is managed through:
- Environment variables (`.env` file)
- `src/shared/config.py` for shared configuration
- Service-specific config files when needed

## Database Schema

Each service has its own database schema:
- `user_management` - User, Role, Permission tables
- `workflow_engine` - Workflow, Job, Task tables
- `model_registry` - Model, ModelVersion, Artifact tables
- `data_pipeline` - Pipeline, Dataset, DataQuality tables

Migrations are managed with Alembic in the `alembic/` directory.

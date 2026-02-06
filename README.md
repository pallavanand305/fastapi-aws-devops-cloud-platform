# ML Workflow Orchestration Platform

A production-ready, cloud-native ML workflow orchestration platform built with FastAPI, demonstrating enterprise-level capabilities across Python Backend Engineering, AWS DevOps, and MLOps domains.

## 🏗️ Architecture

This platform showcases a modern microservices architecture with:

- **FastAPI** - High-performance async web framework
- **PostgreSQL** - Robust relational database with SQLAlchemy ORM
- **Redis** - High-performance caching and session storage
- **Docker** - Containerized development and deployment
- **JWT Authentication** - Secure token-based authentication
- **Role-Based Access Control** - Enterprise-grade authorization
- **Structured Logging** - Comprehensive observability
- **Property-Based Testing** - Advanced testing methodology

📖 **For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md)**

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Git
- Poetry (recommended) or pip

### Automated Setup (Recommended)

Run the automated setup script to configure your development environment:

```bash
# Run the setup script
python scripts/setup_dev_env.py
```

This script will:
- ✅ Verify Python version
- ✅ Check Poetry installation
- ✅ Install all dependencies
- ✅ Configure pre-commit hooks
- ✅ Create .env file from template
- ✅ Verify Docker is running

### Manual Setup

If you prefer manual setup or the automated script fails:

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ml-workflow-platform
```

### 2. Start with Docker (Recommended)

**Windows:**
```cmd
scripts\start.bat
```

**Linux/Mac:**
```bash
chmod +x scripts/start.sh
./scripts/start.sh
```

**Manual Docker Compose:**
```bash
# Copy environment file
cp .env.example .env

# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

### 3. Initialize Database

```bash
# Run setup script to create default users and roles
docker-compose exec app python scripts/setup.py
```

### 4. Access the Platform

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database Admin**: http://localhost:8080
- **API Base**: http://localhost:8000

## 🔐 Default Credentials

After running the setup script:

- **Username**: `admin`
- **Password**: `admin123`
- **Role**: Administrator (full access)

## 📊 Services Overview

### User Management Service
- JWT-based authentication and authorization
- Role-based access control (RBAC)
- User profile management
- Password security with bcrypt

### API Gateway
- Request routing and load balancing
- Circuit breaker patterns
- Rate limiting and security
- CORS and middleware support

### Database Layer
- PostgreSQL with async SQLAlchemy
- Alembic migrations
- Connection pooling
- Health monitoring

### Caching Layer
- Redis for session storage
- API response caching
- Performance optimization

## 🛠️ Development Setup

### Using Make (Recommended)

The project includes a Makefile with convenient commands for common tasks:

```bash
# First-time setup (installs everything and starts services)
make first-time-setup

# Daily development workflow
make quick-start          # Start Docker services and dev server

# Individual commands
make help                 # Show all available commands
make test                 # Run all tests
make test-cov            # Run tests with coverage
make lint                # Run linting
make format              # Format code
make docker-up           # Start Docker services
make migrate             # Run database migrations
make seed                # Seed test data
```

Run `make help` to see all available commands.

### Local Development (without Docker)

1. **Install Dependencies**
```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

2. **Setup Database**
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Setup default data
python scripts/setup.py
```

3. **Start Application**
```bash
# Development server with auto-reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using the module
python -m uvicorn src.main:app --reload
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:

```env
# Application Settings
DEBUG=true
HOST=0.0.0.0
PORT=8000

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ml_platform
DB_USER=postgres
DB_PASSWORD=password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS (for production)
AWS_REGION=us-east-1
AWS_S3_BUCKET=ml-platform-data
```

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Property-based tests only
pytest -m property_test

# Unit tests only
pytest -m unit
```

### Test Categories
- **Unit Tests**: Fast, isolated component tests
- **Property Tests**: Hypothesis-based correctness validation
- **Integration Tests**: Service interaction testing

## 📁 Project Structure

```
ml-workflow-platform/
├── src/
│   ├── shared/                 # Shared utilities and models
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Database setup and utilities
│   │   ├── schemas.py         # Shared Pydantic models
│   │   ├── exceptions.py      # Custom exception classes
│   │   └── logging.py         # Structured logging setup
│   ├── services/              # Microservices
│   │   └── user_management/   # User management service
│   │       ├── models.py      # SQLAlchemy models
│   │       ├── schemas.py     # Pydantic schemas
│   │       ├── repository.py  # Data access layer
│   │       ├── service.py     # Business logic layer
│   │       ├── dependencies.py # FastAPI dependencies
│   │       └── routes.py      # API endpoints
│   └── main.py               # FastAPI application entry point
├── tests/                    # Test suite
├── scripts/                  # Utility scripts
├── docker-compose.yml        # Docker services
├── Dockerfile               # Application container
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Poetry configuration
└── README.md               # This file
```

## 🔧 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Current user profile
- `PUT /api/v1/auth/me` - Update profile
- `PUT /api/v1/auth/me/password` - Change password

### User Management (Admin)
- `POST /api/v1/auth/users` - Create user
- `GET /api/v1/auth/users` - List users
- `GET /api/v1/auth/users/{id}` - Get user
- `PUT /api/v1/auth/users/{id}` - Update user
- `DELETE /api/v1/auth/users/{id}` - Delete user

### Role Management (Admin)
- `POST /api/v1/auth/roles` - Create role
- `GET /api/v1/auth/roles` - List roles
- `GET /api/v1/auth/roles/{id}` - Get role
- `GET /api/v1/auth/permissions` - List permissions

### System
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

## 🔒 Security Features

- **JWT Authentication** with access and refresh tokens
- **Password Hashing** with bcrypt and salt
- **Role-Based Access Control** (RBAC)
- **Rate Limiting** on authentication endpoints
- **CORS Configuration** for web clients
- **Input Validation** with Pydantic
- **SQL Injection Protection** with SQLAlchemy
- **Secure Headers** and HTTPS enforcement

## 📈 Monitoring & Observability

- **Structured Logging** with correlation IDs
- **Health Checks** for all services
- **Prometheus Metrics** endpoint
- **Request/Response Logging**
- **Error Tracking** and alerting
- **Database Connection Monitoring**

## 🚀 Deployment

### Docker Production
```bash
# Build production image
docker build -t ml-platform:latest .

# Run with production settings
docker run -p 8000:8000 --env-file .env.prod ml-platform:latest
```

### Kubernetes (Future)
- Helm charts for deployment
- ConfigMaps and Secrets
- Horizontal Pod Autoscaling
- Service mesh integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Skills Demonstrated

This project showcases:

### Python Backend Engineering
- ✅ FastAPI framework mastery
- ✅ Async/await programming
- ✅ SQLAlchemy ORM and migrations
- ✅ Pydantic data validation
- ✅ Clean architecture patterns
- ✅ Comprehensive testing strategies

### DevOps & Infrastructure
- ✅ Docker containerization
- ✅ Docker Compose orchestration
- ✅ Environment configuration
- ✅ Health checks and monitoring
- ✅ CI/CD pipeline preparation
- ✅ Production deployment patterns

### Security & Best Practices
- ✅ JWT authentication implementation
- ✅ Role-based authorization
- ✅ Password security
- ✅ Input validation and sanitization
- ✅ Error handling and logging
- ✅ API documentation

### Database Design
- ✅ Relational database modeling
- ✅ Migration management
- ✅ Connection pooling
- ✅ Query optimization
- ✅ Data integrity constraints

This platform serves as a comprehensive demonstration of enterprise-level software engineering capabilities suitable for senior Python Backend, DevOps, and MLOps engineering roles.
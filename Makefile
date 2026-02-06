.PHONY: help setup install clean test test-unit test-property test-integration test-cov lint format type-check security-check pre-commit docker-up docker-down docker-logs migrate migrate-create seed dev run build

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)ML Workflow Orchestration Platform - Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Setup and Installation
setup: ## Setup development environment (run this first)
	@echo "$(BLUE)Setting up development environment...$(NC)"
	python scripts/setup_dev_env.py

install: ## Install dependencies with Poetry
	@echo "$(BLUE)Installing dependencies...$(NC)"
	poetry install

install-pre-commit: ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	poetry run pre-commit install

# Cleaning
clean: ## Clean up generated files and caches
	@echo "$(YELLOW)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

# Testing
test: ## Run all tests
	@echo "$(BLUE)Running all tests...$(NC)"
	pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	pytest tests/ -v -m unit

test-property: ## Run property-based tests only
	@echo "$(BLUE)Running property-based tests...$(NC)"
	pytest tests/ -v -m property_test

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	pytest tests/ -v -m integration

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing --cov-report=xml
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	pytest-watch tests/

test-docker: ## Run tests in Docker container
	@echo "$(BLUE)Running tests in Docker...$(NC)"
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit test-app

test-property-docker: ## Run property-based tests in Docker
	@echo "$(BLUE)Running property-based tests in Docker...$(NC)"
	docker-compose -f docker-compose.test.yml --profile property-tests up --build --abort-on-container-exit property-tests

test-ci: ## Run tests as they would run in CI
	@echo "$(BLUE)Running CI test suite...$(NC)"
	HYPOTHESIS_PROFILE=ci pytest tests/ -v --cov=src --cov-report=xml --cov-report=term-missing --junitxml=junit.xml

test-smoke: ## Run quick smoke tests
	@echo "$(BLUE)Running smoke tests...$(NC)"
	pytest tests/ -v -m smoke --tb=short

test-security: ## Run security-focused tests
	@echo "$(BLUE)Running security tests...$(NC)"
	pytest tests/ -v -m security

test-failed: ## Re-run only failed tests
	@echo "$(BLUE)Re-running failed tests...$(NC)"
	pytest tests/ -v --lf

test-debug: ## Run tests with debugging enabled
	@echo "$(BLUE)Running tests in debug mode...$(NC)"
	HYPOTHESIS_PROFILE=debug pytest tests/ -v -s --tb=long

# Code Quality
lint: ## Run linting checks
	@echo "$(BLUE)Running linting checks...$(NC)"
	poetry run flake8 src tests

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	poetry run black src tests
	poetry run isort src tests

format-check: ## Check code formatting without making changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	poetry run black --check src tests
	poetry run isort --check-only src tests

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	poetry run mypy src

security-check: ## Run security checks with bandit
	@echo "$(BLUE)Running security checks...$(NC)"
	poetry run bandit -r src -c pyproject.toml

pre-commit: ## Run all pre-commit hooks
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	poetry run pre-commit run --all-files

# Docker Commands
docker-up: ## Start all Docker services
	@echo "$(BLUE)Starting Docker services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started! Check status with 'make docker-logs'$(NC)"

docker-down: ## Stop all Docker services
	@echo "$(YELLOW)Stopping Docker services...$(NC)"
	docker-compose down

docker-restart: ## Restart all Docker services
	@echo "$(BLUE)Restarting Docker services...$(NC)"
	docker-compose restart

docker-logs: ## Show Docker logs
	docker-compose logs -f

docker-ps: ## Show running Docker containers
	docker-compose ps

docker-clean: ## Remove all Docker containers, volumes, and images
	@echo "$(RED)Cleaning Docker resources...$(NC)"
	docker-compose down -v --rmi all

# Database Commands
migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	poetry run alembic upgrade head

migrate-down: ## Rollback last migration
	@echo "$(YELLOW)Rolling back last migration...$(NC)"
	poetry run alembic downgrade -1

migrate-create: ## Create a new migration (use MESSAGE="description")
	@echo "$(BLUE)Creating new migration...$(NC)"
	@if [ -z "$(MESSAGE)" ]; then \
		echo "$(RED)Error: MESSAGE is required. Usage: make migrate-create MESSAGE='description'$(NC)"; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(MESSAGE)"

migrate-history: ## Show migration history
	poetry run alembic history

seed: ## Seed database with test data
	@echo "$(BLUE)Seeding database...$(NC)"
	poetry run python scripts/setup.py

# Development
dev: ## Start development server with auto-reload
	@echo "$(BLUE)Starting development server...$(NC)"
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

dev-local: ## Start development server with local database
	@echo "$(BLUE)Starting development server (local mode)...$(NC)"
	poetry run uvicorn src.main_local:app --reload --host 0.0.0.0 --port 8000

run: ## Run the application (production mode)
	@echo "$(BLUE)Starting application...$(NC)"
	poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000

# Build
build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t ml-workflow-platform:latest .

# Documentation
docs: ## Open API documentation in browser
	@echo "$(BLUE)Opening API documentation...$(NC)"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "ReDoc: http://localhost:8000/redoc"

# Health Check
health: ## Check application health
	@echo "$(BLUE)Checking application health...$(NC)"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "$(RED)Application not running$(NC)"

# Complete Setup Flow
first-time-setup: setup docker-up migrate seed ## Complete first-time setup (run this for new installations)
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)✅ First-time setup complete!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "$(BLUE)Next steps:$(NC)"
	@echo "1. Start development server: $(GREEN)make dev$(NC)"
	@echo "2. Open API docs: $(GREEN)http://localhost:8000/docs$(NC)"
	@echo "3. Login with: $(GREEN)username=admin, password=admin123$(NC)"
	@echo ""

# Quick Development Start
quick-start: docker-up dev ## Quick start for daily development (starts Docker and dev server)

# CI/CD Commands
ci-test: lint type-check security-check test-cov ## Run all CI checks

# Information
info: ## Show project information
	@echo "$(BLUE)Project Information$(NC)"
	@echo "===================="
	@echo "Python version: $$(python --version)"
	@echo "Poetry version: $$(poetry --version 2>/dev/null || echo 'Not installed')"
	@echo "Docker version: $$(docker --version 2>/dev/null || echo 'Not installed')"
	@echo ""
	@echo "$(BLUE)Project Structure$(NC)"
	@echo "===================="
	@echo "Services:"
	@ls -d src/services/*/ 2>/dev/null | xargs -n 1 basename || echo "No services found"
	@echo ""
	@echo "$(BLUE)Useful Commands$(NC)"
	@echo "===================="
	@echo "Run 'make help' to see all available commands"

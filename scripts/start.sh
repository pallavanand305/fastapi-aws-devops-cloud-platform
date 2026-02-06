#!/bin/bash

# Start script for ML Workflow Platform

echo "🚀 Starting ML Workflow Platform..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your configuration"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start services with Docker Compose
echo "🐳 Starting services with Docker Compose..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is ready"
else
    echo "❌ PostgreSQL is not ready"
fi

# Check Redis
if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is ready"
else
    echo "❌ Redis is not ready"
fi

# Check FastAPI application
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ FastAPI application is ready"
else
    echo "❌ FastAPI application is not ready"
fi

echo ""
echo "🎉 ML Workflow Platform is starting up!"
echo ""
echo "📊 Services:"
echo "   • FastAPI App: http://localhost:8000"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Database Admin: http://localhost:8080"
echo "   • Health Check: http://localhost:8000/health"
echo ""
echo "📝 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
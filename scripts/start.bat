@echo off
echo 🚀 Starting ML Workflow Platform...

REM Check if .env file exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please update .env file with your configuration
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker first.
    pause
    exit /b 1
)

REM Start services with Docker Compose
echo 🐳 Starting services with Docker Compose...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

echo.
echo 🎉 ML Workflow Platform is starting up!
echo.
echo 📊 Services:
echo    • FastAPI App: http://localhost:8000
echo    • API Docs: http://localhost:8000/docs
echo    • Database Admin: http://localhost:8080
echo    • Health Check: http://localhost:8000/health
echo.
echo 📝 To view logs: docker-compose logs -f
echo 🛑 To stop: docker-compose down
echo.
pause
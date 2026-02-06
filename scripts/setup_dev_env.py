#!/usr/bin/env python3
"""
Development Environment Setup Script

This script sets up the development environment including:
- Pre-commit hooks installation
- Virtual environment verification
- Database initialization
- Redis connection check
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], description: str) -> bool:
    """Run a shell command and return success status."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} - SUCCESS")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ {description} - COMMAND NOT FOUND")
        print(f"Please ensure the required tool is installed")
        return False


def check_python_version() -> bool:
    """Check if Python version is 3.11 or higher."""
    print("\n🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        print(f"❌ Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}")
        return False


def check_poetry_installed() -> bool:
    """Check if Poetry is installed."""
    print("\n📦 Checking Poetry installation...")
    try:
        result = subprocess.run(
            ["poetry", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Poetry not found")
        print("Install Poetry: https://python-poetry.org/docs/#installation")
        return False


def install_dependencies() -> bool:
    """Install Python dependencies using Poetry."""
    return run_command(
        ["poetry", "install"],
        "Installing Python dependencies"
    )


def install_pre_commit_hooks() -> bool:
    """Install pre-commit hooks."""
    return run_command(
        ["poetry", "run", "pre-commit", "install"],
        "Installing pre-commit hooks"
    )


def run_pre_commit_on_all_files() -> bool:
    """Run pre-commit on all files to ensure everything is formatted."""
    print("\n🔍 Running pre-commit checks on all files...")
    print("This may take a few minutes on first run...")
    return run_command(
        ["poetry", "run", "pre-commit", "run", "--all-files"],
        "Running pre-commit checks"
    )


def check_docker_running() -> bool:
    """Check if Docker is running."""
    print("\n🐳 Checking Docker status...")
    try:
        result = subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Docker is running")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not running or not installed")
        print("Please start Docker Desktop or install Docker")
        return False


def create_env_file() -> bool:
    """Create .env file from .env.example if it doesn't exist."""
    print("\n⚙️  Checking environment configuration...")
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        env_file.write_text(env_example.read_text())
        print("✅ Created .env file from .env.example")
        print("⚠️  Please review and update .env with your configuration")
        return True
    else:
        print("❌ .env.example not found")
        return False


def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("🚀 ML Workflow Platform - Development Environment Setup")
    print("="*60)
    
    # Track success of each step
    steps = []
    
    # Check Python version
    steps.append(("Python Version", check_python_version()))
    
    # Check Poetry installation
    poetry_installed = check_poetry_installed()
    steps.append(("Poetry Installation", poetry_installed))
    
    if not poetry_installed:
        print("\n❌ Cannot continue without Poetry")
        sys.exit(1)
    
    # Install dependencies
    steps.append(("Dependencies Installation", install_dependencies()))
    
    # Create .env file
    steps.append(("Environment Configuration", create_env_file()))
    
    # Install pre-commit hooks
    steps.append(("Pre-commit Hooks", install_pre_commit_hooks()))
    
    # Run pre-commit on all files (optional, may fail on first run)
    print("\n⚠️  Note: Pre-commit checks may show warnings on first run")
    run_pre_commit_on_all_files()
    
    # Check Docker
    steps.append(("Docker Status", check_docker_running()))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 Setup Summary")
    print("="*60)
    
    for step_name, success in steps:
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
    
    all_success = all(success for _, success in steps)
    
    if all_success:
        print("\n" + "="*60)
        print("🎉 Development environment setup complete!")
        print("="*60)
        print("\n📝 Next steps:")
        print("1. Review and update .env file with your configuration")
        print("2. Start services: docker-compose up -d")
        print("3. Run migrations: poetry run alembic upgrade head")
        print("4. Initialize data: poetry run python scripts/setup.py")
        print("5. Start development: poetry run uvicorn src.main:app --reload")
        print("\n📚 Documentation: http://localhost:8000/docs")
    else:
        print("\n" + "="*60)
        print("⚠️  Setup completed with some issues")
        print("="*60)
        print("Please resolve the failed steps above and run this script again")
        sys.exit(1)


if __name__ == "__main__":
    main()

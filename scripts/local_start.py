#!/usr/bin/env python3
"""
Local development startup script (without Docker).
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check Python version."""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def create_env_file():
    """Create .env file if it doesn't exist."""
    if not Path(".env").exists():
        print("📝 Creating .env file from template...")
        with open(".env.example", "r") as src, open(".env", "w") as dst:
            content = src.read()
            # Update for local development without Docker
            content = content.replace("DB_HOST=localhost", "DB_HOST=localhost")
            content = content.replace("REDIS_HOST=localhost", "REDIS_HOST=localhost")
            dst.write(content)
        print("✅ .env file created")
    else:
        print("✅ .env file already exists")

def install_dependencies():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def start_uvicorn():
    """Start the FastAPI application with uvicorn."""
    print("🚀 Starting FastAPI application...")
    print("📊 Application will be available at:")
    print("   • API: http://localhost:8000")
    print("   • Docs: http://localhost:8000/docs")
    print("   • Health: http://localhost:8000/health")
    print("")
    print("⚠️  Note: Database and Redis connections will fail without those services running")
    print("   Consider using Docker Compose for full functionality")
    print("")
    print("🛑 Press Ctrl+C to stop the server")
    print("")
    
    try:
        # Start uvicorn with local version
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "src.main_local:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")

def main():
    """Main function."""
    print("🚀 ML Workflow Platform - Local Development Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Start application
    start_uvicorn()

if __name__ == "__main__":
    main()
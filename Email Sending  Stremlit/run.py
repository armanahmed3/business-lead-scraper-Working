"""
LeadAI Pro - Startup Script
Complete AI SaaS platform for lead management and email marketing
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import streamlit
        import pandas
        import plotly
        import numpy
        import sklearn
        import fastapi
        import sqlalchemy
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def setup_environment():
    """Set up environment variables"""
    env_file = Path(".env")
    env_example = Path("env_example.txt")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        with open(env_example, 'r') as f:
            content = f.read()
        with open(env_file, 'w') as f:
            f.write(content)
        print("✅ .env file created")
    else:
        print("✅ Environment file already exists")

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    backend_path = Path("backend")
    if backend_path.exists():
        try:
            subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "backend.main:app", 
                "--host", "0.0.0.0", 
                "--port", "8000", 
                "--reload"
            ], cwd=Path.cwd())
            print("✅ Backend started on http://localhost:8000")
            return True
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
    else:
        print("❌ Backend directory not found")
        return False

def start_frontend():
    """Start the Streamlit frontend"""
    print("🚀 Starting Streamlit frontend...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")

def main():
    """Main startup function"""
    print("🚀 LeadAI Pro - AI SaaS Platform")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Setup environment
    setup_environment()
    
    # Start backend
    backend_started = start_backend()
    
    if backend_started:
        print("⏳ Waiting for backend to initialize...")
        import time
        time.sleep(3)
    
    # Start frontend
    start_frontend()

if __name__ == "__main__":
    main()

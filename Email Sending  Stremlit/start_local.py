#!/usr/bin/env python3
"""
LeadAI Pro - Local Development Startup Script
Run this to start the application locally for testing
"""

import subprocess
import sys
import os
import time

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import streamlit
        import pandas
        import sqlite3
        print("✅ All core dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def start_app():
    """Start the Streamlit application"""
    print("🚀 Starting LeadAI Pro...")
    print("📍 Local URL: http://localhost:8501")
    print("📍 Network URL: http://192.168.1.106:8501")
    print("📍 External URL: http://182.190.218.14:8501")
    print("\nPress Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "deploy_app.py",
            "--server.headless", "true",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 LeadAI Pro - AI-Powered Lead Management Platform")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("deploy_app.py"):
        print("❌ Error: deploy_app.py not found!")
        print("Please run this script from the project directory")
        return
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Start the application
    start_app()

if __name__ == "__main__":
    main()

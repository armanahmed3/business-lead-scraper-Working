"""
LeadAI Pro - Simple Startup Script
Starts the Streamlit frontend (backend is optional for demo)
"""

import subprocess
import sys
import os
from pathlib import Path

def start_streamlit():
    """Start the Streamlit frontend"""
    print("🚀 Starting LeadAI Pro Frontend...")
    print("=" * 50)
    
    try:
        # Start Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down LeadAI Pro...")
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")

if __name__ == "__main__":
    print("🎉 LeadAI Pro - AI SaaS Platform")
    print("=" * 50)
    print("🌐 Frontend will be available at: http://localhost:8501")
    print("📊 Backend API: http://localhost:8000 (optional)")
    print("=" * 50)
    
    start_streamlit()

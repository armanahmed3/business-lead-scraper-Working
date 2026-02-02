"""
LeadAI Pro - Setup Verification Script
Verifies that all components are properly configured and ready to run
"""

import sys
import os
from pathlib import Path
import importlib.util

def check_file_structure():
    """Check if all required files exist"""
    required_files = [
        "app.py",
        "run.py", 
        "requirements.txt",
        "env_example.txt",
        "README.md",
        "backend/main.py",
        "backend/database.py",
        "backend/models.py",
        "backend/schemas.py",
        "backend/auth.py",
        "backend/services/lead_service.py",
        "backend/services/email_service.py",
        "backend/services/ai_service.py",
        "backend/services/campaign_service.py",
        "backend/services/analytics_service.py",
        "pages/lead_management.py",
        "pages/email_campaigns.py",
        "pages/data_analytics.py",
        "pages/ai_tools.py",
        "pages/settings.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    else:
        print("✅ All required files present")
        return True

def check_dependencies():
    """Check if required Python packages are available"""
    required_packages = [
        "streamlit",
        "pandas", 
        "plotly",
        "numpy",
        "sklearn",
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "uvicorn"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All required packages installed")
        return True

def check_imports():
    """Check if all modules can be imported without errors"""
    try:
        # Test main app import
        spec = importlib.util.spec_from_file_location("app", "app.py")
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        print("✅ Main app imports successfully")
        
        # Test backend imports
        sys.path.append("backend")
        from backend.main import app
        print("✅ Backend imports successfully")
        
        # Test page imports
        sys.path.append("pages")
        from pages.lead_management import show_lead_management
        from pages.email_campaigns import show_email_campaigns
        from pages.data_analytics import show_data_analytics
        from pages.ai_tools import show_ai_tools
        from pages.settings import show_settings
        print("✅ All pages import successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def check_environment():
    """Check environment configuration"""
    env_file = Path(".env")
    env_example = Path("env_example.txt")
    
    if not env_file.exists():
        if env_example.exists():
            print("⚠️  .env file not found, but env_example.txt exists")
            print("   Run: cp env_example.txt .env")
            return False
        else:
            print("❌ No environment configuration found")
            return False
    else:
        print("✅ Environment file (.env) exists")
        return True

def main():
    """Main verification function"""
    print("🔍 LeadAI Pro - Setup Verification")
    print("=" * 50)
    
    checks = [
        ("File Structure", check_file_structure),
        ("Dependencies", check_dependencies), 
        ("Imports", check_imports),
        ("Environment", check_environment)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        if not check_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! LeadAI Pro is ready to run.")
        print("\n🚀 To start the platform:")
        print("   python run.py")
        print("\n🌐 Access URLs:")
        print("   Frontend: http://localhost:8501")
        print("   Backend:  http://localhost:8000")
        print("   API Docs: http://localhost:8000/docs")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
    
    return all_passed

if __name__ == "__main__":
    main()

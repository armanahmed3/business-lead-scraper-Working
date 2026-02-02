"""
Test script to verify deployment readiness
"""

import sys
import os

def test_imports():
    """Test if all required imports work"""
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import pandas as pd
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
        return False
    
    try:
        import sqlite3
        print("✅ SQLite3 imported successfully")
    except ImportError as e:
        print(f"❌ SQLite3 import failed: {e}")
        return False
    
    try:
        import hashlib
        print("✅ Hashlib imported successfully")
    except ImportError as e:
        print(f"❌ Hashlib import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database initialization"""
    try:
        import sqlite3
        conn = sqlite3.connect("test.db")
        cursor = conn.cursor()
        
        # Test table creation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
        ''')
        
        # Test insert
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test",))
        
        # Test select
        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchone()
        
        conn.close()
        os.remove("test.db")
        
        print("✅ Database operations work correctly")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_file_structure():
    """Test if all required files exist"""
    required_files = [
        "deploy_app.py",
        "requirements.txt",
        "runtime.txt",
        "README.md"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} exists")
        else:
            print(f"❌ {file} missing")
            return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing LeadAI Pro deployment readiness...\n")
    
    tests = [
        ("File Structure", test_file_structure),
        ("Core Imports", test_imports),
        ("Database Operations", test_database)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test passed")
        else:
            print(f"❌ {test_name} test failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment on Hugging Face Spaces.")
        return True
    else:
        print("⚠️ Some tests failed. Please fix issues before deployment.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

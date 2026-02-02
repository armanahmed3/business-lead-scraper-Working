#!/usr/bin/env python3
"""
Test AI features to ensure they work properly
"""

import sys
import os

def test_ai_imports():
    """Test if AI-related imports work"""
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        print("✅ Transformers library imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Transformers import failed: {e}")
        return False

def test_ai_models():
    """Test if AI models can be loaded"""
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        
        print("🔄 Loading AI models... (this may take a moment)")
        
        # Load a lightweight model for testing
        tokenizer = AutoTokenizer.from_pretrained("gpt2")
        model = AutoModelForCausalLM.from_pretrained("gpt2")
        
        # Create text generation pipeline
        text_generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
        
        print("✅ AI models loaded successfully")
        
        # Test generation
        result = text_generator("Hello, this is a test", max_length=30, num_return_sequences=1)
        print(f"✅ AI generation test successful: {result[0]['generated_text'][:50]}...")
        
        return True
    except Exception as e:
        print(f"❌ AI model test failed: {e}")
        return False

def test_app_imports():
    """Test if the main app can be imported"""
    try:
        # Add current directory to path
        sys.path.insert(0, os.getcwd())
        
        # Import the main app functions
        from deploy_app import load_css, hash_password, verify_password, generate_email_content
        
        print("✅ Main app functions imported successfully")
        
        # Test password hashing
        test_password = "test123"
        hashed = hash_password(test_password)
        if verify_password(test_password, hashed):
            print("✅ Password hashing works correctly")
        else:
            print("❌ Password verification failed")
            return False
        
        return True
    except Exception as e:
        print(f"❌ App import test failed: {e}")
        return False

def main():
    """Run all AI feature tests"""
    print("🤖 Testing LeadAI Pro AI Features...\n")
    
    tests = [
        ("AI Library Imports", test_ai_imports),
        ("AI Model Loading", test_ai_models),
        ("App Function Imports", test_app_imports)
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
    
    print(f"\n📊 AI Feature Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All AI features are working! The app is ready to use.")
        return True
    else:
        print("⚠️ Some AI features failed. The app will work but AI features may be limited.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

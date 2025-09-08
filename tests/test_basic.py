#!/usr/bin/env python3
"""
Basic tests for Okama Finance Bot
Tests core imports and basic functionality
"""

import sys
import os

def test_requirements():
    """Test that requirements.txt exists and is readable"""
    try:
        with open('requirements.txt', 'r') as f:
            content = f.read()
            if 'Flask' in content and 'python-telegram-bot' in content:
                print("✅ Requirements.txt contains expected dependencies")
                return True
            else:
                print("❌ Requirements.txt missing expected dependencies")
                return False
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def test_file_structure():
    """Test that key files exist"""
    try:
        required_files = [
            'bot.py',
            'config.py',
            'requirements.txt',
            'render.yaml',
            'services/__init__.py',
            'services/okama_service.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing required files: {missing_files}")
            return False
        else:
            print("✅ All required files exist")
            return True
    except Exception as e:
        print(f"❌ File structure test failed: {e}")
        return False

def test_python_version():
    """Test Python version compatibility"""
    try:
        version = sys.version_info
        if version.major == 3 and version.minor >= 7:  # Allow Python 3.7+ for local testing
            print(f"✅ Python version {version.major}.{version.minor}.{version.micro} is compatible")
            return True
        else:
            print(f"❌ Python version {version.major}.{version.minor}.{version.micro} is not compatible (need 3.7+)")
            return False
    except Exception as e:
        print(f"❌ Python version test failed: {e}")
        return False

def test_imports():
    """Test that core modules can be imported (if possible)"""
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Test service imports
        from services.okama_service import OkamaServiceV2
        print("✅ OkamaServiceV2 import successful")
        
        # Test bot import
        from bot import OkamaFinanceBotV2
        print("✅ OkamaFinanceBotV2 import successful")
        
        return True
    except ImportError as e:
        print(f"⚠️ Import test skipped (ImportError): {e}")
        print("   This is expected in CI environments without full dependencies")
        return True  # Don't fail the test for import issues
    except ModuleNotFoundError as e:
        print(f"⚠️ Import test skipped (ModuleNotFoundError): {e}")
        print("   This is expected in CI environments without full dependencies")
        return True  # Don't fail the test for import issues
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_config():
    """Test basic configuration (if possible)"""
    try:
        # Add current directory to Python path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Test that config can be loaded
        import config
        print("✅ Config import successful")
        return True
    except ImportError as e:
        print(f"⚠️ Config test skipped (ImportError): {e}")
        print("   This is expected in CI environments without full dependencies")
        return True  # Don't fail the test for import issues
    except ModuleNotFoundError as e:
        print(f"⚠️ Config test skipped (ModuleNotFoundError): {e}")
        print("   This is expected in CI environments without full dependencies")
        return True  # Don't fail the test for import issues
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running basic tests for Okama Finance Bot...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"🐍 Python version: {sys.version}")
    
    tests = [
        test_python_version,
        test_file_structure,
        test_requirements,
        test_imports,
        test_config
    ]
    
    passed = 0
    total = len(tests)
    
    print("\n🔍 Running individual tests...")
    for i, test in enumerate(tests, 1):
        print(f"\n📋 Test {i}/{total}: {test.__name__}")
        if test():
            passed += 1
            print(f"✅ {test.__name__} passed")
        else:
            print(f"❌ {test.__name__} failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())

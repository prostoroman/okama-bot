#!/usr/bin/env python3
"""
Test script to verify Okama Finance Bot setup
Run this script to check if all dependencies and services are working
"""

import sys
import os
from dotenv import load_dotenv

def test_imports():
    """Test if all required packages can be imported"""
    print("🔍 Testing package imports...")
    
    try:
        import telegram
        print("✅ python-telegram-bot imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import python-telegram-bot: {e}")
        return False
    
    try:
        import openai
        print("✅ openai imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import openai: {e}")
        return False
    
    try:
        import okama
        print("✅ okama imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import okama: {e}")
        return False
    
    try:
        import matplotlib
        print("✅ matplotlib imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import matplotlib: {e}")
        return False
    
    try:
        import pandas
        print("✅ pandas imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import pandas: {e}")
        return False
    
    try:
        import numpy
        print("✅ numpy imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import numpy: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\n🔍 Testing configuration...")
    
    # Load environment variables
    load_dotenv()
    
    required_vars = ['TELEGRAM_BOT_TOKEN', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please create a .env file with the required variables")
        return False
    else:
        print("✅ All required environment variables found")
        return True

def test_services():
    """Test service initialization"""
    print("\n🔍 Testing service initialization...")
    
    try:
        from config import Config
        Config.validate()
        print("✅ Configuration validation passed")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False
    
    try:
        from okama_service import OkamaService
        okama_service = OkamaService()
        print("✅ OkamaService initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize OkamaService: {e}")
        return False
    
    try:
        from chatgpt_service import ChatGPTService
        chatgpt_service = ChatGPTService()
        print("✅ ChatGPTService initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize ChatGPTService: {e}")
        return False
    
    return True

def test_bot():
    """Test bot initialization"""
    print("\n🔍 Testing bot initialization...")
    
    try:
        from bot import OkamaFinanceBot
        bot = OkamaFinanceBot()
        print("✅ OkamaFinanceBot initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize OkamaFinanceBot: {e}")
        return False
    
    return True

def test_okama_functionality():
    """Test basic Okama functionality"""
    print("\n🔍 Testing Okama functionality...")
    
    try:
        from okama_service import OkamaService
        service = OkamaService()
        
        # Test asset info retrieval
        asset_info = service.get_asset_info('AAPL')
        if 'error' not in asset_info:
            print("✅ Asset info retrieval working")
        else:
            print("⚠️  Asset info retrieval failed (may be network/data issue)")
        
        # Test portfolio creation
        try:
            portfolio = service.create_portfolio(['AAPL', 'MSFT'])
            print("✅ Portfolio creation working")
        except Exception as e:
            print(f"⚠️  Portfolio creation failed: {e}")
        
    except Exception as e:
        print(f"❌ Okama functionality test failed: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Okama Finance Bot - Setup Test")
    print("=" * 50)
    
    tests = [
        ("Package Imports", test_imports),
        ("Configuration", test_config),
        ("Service Initialization", test_services),
        ("Bot Initialization", test_bot),
        ("Okama Functionality", test_okama_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your bot is ready to run.")
        print("\nTo start the bot, run:")
        print("   python bot.py")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Create .env file with required API keys")
        print("3. Check internet connection for data access")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

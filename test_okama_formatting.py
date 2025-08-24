#!/usr/bin/env python3
"""
Test script for Okama formatting functionality in YandexGPT service.
This script tests the new prompts and methods for converting instrument names.
"""

import os
import sys
from yandexgpt_service import YandexGPTService

def test_okama_formatting():
    """Test the Okama formatting functionality"""
    print("🧪 Testing Okama Formatting Functionality")
    print("=" * 50)
    
    # Initialize the service
    service = YandexGPTService()
    
    # Test cases with different instrument names
    test_cases = [
        "Покажи анализ портфеля с Apple и Tesla",
        "Сравни S&P 500 и Bitcoin",
        "Оцени риск по акциям Сбербанка и Газпрома",
        "Покажи корреляцию между золотом и нефтью",
        "Анализ EUR/USD и GBP/USD",
        "Портфель из акций Google, Microsoft и Amazon"
    ]
    
    print("\n📋 Test Cases:")
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case}")
    
    print("\n🔍 Testing analyze_query method:")
    print("-" * 30)
    
    for test_case in test_cases[:3]:  # Test first 3 cases
        print(f"\nTesting: '{test_case}'")
        try:
            result = service.analyze_query(test_case)
            print(f"Intent: {result.get('intent')}")
            print(f"Symbols: {result.get('symbols')}")
            print(f"Time period: {result.get('time_period')}")
            print(f"Is chat: {result.get('is_chat')}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n🔍 Testing process_freeform_command method:")
    print("-" * 40)
    
    for test_case in test_cases[3:6]:  # Test last 3 cases
        print(f"\nTesting: '{test_case}'")
        try:
            result = service.process_freeform_command(test_case)
            print(f"Command type: {result.get('command_type')}")
            print(f"Symbols: {result.get('symbols')}")
            print(f"Parameters: {result.get('parameters')}")
            print(f"Suggested command: {result.get('suggested_command')}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n🔍 Testing fallback analysis:")
    print("-" * 25)
    
    # Test fallback with common names
    fallback_test = "Покажи Apple, Tesla и Bitcoin"
    print(f"Testing fallback: '{fallback_test}'")
    try:
        result = service._fallback_analysis(fallback_test)
        print(f"Intent: {result.get('intent')}")
        print(f"Symbols: {result.get('symbols')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n✅ Testing completed!")

def test_system_prompt():
    """Test the system prompt content"""
    print("\n📝 Testing System Prompt Content")
    print("=" * 40)
    
    service = YandexGPTService()
    
    # Check if Okama namespaces are in the prompt
    prompt = service.system_prompt
    
    required_elements = [
        "CBR", "CC", "COMM", "FX", "INDX", "INFL", "LSE", "MOEX",
        "PF", "PIF", "RATE", "RATIO", "RE", "US", "XAMS", "XETR",
        "XFRA", "XSTU", "XTAE"
    ]
    
    print("Checking required namespace elements:")
    for element in required_elements:
        if element in prompt:
            print(f"✅ {element} - Found")
        else:
            print(f"❌ {element} - Missing")
    
    # Check for formatting examples
    examples = [
        "SPX.INDX", "AAPL.US", "BTC.CC", "XAU.COMM", "EURUSD.FX"
    ]
    
    print("\nChecking formatting examples:")
    for example in examples:
        if example in prompt:
            print(f"✅ {example} - Found")
        else:
            print(f"❌ {example} - Missing")

if __name__ == "__main__":
    print("🚀 Okama Formatting Test Suite")
    print("=" * 40)
    
    # Check if we have the required configuration
    if not os.getenv('YANDEX_API_KEY') or not os.getenv('YANDEX_FOLDER_ID'):
        print("⚠️  Warning: YandexGPT API configuration not found")
        print("   Set YANDEX_API_KEY and YANDEX_FOLDER_ID environment variables")
        print("   Some tests may fail without proper configuration")
        print()
    
    try:
        test_system_prompt()
        test_okama_formatting()
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n🎉 All tests completed successfully!")

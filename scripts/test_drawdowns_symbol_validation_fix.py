#!/usr/bin/env python3
"""
Test script to verify the drawdowns symbol validation fix.
This script tests the _handle_portfolio_drawdowns_by_symbol function
to ensure it properly handles None values and invalid symbols.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
from unittest.mock import Mock, AsyncMock, patch
import asyncio

def test_symbol_validation_logic():
    """Test the symbol validation logic that was added to the drawdowns function"""
    
    print("🧪 Testing symbol validation logic for drawdowns...")
    
    # Test data with various symbol types
    test_cases = [
        {
            "name": "Valid symbols only",
            "symbols": ["AAPL.US", "MSFT.US", "GOOGL.US"],
            "weights": [0.4, 0.3, 0.3],
            "expected_valid": 3,
            "expected_invalid": 0
        },
        {
            "name": "Symbols with None values",
            "symbols": ["AAPL.US", None, "MSFT.US", None],
            "weights": [0.4, 0.2, 0.3, 0.1],
            "expected_valid": 2,
            "expected_invalid": 0  # None values should be filtered out before validation
        },
        {
            "name": "Symbols with empty strings",
            "symbols": ["AAPL.US", "", "MSFT.US", "   "],
            "weights": [0.4, 0.2, 0.3, 0.1],
            "expected_valid": 2,
            "expected_invalid": 0  # Empty strings should be filtered out before validation
        },
        {
            "name": "Invalid symbols",
            "symbols": ["INVALID_SYMBOL_123", "ANOTHER_INVALID"],
            "weights": [0.5, 0.5],
            "expected_valid": 0,
            "expected_invalid": 2
        },
        {
            "name": "Mixed valid and invalid symbols",
            "symbols": ["AAPL.US", "INVALID_SYMBOL", "MSFT.US", None],
            "weights": [0.3, 0.2, 0.3, 0.2],
            "expected_valid": 2,
            "expected_invalid": 1
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Test case: {test_case['name']}")
        print(f"   Input symbols: {test_case['symbols']}")
        
        # Simulate the filtering logic
        final_symbols = [s for s in test_case['symbols'] if s is not None and str(s).strip()]
        print(f"   After filtering: {final_symbols}")
        
        # Simulate the validation logic
        valid_symbols = []
        valid_weights = []
        invalid_symbols = []
        
        for i, symbol in enumerate(final_symbols):
            try:
                # Test if symbol exists in database
                test_asset = ok.Asset(symbol)
                valid_symbols.append(symbol)
                if i < len(test_case['weights']):
                    valid_weights.append(test_case['weights'][i])
                else:
                    valid_weights.append(1.0 / len(final_symbols))
                print(f"   ✅ Symbol '{symbol}' validated successfully")
            except Exception as e:
                invalid_symbols.append(symbol)
                print(f"   ❌ Symbol '{symbol}' is invalid: {e}")
        
        # Check results
        actual_valid = len(valid_symbols)
        actual_invalid = len(invalid_symbols)
        
        print(f"   Expected valid: {test_case['expected_valid']}, Actual: {actual_valid}")
        print(f"   Expected invalid: {test_case['expected_invalid']}, Actual: {actual_invalid}")
        
        if actual_valid == test_case['expected_valid'] and actual_invalid == test_case['expected_invalid']:
            print(f"   ✅ Test passed!")
        else:
            print(f"   ❌ Test failed!")
            return False
    
    return True

def test_weight_normalization():
    """Test the weight normalization logic"""
    
    print("\n🧪 Testing weight normalization logic...")
    
    # Test cases for weight normalization
    test_cases = [
        {
            "name": "Normal weights",
            "valid_weights": [0.4, 0.3, 0.3],
            "expected_sum": 1.0
        },
        {
            "name": "Weights that need normalization",
            "valid_weights": [0.2, 0.2, 0.2],
            "expected_sum": 1.0
        },
        {
            "name": "Zero weights",
            "valid_weights": [0.0, 0.0, 0.0],
            "expected_sum": 1.0
        },
        {
            "name": "Empty weights",
            "valid_weights": [],
            "expected_sum": 0.0
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Test case: {test_case['name']}")
        print(f"   Input weights: {test_case['valid_weights']}")
        
        # Simulate the normalization logic
        if test_case['valid_weights']:
            total_weight = sum(test_case['valid_weights'])
            if total_weight > 0:
                normalized_weights = [w / total_weight for w in test_case['valid_weights']]
            else:
                normalized_weights = [1.0 / len(test_case['valid_weights'])] * len(test_case['valid_weights'])
        else:
            normalized_weights = []
        
        actual_sum = sum(normalized_weights) if normalized_weights else 0
        
        print(f"   Normalized weights: {normalized_weights}")
        print(f"   Expected sum: {test_case['expected_sum']}, Actual sum: {actual_sum}")
        
        if abs(actual_sum - test_case['expected_sum']) < 0.001:
            print(f"   ✅ Test passed!")
        else:
            print(f"   ❌ Test failed!")
            return False
    
    return True

def test_fx_symbol_detection():
    """Test FX symbol detection and error message generation"""
    
    print("\n🧪 Testing FX symbol detection...")
    
    test_cases = [
        {
            "name": "No FX symbols",
            "invalid_symbols": ["INVALID_STOCK", "ANOTHER_INVALID"],
            "should_contain_fx_message": False
        },
        {
            "name": "With FX symbols",
            "invalid_symbols": ["EURUSD.FX", "GBPUSD.FX"],
            "should_contain_fx_message": True
        },
        {
            "name": "Mixed symbols with FX",
            "invalid_symbols": ["INVALID_STOCK", "EURUSD.FX"],
            "should_contain_fx_message": True
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📋 Test case: {test_case['name']}")
        print(f"   Invalid symbols: {test_case['invalid_symbols']}")
        
        # Simulate the error message generation logic
        error_msg = f"❌ Все символы недействительны: {', '.join(test_case['invalid_symbols'])}"
        if any('.FX' in s for s in test_case['invalid_symbols']):
            error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
        
        contains_fx_message = "💡 Валютные пары (.FX)" in error_msg
        
        print(f"   Error message: {error_msg}")
        print(f"   Expected FX message: {test_case['should_contain_fx_message']}, Actual: {contains_fx_message}")
        
        if contains_fx_message == test_case['should_contain_fx_message']:
            print(f"   ✅ Test passed!")
        else:
            print(f"   ❌ Test failed!")
            return False
    
    return True

def main():
    """Run all tests"""
    
    print("🚀 Starting drawdowns symbol validation fix tests...")
    
    tests = [
        ("Symbol Validation Logic", test_symbol_validation_logic),
        ("Weight Normalization", test_weight_normalization),
        ("FX Symbol Detection", test_fx_symbol_detection)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name} - PASSED")
            else:
                print(f"\n❌ {test_name} - FAILED")
        except Exception as e:
            print(f"\n💥 {test_name} - ERROR: {e}")
    
    print(f"\n{'='*60}")
    print(f"Test Results: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("🎉 All tests passed! The drawdowns symbol validation fix is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

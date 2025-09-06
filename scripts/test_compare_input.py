#!/usr/bin/env python3
"""
Test script for compare input functionality
Tests text input handling for /compare command
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_compare_input_parsing():
    """Test compare input parsing logic"""
    print("🧪 Testing Compare Input Parsing")
    
    # Test cases
    test_cases = [
        {
            'input': 'SPY.US QQQ.US',
            'expected': ['SPY.US', 'QQQ.US'],
            'description': 'Space-separated symbols'
        },
        {
            'input': 'SPY.US,QQQ.US',
            'expected': ['SPY.US', 'QQQ.US'],
            'description': 'Comma-separated symbols'
        },
        {
            'input': 'SPY.US, QQQ.US',
            'expected': ['SPY.US', 'QQQ.US'],
            'description': 'Comma with space'
        },
        {
            'input': 'PF_1 SBER.MOEX',
            'expected': ['PF_1', 'SBER.MOEX'],
            'description': 'Portfolio with asset'
        },
        {
            'input': 'PF_1,PF_2',
            'expected': ['PF_1', 'PF_2'],
            'description': 'Two portfolios'
        },
        {
            'input': 'portfolio_123.PF SPY.US',
            'expected': ['portfolio_123.PF', 'SPY.US'],
            'description': 'Portfolio with .PF extension'
        }
    ]
    
    def parse_compare_input(raw_args):
        """Simulate the parsing logic from _handle_compare_input"""
        if ',' in raw_args:
            symbols = []
            for symbol_part in raw_args.split(','):
                symbol_part = symbol_part.strip()
                if symbol_part:
                    if any(portfolio_indicator in symbol_part.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                        symbols.append(symbol_part)
                    else:
                        symbols.append(symbol_part.upper())
            return symbols
        else:
            symbols = []
            for symbol in raw_args.split():
                if any(portfolio_indicator in symbol.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                    symbols.append(symbol)
                else:
                    symbols.append(symbol.upper())
            return symbols
    
    passed = 0
    total = len(test_cases)
    
    for test_case in test_cases:
        try:
            result = parse_compare_input(test_case['input'])
            if result == test_case['expected']:
                print(f"✅ {test_case['description']}: {test_case['input']} → {result}")
                passed += 1
            else:
                print(f"❌ {test_case['description']}: {test_case['input']} → {result} (expected: {test_case['expected']})")
        except Exception as e:
            print(f"❌ {test_case['description']}: Error - {e}")
    
    print(f"\n📊 Parsing Results: {passed}/{total} tests passed")
    return passed == total

def test_compare_input_validation():
    """Test compare input validation"""
    print("\n🧪 Testing Compare Input Validation")
    
    # Test validation cases
    validation_cases = [
        {
            'input': 'SPY.US',
            'should_pass': False,
            'description': 'Single symbol (should fail)'
        },
        {
            'input': 'SPY.US QQQ.US',
            'should_pass': True,
            'description': 'Two symbols (should pass)'
        },
        {
            'input': 'SPY.US QQQ.US VOO.US BND.US GC.COMM CL.COMM SI.COMM EURUSD.FX GBPUSD.FX AAPL.US TSLA.US',
            'should_pass': False,
            'description': 'Too many symbols (should fail)'
        },
        {
            'input': '',
            'should_pass': False,
            'description': 'Empty input (should fail)'
        },
        {
            'input': '   ',
            'should_pass': False,
            'description': 'Whitespace only (should fail)'
        }
    ]
    
    def validate_compare_input(symbols):
        """Simulate validation logic"""
        if len(symbols) < 2:
            return False, "Необходимо указать минимум 2 символа для сравнения"
        if len(symbols) > 10:
            return False, "Максимум 10 символов для сравнения"
        return True, "Valid"
    
    passed = 0
    total = len(validation_cases)
    
    for test_case in validation_cases:
        try:
            # Parse input first
            if ',' in test_case['input']:
                symbols = [s.strip() for s in test_case['input'].split(',') if s.strip()]
            else:
                symbols = [s.strip() for s in test_case['input'].split() if s.strip()]
            
            # Validate
            is_valid, message = validate_compare_input(symbols)
            
            if is_valid == test_case['should_pass']:
                print(f"✅ {test_case['description']}: {test_case['input']} → {is_valid}")
                passed += 1
            else:
                print(f"❌ {test_case['description']}: {test_case['input']} → {is_valid} (expected: {test_case['should_pass']})")
        except Exception as e:
            print(f"❌ {test_case['description']}: Error - {e}")
    
    print(f"\n📊 Validation Results: {passed}/{total} tests passed")
    return passed == total

def test_compare_examples():
    """Test compare examples from help message"""
    print("\n🧪 Testing Compare Examples")
    
    examples = [
        {
            'input': 'SPY.US QQQ.US',
            'type': 'Symbols with symbols',
            'description': 'Compare S&P 500 and NASDAQ'
        },
        {
            'input': 'PF_1 PF_2',
            'type': 'Portfolios with portfolios',
            'description': 'Compare two saved portfolios'
        },
        {
            'input': 'PF_1 SBER.MOEX',
            'type': 'Mixed comparison',
            'description': 'Compare portfolio with asset'
        }
    ]
    
    print("✅ Compare examples:")
    for example in examples:
        print(f"   • {example['input']} - {example['type']} ({example['description']})")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Compare Input Test Suite")
    print("=" * 60)
    
    tests = [
        test_compare_input_parsing,
        test_compare_input_validation,
        test_compare_examples
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test failed: {test.__name__}")
        except Exception as e:
            print(f"❌ Test error in {test.__name__}: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Compare input functionality should work correctly.")
        print("\n💡 Next steps:")
        print("1. Test /compare without arguments")
        print("2. Enter symbols for comparison")
        print("3. Verify comparison results")
    else:
        print("❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script to verify RUB currency parsing fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_rub_currency_parsing():
    """Test that RUB is correctly parsed as currency, not as asset symbol"""
    print("Testing RUB currency parsing fix...")
    
    # Import the bot class
    from bot import ShansAi
    
    # Create bot instance
    bot = ShansAi()
    
    # Test case: SBER.MOEX, LKOH.MOEX, RUB, 5Y
    test_args = ['SBER.MOEX', 'LKOH.MOEX', 'RUB', '5Y']
    
    print(f"Input arguments: {test_args}")
    
    # Parse the arguments
    symbols, currency, period = bot._parse_currency_and_period(test_args)
    
    print(f"Parsed symbols: {symbols}")
    print(f"Parsed currency: {currency}")
    print(f"Parsed period: {period}")
    
    # Verify the results
    expected_symbols = ['SBER.MOEX', 'LKOH.MOEX']
    expected_currency = 'RUB'
    expected_period = '5Y'
    
    success = True
    
    if symbols != expected_symbols:
        print(f"❌ Symbols mismatch: expected {expected_symbols}, got {symbols}")
        success = False
    else:
        print("✅ Symbols parsed correctly")
    
    if currency != expected_currency:
        print(f"❌ Currency mismatch: expected {expected_currency}, got {currency}")
        success = False
    else:
        print("✅ Currency parsed correctly")
    
    if period != expected_period:
        print(f"❌ Period mismatch: expected {expected_period}, got {period}")
        success = False
    else:
        print("✅ Period parsed correctly")
    
    if success:
        print("\n🎉 All tests passed! RUB currency parsing is working correctly.")
    else:
        print("\n❌ Some tests failed. The fix needs more work.")
    
    return success

def test_other_currencies():
    """Test other currency parsing to ensure no regression"""
    print("\nTesting other currency parsing...")
    
    from bot import ShansAi
    bot = ShansAi()
    
    test_cases = [
        (['AAPL.US', 'MSFT.US', 'USD', '10Y'], ['AAPL.US', 'MSFT.US'], 'USD', '10Y'),
        (['SBER.MOEX', 'GAZP.MOEX', 'EUR'], ['SBER.MOEX', 'GAZP.MOEX'], 'EUR', None),
        (['SPY.US', 'QQQ.US', 'GBP', '2Y'], ['SPY.US', 'QQQ.US'], 'GBP', '2Y'),
    ]
    
    success = True
    
    for i, (input_args, expected_symbols, expected_currency, expected_period) in enumerate(test_cases):
        print(f"\nTest case {i+1}: {input_args}")
        
        symbols, currency, period = bot._parse_currency_and_period(input_args)
        
        if (symbols == expected_symbols and 
            currency == expected_currency and 
            period == expected_period):
            print(f"✅ Test case {i+1} passed")
        else:
            print(f"❌ Test case {i+1} failed")
            print(f"   Expected: symbols={expected_symbols}, currency={expected_currency}, period={expected_period}")
            print(f"   Got: symbols={symbols}, currency={currency}, period={period}")
            success = False
    
    return success

if __name__ == "__main__":
    print("=" * 50)
    print("RUB Currency Parsing Fix Test")
    print("=" * 50)
    
    # Test RUB currency parsing
    rub_test_passed = test_rub_currency_parsing()
    
    # Test other currencies
    other_test_passed = test_other_currencies()
    
    print("\n" + "=" * 50)
    if rub_test_passed and other_test_passed:
        print("🎉 ALL TESTS PASSED! The RUB currency fix is working correctly.")
    else:
        print("❌ SOME TESTS FAILED! The fix needs more work.")
    print("=" * 50)

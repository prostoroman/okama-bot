#!/usr/bin/env python3
"""
Test script for currency and period parameters in /compare and /portfolio commands.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

def test_parse_currency_and_period():
    """Test the _parse_currency_and_period function"""
    bot = ShansAi()
    
    # Test cases
    test_cases = [
        # (input_args, expected_symbols, expected_currency, expected_period)
        (["SBER.MOEX", "LKOH.MOEX"], ["SBER.MOEX", "LKOH.MOEX"], None, None),
        (["SBER.MOEX", "LKOH.MOEX", "RUB"], ["SBER.MOEX", "LKOH.MOEX"], "RUB", None),
        (["SBER.MOEX", "LKOH.MOEX", "5Y"], ["SBER.MOEX", "LKOH.MOEX"], None, "5Y"),
        (["SBER.MOEX", "LKOH.MOEX", "RUB", "5Y"], ["SBER.MOEX", "LKOH.MOEX"], "RUB", "5Y"),
        (["SPY.US:0.5", "QQQ.US:0.5", "USD", "10Y"], ["SPY.US:0.5", "QQQ.US:0.5"], "USD", "10Y"),
        (["SBER.MOEX:0.4", "GAZP.MOEX:0.3", "LKOH.MOEX:0.3", "EUR", "2Y"], 
         ["SBER.MOEX:0.4", "GAZP.MOEX:0.3", "LKOH.MOEX:0.3"], "EUR", "2Y"),
        ([], [], None, None),
        (["RUB"], [], "RUB", None),
        (["5Y"], [], None, "5Y"),
        (["RUB", "5Y"], [], "RUB", "5Y"),
    ]
    
    print("Testing _parse_currency_and_period function...")
    
    for i, (input_args, expected_symbols, expected_currency, expected_period) in enumerate(test_cases):
        print(f"\nTest case {i+1}: {input_args}")
        
        symbols, currency, period = bot._parse_currency_and_period(input_args)
        
        print(f"  Expected: symbols={expected_symbols}, currency={expected_currency}, period={expected_period}")
        print(f"  Got:      symbols={symbols}, currency={currency}, period={period}")
        
        # Check results
        success = (symbols == expected_symbols and 
                  currency == expected_currency and 
                  period == expected_period)
        
        if success:
            print("  ✅ PASS")
        else:
            print("  ❌ FAIL")
            return False
    
    print("\n✅ All tests passed!")
    return True

def test_currency_validation():
    """Test currency validation"""
    bot = ShansAi()
    
    # Test valid currencies
    valid_currencies = ["USD", "RUB", "EUR", "GBP", "CNY", "HKD", "JPY"]
    
    print("\nTesting currency validation...")
    
    for currency in valid_currencies:
        symbols, parsed_currency, period = bot._parse_currency_and_period([currency])
        if parsed_currency == currency:
            print(f"  ✅ {currency} - valid")
        else:
            print(f"  ❌ {currency} - invalid")
            return False
    
    # Test invalid currency
    symbols, parsed_currency, period = bot._parse_currency_and_period(["INVALID"])
    if parsed_currency is None:
        print(f"  ✅ INVALID - correctly rejected")
    else:
        print(f"  ❌ INVALID - incorrectly accepted")
        return False
    
    return True

def test_period_validation():
    """Test period validation"""
    bot = ShansAi()
    
    # Test valid periods
    valid_periods = ["1Y", "2Y", "5Y", "10Y", "20Y"]
    
    print("\nTesting period validation...")
    
    for period in valid_periods:
        symbols, currency, parsed_period = bot._parse_currency_and_period([period])
        if parsed_period == period:
            print(f"  ✅ {period} - valid")
        else:
            print(f"  ❌ {period} - invalid")
            return False
    
    # Test invalid periods
    invalid_periods = ["1M", "5D", "Y5", "5", "INVALID"]
    
    for period in invalid_periods:
        symbols, currency, parsed_period = bot._parse_currency_and_period([period])
        if parsed_period is None:
            print(f"  ✅ {period} - correctly rejected")
        else:
            print(f"  ❌ {period} - incorrectly accepted")
            return False
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Currency and Period Parameters")
    print("=" * 60)
    
    success = True
    
    # Run tests
    success &= test_parse_currency_and_period()
    success &= test_currency_validation()
    success &= test_period_validation()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Currency and period parameters are working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    print("=" * 60)

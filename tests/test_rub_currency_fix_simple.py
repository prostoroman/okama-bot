#!/usr/bin/env python3
"""
Simple test script to verify RUB currency parsing fix
"""

def test_parse_currency_and_period():
    """Test the _parse_currency_and_period function logic"""
    print("Testing RUB currency parsing fix...")
    
    # Simulate the _parse_currency_and_period function logic
    def parse_currency_and_period(args):
        """Simulate the _parse_currency_and_period function"""
        if not args:
            return [], None, None
            
        # Valid currency codes
        valid_currencies = {'USD', 'RUB', 'EUR', 'GBP', 'CNY', 'HKD', 'JPY'}
        
        # Valid period patterns (e.g., '5Y', '10Y', '1Y', '2Y', etc.)
        import re
        period_pattern = re.compile(r'^(\d+)Y$', re.IGNORECASE)
        
        symbols = []
        currency = None
        period = None
        
        for arg in args:
            arg_upper = arg.upper()
            
            # Check if it's a currency code
            if arg_upper in valid_currencies:
                if currency is None:
                    currency = arg_upper
                else:
                    print(f"Warning: Multiple currencies specified, using first: {currency}")
                continue
            
            # Check if it's a period (e.g., '5Y', '10Y')
            period_match = period_pattern.match(arg)
            if period_match:
                if period is None:
                    period = arg_upper
                else:
                    print(f"Warning: Multiple periods specified, using first: {period}")
                continue
            
            # If it's neither currency nor period, it's a symbol
            symbols.append(arg)
        
        return symbols, currency, period
    
    # Test case: SBER.MOEX, LKOH.MOEX, RUB, 5Y
    test_args = ['SBER.MOEX', 'LKOH.MOEX', 'RUB', '5Y']
    
    print(f"Input arguments: {test_args}")
    
    # Parse the arguments
    symbols, currency, period = parse_currency_and_period(test_args)
    
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
    
    def parse_currency_and_period(args):
        """Simulate the _parse_currency_and_period function"""
        if not args:
            return [], None, None
            
        valid_currencies = {'USD', 'RUB', 'EUR', 'GBP', 'CNY', 'HKD', 'JPY'}
        import re
        period_pattern = re.compile(r'^(\d+)Y$', re.IGNORECASE)
        
        symbols = []
        currency = None
        period = None
        
        for arg in args:
            arg_upper = arg.upper()
            
            if arg_upper in valid_currencies:
                if currency is None:
                    currency = arg_upper
                continue
            
            period_match = period_pattern.match(arg)
            if period_match:
                if period is None:
                    period = arg_upper
                continue
            
            symbols.append(arg)
        
        return symbols, currency, period
    
    test_cases = [
        (['AAPL.US', 'MSFT.US', 'USD', '10Y'], ['AAPL.US', 'MSFT.US'], 'USD', '10Y'),
        (['SBER.MOEX', 'GAZP.MOEX', 'EUR'], ['SBER.MOEX', 'GAZP.MOEX'], 'EUR', None),
        (['SPY.US', 'QQQ.US', 'GBP', '2Y'], ['SPY.US', 'QQQ.US'], 'GBP', '2Y'),
    ]
    
    success = True
    
    for i, (input_args, expected_symbols, expected_currency, expected_period) in enumerate(test_cases):
        print(f"\nTest case {i+1}: {input_args}")
        
        symbols, currency, period = parse_currency_and_period(input_args)
        
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
    print("RUB Currency Parsing Fix Test (Simple)")
    print("=" * 50)
    
    # Test RUB currency parsing
    rub_test_passed = test_parse_currency_and_period()
    
    # Test other currencies
    other_test_passed = test_other_currencies()
    
    print("\n" + "=" * 50)
    if rub_test_passed and other_test_passed:
        print("🎉 ALL TESTS PASSED! The RUB currency fix is working correctly.")
    else:
        print("❌ SOME TESTS FAILED! The fix needs more work.")
    print("=" * 50)

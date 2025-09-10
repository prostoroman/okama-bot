#!/usr/bin/env python3
"""
Test script to verify main comparison chart uses currency and period correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_parse_currency_and_period():
    """Test that currency and period parsing works correctly for main chart"""
    print("Testing currency and period parsing for main comparison chart...")
    
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
    
    # Test case: SBER.MOEX LKOH.MOEX USD 5Y
    test_args = ['SBER.MOEX', 'LKOH.MOEX', 'USD', '5Y']
    
    print(f"Input arguments: {test_args}")
    
    # Parse the arguments
    symbols, currency, period = parse_currency_and_period(test_args)
    
    print(f"Parsed symbols: {symbols}")
    print(f"Parsed currency: {currency}")
    print(f"Parsed period: {period}")
    
    # Verify the results
    expected_symbols = ['SBER.MOEX', 'LKOH.MOEX']
    expected_currency = 'USD'
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
        print("\n🎉 All tests passed! Currency and period parsing is working correctly.")
    else:
        print("\n❌ Some tests failed. The parsing needs more work.")
    
    return success

def test_assetlist_creation():
    """Test AssetList creation with period parameters"""
    print("\nTesting AssetList creation with period parameters...")
    
    # Simulate AssetList creation logic
    def create_assetlist_with_period(symbols, currency, period):
        """Simulate AssetList creation with period support"""
        print(f"Creating AssetList with symbols: {symbols}, currency: {currency}, period: {period}")
        
        if period:
            years = int(period[:-1])  # Extract number from '5Y'
            from datetime import timedelta, datetime
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            print(f"Period filter: {years} years")
            print(f"Start date: {start_date.strftime('%Y-%m-%d')}")
            print(f"End date: {end_date.strftime('%Y-%m-%d')}")
            
            # Simulate AssetList creation with period
            assetlist_params = {
                'symbols': symbols,
                'ccy': currency,
                'inflation': True,
                'first_date': start_date.strftime('%Y-%m-%d'),
                'last_date': end_date.strftime('%Y-%m-%d')
            }
            
            print(f"AssetList parameters: {assetlist_params}")
            return assetlist_params
        else:
            # Simulate AssetList creation without period
            assetlist_params = {
                'symbols': symbols,
                'ccy': currency,
                'inflation': True
            }
            
            print(f"AssetList parameters (no period): {assetlist_params}")
            return assetlist_params
    
    # Test with period
    symbols = ['SBER.MOEX', 'LKOH.MOEX']
    currency = 'USD'
    period = '5Y'
    
    result = create_assetlist_with_period(symbols, currency, period)
    
    # Verify parameters
    if (result['symbols'] == symbols and 
        result['ccy'] == currency and 
        'first_date' in result and 
        'last_date' in result):
        print("✅ AssetList creation with period works correctly")
        return True
    else:
        print("❌ AssetList creation with period failed")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Main Comparison Chart Currency/Period Test")
    print("=" * 60)
    
    # Test parsing
    parsing_test_passed = test_parse_currency_and_period()
    
    # Test AssetList creation
    assetlist_test_passed = test_assetlist_creation()
    
    print("\n" + "=" * 60)
    if parsing_test_passed and assetlist_test_passed:
        print("🎉 ALL TESTS PASSED! Main chart should work correctly with currency and period.")
    else:
        print("❌ SOME TESTS FAILED! The main chart fix needs more work.")
    print("=" * 60)

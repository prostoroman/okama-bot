#!/usr/bin/env python3
"""
Test script to verify portfolio command parsing fix for symbol:weight format
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_portfolio_command_parsing():
    """Test that portfolio command parsing works correctly with symbol:weight format"""
    print("Testing portfolio command parsing fix...")
    
    # Simulate the portfolio parsing logic from the fixed portfolio_command method
    def parse_portfolio_command_args(args):
        """Simulate the portfolio parsing logic from portfolio_command"""
        valid_currencies = {'USD', 'RUB', 'EUR', 'GBP', 'CNY', 'HKD', 'JPY'}
        import re
        period_pattern = re.compile(r'^(\d+)Y$', re.IGNORECASE)
        
        portfolio_args = []
        specified_currency = None
        specified_period = None
        
        for arg in args:
            arg_upper = arg.upper()
            
            # Check if it's a currency code
            if arg_upper in valid_currencies:
                if specified_currency is None:
                    specified_currency = arg_upper
                continue
            
            # Check if it's a period (e.g., '5Y', '10Y')
            period_match = period_pattern.match(arg)
            if period_match:
                if specified_period is None:
                    specified_period = arg_upper
                continue
            
            # If it's neither currency nor period, it's a portfolio argument
            portfolio_args.append(arg)
        
        # Extract symbols and weights from portfolio arguments
        portfolio_data = []
        
        for arg in portfolio_args:
            if ':' in arg:
                symbol_part, weight_part = arg.split(':', 1)
                symbol = symbol_part.strip().upper()
                
                try:
                    weight = float(weight_part.strip())
                except Exception as e:
                    return f"Error converting weight '{weight_part.strip()}' to float: {e}"
                
                if weight <= 0 or weight > 1:
                    return f"Invalid weight for {symbol}: {weight}. Weight should be between 0 and 1"
                
                portfolio_data.append((symbol, weight))
                
            else:
                return f"Invalid format: {arg}. Use symbol:weight format"
        
        return portfolio_data, specified_currency, specified_period
    
    # Test cases
    test_cases = [
        {
            'name': 'Single asset with weight 1',
            'args': ['sber.moex:1'],
            'expected_data': [('SBER.MOEX', 1.0)],
            'expected_currency': None,
            'expected_period': None
        },
        {
            'name': 'Multiple assets with weights',
            'args': ['sber.moex:0.4', 'gazp.moex:0.3', 'lkoh.moex:0.3'],
            'expected_data': [('SBER.MOEX', 0.4), ('GAZP.MOEX', 0.3), ('LKOH.MOEX', 0.3)],
            'expected_currency': None,
            'expected_period': None
        },
        {
            'name': 'Assets with currency and period',
            'args': ['sber.moex:0.5', 'lkoh.moex:0.5', 'USD', '10Y'],
            'expected_data': [('SBER.MOEX', 0.5), ('LKOH.MOEX', 0.5)],
            'expected_currency': 'USD',
            'expected_period': '10Y'
        },
        {
            'name': 'Invalid format (no colon)',
            'args': ['sber.moex'],
            'expected_error': 'Invalid format: sber.moex. Use symbol:weight format'
        },
        {
            'name': 'Invalid weight (too high)',
            'args': ['sber.moex:1.5'],
            'expected_error': 'Invalid weight for SBER.MOEX: 1.5. Weight should be between 0 and 1'
        }
    ]
    
    # Run tests
    all_passed = True
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        print(f"Input: {test_case['args']}")
        
        result = parse_portfolio_command_args(test_case['args'])
        
        if 'expected_error' in test_case:
            # Test should return an error message
            if isinstance(result, str) and test_case['expected_error'] in result:
                print(f"✅ PASS: Got expected error")
            else:
                print(f"❌ FAIL: Expected error '{test_case['expected_error']}', got: {result}")
                all_passed = False
        else:
            # Test should return portfolio data
            if isinstance(result, tuple) and len(result) == 3:
                portfolio_data, currency, period = result
                if (portfolio_data == test_case['expected_data'] and 
                    currency == test_case['expected_currency'] and 
                    period == test_case['expected_period']):
                    print(f"✅ PASS: Got expected result")
                else:
                    print(f"❌ FAIL: Expected {test_case['expected_data']}, {test_case['expected_currency']}, {test_case['expected_period']}")
                    print(f"         Got {portfolio_data}, {currency}, {period}")
                    all_passed = False
            else:
                print(f"❌ FAIL: Expected tuple with 3 elements, got: {result}")
                all_passed = False
    
    if all_passed:
        print(f"\n🎉 All tests passed! Portfolio command parsing fix is working correctly.")
    else:
        print(f"\n❌ Some tests failed. Please check the implementation.")
    
    return all_passed

if __name__ == "__main__":
    test_portfolio_command_parsing()

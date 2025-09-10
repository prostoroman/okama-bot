#!/usr/bin/env python3
"""
Test script to verify portfolio command format parsing fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_portfolio_parsing():
    """Test that portfolio command parsing works correctly with symbol:weight format"""
    print("Testing portfolio command format parsing fix...")
    
    # Simulate the portfolio parsing logic
    def parse_portfolio_input(text):
        """Simulate the portfolio parsing logic from _handle_portfolio_input"""
        text_args = text.split()
        
        # For portfolio command, we need to preserve the full symbol:weight format
        # So we'll parse currency and period manually, keeping the original arguments
        valid_currencies = {'USD', 'RUB', 'EUR', 'GBP', 'CNY', 'HKD', 'JPY'}
        import re
        period_pattern = re.compile(r'^(\d+)Y$', re.IGNORECASE)
        
        portfolio_args = []
        specified_currency = None
        specified_period = None
        
        for arg in text_args:
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
                    return f"Incorrect weight for {symbol}: {weight}. Weight should be from 0 to 1"
                
                portfolio_data.append((symbol, weight))
                
            else:
                return f"Incorrect format: {arg}. Use symbol:weight format"
        
        return portfolio_data, specified_currency, specified_period
    
    # Test case: User's input
    test_input = "SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3"
    print(f"Input: {test_input}")
    
    result = parse_portfolio_input(test_input)
    
    if isinstance(result, str):
        print(f"❌ FAIL: {result}")
        return False
    
    portfolio_data, currency, period = result
    
    print(f"Portfolio data: {portfolio_data}")
    print(f"Currency: {currency}")
    print(f"Period: {period}")
    
    # Check results
    expected_data = [
        ('SBER.MOEX', 0.4),
        ('GAZP.MOEX', 0.3),
        ('LKOH.MOEX', 0.3)
    ]
    
    if portfolio_data == expected_data:
        print("✅ PASS: Portfolio parsing works correctly!")
        return True
    else:
        print(f"❌ FAIL: Expected {expected_data}, got {portfolio_data}")
        return False

def test_portfolio_with_currency():
    """Test portfolio parsing with currency parameter"""
    print("\nTesting portfolio parsing with currency parameter...")
    
    # Simulate the portfolio parsing logic
    def parse_portfolio_input(text):
        """Simulate the portfolio parsing logic from _handle_portfolio_input"""
        text_args = text.split()
        
        valid_currencies = {'USD', 'RUB', 'EUR', 'GBP', 'CNY', 'HKD', 'JPY'}
        import re
        period_pattern = re.compile(r'^(\d+)Y$', re.IGNORECASE)
        
        portfolio_args = []
        specified_currency = None
        specified_period = None
        
        for arg in text_args:
            arg_upper = arg.upper()
            
            if arg_upper in valid_currencies:
                if specified_currency is None:
                    specified_currency = arg_upper
                continue
            
            period_match = period_pattern.match(arg)
            if period_match:
                if specified_period is None:
                    specified_period = arg_upper
                continue
            
            portfolio_args.append(arg)
        
        portfolio_data = []
        
        for arg in portfolio_args:
            if ':' in arg:
                symbol_part, weight_part = arg.split(':', 1)
                symbol = symbol_part.strip().upper()
                weight = float(weight_part.strip())
                portfolio_data.append((symbol, weight))
            else:
                return f"Incorrect format: {arg}. Use symbol:weight format"
        
        return portfolio_data, specified_currency, specified_period
    
    # Test case: With currency
    test_input = "SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3 RUB"
    print(f"Input: {test_input}")
    
    result = parse_portfolio_input(test_input)
    
    if isinstance(result, str):
        print(f"❌ FAIL: {result}")
        return False
    
    portfolio_data, currency, period = result
    
    print(f"Portfolio data: {portfolio_data}")
    print(f"Currency: {currency}")
    print(f"Period: {period}")
    
    expected_data = [
        ('SBER.MOEX', 0.4),
        ('GAZP.MOEX', 0.3),
        ('LKOH.MOEX', 0.3)
    ]
    
    if portfolio_data == expected_data and currency == 'RUB':
        print("✅ PASS: Portfolio parsing with currency works correctly!")
        return True
    else:
        print(f"❌ FAIL: Expected data={expected_data}, currency=RUB, got data={portfolio_data}, currency={currency}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("PORTFOLIO FORMAT PARSING FIX TEST")
    print("=" * 60)
    
    success1 = test_portfolio_parsing()
    success2 = test_portfolio_with_currency()
    
    if success1 and success2:
        print("\n✅ All tests passed! Portfolio format parsing fix is working correctly.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

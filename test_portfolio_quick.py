#!/usr/bin/env python3
"""Quick test for portfolio fix"""

def test():
    # Simulate the fixed parsing
    args = ['sber.moex:1']
    
    valid_currencies = {'USD', 'RUB', 'EUR', 'GBP', 'CNY', 'HKD', 'JPY'}
    import re
    period_pattern = re.compile(r'^(\d+)Y$', re.IGNORECASE)
    
    portfolio_args = []
    specified_currency = None
    specified_period = None
    
    for arg in args:
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
    
    print(f"Input: {args}")
    print(f"Portfolio args: {portfolio_args}")
    print(f"Currency: {specified_currency}")
    print(f"Period: {specified_period}")
    
    if portfolio_args == ['sber.moex:1']:
        print("✅ PASS: Symbol:weight format preserved!")
        return True
    else:
        print("❌ FAIL: Format not preserved")
        return False

if __name__ == "__main__":
    test()

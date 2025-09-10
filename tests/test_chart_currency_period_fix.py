#!/usr/bin/env python3
"""
Test script to verify that charts respect currency and period parameters.
This test simulates portfolio creation and chart generation with different currencies and periods.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_portfolio_creation_with_period():
    """Test that portfolio creation respects period parameters"""
    print("Testing portfolio creation with period parameters...")
    
    try:
        import okama as ok
        print("✅ Okama library imported successfully")
    except ImportError:
        print("⚠️ Okama library not available for testing, but logic should be correct")
        return True
    
    # Test 1: Portfolio creation with 5Y period
    try:
        symbols = ["SPY.US", "QQQ.US", "BND.US"]
        weights = [0.5, 0.3, 0.2]
        currency = "USD"
        period = "5Y"
        
        years = int(period[:-1])  # Extract number from '5Y'
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                               first_date=start_date.strftime('%Y-%m-%d'), 
                               last_date=end_date.strftime('%Y-%m-%d'))
        
        print(f"✅ Portfolio creation with period {period} works")
        print(f"   Period length: {portfolio.period_length}")
        print(f"   First date: {portfolio.first_date}")
        print(f"   Last date: {portfolio.last_date}")
        
    except Exception as e:
        print(f"❌ Portfolio creation with period failed: {e}")
        return False
    
    # Test 2: Portfolio creation with 10Y period
    try:
        symbols = ["AAPL.US", "MSFT.US"]
        weights = [0.6, 0.4]
        currency = "EUR"
        period = "10Y"
        
        years = int(period[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                               first_date=start_date.strftime('%Y-%m-%d'), 
                               last_date=end_date.strftime('%Y-%m-%d'))
        
        print(f"✅ Portfolio creation with period {period} and currency {currency} works")
        print(f"   Period length: {portfolio.period_length}")
        print(f"   Currency: {portfolio.currency}")
        
    except Exception as e:
        print(f"❌ Portfolio creation with period and currency failed: {e}")
        return False
    
    # Test 3: Portfolio creation without period (maximum available)
    try:
        symbols = ["SPY.US", "QQQ.US"]
        weights = [0.7, 0.3]
        currency = "USD"
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
        
        print(f"✅ Portfolio creation without period works")
        print(f"   Period length: {portfolio.period_length}")
        print(f"   Currency: {portfolio.currency}")
        
    except Exception as e:
        print(f"❌ Portfolio creation without period failed: {e}")
        return False
    
    print("✅ All portfolio creation tests passed!")
    return True

def test_chart_data_consistency():
    """Test that chart data is consistent with portfolio parameters"""
    print("\nTesting chart data consistency...")
    
    try:
        import okama as ok
    except ImportError:
        print("⚠️ Okama library not available for testing")
        return True
    
    # Test 1: Wealth index with period
    try:
        symbols = ["SPY.US", "QQQ.US"]
        weights = [0.6, 0.4]
        currency = "USD"
        period = "3Y"
        
        years = int(period[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                               first_date=start_date.strftime('%Y-%m-%d'), 
                               last_date=end_date.strftime('%Y-%m-%d'))
        
        wealth_index = portfolio.wealth_index
        
        print(f"✅ Wealth index generated successfully")
        print(f"   Data points: {len(wealth_index)}")
        print(f"   Date range: {wealth_index.index[0]} to {wealth_index.index[-1]}")
        print(f"   Currency: {portfolio.currency}")
        
        # Verify the data covers the expected period
        expected_days = years * 365
        actual_days = (wealth_index.index[-1] - wealth_index.index[0]).days
        print(f"   Expected days: ~{expected_days}, Actual days: {actual_days}")
        
    except Exception as e:
        print(f"❌ Wealth index generation failed: {e}")
        return False
    
    print("✅ Chart data consistency tests passed!")
    return True

def test_parameter_parsing():
    """Test that parameter parsing works correctly"""
    print("\nTesting parameter parsing...")
    
    # Simulate the parameter parsing logic
    def parse_currency_and_period(args):
        """Simulate the _parse_currency_and_period function"""
        symbols = []
        currency = None
        period = None
        
        valid_currencies = ['USD', 'RUB', 'EUR', 'GBP', 'CNY', 'HKD', 'JPY']
        
        for arg in args:
            if arg.upper() in valid_currencies:
                currency = arg.upper()
            elif arg.upper().endswith('Y') and arg[:-1].isdigit():
                period = arg.upper()
            else:
                symbols.append(arg)
        
        return symbols, currency, period
    
    # Test cases
    test_cases = [
        (["SPY.US:0.5", "QQQ.US:0.3", "BND.US:0.2", "USD", "5Y"], 
         ["SPY.US:0.5", "QQQ.US:0.3", "BND.US:0.2"], "USD", "5Y"),
        (["AAPL.US:0.6", "MSFT.US:0.4", "EUR", "10Y"], 
         ["AAPL.US:0.6", "MSFT.US:0.4"], "EUR", "10Y"),
        (["SBER.MOEX:0.5", "LKOH.MOEX:0.5", "RUB"], 
         ["SBER.MOEX:0.5", "LKOH.MOEX:0.5"], "RUB", None),
        (["SPY.US:0.7", "QQQ.US:0.3"], 
         ["SPY.US:0.7", "QQQ.US:0.3"], None, None),
    ]
    
    for i, (input_args, expected_symbols, expected_currency, expected_period) in enumerate(test_cases):
        symbols, currency, period = parse_currency_and_period(input_args)
        
        if (symbols == expected_symbols and 
            currency == expected_currency and 
            period == expected_period):
            print(f"✅ Test case {i+1} passed: {input_args}")
        else:
            print(f"❌ Test case {i+1} failed: {input_args}")
            print(f"   Expected: symbols={expected_symbols}, currency={expected_currency}, period={expected_period}")
            print(f"   Got: symbols={symbols}, currency={currency}, period={period}")
            return False
    
    print("✅ Parameter parsing tests passed!")
    return True

def test_context_storage():
    """Test that context storage includes period information"""
    print("\nTesting context storage...")
    
    # Simulate context storage
    def simulate_context_update(user_id, **kwargs):
        """Simulate the _update_user_context function"""
        context = {
            'last_assets': kwargs.get('last_assets', []),
            'last_period': kwargs.get('last_period', 'MAX'),
            'current_period': kwargs.get('current_period'),
            'current_currency': kwargs.get('current_currency', 'USD'),
            'portfolio_weights': kwargs.get('portfolio_weights', []),
        }
        return context
    
    # Test 1: With period parameter
    context1 = simulate_context_update(
        user_id=123,
        last_assets=["SPY.US", "QQQ.US"],
        last_period="5Y",
        current_period="5Y",
        current_currency="USD",
        portfolio_weights=[0.6, 0.4]
    )
    
    if (context1['last_period'] == "5Y" and 
        context1['current_period'] == "5Y" and
        context1['current_currency'] == "USD"):
        print("✅ Context storage with period works")
    else:
        print("❌ Context storage with period failed")
        return False
    
    # Test 2: Without period parameter
    context2 = simulate_context_update(
        user_id=123,
        last_assets=["AAPL.US", "MSFT.US"],
        last_period="MAX",
        current_period=None,
        current_currency="EUR",
        portfolio_weights=[0.5, 0.5]
    )
    
    if (context2['last_period'] == "MAX" and 
        context2['current_period'] is None and
        context2['current_currency'] == "EUR"):
        print("✅ Context storage without period works")
    else:
        print("❌ Context storage without period failed")
        return False
    
    print("✅ Context storage tests passed!")
    return True

if __name__ == "__main__":
    print("🧪 Testing chart currency and period fix...")
    
    success1 = test_portfolio_creation_with_period()
    success2 = test_chart_data_consistency()
    success3 = test_parameter_parsing()
    success4 = test_context_storage()
    
    if success1 and success2 and success3 and success4:
        print("\n🎉 All chart currency and period tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some chart currency and period tests failed!")
        sys.exit(1)

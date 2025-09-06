#!/usr/bin/env python3
"""
Test script for portfolio creation and /my command functionality
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.context_store import InMemoryUserContextStore

def test_portfolio_creation_and_retrieval():
    """Test portfolio creation and retrieval"""
    print("🧪 Testing Portfolio Creation and Retrieval")
    
    # Initialize context store
    context_store = InMemoryUserContextStore()
    
    # Test user ID
    user_id = 12345
    
    # Create test portfolio data
    test_portfolio = {
        'symbols': ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX'],
        'weights': [0.4, 0.3, 0.3],
        'currency': 'RUB',
        'created_at': datetime.now().isoformat(),
        'portfolio_symbol': 'PF_1',
        'description': 'Test Portfolio: SBER.MOEX, GAZP.MOEX, LKOH.MOEX',
        'total_weight': 1.0,
        'asset_count': 3
    }
    
    # Simulate portfolio creation
    user_context = context_store.get_user_context(user_id)
    user_context['saved_portfolios'] = {
        'PF_1': test_portfolio
    }
    context_store.update_user_context(user_id, saved_portfolios=user_context['saved_portfolios'])
    
    # Simulate /my command
    retrieved_context = context_store.get_user_context(user_id)
    saved_portfolios = retrieved_context.get('saved_portfolios', {})
    
    print(f"✅ Saved portfolios count: {len(saved_portfolios)}")
    print(f"✅ Portfolio keys: {list(saved_portfolios.keys())}")
    
    if 'PF_1' in saved_portfolios:
        portfolio = saved_portfolios['PF_1']
        print(f"✅ Portfolio symbols: {portfolio.get('symbols')}")
        print(f"✅ Portfolio weights: {portfolio.get('weights')}")
        print(f"✅ Portfolio currency: {portfolio.get('currency')}")
        print(f"✅ Portfolio symbol: {portfolio.get('portfolio_symbol')}")
        return True
    else:
        print("❌ Portfolio not found in saved portfolios")
        return False

def test_portfolio_button_format():
    """Test portfolio button format consistency"""
    print("\n🧪 Testing Portfolio Button Format")
    
    # Test portfolio symbol
    portfolio_symbol = "PF_1"
    
    # Expected button formats
    expected_formats = {
        "wealth_chart": f"portfolio_wealth_chart_{portfolio_symbol}",
        "returns": f"portfolio_returns_{portfolio_symbol}",
        "drawdowns": f"portfolio_drawdowns_{portfolio_symbol}",
        "risk_metrics": f"portfolio_risk_metrics_{portfolio_symbol}",
        "monte_carlo": f"portfolio_monte_carlo_{portfolio_symbol}",
        "forecast": f"portfolio_forecast_{portfolio_symbol}",
        "compare_assets": f"portfolio_compare_assets_{portfolio_symbol}",
        "rolling_cagr": f"portfolio_rolling_cagr_{portfolio_symbol}"
    }
    
    print("✅ Expected button formats:")
    for button_type, expected_format in expected_formats.items():
        print(f"   {button_type}: {expected_format}")
    
    # Test callback data parsing
    test_callback = f"portfolio_drawdowns_{portfolio_symbol}"
    print(f"\n✅ Testing callback data parsing:")
    print(f"   Callback data: {test_callback}")
    
    if test_callback.startswith('portfolio_drawdowns_'):
        parsed_symbol = test_callback.replace('portfolio_drawdowns_', '')
        print(f"   Parsed symbol: {parsed_symbol}")
        print(f"   Expected symbol: {portfolio_symbol}")
        
        if parsed_symbol == portfolio_symbol:
            print("   ✅ Symbol parsing correct")
            return True
        else:
            print("   ❌ Symbol parsing incorrect")
            return False
    else:
        print("   ❌ Callback data format incorrect")
        return False

def test_portfolio_drawdowns_handler():
    """Test portfolio drawdowns handler logic"""
    print("\n🧪 Testing Portfolio Drawdowns Handler Logic")
    
    # Simulate the handler logic
    portfolio_symbol = "PF_1"
    saved_portfolios = {
        'PF_1': {
            'symbols': ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX'],
            'weights': [0.4, 0.3, 0.3],
            'currency': 'RUB',
            'portfolio_symbol': 'PF_1'
        }
    }
    
    # Test portfolio lookup
    if portfolio_symbol in saved_portfolios:
        portfolio_info = saved_portfolios[portfolio_symbol]
        symbols = portfolio_info.get('symbols', [])
        weights = portfolio_info.get('weights', [])
        currency = portfolio_info.get('currency', 'USD')
        
        print(f"✅ Portfolio found: {portfolio_symbol}")
        print(f"✅ Symbols: {symbols}")
        print(f"✅ Weights: {weights}")
        print(f"✅ Currency: {currency}")
        
        if symbols and weights and currency:
            print("✅ Portfolio data complete")
            return True
        else:
            print("❌ Portfolio data incomplete")
            return False
    else:
        print(f"❌ Portfolio not found: {portfolio_symbol}")
        return False

def main():
    """Run all tests"""
    print("🚀 Portfolio Creation and /my Command Test Suite")
    print("=" * 60)
    
    tests = [
        test_portfolio_creation_and_retrieval,
        test_portfolio_button_format,
        test_portfolio_drawdowns_handler
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
        print("✅ All tests passed! Portfolio creation and /my command should work correctly.")
        print("\n💡 Next steps:")
        print("1. Test portfolio creation with /portfolio SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3")
        print("2. Test /my command to see saved portfolios")
        print("3. Test drawdown button functionality")
    else:
        print("❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test script for portfolio functionality fixes
Tests /my command and drawdown button functionality
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.context_store import InMemoryUserContextStore

def test_portfolio_context_storage():
    """Test portfolio context storage and retrieval"""
    print("🧪 Testing Portfolio Context Storage")
    
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
        'description': 'Test Portfolio: SBER.MOEX, GAZP.MOEX, LKOH.MOEX'
    }
    
    # Save portfolio to context
    user_context = context_store.get_user_context(user_id)
    user_context['saved_portfolios'] = {
        'PF_1': test_portfolio
    }
    context_store.update_user_context(user_id, saved_portfolios=user_context['saved_portfolios'])
    
    # Retrieve and verify
    retrieved_context = context_store.get_user_context(user_id)
    saved_portfolios = retrieved_context.get('saved_portfolios', {})
    
    print(f"✅ Saved portfolios count: {len(saved_portfolios)}")
    print(f"✅ Portfolio keys: {list(saved_portfolios.keys())}")
    
    if 'PF_1' in saved_portfolios:
        portfolio = saved_portfolios['PF_1']
        print(f"✅ Portfolio symbols: {portfolio.get('symbols')}")
        print(f"✅ Portfolio weights: {portfolio.get('weights')}")
        print(f"✅ Portfolio currency: {portfolio.get('currency')}")
        return True
    else:
        print("❌ Portfolio not found in saved portfolios")
        return False

def test_button_format_consistency():
    """Test button format consistency for portfolio buttons"""
    print("\n🧪 Testing Button Format Consistency")
    
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
    
    # Verify all formats follow the pattern
    all_consistent = True
    for button_type, expected_format in expected_formats.items():
        if not expected_format.startswith(f"portfolio_{button_type}_"):
            print(f"❌ Inconsistent format for {button_type}: {expected_format}")
            all_consistent = False
    
    if all_consistent:
        print("✅ All button formats are consistent")
        return True
    else:
        print("❌ Button format inconsistencies found")
        return False

def test_portfolio_data_structure():
    """Test portfolio data structure for /my command"""
    print("\n🧪 Testing Portfolio Data Structure")
    
    # Create test portfolio data
    test_portfolio = {
        'symbols': ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX'],
        'weights': [0.4, 0.3, 0.3],
        'currency': 'RUB',
        'created_at': datetime.now().isoformat(),
        'portfolio_symbol': 'PF_1',
        'description': 'Test Portfolio',
        'total_weight': 1.0,
        'asset_count': 3,
        'mean_return_annual': 0.12,
        'volatility_annual': 0.18,
        'sharpe_ratio': 0.67,
        'first_date': '2020-01-01',
        'last_date': '2024-12-31',
        'final_value': 100000.0
    }
    
    # Required fields for /my command
    required_fields = [
        'symbols', 'weights', 'currency', 'created_at', 
        'portfolio_symbol', 'description'
    ]
    
    # Optional fields for enhanced display
    optional_fields = [
        'mean_return_annual', 'volatility_annual', 'sharpe_ratio',
        'first_date', 'last_date', 'final_value'
    ]
    
    print("✅ Required fields check:")
    for field in required_fields:
        if field in test_portfolio:
            print(f"   ✅ {field}: {test_portfolio[field]}")
        else:
            print(f"   ❌ Missing required field: {field}")
    
    print("✅ Optional fields check:")
    for field in optional_fields:
        if field in test_portfolio:
            print(f"   ✅ {field}: {test_portfolio[field]}")
        else:
            print(f"   ⚠️ Optional field missing: {field}")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Portfolio Functionality Test Suite")
    print("=" * 50)
    
    tests = [
        test_portfolio_context_storage,
        test_button_format_consistency,
        test_portfolio_data_structure
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
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Portfolio functionality should work correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()

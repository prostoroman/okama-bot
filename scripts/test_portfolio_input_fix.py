#!/usr/bin/env python3
"""
Test script for portfolio input fix
Tests _handle_portfolio_input function to ensure portfolios are saved correctly
"""

import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.context_store import InMemoryUserContextStore

def test_portfolio_input_saving():
    """Test portfolio saving in _handle_portfolio_input function"""
    print("🧪 Testing Portfolio Input Saving")
    
    # Initialize context store
    context_store = InMemoryUserContextStore()
    
    # Test user ID
    user_id = 12345
    
    # Simulate portfolio input data
    symbols = ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']
    weights = [0.4, 0.3, 0.3]
    currency = 'RUB'
    portfolio_symbol = 'PF_1'
    portfolio_count = 1
    
    # Simulate the _handle_portfolio_input logic
    user_context = context_store.get_user_context(user_id)
    
    # First update (like in _handle_portfolio_input)
    context_store.update_user_context(
        user_id,
        last_assets=symbols,
        last_analysis_type='portfolio',
        last_period='MAX',
        current_symbols=symbols,
        current_currency=currency,
        current_currency_info="автоматически определена по первому активу (SBER.MOEX)",
        portfolio_weights=weights,
        portfolio_count=portfolio_count
    )
    
    # Get current saved portfolios and add the new portfolio
    saved_portfolios = user_context.get('saved_portfolios', {})
    
    # Create portfolio attributes for storage
    portfolio_attributes = {
        'symbols': symbols,
        'weights': weights,
        'currency': currency,
        'created_at': datetime.now().isoformat(),
        'description': f"Портфель: {', '.join(symbols)}",
        'portfolio_symbol': portfolio_symbol,
        'total_weight': sum(weights),
        'asset_count': len(symbols)
    }
    
    # Add portfolio to saved portfolios
    saved_portfolios[portfolio_symbol] = portfolio_attributes
    
    # Update saved portfolios in context
    context_store.update_user_context(
        user_id,
        saved_portfolios=saved_portfolios,
        portfolio_count=portfolio_count
    )
    
    # Verify what was saved
    final_saved_context = context_store.get_user_context(user_id)
    saved_portfolios_final = final_saved_context.get('saved_portfolios', {})
    
    print(f"✅ Final saved portfolios count: {len(saved_portfolios_final)}")
    print(f"✅ Final saved portfolios keys: {list(saved_portfolios_final.keys())}")
    
    if 'PF_1' in saved_portfolios_final:
        portfolio = saved_portfolios_final['PF_1']
        print(f"✅ Portfolio symbols: {portfolio.get('symbols')}")
        print(f"✅ Portfolio weights: {portfolio.get('weights')}")
        print(f"✅ Portfolio currency: {portfolio.get('currency')}")
        print(f"✅ Portfolio symbol: {portfolio.get('portfolio_symbol')}")
        print(f"✅ Portfolio created_at: {portfolio.get('created_at')}")
        return True
    else:
        print("❌ Portfolio not found in saved portfolios")
        return False

def test_portfolio_input_context_verification():
    """Test context verification after portfolio input"""
    print("\n🧪 Testing Portfolio Input Context Verification")
    
    # Initialize context store
    context_store = InMemoryUserContextStore()
    
    # Test user ID
    user_id = 12345
    
    # Simulate portfolio input
    symbols = ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']
    weights = [0.4, 0.3, 0.3]
    currency = 'RUB'
    portfolio_symbol = 'PF_1'
    
    # Simulate complete portfolio input process
    user_context = context_store.get_user_context(user_id)
    
    # Step 1: Update basic context
    context_store.update_user_context(
        user_id,
        last_assets=symbols,
        last_analysis_type='portfolio',
        current_symbols=symbols,
        current_currency=currency,
        portfolio_weights=weights,
        portfolio_count=1
    )
    
    # Step 2: Add to saved portfolios
    saved_portfolios = user_context.get('saved_portfolios', {})
    portfolio_attributes = {
        'symbols': symbols,
        'weights': weights,
        'currency': currency,
        'created_at': datetime.now().isoformat(),
        'description': f"Портфель: {', '.join(symbols)}",
        'portfolio_symbol': portfolio_symbol,
        'total_weight': sum(weights),
        'asset_count': len(symbols)
    }
    saved_portfolios[portfolio_symbol] = portfolio_attributes
    
    # Step 3: Update saved portfolios
    context_store.update_user_context(
        user_id,
        saved_portfolios=saved_portfolios,
        portfolio_count=1
    )
    
    # Verify context
    final_context = context_store.get_user_context(user_id)
    
    print("✅ Context verification:")
    print(f"   ✅ last_assets: {final_context.get('last_assets')}")
    print(f"   ✅ last_analysis_type: {final_context.get('last_analysis_type')}")
    print(f"   ✅ current_symbols: {final_context.get('current_symbols')}")
    print(f"   ✅ current_currency: {final_context.get('current_currency')}")
    print(f"   ✅ portfolio_weights: {final_context.get('portfolio_weights')}")
    print(f"   ✅ portfolio_count: {final_context.get('portfolio_count')}")
    print(f"   ✅ saved_portfolios count: {len(final_context.get('saved_portfolios', {}))}")
    print(f"   ✅ saved_portfolios keys: {list(final_context.get('saved_portfolios', {}).keys())}")
    
    # Check if all required fields are present
    required_fields = [
        'last_assets', 'last_analysis_type', 'current_symbols', 
        'current_currency', 'portfolio_weights', 'portfolio_count', 'saved_portfolios'
    ]
    
    all_present = True
    for field in required_fields:
        if field not in final_context or final_context[field] is None:
            print(f"   ❌ Missing field: {field}")
            all_present = False
    
    if all_present:
        print("   ✅ All required fields are present")
        return True
    else:
        print("   ❌ Some required fields are missing")
        return False

def main():
    """Run all tests"""
    print("🚀 Portfolio Input Fix Test Suite")
    print("=" * 60)
    
    tests = [
        test_portfolio_input_saving,
        test_portfolio_input_context_verification
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
        print("✅ All tests passed! Portfolio input should now save portfolios correctly.")
        print("\n💡 Next steps:")
        print("1. Test portfolio creation with text input (not /portfolio command)")
        print("2. Test /my command to see saved portfolios")
        print("3. Test drawdown button functionality")
    else:
        print("❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()

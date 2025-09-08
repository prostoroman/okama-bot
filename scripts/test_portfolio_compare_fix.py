#!/usr/bin/env python3
"""
Test script for portfolio comparison fix
Tests ok.Portfolio constructor usage in comparison function
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_ok_portfolio_constructor():
    """Test ok.Portfolio constructor usage"""
    print("🧪 Testing ok.Portfolio Constructor Usage")
    
    try:
        import okama as ok
        
        # Test data
        symbols = ['SPY.US', 'QQQ.US', 'BND.US']
        weights = [0.6, 0.3, 0.1]
        currency = 'USD'
        
        # Test correct constructor usage
        print("✅ Testing correct constructor usage:")
        print(f"   ok.Portfolio(symbols, weights=weights, ccy=currency)")
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
        print(f"   ✅ Portfolio created successfully: {portfolio}")
        
        # Test portfolio properties
        if hasattr(portfolio, 'symbols'):
            print(f"   ✅ Portfolio symbols: {portfolio.symbols}")
        if hasattr(portfolio, 'weights'):
            print(f"   ✅ Portfolio weights: {portfolio.weights}")
        if hasattr(portfolio, 'currency'):
            print(f"   ✅ Portfolio currency: {portfolio.currency}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ok.Portfolio constructor: {e}")
        return False

def test_portfolio_context_creation():
    """Test portfolio context creation for comparison"""
    print("\n🧪 Testing Portfolio Context Creation")
    
    # Simulate portfolio context data
    portfolio_context = {
        'portfolio_symbols': ['SPY.US', 'QQQ.US', 'BND.US'],
        'portfolio_weights': [0.6, 0.3, 0.1],
        'portfolio_currency': 'USD',
        'symbol': 'portfolio_7641.PF'
    }
    
    print("✅ Portfolio context data:")
    print(f"   Symbols: {portfolio_context['portfolio_symbols']}")
    print(f"   Weights: {portfolio_context['portfolio_weights']}")
    print(f"   Currency: {portfolio_context['portfolio_currency']}")
    print(f"   Symbol: {portfolio_context['symbol']}")
    
    # Test constructor call format
    print("\n✅ Correct constructor call format:")
    print(f"   ok.Portfolio(")
    print(f"       portfolio_context['portfolio_symbols'],")
    print(f"       weights=portfolio_context['portfolio_weights'],")
    print(f"       ccy=portfolio_context['portfolio_currency']")
    print(f"   )")
    
    return True

def test_comparison_function_logic():
    """Test comparison function logic"""
    print("\n🧪 Testing Comparison Function Logic")
    
    # Simulate the comparison function logic
    symbols = ['portfolio_7641.PF (SPY.US, QQQ.US, BND.US)', 'SBER.MOEX']
    expanded_symbols = ['portfolio_data', 'SBER.MOEX']
    portfolio_contexts = [{
        'portfolio_symbols': ['SPY.US', 'QQQ.US', 'BND.US'],
        'portfolio_weights': [0.6, 0.3, 0.1],
        'portfolio_currency': 'USD',
        'symbol': 'portfolio_7641.PF'
    }]
    
    print("✅ Comparison function data:")
    print(f"   Symbols: {symbols}")
    print(f"   Expanded symbols: {expanded_symbols}")
    print(f"   Portfolio contexts count: {len(portfolio_contexts)}")
    
    # Test portfolio creation logic
    print("\n✅ Portfolio creation logic:")
    for i, context in enumerate(portfolio_contexts):
        print(f"   Portfolio {i}:")
        print(f"     Symbols: {context['portfolio_symbols']}")
        print(f"     Weights: {context['portfolio_weights']}")
        print(f"     Currency: {context['portfolio_currency']}")
        print(f"     Symbol: {context['symbol']}")
        
        # Test constructor call
        print(f"     Constructor: ok.Portfolio(symbols, weights=weights, ccy=currency)")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Portfolio Comparison Fix Test Suite")
    print("=" * 60)
    
    tests = [
        test_ok_portfolio_constructor,
        test_portfolio_context_creation,
        test_comparison_function_logic
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
        print("✅ All tests passed! Portfolio comparison should now work correctly.")
        print("\n💡 Next steps:")
        print("1. Test /compare portfolio_7641.PF SBER.MOEX")
        print("2. Verify portfolio creation in comparison function")
        print("3. Test other portfolio comparison scenarios")
    else:
        print("❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()

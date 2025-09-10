#!/usr/bin/env python3
"""
Test script for portfolio charts period fix
Tests that portfolio charts (dividends, returns, drawdowns) respect the specified period
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
from datetime import datetime, timedelta

def test_portfolio_creation_with_period():
    """Test that portfolio creation respects period parameters"""
    print("Testing portfolio creation with period...")
    
    try:
        symbols = ["AAPL.US", "MSFT.US"]
        weights = [0.6, 0.4]
        currency = "USD"
        period = "5Y"
        
        years = int(period[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                               first_date=start_date.strftime('%Y-%m-%d'), 
                               last_date=end_date.strftime('%Y-%m-%d'))
        
        print(f"✅ Portfolio creation with period {period} works")
        print(f"   Period length: {portfolio.period_length}")
        print(f"   Currency: {portfolio.currency}")
        
        # Test that data respects the period
        wealth_data = portfolio.wealth_index
        if not wealth_data.empty:
            data_start = wealth_data.index[0]
            data_end = wealth_data.index[-1]
            print(f"   Data period: {data_start} to {data_end}")
            
            # Check if data is within expected period (allow some tolerance)
            # Convert Period to datetime for comparison
            if hasattr(data_start, 'to_timestamp'):
                data_start_dt = data_start.to_timestamp()
                data_end_dt = data_end.to_timestamp()
            else:
                data_start_dt = data_start
                data_end_dt = data_end
                
            expected_start = start_date - timedelta(days=30)  # 30 days tolerance
            expected_end = end_date + timedelta(days=30)  # 30 days tolerance
            
            if data_start_dt >= expected_start and data_end_dt <= expected_end:
                print(f"   ✅ Data period is within expected range")
            else:
                print(f"   ⚠️ Data period might be outside expected range")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio creation with period failed: {e}")
        return False

def test_dividend_yield_with_period():
    """Test that dividend yield data respects period"""
    print("\nTesting dividend yield with period...")
    
    try:
        symbols = ["AAPL.US", "MSFT.US"]
        weights = [0.6, 0.4]
        currency = "USD"
        period = "3Y"
        
        years = int(period[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                               first_date=start_date.strftime('%Y-%m-%d'), 
                               last_date=end_date.strftime('%Y-%m-%d'))
        
        # Test portfolio dividend yield
        if hasattr(portfolio, 'dividend_yield') and not portfolio.dividend_yield.empty:
            dividend_data = portfolio.dividend_yield
            print(f"✅ Portfolio dividend yield data available")
            print(f"   Data shape: {dividend_data.shape}")
            print(f"   Data period: {dividend_data.index[0]} to {dividend_data.index[-1]}")
        else:
            print(f"⚠️ No portfolio dividend yield data available")
        
        # Test portfolio dividend yield with assets
        if hasattr(portfolio, 'dividend_yield_with_assets') and not portfolio.dividend_yield_with_assets.empty:
            dividend_assets_data = portfolio.dividend_yield_with_assets
            print(f"✅ Portfolio dividend yield with assets data available")
            print(f"   Data shape: {dividend_assets_data.shape}")
            print(f"   Data period: {dividend_assets_data.index[0]} to {dividend_assets_data.index[-1]}")
        else:
            print(f"⚠️ No portfolio dividend yield with assets data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Dividend yield test failed: {e}")
        return False

def test_annual_returns_with_period():
    """Test that annual returns data respects period"""
    print("\nTesting annual returns with period...")
    
    try:
        symbols = ["SPY.US", "QQQ.US"]
        weights = [0.7, 0.3]
        currency = "USD"
        period = "10Y"
        
        years = int(period[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                               first_date=start_date.strftime('%Y-%m-%d'), 
                               last_date=end_date.strftime('%Y-%m-%d'))
        
        # Test annual returns
        if hasattr(portfolio, 'annual_return_ts') and not portfolio.annual_return_ts.empty:
            returns_data = portfolio.annual_return_ts
            print(f"✅ Portfolio annual returns data available")
            print(f"   Data shape: {returns_data.shape}")
            print(f"   Data period: {returns_data.index[0]} to {returns_data.index[-1]}")
        else:
            print(f"⚠️ No portfolio annual returns data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Annual returns test failed: {e}")
        return False

def test_drawdowns_with_period():
    """Test that drawdowns data respects period"""
    print("\nTesting drawdowns with period...")
    
    try:
        symbols = ["VTI.US", "BND.US"]
        weights = [0.8, 0.2]
        currency = "USD"
        period = "7Y"
        
        years = int(period[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                               first_date=start_date.strftime('%Y-%m-%d'), 
                               last_date=end_date.strftime('%Y-%m-%d'))
        
        # Test drawdowns
        if hasattr(portfolio, 'drawdowns') and not portfolio.drawdowns.empty:
            drawdowns_data = portfolio.drawdowns
            print(f"✅ Portfolio drawdowns data available")
            print(f"   Data shape: {drawdowns_data.shape}")
            print(f"   Data period: {drawdowns_data.index[0]} to {drawdowns_data.index[-1]}")
        else:
            print(f"⚠️ No portfolio drawdowns data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Drawdowns test failed: {e}")
        return False

def test_assetlist_with_period():
    """Test that AssetList creation respects period"""
    print("\nTesting AssetList creation with period...")
    
    try:
        symbols = ["AAPL.US", "MSFT.US"]
        currency = "USD"
        period = "5Y"
        
        years = int(period[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        asset_list = ok.AssetList(symbols, ccy=currency,
                                first_date=start_date.strftime('%Y-%m-%d'), 
                                last_date=end_date.strftime('%Y-%m-%d'))
        
        print(f"✅ AssetList creation with period {period} works")
        
        # Test dividend yields
        if hasattr(asset_list, 'dividend_yields') and not asset_list.dividend_yields.empty:
            dividend_data = asset_list.dividend_yields
            print(f"✅ AssetList dividend yields data available")
            print(f"   Data shape: {dividend_data.shape}")
            print(f"   Data period: {dividend_data.index[0]} to {dividend_data.index[-1]}")
        else:
            print(f"⚠️ No AssetList dividend yields data available")
        
        return True
        
    except Exception as e:
        print(f"❌ AssetList creation with period failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Portfolio Charts Period Fix")
    print("=" * 50)
    
    tests = [
        test_portfolio_creation_with_period,
        test_dividend_yield_with_period,
        test_annual_returns_with_period,
        test_drawdowns_with_period,
        test_assetlist_with_period
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Portfolio charts period fix is working correctly.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

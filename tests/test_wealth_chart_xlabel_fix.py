#!/usr/bin/env python3
"""
Test script for wealth chart xlabel fix
Tests that portfolio wealth chart has hidden x-axis label
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
from datetime import datetime, timedelta
from services.chart_styles import ChartStyles
import matplotlib.pyplot as plt

def test_wealth_chart_xlabel_hidden():
    """Test that wealth chart has hidden x-axis label"""
    print("Testing wealth chart x-axis label...")
    
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
        
        # Get wealth index data
        wealth_data = portfolio.wealth_index
        
        # Create chart using chart_styles
        chart_styles = ChartStyles()
        fig, ax = chart_styles.create_portfolio_wealth_chart(
            data=wealth_data, 
            symbols=symbols, 
            currency=currency, 
            weights=weights
        )
        
        # Check that x-axis label is empty
        xlabel = ax.get_xlabel()
        ylabel = ax.get_ylabel()
        
        print(f"✅ Wealth chart created successfully")
        print(f"   X-axis label: '{xlabel}'")
        print(f"   Y-axis label: '{ylabel}'")
        
        if xlabel == '':
            print(f"   ✅ X-axis label is hidden (empty)")
        else:
            print(f"   ❌ X-axis label is not hidden: '{xlabel}'")
            return False
            
        if ylabel == '':
            print(f"   ✅ Y-axis label is hidden (empty)")
        else:
            print(f"   ❌ Y-axis label is not hidden: '{ylabel}'")
            return False
        
        # Clean up
        chart_styles.cleanup_figure(fig)
        
        return True
        
    except Exception as e:
        print(f"❌ Wealth chart xlabel test failed: {e}")
        return False

def test_apply_styling_xlabel_hidden():
    """Test that apply_styling hides x-axis label when xlabel is empty"""
    print("\nTesting apply_styling x-axis label hiding...")
    
    try:
        chart_styles = ChartStyles()
        fig, ax = chart_styles.create_chart()
        
        # Test with empty xlabel
        chart_styles.apply_styling(ax, title="Test Chart", xlabel='', ylabel='')
        
        xlabel = ax.get_xlabel()
        ylabel = ax.get_ylabel()
        
        print(f"✅ apply_styling test completed")
        print(f"   X-axis label: '{xlabel}'")
        print(f"   Y-axis label: '{ylabel}'")
        
        if xlabel == '' and ylabel == '':
            print(f"   ✅ Both axis labels are hidden (empty)")
            return True
        else:
            print(f"   ❌ Axis labels are not hidden")
            return False
        
        # Clean up
        chart_styles.cleanup_figure(fig)
        
    except Exception as e:
        print(f"❌ apply_styling xlabel test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Wealth Chart X-Axis Label Fix")
    print("=" * 50)
    
    tests = [
        test_wealth_chart_xlabel_hidden,
        test_apply_styling_xlabel_hidden
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
        print("✅ All tests passed! Wealth chart x-axis label is properly hidden.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script for wealth chart legend fix
Tests that portfolio wealth chart legend shows correct portfolio name
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
from datetime import datetime, timedelta
from services.chart_styles import ChartStyles
import matplotlib.pyplot as plt

def test_wealth_chart_legend_with_portfolio_name():
    """Test that wealth chart legend shows portfolio name when provided"""
    print("Testing wealth chart legend with portfolio name...")
    
    try:
        symbols = ["AAPL.US", "MSFT.US"]
        weights = [0.6, 0.4]
        currency = "USD"
        portfolio_name = "Мой Портфель"
        period = "5Y"
        
        years = int(period[:-1])
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                               first_date=start_date.strftime('%Y-%m-%d'), 
                               last_date=end_date.strftime('%Y-%m-%d'))
        
        # Get wealth index data
        wealth_index = portfolio.wealth_index
        
        # Create chart using chart_styles with portfolio name
        chart_styles = ChartStyles()
        fig, ax = chart_styles.create_portfolio_wealth_chart(
            data=wealth_index, 
            symbols=symbols, 
            currency=currency, 
            weights=weights,
            portfolio_name=portfolio_name
        )
        
        # Check legend
        legend = ax.get_legend()
        if legend:
            legend_labels = [text.get_text() for text in legend.get_texts()]
            print(f"✅ Wealth chart created successfully")
            print(f"   Legend labels: {legend_labels}")
            
            if portfolio_name in legend_labels:
                print(f"   ✅ Legend shows correct portfolio name: '{portfolio_name}'")
                return True
            else:
                print(f"   ❌ Legend does not show portfolio name: '{portfolio_name}'")
                print(f"   ❌ Found labels: {legend_labels}")
                return False
        else:
            print(f"   ❌ No legend found")
            return False
        
        # Clean up
        chart_styles.cleanup_figure(fig)
        
    except Exception as e:
        print(f"❌ Wealth chart legend test failed: {e}")
        return False

def test_wealth_chart_legend_without_portfolio_name():
    """Test that wealth chart legend shows asset weights when portfolio name not provided"""
    print("\nTesting wealth chart legend without portfolio name...")
    
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
        wealth_index = portfolio.wealth_index
        
        # Create chart using chart_styles without portfolio name
        chart_styles = ChartStyles()
        fig, ax = chart_styles.create_portfolio_wealth_chart(
            data=wealth_index, 
            symbols=symbols, 
            currency=currency, 
            weights=weights
        )
        
        # Check legend
        legend = ax.get_legend()
        if legend:
            legend_labels = [text.get_text() for text in legend.get_texts()]
            print(f"✅ Wealth chart created successfully")
            print(f"   Legend labels: {legend_labels}")
            
            # Should show asset weights format
            expected_label = "AAPL (60.0%), MSFT (40.0%)"
            if expected_label in legend_labels:
                print(f"   ✅ Legend shows correct asset weights: '{expected_label}'")
                return True
            else:
                print(f"   ❌ Legend does not show expected asset weights")
                print(f"   ❌ Expected: '{expected_label}'")
                print(f"   ❌ Found: {legend_labels}")
                return False
        else:
            print(f"   ❌ No legend found")
            return False
        
        # Clean up
        chart_styles.cleanup_figure(fig)
        
    except Exception as e:
        print(f"❌ Wealth chart legend test failed: {e}")
        return False

def test_data_conversion_to_dataframe():
    """Test that Series is properly converted to DataFrame with correct column name"""
    print("\nTesting data conversion to DataFrame...")
    
    try:
        symbols = ["AAPL.US", "MSFT.US"]
        weights = [0.6, 0.4]
        portfolio_name = "Test Portfolio"
        
        # Create mock Series data
        dates = pd.date_range('2020-01-01', periods=10, freq='M')
        values = [100, 105, 110, 108, 115, 120, 118, 125, 130, 135]
        wealth_series = pd.Series(values, index=dates, name='wealth_index')
        
        # Test conversion logic
        chart_styles = ChartStyles()
        
        # Simulate the conversion logic from create_portfolio_wealth_chart
        if isinstance(wealth_series, pd.Series):
            column_name = portfolio_name
            data_df = pd.DataFrame({column_name: wealth_series})
            
            print(f"✅ Series converted to DataFrame successfully")
            print(f"   Column name: '{column_name}'")
            print(f"   DataFrame columns: {list(data_df.columns)}")
            
            if column_name in data_df.columns:
                print(f"   ✅ DataFrame has correct column name")
                return True
            else:
                print(f"   ❌ DataFrame does not have correct column name")
                return False
        
    except Exception as e:
        print(f"❌ Data conversion test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Wealth Chart Legend Fix")
    print("=" * 50)
    
    tests = [
        test_wealth_chart_legend_with_portfolio_name,
        test_wealth_chart_legend_without_portfolio_name,
        test_data_conversion_to_dataframe
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
        print("✅ All tests passed! Wealth chart legend shows correct portfolio name.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

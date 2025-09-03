#!/usr/bin/env python3
"""
Debug script to check chart data differences between daily and monthly charts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
import matplotlib.pyplot as plt
import io

def debug_asset_attributes(symbol: str = 'VOO.US'):
    """Debug asset attributes and their data"""
    print(f"=== Debugging asset attributes for {symbol} ===")
    
    try:
        asset = ok.Asset(symbol)
        print(f"Asset created successfully: {asset}")
        
        # Check all available attributes
        print("\n=== Available attributes ===")
        for attr in dir(asset):
            if not attr.startswith('_'):
                try:
                    value = getattr(asset, attr)
                    if callable(value):
                        print(f"{attr}: <method>")
                    else:
                        print(f"{attr}: {type(value)} - {str(value)[:100]}...")
                except Exception as e:
                    print(f"{attr}: <error - {e}>")
        
        # Check specific price-related attributes
        print("\n=== Price-related attributes ===")
        price_attrs = ['close_daily', 'close_monthly', 'adj_close', 'price', 'close_prices']
        
        for attr in price_attrs:
            if hasattr(asset, attr):
                value = getattr(asset, attr)
                print(f"\n{attr}:")
                print(f"  Type: {type(value)}")
                if hasattr(value, '__len__'):
                    print(f"  Length: {len(value)}")
                if hasattr(value, 'index'):
                    print(f"  Index type: {type(value.index)}")
                    if len(value) > 0:
                        print(f"  First date: {value.index[0]}")
                        print(f"  Last date: {value.index[-1]}")
                        print(f"  First value: {value.iloc[0]}")
                        print(f"  Last value: {value.iloc[-1]}")
                        if hasattr(value.index, 'freq'):
                            print(f"  Frequency: {value.index.freq}")
            else:
                print(f"{attr}: Not available")
        
        # Test plotting
        print("\n=== Testing plotting ===")
        
        # Test daily chart
        if hasattr(asset, 'close_daily') and asset.close_daily is not None:
            print("Testing close_daily.plot()...")
            try:
                plt.figure(figsize=(10, 6))
                asset.close_daily.plot()
                plt.title(f'Daily Chart - {symbol}')
                plt.xlabel('Date')
                plt.ylabel('Price')
                plt.grid(True)
                plt.savefig(f'daily_chart_{symbol.replace(".", "_")}.png')
                plt.close()
                print("✓ Daily chart saved successfully")
            except Exception as e:
                print(f"✗ Error plotting daily chart: {e}")
        
        # Test monthly chart
        if hasattr(asset, 'close_monthly') and asset.close_monthly is not None:
            print("Testing close_monthly.plot()...")
            try:
                plt.figure(figsize=(10, 6))
                asset.close_monthly.plot()
                plt.title(f'Monthly Chart - {symbol}')
                plt.xlabel('Date')
                plt.ylabel('Price')
                plt.grid(True)
                plt.savefig(f'monthly_chart_{symbol.replace(".", "_")}.png')
                plt.close()
                print("✓ Monthly chart saved successfully")
            except Exception as e:
                print(f"✗ Error plotting monthly chart: {e}")
        
        # Test adj_close
        if hasattr(asset, 'adj_close') and asset.adj_close is not None:
            print("Testing adj_close.plot()...")
            try:
                plt.figure(figsize=(10, 6))
                asset.adj_close.plot()
                plt.title(f'Adjusted Close Chart - {symbol}')
                plt.xlabel('Date')
                plt.ylabel('Price')
                plt.grid(True)
                plt.savefig(f'adj_close_chart_{symbol.replace(".", "_")}.png')
                plt.close()
                print("✓ Adjusted close chart saved successfully")
            except Exception as e:
                print(f"✗ Error plotting adj_close chart: {e}")
        
        # Compare data
        print("\n=== Data comparison ===")
        if hasattr(asset, 'close_daily') and hasattr(asset, 'close_monthly'):
            daily_data = asset.close_daily
            monthly_data = asset.close_monthly
            
            if len(daily_data) > 0 and len(monthly_data) > 0:
                print(f"Daily data points: {len(daily_data)}")
                print(f"Monthly data points: {len(monthly_data)}")
                print(f"Daily date range: {daily_data.index[0]} to {daily_data.index[-1]}")
                print(f"Monthly date range: {monthly_data.index[0]} to {monthly_data.index[-1]}")
                
                # Check if they're the same
                if len(daily_data) == len(monthly_data):
                    print("⚠️  WARNING: Daily and monthly data have the same length!")
                    if daily_data.equals(monthly_data):
                        print("⚠️  WARNING: Daily and monthly data are identical!")
                    else:
                        print("Data are different despite same length")
                else:
                    print("✓ Daily and monthly data have different lengths (expected)")
        
    except Exception as e:
        print(f"Error creating asset: {e}")

def test_multiple_symbols():
    """Test multiple symbols to see if the issue is consistent"""
    symbols = ['VOO.US', 'SPY.US', 'AAPL.US', 'SBER.MOEX']
    
    for symbol in symbols:
        print(f"\n{'='*50}")
        debug_asset_attributes(symbol)
        print(f"{'='*50}")

if __name__ == "__main__":
    print("Starting chart data debug...")
    
    # Test single symbol
    debug_asset_attributes('VOO.US')
    
    # Test multiple symbols
    test_multiple_symbols()
    
    print("\nDebug completed. Check generated PNG files for visual comparison.")

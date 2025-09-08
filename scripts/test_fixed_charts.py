#!/usr/bin/env python3
"""
Test script to verify fixed chart methods
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import matplotlib.pyplot as plt
import io
import pandas as pd
import okama as ok

async def test_fixed_chart_methods():
    """Test the fixed chart methods"""
    symbol = 'VOO.US'
    
    print(f"Testing fixed chart methods for {symbol}")
    
    # Test daily chart
    print("\n=== Testing Daily Chart ===")
    try:
        # Create asset
        asset = ok.Asset(symbol)
        currency = getattr(asset, 'currency', '')
        
        # Get daily data
        if hasattr(asset, 'close_daily') and asset.close_daily is not None:
            daily_data = asset.close_daily
            
            # Filter data on 1 year
            if len(daily_data) > 365:
                daily_data = daily_data.tail(365)
            
            # Create chart with proper styles
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Convert PeriodIndex to DatetimeIndex for better display
            if isinstance(daily_data.index, pd.PeriodIndex):
                x_values = daily_data.index.to_timestamp()
            else:
                x_values = daily_data.index
            
            ax.plot(x_values, daily_data.values, linewidth=2, color='#1f77b4', alpha=0.8)
            ax.set_title(f'Ежедневный график {symbol}', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Дата', fontsize=12)
            ax.set_ylabel(f'Цена ({currency})', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
            
            # Format axes
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Add data information
            if len(daily_data) > 0:
                current_price = daily_data.iloc[-1]
                start_price = daily_data.iloc[0]
                change_pct = ((current_price - start_price) / start_price) * 100
                
                # Add annotation with current price
                ax.annotate(f'Текущая цена: {current_price:.2f} {currency}\nИзменение: {change_pct:+.2f}%', 
                          xy=(0.02, 0.98), xycoords='axes fraction',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
                          fontsize=10, verticalalignment='top')
            
            # Save chart
            plt.savefig(f'fixed_daily_chart_{symbol.replace(".", "_")}.png', 
                       format='PNG', dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"✓ Daily chart saved: fixed_daily_chart_{symbol.replace('.', '_')}.png")
            print(f"  Data points: {len(daily_data)}")
            print(f"  Date range: {daily_data.index[0]} to {daily_data.index[-1]}")
            print(f"  Price range: {daily_data.min():.2f} to {daily_data.max():.2f}")
        else:
            print("✗ No adj_close data available")
            
    except Exception as e:
        print(f"✗ Error creating daily chart: {e}")
    
    # Test monthly chart
    print("\n=== Testing Monthly Chart ===")
    try:
        # Get monthly data
        if hasattr(asset, 'close_monthly') and asset.close_monthly is not None:
            monthly_data = asset.close_monthly
            
            # Filter data on 10 years (120 months)
            if len(monthly_data) > 120:
                monthly_data = monthly_data.tail(120)
            
            # Create chart with proper styles
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Convert PeriodIndex to DatetimeIndex for better display
            if isinstance(monthly_data.index, pd.PeriodIndex):
                x_values = monthly_data.index.to_timestamp()
            else:
                x_values = monthly_data.index
            
            ax.plot(x_values, monthly_data.values, linewidth=2, color='#ff7f0e', alpha=0.8)
            ax.set_title(f'Месячный график {symbol}', fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel('Дата', fontsize=12)
            ax.set_ylabel(f'Цена ({currency})', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
            
            # Format axes
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # Add data information
            if len(monthly_data) > 0:
                current_price = monthly_data.iloc[-1]
                start_price = monthly_data.iloc[0]
                change_pct = ((current_price - start_price) / start_price) * 100
                
                # Add annotation with current price
                ax.annotate(f'Текущая цена: {current_price:.2f} {currency}\nИзменение: {change_pct:+.2f}%', 
                          xy=(0.02, 0.98), xycoords='axes fraction',
                          bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8),
                          fontsize=10, verticalalignment='top')
            
            # Save chart
            plt.savefig(f'fixed_monthly_chart_{symbol.replace(".", "_")}.png', 
                       format='PNG', dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            print(f"✓ Monthly chart saved: fixed_monthly_chart_{symbol.replace('.', '_')}.png")
            print(f"  Data points: {len(monthly_data)}")
            print(f"  Date range: {monthly_data.index[0]} to {monthly_data.index[-1]}")
            print(f"  Price range: {monthly_data.min():.2f} to {monthly_data.max():.2f}")
        else:
            print("✗ No close_monthly data available")
            
    except Exception as e:
        print(f"✗ Error creating monthly chart: {e}")
    
    # Compare data
    print("\n=== Data Comparison ===")
    if hasattr(asset, 'adj_close') and hasattr(asset, 'close_monthly'):
        daily_data = asset.adj_close.tail(365) if len(asset.adj_close) > 365 else asset.adj_close
        monthly_data = asset.close_monthly.tail(120) if len(asset.close_monthly) > 120 else asset.close_monthly
        
        print(f"Daily data points: {len(daily_data)}")
        print(f"Monthly data points: {len(monthly_data)}")
        print(f"Daily date range: {daily_data.index[0]} to {daily_data.index[-1]}")
        print(f"Monthly date range: {monthly_data.index[0]} to {monthly_data.index[-1]}")
        
        # Check if they're different
        if len(daily_data) != len(monthly_data):
            print("✓ Daily and monthly data have different lengths (expected)")
        else:
            print("⚠️  WARNING: Daily and monthly data have the same length!")
            
        if not daily_data.equals(monthly_data):
            print("✓ Daily and monthly data are different (expected)")
        else:
            print("⚠️  WARNING: Daily and monthly data are identical!")

if __name__ == "__main__":
    print("Testing fixed chart methods...")
    asyncio.run(test_fixed_chart_methods())
    print("\nTest completed. Check generated PNG files for visual comparison.")

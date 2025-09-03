#!/usr/bin/env python3
"""
Compare close_daily vs adj_close data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
import matplotlib.pyplot as plt

def compare_daily_data(symbol: str = 'VOO.US'):
    """Compare close_daily vs adj_close data"""
    print(f"=== Comparing daily data for {symbol} ===")
    
    try:
        asset = ok.Asset(symbol)
        
        # Get both datasets
        close_daily = asset.close_daily
        adj_close = asset.adj_close
        
        print(f"\nData comparison:")
        print(f"close_daily points: {len(close_daily)}")
        print(f"adj_close points: {len(adj_close)}")
        
        # Compare recent data (last 30 days)
        recent_close = close_daily.tail(30)
        recent_adj = adj_close.tail(30)
        
        print(f"\nRecent 30 days comparison:")
        print(f"close_daily range: {recent_close.min():.2f} to {recent_close.max():.2f}")
        print(f"adj_close range: {recent_adj.min():.2f} to {recent_adj.max():.2f}")
        
        # Check if they're the same
        if recent_close.equals(recent_adj):
            print("⚠️  WARNING: Recent close_daily and adj_close are identical!")
        else:
            print("✓ Recent close_daily and adj_close are different")
            
            # Show some sample values
            print(f"\nSample values (last 5 days):")
            for i in range(-5, 0):
                print(f"  {recent_close.index[i]}: close_daily={recent_close.iloc[i]:.2f}, adj_close={recent_adj.iloc[i]:.2f}")
        
        # Create comparison chart
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Plot close_daily
        ax1.plot(recent_close.index.to_timestamp(), recent_close.values, 
                linewidth=2, color='#1f77b4', label='close_daily')
        ax1.set_title(f'close_daily - {symbol} (Last 30 days)', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Price')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot adj_close
        ax2.plot(recent_adj.index.to_timestamp(), recent_adj.values, 
                linewidth=2, color='#ff7f0e', label='adj_close')
        ax2.set_title(f'adj_close - {symbol} (Last 30 days)', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Price')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig(f'daily_comparison_{symbol.replace(".", "_")}.png', 
                   format='PNG', dpi=96, bbox_inches='tight')
        plt.close()
        
        print(f"\n✓ Comparison chart saved: daily_comparison_{symbol.replace('.', '_')}.png")
        
    except Exception as e:
        print(f"Error comparing data: {e}")

def test_multiple_symbols():
    """Test multiple symbols to see differences"""
    symbols = ['VOO.US', 'AAPL.US', 'SPY.US']
    
    for symbol in symbols:
        print(f"\n{'='*60}")
        compare_daily_data(symbol)
        print(f"{'='*60}")

if __name__ == "__main__":
    print("Comparing close_daily vs adj_close data...")
    test_multiple_symbols()
    print("\nComparison completed.")

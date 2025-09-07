#!/usr/bin/env python3
"""
Demo script to show adaptive table formatting for different numbers of assets
"""

import pandas as pd
import sys
import os

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

def demo_adaptive_formatting():
    """Demonstrate adaptive table formatting for different scenarios"""
    
    bot = ShansAi()
    
    print("=== ADAPTIVE TABLE FORMATTING DEMO ===\n")
    
    # Scenario 1: 2 assets (Pipe format)
    print("1. 2 ASSETS - PIPE FORMAT:")
    print("=" * 50)
    data_2 = {
        'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
        'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81]
    }
    index = ['Compound return', 'CAGR (1Y)', 'CAGR (5Y)', 'Annualized mean return', 'Dividend yield', 'Risk', 'Max drawdowns']
    df_2 = pd.DataFrame(data_2, index=index)
    
    mock_asset_list_2 = Mock()
    mock_asset_list_2.describe.return_value = df_2
    
    result_2 = bot._format_describe_table(mock_asset_list_2)
    print(result_2)
    print(f"Length: {len(result_2)} characters\n")
    
    # Scenario 2: 4 assets (Simple format)
    print("2. 4 ASSETS - SIMPLE FORMAT:")
    print("=" * 50)
    data_4 = {
        'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
        'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81],
        'AAPL.US': [0.12, 0.22, 0.19, 0.14, 0.01, 0.25, -0.45],
        'MSFT.US': [0.10, 0.20, 0.17, 0.12, 0.01, 0.23, -0.40]
    }
    df_4 = pd.DataFrame(data_4, index=index)
    
    mock_asset_list_4 = Mock()
    mock_asset_list_4.describe.return_value = df_4
    
    result_4 = bot._format_describe_table(mock_asset_list_4)
    print(result_4)
    print(f"Length: {len(result_4)} characters\n")
    
    # Scenario 3: 6 assets (Vertical format)
    print("3. 6 ASSETS - VERTICAL FORMAT:")
    print("=" * 50)
    data_6 = {
        'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
        'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81],
        'AAPL.US': [0.12, 0.22, 0.19, 0.14, 0.01, 0.25, -0.45],
        'MSFT.US': [0.10, 0.20, 0.17, 0.12, 0.01, 0.23, -0.40],
        'GOOGL.US': [0.13, 0.23, 0.20, 0.15, 0.00, 0.26, -0.50],
        'AMZN.US': [0.09, 0.19, 0.16, 0.11, 0.00, 0.24, -0.35]
    }
    df_6 = pd.DataFrame(data_6, index=index)
    
    mock_asset_list_6 = Mock()
    mock_asset_list_6.describe.return_value = df_6
    
    result_6 = bot._format_describe_table(mock_asset_list_6)
    print(result_6)
    print(f"Length: {len(result_6)} characters\n")
    
    # Scenario 4: Fallback without tabulate
    print("4. FALLBACK WITHOUT TABULATE (4 assets):")
    print("=" * 50)
    
    # Mock TABULATE_AVAILABLE as False
    with patch('bot.TABULATE_AVAILABLE', False):
        result_fallback = bot._format_describe_table_simple(mock_asset_list_4)
        print(result_fallback)
        print(f"Length: {len(result_fallback)} characters\n")
    
    print("=== SUMMARY ===")
    print("✅ 2 assets: Pipe format (most readable)")
    print("✅ 3-4 assets: Simple format (compact but readable)")
    print("✅ 5+ assets: Vertical format (mobile-friendly)")
    print("✅ Fallback: Adaptive formatting even without tabulate")
    print("✅ All formats optimized for Telegram display")

if __name__ == '__main__':
    from unittest.mock import Mock, patch
    demo_adaptive_formatting()

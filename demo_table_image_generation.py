#!/usr/bin/env python3
"""
Demo script to show table image generation functionality
"""

import pandas as pd
import sys
import os
import io

# Add the parent directory to the path to import chart_styles
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chart_styles import ChartStyles

def demo_table_image_generation():
    """Demonstrate table image generation for different scenarios"""
    
    chart_styles = ChartStyles()
    
    print("=== TABLE IMAGE GENERATION DEMO ===\n")
    
    # Scenario 1: 2 assets
    print("1. 2 ASSETS TABLE IMAGE:")
    print("=" * 50)
    data_2 = {
        'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
        'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81]
    }
    index = ['Compound return', 'CAGR (1Y)', 'CAGR (5Y)', 'Annualized mean return', 'Dividend yield', 'Risk', 'Max drawdowns']
    df_2 = pd.DataFrame(data_2, index=index)
    
    fig_2, ax_2 = chart_styles.create_table_image(df_2, "📊 Статистика активов (2 актива)", ['SPY.US', 'QQQ.US'])
    
    # Save to file for demonstration
    fig_2.savefig('table_2_assets.png', dpi=96, bbox_inches='tight')
    print("✅ Table image created: table_2_assets.png")
    print(f"   Size: {fig_2.get_size_inches()}")
    
    # Save to bytes
    buffer_2 = io.BytesIO()
    chart_styles.save_figure(fig_2, buffer_2)
    buffer_2.seek(0)
    image_bytes_2 = buffer_2.getvalue()
    print(f"   Image size: {len(image_bytes_2)} bytes")
    
    chart_styles.cleanup_figure(fig_2)
    print()
    
    # Scenario 2: 4 assets
    print("2. 4 ASSETS TABLE IMAGE:")
    print("=" * 50)
    data_4 = {
        'SPY.US': [0.08, 0.16, 0.14, 0.09, 0.01, 0.17, -0.51],
        'QQQ.US': [0.11, 0.21, 0.18, 0.13, 0.00, 0.27, -0.81],
        'AAPL.US': [0.12, 0.22, 0.19, 0.14, 0.01, 0.25, -0.45],
        'MSFT.US': [0.10, 0.20, 0.17, 0.12, 0.01, 0.23, -0.40]
    }
    df_4 = pd.DataFrame(data_4, index=index)
    
    fig_4, ax_4 = chart_styles.create_table_image(df_4, "📊 Статистика активов (4 актива)", ['SPY.US', 'QQQ.US', 'AAPL.US', 'MSFT.US'])
    
    # Save to file for demonstration
    fig_4.savefig('table_4_assets.png', dpi=96, bbox_inches='tight')
    print("✅ Table image created: table_4_assets.png")
    print(f"   Size: {fig_4.get_size_inches()}")
    
    # Save to bytes
    buffer_4 = io.BytesIO()
    chart_styles.save_figure(fig_4, buffer_4)
    buffer_4.seek(0)
    image_bytes_4 = buffer_4.getvalue()
    print(f"   Image size: {len(image_bytes_4)} bytes")
    
    chart_styles.cleanup_figure(fig_4)
    print()
    
    # Scenario 3: 6 assets
    print("3. 6 ASSETS TABLE IMAGE:")
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
    
    fig_6, ax_6 = chart_styles.create_table_image(df_6, "📊 Статистика активов (6 активов)", ['SPY.US', 'QQQ.US', 'AAPL.US', 'MSFT.US', 'GOOGL.US', 'AMZN.US'])
    
    # Save to file for demonstration
    fig_6.savefig('table_6_assets.png', dpi=96, bbox_inches='tight')
    print("✅ Table image created: table_6_assets.png")
    print(f"   Size: {fig_6.get_size_inches()}")
    
    # Save to bytes
    buffer_6 = io.BytesIO()
    chart_styles.save_figure(fig_6, buffer_6)
    buffer_6.seek(0)
    image_bytes_6 = buffer_6.getvalue()
    print(f"   Image size: {len(image_bytes_6)} bytes")
    
    chart_styles.cleanup_figure(fig_6)
    print()
    
    # Scenario 4: With NaN values
    print("4. TABLE WITH NaN VALUES:")
    print("=" * 50)
    data_nan = {
        'SPY.US': [0.08, 0.16, float('nan'), 0.09],
        'QQQ.US': [0.11, 0.21, 0.18, float('nan')],
        'AAPL.US': [0.12, 0.22, 0.19, 0.14]
    }
    index_nan = ['Compound return', 'CAGR (1Y)', 'CAGR (5Y)', 'Annualized mean return']
    df_nan = pd.DataFrame(data_nan, index=index_nan)
    
    fig_nan, ax_nan = chart_styles.create_table_image(df_nan, "📊 Статистика с NaN значениями", ['SPY.US', 'QQQ.US', 'AAPL.US'])
    
    # Save to file for demonstration
    fig_nan.savefig('table_with_nan.png', dpi=96, bbox_inches='tight')
    print("✅ Table image created: table_with_nan.png")
    print(f"   Size: {fig_nan.get_size_inches()}")
    
    chart_styles.cleanup_figure(fig_nan)
    print()
    
    print("=== SUMMARY ===")
    print("✅ 2 assets: 10x6 inches, compact table")
    print("✅ 4 assets: 14x6 inches, medium table")
    print("✅ 6 assets: 16x6 inches, wide table")
    print("✅ NaN handling: Shows 'N/A' for missing values")
    print("✅ Performance highlighting: Green for best returns, red for worst risks")
    print("✅ Professional styling: Blue headers, gray metrics, white data")
    print("✅ All images saved as PNG files for inspection")
    print("✅ Images optimized for Telegram display")

if __name__ == '__main__':
    demo_table_image_generation()

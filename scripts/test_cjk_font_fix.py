#!/usr/bin/env python3
"""
Test script to debug CJK font issues and chart generation for Chinese stocks
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
from services.chart_styles import ChartStyles
from services.tushare_service import TushareService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cjk_fonts():
    """Test CJK font availability"""
    print("=== Testing CJK Font Availability ===")
    
    # Get available fonts
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # CJK fonts to check
    cjk_fonts = [
        'DejaVu Sans',
        'Arial Unicode MS',
        'SimHei',
        'Microsoft YaHei',
        'PingFang SC',
        'Hiragino Sans GB',
        'Noto Sans CJK SC',
        'Source Han Sans SC',
        'WenQuanYi Micro Hei',
        'Droid Sans Fallback',
    ]
    
    print("Available CJK fonts:")
    for font in cjk_fonts:
        if font in available_fonts:
            print(f"  ✅ {font}")
        else:
            print(f"  ❌ {font}")
    
    print(f"\nTotal available fonts: {len(available_fonts)}")
    
    # Test matplotlib font configuration
    print("\n=== Testing Matplotlib Font Configuration ===")
    print(f"Current font family: {plt.rcParams['font.family']}")
    print(f"Current sans-serif fonts: {plt.rcParams['font.sans-serif']}")
    print(f"Unicode minus: {plt.rcParams['axes.unicode_minus']}")

def test_chart_generation():
    """Test chart generation with Chinese text"""
    print("\n=== Testing Chart Generation ===")
    
    try:
        # Initialize chart styles
        chart_styles = ChartStyles()
        
        # Create test data with Chinese text
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        prices = np.random.randn(30).cumsum() + 100
        
        test_data = pd.Series(prices, index=dates)
        
        # Test chart creation with Chinese symbol
        symbol = "000001.SH"
        currency = "CNY"
        
        print(f"Creating chart for symbol: {symbol}")
        
        fig, ax = chart_styles.create_price_chart(
            data=test_data,
            symbol=symbol,
            currency=currency,
            period='ежедневный'
        )
        
        # Save test chart
        output_path = '/tmp/test_chart.png'
        fig.savefig(output_path, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        
        print(f"✅ Chart created successfully: {output_path}")
        
        # Check if file was created
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"Chart file size: {file_size} bytes")
        else:
            print("❌ Chart file was not created")
            
    except Exception as e:
        print(f"❌ Error creating chart: {e}")
        import traceback
        traceback.print_exc()

def test_tushare_data():
    """Test Tushare data retrieval"""
    print("\n=== Testing Tushare Data Retrieval ===")
    
    try:
        # Initialize Tushare service
        tushare_service = TushareService()
        
        if not tushare_service:
            print("❌ Tushare service not available")
            return
        
        symbol = "000001.SH"
        print(f"Testing data retrieval for: {symbol}")
        
        # Test daily data
        daily_data = tushare_service.get_daily_data(symbol)
        print(f"Daily data shape: {daily_data.shape}")
        print(f"Daily data columns: {list(daily_data.columns)}")
        print(f"Daily data empty: {daily_data.empty}")
        
        if not daily_data.empty:
            print("Sample daily data:")
            print(daily_data.head())
        
        # Test monthly data
        monthly_data = tushare_service.get_monthly_data(symbol)
        print(f"Monthly data shape: {monthly_data.shape}")
        print(f"Monthly data empty: {monthly_data.empty}")
        
        if not monthly_data.empty:
            print("Sample monthly data:")
            print(monthly_data.head())
            
    except Exception as e:
        print(f"❌ Error with Tushare data: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("CJK Font and Chart Generation Test")
    print("=" * 50)
    
    test_cjk_fonts()
    test_chart_generation()
    test_tushare_data()
    
    print("\nTest completed!")
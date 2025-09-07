#!/usr/bin/env python3
"""
Debug script to identify why daily chart generation is failing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from services.chart_styles import ChartStyles
from services.tushare_service import TushareService
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_daily_chart():
    """Debug daily chart generation step by step"""
    print("=== Debugging Daily Chart Generation ===")
    
    symbol = "000001.SH"
    print(f"Symbol: {symbol}")
    
    try:
        # Step 1: Initialize services
        print("\nStep 1: Initialize services")
        tushare_service = TushareService()
        chart_styles = ChartStyles()
        print("✅ Services initialized")
        
        # Step 2: Get daily data
        print("\nStep 2: Get daily data")
        daily_data = tushare_service.get_daily_data(symbol)
        print(f"Data shape: {daily_data.shape}")
        print(f"Data empty: {daily_data.empty}")
        print(f"Columns: {list(daily_data.columns)}")
        
        if daily_data.empty:
            print("❌ Daily data is empty")
            return
        
        print("✅ Daily data retrieved")
        
        # Step 3: Prepare chart data
        print("\nStep 3: Prepare chart data")
        chart_data = daily_data.set_index('trade_date')['close']
        print(f"Chart data shape: {chart_data.shape}")
        print(f"Chart data type: {type(chart_data)}")
        print(f"Chart data index type: {type(chart_data.index)}")
        print("Sample chart data:")
        print(chart_data.head())
        print("✅ Chart data prepared")
        
        # Step 4: Determine currency
        print("\nStep 4: Determine currency")
        currency = 'HKD' if symbol.endswith('.HK') else 'CNY'
        print(f"Currency: {currency}")
        print("✅ Currency determined")
        
        # Step 5: Create chart
        print("\nStep 5: Create chart")
        fig, ax = chart_styles.create_price_chart(
            data=chart_data,
            symbol=symbol,
            currency=currency,
            period='ежедневный'
        )
        print("✅ Chart created")
        
        # Step 6: Save chart
        print("\nStep 6: Save chart")
        import io
        buffer = io.BytesIO()
        fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        chart_bytes = buffer.getvalue()
        buffer.close()
        plt.close(fig)
        
        print(f"✅ Chart saved: {len(chart_bytes)} bytes")
        
        # Step 7: Test with thread executor (like in bot)
        print("\nStep 7: Test with thread executor")
        import concurrent.futures
        
        def create_chart_in_thread():
            try:
                # Get daily data from Tushare
                daily_data = tushare_service.get_daily_data(symbol)
                
                if daily_data.empty:
                    print("❌ Daily data is empty in thread")
                    return None
                
                # Prepare data for chart - set trade_date as index
                chart_data = daily_data.set_index('trade_date')['close']
                
                # Determine currency based on exchange
                currency = 'HKD' if symbol.endswith('.HK') else 'CNY'
                
                # Create chart using ChartStyles
                fig, ax = chart_styles.create_price_chart(
                    data=chart_data,
                    symbol=symbol,
                    currency=currency,
                    period='ежедневный'
                )
                
                # Save to bytes
                buffer = io.BytesIO()
                fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
                buffer.seek(0)
                chart_bytes = buffer.getvalue()
                buffer.close()
                plt.close(fig)
                
                return chart_bytes
            except Exception as e:
                print(f"❌ Error in thread: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(create_chart_in_thread)
            chart_bytes = future.result(timeout=30)
            
        if chart_bytes:
            print(f"✅ Thread executor test successful: {len(chart_bytes)} bytes")
        else:
            print("❌ Thread executor test failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Daily Chart Debug Test")
    print("=" * 50)
    
    debug_daily_chart()
    
    print("\nDebug completed!")

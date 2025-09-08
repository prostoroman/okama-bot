#!/usr/bin/env python3
"""
Debug script for HK symbols comparison x-axis issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from services.tushare_service import TushareService
from config import Config

def debug_hk_symbols():
    """Debug HK symbols data structure and x-axis issue using Tushare"""
    symbols = ['00001.HK', '00005.HK']
    
    print(f"=== Debugging HK symbols: {symbols} ===")
    
    try:
        # Initialize Tushare service
        tushare_service = TushareService()
        
        # Get data for each symbol
        chinese_data = {}
        all_dates = set()
        
        for symbol in symbols:
            print(f"\n=== Processing {symbol} ===")
            
            try:
                # Get symbol info
                symbol_info = tushare_service.get_symbol_info(symbol)
                print(f"Symbol info: {symbol_info}")
                
                # Get monthly data
                historical_data = tushare_service.get_monthly_data(symbol, start_date='19900101')
                print(f"Historical data shape: {historical_data.shape}")
                print(f"Historical data columns: {historical_data.columns.tolist()}")
                
                if not historical_data.empty:
                    # Set date as index
                    historical_data = historical_data.set_index('trade_date')
                    print(f"After setting index - shape: {historical_data.shape}")
                    print(f"Index type: {type(historical_data.index)}")
                    print(f"Index dtype: {historical_data.index.dtype}")
                    
                    chinese_data[symbol] = {
                        'info': symbol_info,
                        'data': historical_data
                    }
                    all_dates.update(historical_data.index)
                    
                    print(f"Date range: {historical_data.index[0]} to {historical_data.index[-1]}")
                    print(f"Total data points: {len(historical_data.index)}")
                    
            except Exception as e:
                print(f"Error processing {symbol}: {e}")
                import traceback
                traceback.print_exc()
        
        if not chinese_data:
            print("❌ No data retrieved for any symbol")
            return
        
        # Prepare comparison data
        print(f"\n=== Preparing comparison data ===")
        comparison_data = {}
        
        for symbol, data_dict in chinese_data.items():
            historical_data = data_dict['data']
            symbol_info = data_dict['info']
            
            if not historical_data.empty:
                # Normalize data to base value (1000) like okama
                normalized_data = historical_data['close'] / historical_data['close'].iloc[0] * 1000
                
                # Get English name for legend
                symbol_name = symbol_info.get('name', symbol)
                if 'enname' in symbol_info and symbol_info['enname'] and symbol_info['enname'].strip():
                    symbol_name = symbol_info['enname']
                
                print(f"Symbol {symbol}: name='{symbol_name}', data points: {len(normalized_data)}")
                
                comparison_data[f"{symbol} - {symbol_name}"] = normalized_data
        
        # Create DataFrame
        comparison_df = pd.DataFrame(comparison_data)
        print(f"\nComparison DataFrame shape: {comparison_df.shape}")
        print(f"Comparison DataFrame index type: {type(comparison_df.index)}")
        print(f"Comparison DataFrame index dtype: {comparison_df.index.dtype}")
        
        # Test x-axis optimization logic
        print(f"\n=== Testing x-axis optimization logic ===")
        date_index = comparison_df.index
        
        # Convert PeriodIndex if needed
        if hasattr(date_index, 'dtype') and str(date_index.dtype).startswith('period'):
            print(f"⚠️  PeriodIndex detected: {date_index.dtype}")
            date_index = date_index.to_timestamp()
            print(f"After conversion - index type: {type(date_index)}")
            print(f"After conversion - index dtype: {date_index.dtype}")
        else:
            print(f"✓ Regular DatetimeIndex: {date_index.dtype}")
        
        num_points = len(date_index)
        print(f"Number of data points: {num_points}")
        
        # Determine which category it falls into
        if num_points <= 10:
            category = "≤10 points - Monthly"
            locator = "MonthLocator()"
            formatter = "DateFormatter('%Y-%m')"
        elif num_points <= 30:
            category = "≤30 points - Monthly"
            locator = "MonthLocator()"
            formatter = "DateFormatter('%Y-%m')"
        elif num_points <= 60:
            category = "≤60 points - Bi-monthly"
            locator = "MonthLocator(interval=2)"
            formatter = "DateFormatter('%Y-%m')"
        elif num_points <= 120:
            category = "≤120 points - Quarterly"
            locator = "MonthLocator(interval=3)"
            formatter = "DateFormatter('%Y-%m')"
        else:
            category = ">120 points - Yearly"
            locator = "YearLocator()"
            formatter = "DateFormatter('%Y')"
        
        print(f"Category: {category}")
        print(f"Locator: {locator}")
        print(f"Formatter: {formatter}")
        
        # Test the fixed chart_styles.create_comparison_chart function
        print(f"\n=== Testing fixed chart_styles.create_comparison_chart ===")
        from services.chart_styles import chart_styles
        
        # Create chart using the fixed function
        fig, ax = chart_styles.create_comparison_chart(
            data=comparison_df,
            symbols=list(comparison_data.keys()),
            currency='HKD',
            title=f'HK Symbols Comparison (Fixed)\n{category} - {num_points} points'
        )
        
        plt.tight_layout()
        plt.savefig('hk_comparison_fixed.png', format='PNG', dpi=96, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Fixed chart saved: hk_comparison_fixed.png")
        
        # Also create the old manual chart for comparison
        print(f"\n=== Creating manual chart for comparison ===")
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot data
        for i, column in enumerate(comparison_df.columns):
            ax.plot(comparison_df.index, comparison_df[column].values, 
                   label=column, linewidth=2)
        
        # Apply x-axis optimization manually
        if num_points <= 10:
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        elif num_points <= 30:
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        elif num_points <= 60:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        elif num_points <= 120:
            ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        else:
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        
        ax.tick_params(axis='x', rotation=45)
        ax.set_title(f'HK Symbols Comparison (Manual)\n{category} - {num_points} points')
        ax.set_xlabel('Date')
        ax.set_ylabel('Wealth Index')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('hk_comparison_manual.png', format='PNG', dpi=96, bbox_inches='tight')
        plt.close()
        
        print(f"✓ Manual chart saved: hk_comparison_manual.png")
        
    except Exception as e:
        print(f"Error in debug: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_hk_symbols()

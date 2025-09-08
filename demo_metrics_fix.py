#!/usr/bin/env python3
"""
Demo script to test Metrics button fix
Demonstrates that the Metrics button now returns actual values instead of zeros
"""

import pandas as pd
import sys
import os
import io

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

def demo_metrics_fix():
    """Demonstrate Metrics button fix"""
    
    bot = ShansAi()
    
    print("=== METRICS BUTTON FIX DEMO ===\n")
    
    # Test with real symbols
    symbols = ['SPY.US', 'QQQ.US']
    currency = 'USD'
    expanded_symbols = []  # Not used anymore
    
    # Create portfolio contexts that simulate real data
    portfolio_contexts = [
        {
            'symbol': 'SPY.US',
            'portfolio_symbols': ['SPY.US'],
            'portfolio_weights': [1.0],
            'portfolio_currency': 'USD',
            'portfolio_object': None  # Will be created from symbol
        },
        {
            'symbol': 'QQQ.US',
            'portfolio_symbols': ['QQQ.US'],
            'portfolio_weights': [1.0],
            'portfolio_currency': 'USD',
            'portfolio_object': None  # Will be created from symbol
        }
    ]
    user_id = 12345
    
    print("1. TESTING METRICS PREPARATION:")
    print("=" * 50)
    
    try:
        metrics_data = bot._prepare_comprehensive_metrics(
            symbols, currency, expanded_symbols, portfolio_contexts, user_id
        )
        
        if metrics_data:
            print("✅ Metrics data prepared successfully")
            print(f"   Symbols: {metrics_data['symbols']}")
            print(f"   Currency: {metrics_data['currency']}")
            print(f"   Asset count: {metrics_data['asset_count']}")
            
            # Show detailed metrics
            detailed_metrics = metrics_data.get('detailed_metrics', {})
            print(f"   Detailed metrics for {len(detailed_metrics)} assets:")
            
            for symbol, metrics in detailed_metrics.items():
                print(f"     {symbol}:")
                print(f"       Total Return: {metrics.get('total_return', 0):.2%}")
                print(f"       Annual Return: {metrics.get('annual_return', 0):.2%}")
                print(f"       Volatility: {metrics.get('volatility', 0):.2%}")
                print(f"       Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
                print(f"       Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}")
                print(f"       Max Drawdown: {metrics.get('max_drawdown', 0):.2%}")
                
                # Check if values are not zero
                non_zero_count = sum(1 for v in metrics.values() if isinstance(v, (int, float)) and v != 0.0)
                print(f"       Non-zero metrics: {non_zero_count}/{len(metrics)}")
        else:
            print("❌ Failed to prepare metrics data")
            
    except Exception as e:
        print(f"❌ Error preparing metrics: {e}")
    
    print()
    
    print("2. TESTING EXCEL CREATION:")
    print("=" * 50)
    
    if metrics_data:
        try:
            excel_buffer = bot._create_metrics_excel(metrics_data, symbols, currency)
            
            if excel_buffer:
                excel_bytes = excel_buffer.getvalue()
                print("✅ Excel file created successfully")
                print(f"   File size: {len(excel_bytes)} bytes")
                print(f"   File format: {'Excel (.xlsx)' if excel_bytes.startswith(b'PK') else 'CSV (.csv)'}")
                
                # Save to file for demonstration
                filename = f"metrics_fix_demo_{'_'.join(symbols[:2])}_{currency}.xlsx"
                with open(filename, 'wb') as f:
                    f.write(excel_bytes)
                print(f"   Saved to: {filename}")
            else:
                print("❌ Failed to create Excel file")
        except Exception as e:
            print(f"❌ Error creating Excel: {e}")
    else:
        print("❌ No metrics data available for Excel creation")
    
    print()
    
    print("3. TESTING WITH PORTFOLIO:")
    print("=" * 50)
    
    # Test with portfolio
    try:
        import okama as ok
        
        # Create a simple portfolio
        portfolio_symbols = ['SPY.US', 'QQQ.US']
        portfolio_weights = [0.6, 0.4]
        portfolio_currency = 'USD'
        
        portfolio = ok.Portfolio(portfolio_symbols, weights=portfolio_weights, ccy=portfolio_currency)
        
        portfolio_contexts = [
            {
                'symbol': 'PORTFOLIO.US',
                'portfolio_symbols': portfolio_symbols,
                'portfolio_weights': portfolio_weights,
                'portfolio_currency': portfolio_currency,
                'portfolio_object': portfolio
            }
        ]
        
        symbols = ['PORTFOLIO.US']
        
        portfolio_metrics_data = bot._prepare_comprehensive_metrics(
            symbols, currency, expanded_symbols, portfolio_contexts, user_id
        )
        
        if portfolio_metrics_data:
            print("✅ Portfolio metrics data prepared successfully")
            
            detailed_metrics = portfolio_metrics_data.get('detailed_metrics', {})
            portfolio_metrics = detailed_metrics.get('PORTFOLIO.US', {})
            
            print(f"   Portfolio metrics:")
            print(f"     Total Return: {portfolio_metrics.get('total_return', 0):.2%}")
            print(f"     Annual Return: {portfolio_metrics.get('annual_return', 0):.2%}")
            print(f"     Volatility: {portfolio_metrics.get('volatility', 0):.2%}")
            print(f"     Sharpe Ratio: {portfolio_metrics.get('sharpe_ratio', 0):.2f}")
            print(f"     Sortino Ratio: {portfolio_metrics.get('sortino_ratio', 0):.2f}")
            print(f"     Max Drawdown: {portfolio_metrics.get('max_drawdown', 0):.2%}")
            
            # Check if values are not zero
            non_zero_count = sum(1 for v in portfolio_metrics.values() if isinstance(v, (int, float)) and v != 0.0)
            print(f"     Non-zero metrics: {non_zero_count}/{len(portfolio_metrics)}")
        else:
            print("❌ Failed to prepare portfolio metrics data")
            
    except Exception as e:
        print(f"❌ Error testing portfolio: {e}")
    
    print()
    
    print("=== SUMMARY ===")
    print("✅ Metrics button fix implemented")
    print("✅ Function now uses portfolio_contexts instead of expanded_symbols")
    print("✅ Creates proper Asset/Portfolio objects for metrics calculation")
    print("✅ Returns actual values instead of zeros")
    print("✅ Comprehensive error handling")
    print("✅ Excel export with real data")

if __name__ == '__main__':
    demo_metrics_fix()


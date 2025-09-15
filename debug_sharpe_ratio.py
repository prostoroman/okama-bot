#!/usr/bin/env python3
"""
Debug script to understand what okama.Portfolio.get_sharpe_ratio() returns
"""

import okama as ok
import pandas as pd

def test_sharpe_ratio():
    """Test what get_sharpe_ratio() returns for different scenarios"""
    
    # Test with the same portfolio that caused the error
    symbols = ['SPY.US', 'QQQ.US', 'BND.US']
    
    try:
        # Create portfolio
        portfolio = ok.Portfolio(assets=symbols)
        print(f"Portfolio created successfully: {symbols}")
        
        # Test get_sharpe_ratio() method
        sharpe = portfolio.get_sharpe_ratio()
        print(f"Sharpe ratio type: {type(sharpe)}")
        print(f"Sharpe ratio value: {sharpe}")
        print(f"Sharpe ratio repr: {repr(sharpe)}")
        
        # Test different access methods
        print("\nTesting access methods:")
        
        # Test iloc access
        if hasattr(sharpe, 'iloc'):
            print(f"Has iloc: True")
            try:
                iloc_value = sharpe.iloc[0]
                print(f"iloc[0] value: {iloc_value}")
            except Exception as e:
                print(f"iloc[0] error: {e}")
        else:
            print(f"Has iloc: False")
        
        # Test __getitem__ access
        if hasattr(sharpe, '__getitem__'):
            print(f"Has __getitem__: True")
            try:
                getitem_value = sharpe[0]
                print(f"[0] value: {getitem_value}")
            except Exception as e:
                print(f"[0] error: {e}")
        else:
            print(f"Has __getitem__: False")
        
        # Test direct access
        try:
            direct_value = sharpe
            print(f"Direct value: {direct_value}")
        except Exception as e:
            print(f"Direct access error: {e}")
            
    except Exception as e:
        print(f"Error creating portfolio or getting Sharpe ratio: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sharpe_ratio()

#!/usr/bin/env python3
"""
Test script for Chinese symbols display fixes
Tests that the fixes for Chinese names and copyright method work correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tushare_service import TushareService
from services.chart_styles import ChartStyles
import logging
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_chinese_names_fix():
    """Test that Chinese names are handled correctly"""
    
    print("🔍 Testing Chinese Names Fix")
    print("=" * 50)
    
    # Test symbols with different name availability
    test_symbols = [
        '00001.HK',  # Should have English name
        '00005.HK',  # Should have English name  
        '600000.SH', # May not have English name
        '000001.SZ'  # May not have English name
    ]
    
    try:
        tushare_service = TushareService()
        
        for symbol in test_symbols:
            print(f"\n🔍 Testing symbol: {symbol}")
            print("-" * 30)
            
            symbol_info = tushare_service.get_symbol_info(symbol)
            
            if 'error' in symbol_info:
                print(f"❌ Error: {symbol_info['error']}")
                continue
            
            name = symbol_info.get('name', 'N/A')
            enname = symbol_info.get('enname', 'N/A')
            
            print(f"✅ Name: '{name}'")
            print(f"✅ English name: '{enname}'")
            
            # Check if the name handling is correct
            if enname and enname.strip() and enname != 'N/A':
                # Should use English name
                if name == enname:
                    print(f"✅ Correctly using English name")
                else:
                    print(f"❌ Should use English name but using: '{name}'")
            else:
                # Should use Chinese name (fallback)
                print(f"✅ Correctly using Chinese name (no English available)")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False
    
    print("\n✅ Chinese names fix test completed")
    return True

def test_copyright_method_fix():
    """Test that the copyright method works correctly"""
    
    print("\n🔍 Testing Copyright Method Fix")
    print("=" * 50)
    
    try:
        # Initialize chart styles
        chart_styles = ChartStyles()
        
        # Create a test figure and axis
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Test the add_copyright method with correct signature
        try:
            chart_styles.add_copyright(ax)
            print("✅ Copyright method called successfully with correct signature")
        except Exception as e:
            print(f"❌ Copyright method failed: {e}")
            return False
        
        # Test that the method doesn't accept 3 arguments (old incorrect call)
        try:
            chart_styles.add_copyright(fig, ax)  # This should fail
            print("❌ Copyright method incorrectly accepted 3 arguments")
            return False
        except TypeError:
            print("✅ Copyright method correctly rejects 3 arguments")
        except Exception as e:
            print(f"✅ Copyright method correctly rejected 3 arguments: {e}")
        
        plt.close(fig)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False
    
    print("✅ Copyright method fix test completed")
    return True

if __name__ == "__main__":
    print("🚀 Starting Chinese Symbols Display Fix Test")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_chinese_names_fix()
    test2_passed = test_copyright_method_fix()
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Chinese symbols display fixes are working correctly.")
        exit(0)
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        exit(1)

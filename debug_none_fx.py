#!/usr/bin/env python3
"""Debug script to test None.FX issue"""

import okama as ok

def test_none_fx():
    """Test if None values cause None.FX error"""
    print("Testing None.FX issue...")
    
    # Test 1: Direct None value
    try:
        print("Test 1: Direct None value")
        asset = ok.Asset(None)
        print("✅ None value accepted")
    except Exception as e:
        print(f"❌ None value error: {e}")
    
    # Test 2: None string
    try:
        print("Test 2: 'None' string")
        asset = ok.Asset("None")
        print("✅ 'None' string accepted")
    except Exception as e:
        print(f"❌ 'None' string error: {e}")
    
    # Test 3: None.FX string
    try:
        print("Test 3: 'None.FX' string")
        asset = ok.Asset("None.FX")
        print("✅ 'None.FX' string accepted")
    except Exception as e:
        print(f"❌ 'None.FX' string error: {e}")
    
    # Test 4: Portfolio with None
    try:
        print("Test 4: Portfolio with None")
        portfolio = ok.Portfolio([None], weights=[1.0], ccy="USD")
        print("✅ Portfolio with None created")
    except Exception as e:
        print(f"❌ Portfolio with None error: {e}")
    
    # Test 5: Portfolio with None.FX
    try:
        print("Test 5: Portfolio with None.FX")
        portfolio = ok.Portfolio(["None.FX"], weights=[1.0], ccy="USD")
        print("✅ Portfolio with None.FX created")
    except Exception as e:
        print(f"❌ Portfolio with None.FX error: {e}")

if __name__ == "__main__":
    test_none_fx()

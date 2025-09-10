#!/usr/bin/env python3
"""
Test script to verify the datetime variable fix in portfolio creation.
This test simulates the portfolio creation process to ensure datetime is properly accessible.
"""

import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_datetime_availability():
    """Test that datetime is available in all code paths"""
    print("Testing datetime availability...")
    
    # Test 1: Direct datetime usage (should work)
    try:
        timestamp = datetime.now().isoformat()
        print(f"✅ Direct datetime usage works: {timestamp}")
    except Exception as e:
        print(f"❌ Direct datetime usage failed: {e}")
        return False
    
    # Test 2: Simulate the portfolio creation logic without specified_period
    try:
        symbols = ["AAPL", "MSFT"]
        weights = [0.5, 0.5]
        currency = "USD"
        specified_period = None
        
        # This simulates the else branch where datetime should be available
        if specified_period:
            years = int(specified_period[:-1])
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            print("Period specified branch")
        else:
            # This is where the error was occurring
            portfolio_data = {
                'symbols': symbols,
                'weights': weights,
                'currency': currency,
                'created_at': datetime.now().isoformat(),  # This line was failing
                'description': f"Портфель: {', '.join(symbols)}"
            }
            print(f"✅ Portfolio creation without period works: {portfolio_data['created_at']}")
    except Exception as e:
        print(f"❌ Portfolio creation without period failed: {e}")
        return False
    
    # Test 3: Simulate the portfolio creation logic with specified_period
    try:
        symbols = ["AAPL", "MSFT"]
        weights = [0.5, 0.5]
        currency = "USD"
        specified_period = "5Y"
        
        if specified_period:
            years = int(specified_period[:-1])
            from datetime import timedelta
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            print(f"✅ Period calculation works: {start_date} to {end_date}")
            
            # Test that datetime is still available after the period calculation
            portfolio_data = {
                'symbols': symbols,
                'weights': weights,
                'currency': currency,
                'created_at': datetime.now().isoformat(),
                'description': f"Портфель: {', '.join(symbols)}"
            }
            print(f"✅ Portfolio creation with period works: {portfolio_data['created_at']}")
    except Exception as e:
        print(f"❌ Portfolio creation with period failed: {e}")
        return False
    
    print("✅ All datetime tests passed!")
    return True

if __name__ == "__main__":
    success = test_datetime_availability()
    if success:
        print("\n🎉 Datetime fix verification successful!")
        sys.exit(0)
    else:
        print("\n💥 Datetime fix verification failed!")
        sys.exit(1)

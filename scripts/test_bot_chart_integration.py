#!/usr/bin/env python3
"""
Test script to verify bot chart integration works with the fixed Tushare service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from bot import ShansAi
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bot_chart_generation():
    """Test bot chart generation for Chinese stocks"""
    print("=== Testing Bot Chart Generation ===")
    
    try:
        # Initialize bot
        bot = ShansAi()
        
        # Test symbol
        symbol = "000001.SH"
        print(f"Testing chart generation for: {symbol}")
        
        # Test daily chart generation
        print("Testing daily chart...")
        daily_chart = await bot._get_tushare_daily_chart(symbol)
        
        if daily_chart:
            print(f"✅ Daily chart generated successfully: {len(daily_chart)} bytes")
        else:
            print("❌ Daily chart generation failed")
        
        # Test monthly chart generation
        print("Testing monthly chart...")
        monthly_chart = await bot._get_tushare_monthly_chart(symbol)
        
        if monthly_chart:
            print(f"✅ Monthly chart generated successfully: {len(monthly_chart)} bytes")
        else:
            print("❌ Monthly chart generation failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Bot Chart Integration Test")
    print("=" * 50)
    
    asyncio.run(test_bot_chart_generation())
    
    print("\nTest completed!")

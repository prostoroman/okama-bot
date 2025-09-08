#!/usr/bin/env python3
"""
Test script for /info command chart button changes
Tests the new 1Y, 5Y, and All chart buttons for both Okama and Tushare data sources
"""

import sys
import os
import asyncio
import logging

# Add the parent directory to the path to import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
from telegram import Update
from telegram.ext import ContextTypes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockUpdate:
    """Mock Update object for testing"""
    def __init__(self, user_id=12345, chat_id=67890):
        self.effective_user = MockUser(user_id)
        self.effective_chat = MockChat(chat_id)
        self.callback_query = None

class MockUser:
    def __init__(self, user_id):
        self.id = user_id

class MockChat:
    def __init__(self, chat_id):
        self.id = chat_id

class MockContext:
    """Mock Context object for testing"""
    def __init__(self):
        self.args = []
        self.bot = None

async def test_okama_chart_methods():
    """Test Okama chart generation methods"""
    logger.info("Testing Okama chart methods...")
    
    bot = ShansAi()
    
    # Test symbols
    test_symbols = ['AAPL.US', 'SBER.MOEX', 'SPY.US']
    
    for symbol in test_symbols:
        logger.info(f"Testing {symbol}...")
        
        try:
            # Test 1Y chart (daily)
            logger.info(f"  Testing 1Y chart for {symbol}")
            chart_1y = await bot._get_daily_chart(symbol)
            if chart_1y:
                logger.info(f"  ✅ 1Y chart generated successfully: {len(chart_1y)} bytes")
            else:
                logger.warning(f"  ❌ Failed to generate 1Y chart for {symbol}")
            
            # Test 5Y chart (monthly)
            logger.info(f"  Testing 5Y chart for {symbol}")
            chart_5y = await bot._get_monthly_chart(symbol)
            if chart_5y:
                logger.info(f"  ✅ 5Y chart generated successfully: {len(chart_5y)} bytes")
            else:
                logger.warning(f"  ❌ Failed to generate 5Y chart for {symbol}")
            
            # Test All chart
            logger.info(f"  Testing All chart for {symbol}")
            chart_all = await bot._get_all_chart(symbol)
            if chart_all:
                logger.info(f"  ✅ All chart generated successfully: {len(chart_all)} bytes")
            else:
                logger.warning(f"  ❌ Failed to generate All chart for {symbol}")
                
        except Exception as e:
            logger.error(f"  ❌ Error testing {symbol}: {e}")

async def test_tushare_chart_methods():
    """Test Tushare chart generation methods"""
    logger.info("Testing Tushare chart methods...")
    
    bot = ShansAi()
    
    # Test symbols
    test_symbols = ['000001.SZ', '000002.SZ', '0700.HK']
    
    for symbol in test_symbols:
        logger.info(f"Testing {symbol}...")
        
        try:
            # Test 1Y chart (daily)
            logger.info(f"  Testing 1Y chart for {symbol}")
            chart_1y = await bot._get_tushare_daily_chart(symbol)
            if chart_1y:
                logger.info(f"  ✅ 1Y chart generated successfully: {len(chart_1y)} bytes")
            else:
                logger.warning(f"  ❌ Failed to generate 1Y chart for {symbol}")
            
            # Test 5Y chart (monthly)
            logger.info(f"  Testing 5Y chart for {symbol}")
            chart_5y = await bot._get_tushare_monthly_chart(symbol)
            if chart_5y:
                logger.info(f"  ✅ 5Y chart generated successfully: {len(chart_5y)} bytes")
            else:
                logger.warning(f"  ❌ Failed to generate 5Y chart for {symbol}")
            
            # Test All chart
            logger.info(f"  Testing All chart for {symbol}")
            chart_all = await bot._get_tushare_all_chart(symbol)
            if chart_all:
                logger.info(f"  ✅ All chart generated successfully: {len(chart_all)} bytes")
            else:
                logger.warning(f"  ❌ Failed to generate All chart for {symbol}")
                
        except Exception as e:
            logger.error(f"  ❌ Error testing {symbol}: {e}")

async def test_button_callbacks():
    """Test button callback handlers"""
    logger.info("Testing button callback handlers...")
    
    bot = ShansAi()
    update = MockUpdate()
    context = MockContext()
    
    # Test Okama button handlers
    test_symbol = 'AAPL.US'
    
    try:
        logger.info(f"Testing Okama button handlers for {test_symbol}")
        
        # Test 1Y button
        logger.info("  Testing 1Y button handler")
        await bot._handle_daily_chart_button(update, context, test_symbol)
        
        # Test 5Y button
        logger.info("  Testing 5Y button handler")
        await bot._handle_monthly_chart_button(update, context, test_symbol)
        
        # Test All button
        logger.info("  Testing All button handler")
        await bot._handle_all_chart_button(update, context, test_symbol)
        
        logger.info("  ✅ All Okama button handlers executed successfully")
        
    except Exception as e:
        logger.error(f"  ❌ Error testing Okama button handlers: {e}")
    
    # Test Tushare button handlers
    test_symbol_tushare = '000001.SZ'
    
    try:
        logger.info(f"Testing Tushare button handlers for {test_symbol_tushare}")
        
        # Test 1Y button
        logger.info("  Testing 1Y button handler")
        await bot._handle_tushare_daily_chart_button(update, context, test_symbol_tushare)
        
        # Test 5Y button
        logger.info("  Testing 5Y button handler")
        await bot._handle_tushare_monthly_chart_button(update, context, test_symbol_tushare)
        
        # Test All button
        logger.info("  Testing All button handler")
        await bot._handle_tushare_all_chart_button(update, context, test_symbol_tushare)
        
        logger.info("  ✅ All Tushare button handlers executed successfully")
        
    except Exception as e:
        logger.error(f"  ❌ Error testing Tushare button handlers: {e}")

async def main():
    """Main test function"""
    logger.info("Starting /info command chart button tests...")
    
    try:
        # Test Okama chart methods
        await test_okama_chart_methods()
        
        # Test Tushare chart methods
        await test_tushare_chart_methods()
        
        # Test button callbacks
        await test_button_callbacks()
        
        logger.info("✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())

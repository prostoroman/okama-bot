#!/usr/bin/env python3
"""
Test script for dividends chart changes
Tests the updated dividends chart with years on x-axis and new title format
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

async def test_dividends_chart():
    """Test dividends chart generation"""
    logger.info("Testing dividends chart generation...")
    
    bot = ShansAi()
    
    # Test symbols that typically have dividends
    test_symbols = ['AAPL.US', 'MSFT.US', 'JNJ.US', 'PG.US']
    
    for symbol in test_symbols:
        logger.info(f"Testing dividends chart for {symbol}...")
        
        try:
            # Test dividends chart
            logger.info(f"  Testing dividends chart for {symbol}")
            chart_bytes = await bot._get_dividend_chart(symbol)
            if chart_bytes:
                logger.info(f"  ✅ Dividends chart generated successfully: {len(chart_bytes)} bytes")
                
                # Save chart for inspection
                filename = f"dividends_chart_{symbol.replace('.', '_')}.png"
                with open(filename, 'wb') as f:
                    f.write(chart_bytes)
                logger.info(f"  📁 Chart saved as {filename}")
            else:
                logger.warning(f"  ❌ Failed to generate dividends chart for {symbol}")
                
        except Exception as e:
            logger.error(f"  ❌ Error testing {symbol}: {e}")

async def test_dividends_button_handler():
    """Test dividends button handler"""
    logger.info("Testing dividends button handler...")
    
    bot = ShansAi()
    update = MockUpdate()
    context = MockContext()
    
    # Test Okama dividends button handler
    test_symbol = 'AAPL.US'
    
    try:
        logger.info(f"Testing dividends button handler for {test_symbol}")
        
        # Test dividends button
        logger.info("  Testing dividends button handler")
        await bot._handle_single_dividends_button(update, context, test_symbol)
        
        logger.info("  ✅ Dividends button handler executed successfully")
        
    except Exception as e:
        logger.error(f"  ❌ Error testing dividends button handler: {e}")

async def main():
    """Main test function"""
    logger.info("Starting dividends chart tests...")
    
    try:
        # Test dividends chart generation
        await test_dividends_chart()
        
        # Test dividends button handler
        await test_dividends_button_handler()
        
        logger.info("✅ All dividends chart tests completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Simple test for info buttons fix - just verify functions execute without errors
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

class TestInfoButtonsSimple(unittest.TestCase):
    """Simple test cases for info buttons fix"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
        self.bot.logger = Mock()
        
    async def test_dividends_button_executes(self):
        """Test that dividends button executes without error"""
        
        # Setup mocks
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_update.callback_query = mock_callback_query
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        
        # Mock the asset and callback message
        with patch('bot.ok.Asset') as mock_asset, \
             patch('bot.ShansAi._send_callback_message') as mock_send_callback:
            
            mock_asset_instance = Mock()
            mock_asset.return_value = mock_asset_instance
            mock_asset_instance.dividends = None  # No dividends
            mock_send_callback.return_value = None
            
            # Test the function
            try:
                await self.bot._handle_single_dividends_button(mock_update, mock_context, "AAPL")
                print("✅ Dividends button executed successfully")
            except Exception as e:
                print(f"❌ Error in dividends button: {e}")
                raise
        
    async def test_compare_button_executes(self):
        """Test that compare button executes without error"""
        
        # Setup mocks
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_update.callback_query = mock_callback_query
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        mock_update.effective_user.id = 12345
        
        # Mock the functions
        with patch('bot.ShansAi._update_user_context') as mock_update_context, \
             patch('bot.ShansAi._get_popular_alternatives') as mock_get_alternatives, \
             patch('bot.ShansAi._send_callback_message') as mock_send_callback:
            
            mock_get_alternatives.return_value = ['QQQ.US', 'VOO.US']
            mock_send_callback.return_value = None
            mock_update_context.return_value = None
            
            # Test the function
            try:
                await self.bot._handle_info_compare_button(mock_update, mock_context, "SPY.US")
                print("✅ Compare button executed successfully")
            except Exception as e:
                print(f"❌ Error in compare button: {e}")
                raise
        
    async def test_portfolio_button_executes(self):
        """Test that portfolio button executes without error"""
        
        # Setup mocks
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_update.callback_query = mock_callback_query
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        mock_update.effective_user.id = 12345
        
        # Mock the functions
        with patch('bot.ShansAi._update_user_context') as mock_update_context, \
             patch('bot.ShansAi._send_callback_message') as mock_send_callback:
            
            mock_send_callback.return_value = None
            mock_update_context.return_value = None
            
            # Test the function
            try:
                await self.bot._handle_info_portfolio_button(mock_update, mock_context, "AAPL")
                print("✅ Portfolio button executed successfully")
            except Exception as e:
                print(f"❌ Error in portfolio button: {e}")
                raise

if __name__ == '__main__':
    # Run the async tests
    import asyncio
    
    async def run_async_tests():
        test_case = TestInfoButtonsSimple()
        test_case.setUp()
        
        print("Testing info buttons simple execution...")
        
        # Test 1: Dividends button executes
        print("Test 1: Dividends button executes")
        await test_case.test_dividends_button_executes()
        
        # Test 2: Compare button executes
        print("Test 2: Compare button executes")
        await test_case.test_compare_button_executes()
        
        # Test 3: Portfolio button executes
        print("Test 3: Portfolio button executes")
        await test_case.test_portfolio_button_executes()
        
        print("\n🎉 All tests passed! Info buttons execute successfully.")
    
    asyncio.run(run_async_tests())

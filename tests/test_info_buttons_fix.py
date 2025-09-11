#!/usr/bin/env python3
"""
Test for info buttons fix - ensuring buttons are removed from old message
when clicking Dividends, Compare, Portfolio buttons in /info command
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

class TestInfoButtonsFix(unittest.TestCase):
    """Test cases for info buttons fix"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
        self.bot.logger = Mock()
        
    @patch('bot.ok.Asset')
    @patch('bot.ShansAi._send_callback_message')
    async def test_dividends_button_removes_old_buttons(self, mock_send_callback, mock_asset):
        """Test that dividends button removes buttons from old message"""
        
        # Setup mocks
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_update.callback_query = mock_callback_query
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        
        mock_asset_instance = Mock()
        mock_asset.return_value = mock_asset_instance
        mock_asset_instance.dividends = None  # No dividends
        mock_send_callback.return_value = None
        
        # Test the function
        try:
            await self.bot._handle_single_dividends_button(mock_update, mock_context, "AAPL")
        except Exception as e:
            print(f"Error in test: {e}")
            # Continue with assertions even if there's an error
        
        # Verify that edit_message_reply_markup was called to remove buttons
        mock_callback_query.edit_message_reply_markup.assert_called_once_with(reply_markup=None)
        
        # Verify that callback message was sent
        mock_send_callback.assert_called()
        
    @patch('bot.ShansAi._update_user_context')
    @patch('bot.ShansAi._get_popular_alternatives')
    @patch('bot.ShansAi._send_callback_message')
    async def test_compare_button_removes_old_buttons(self, mock_send_callback, mock_get_alternatives, mock_update_context):
        """Test that compare button removes buttons from old message"""
        
        # Setup mocks
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_update.callback_query = mock_callback_query
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        mock_update.effective_user.id = 12345
        
        mock_get_alternatives.return_value = ['QQQ.US', 'VOO.US']
        mock_send_callback.return_value = None
        mock_update_context.return_value = None
        
        # Test the function
        await self.bot._handle_info_compare_button(mock_update, mock_context, "SPY.US")
        
        # Verify that edit_message_reply_markup was called to remove buttons
        mock_callback_query.edit_message_reply_markup.assert_called_once_with(reply_markup=None)
        
        # Verify that user context was updated
        mock_update_context.assert_called_once()
        
        # Verify that callback message was sent
        mock_send_callback.assert_called()
        
    @patch('bot.ShansAi._update_user_context')
    @patch('bot.ShansAi._send_callback_message')
    async def test_portfolio_button_removes_old_buttons(self, mock_send_callback, mock_update_context):
        """Test that portfolio button removes buttons from old message"""
        
        # Setup mocks
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_update.callback_query = mock_callback_query
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        mock_update.effective_user.id = 12345
        
        mock_send_callback.return_value = None
        mock_update_context.return_value = None
        
        # Test the function
        await self.bot._handle_info_portfolio_button(mock_update, mock_context, "AAPL")
        
        # Verify that edit_message_reply_markup was called to remove buttons
        mock_callback_query.edit_message_reply_markup.assert_called_once_with(reply_markup=None)
        
        # Verify that user context was updated
        mock_update_context.assert_called_once()
        
        # Verify that callback message was sent
        mock_send_callback.assert_called()
        
    @patch('bot.ok.Asset')
    @patch('bot.ShansAi._send_callback_message')
    async def test_dividends_button_handles_edit_error_gracefully(self, mock_send_callback, mock_asset):
        """Test that dividends button handles edit_message_reply_markup errors gracefully"""
        
        # Setup mocks
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_update.callback_query = mock_callback_query
        mock_callback_query.edit_message_reply_markup = AsyncMock(side_effect=Exception("Edit failed"))
        
        mock_asset_instance = Mock()
        mock_asset.return_value = mock_asset_instance
        mock_asset_instance.dividends = None  # No dividends
        mock_send_callback.return_value = None
        
        # Test the function
        await self.bot._handle_single_dividends_button(mock_update, mock_context, "AAPL")
        
        # Verify that edit_message_reply_markup was called (even though it failed)
        mock_callback_query.edit_message_reply_markup.assert_called_once_with(reply_markup=None)
        
        # Verify that warning was logged
        self.bot.logger.warning.assert_called()
        
        # Verify that function continued and sent callback message
        mock_send_callback.assert_called()

if __name__ == '__main__':
    # Run the async tests
    import asyncio
    
    async def run_async_tests():
        test_case = TestInfoButtonsFix()
        test_case.setUp()
        
        print("Testing info buttons fix...")
        
        # Test 1: Dividends button removes old buttons
        print("Test 1: Dividends button removes old buttons")
        await test_case.test_dividends_button_removes_old_buttons()
        print("✅ Test 1 passed")
        
        # Test 2: Compare button removes old buttons
        print("Test 2: Compare button removes old buttons")
        await test_case.test_compare_button_removes_old_buttons()
        print("✅ Test 2 passed")
        
        # Test 3: Portfolio button removes old buttons
        print("Test 3: Portfolio button removes old buttons")
        await test_case.test_portfolio_button_removes_old_buttons()
        print("✅ Test 3 passed")
        
        # Test 4: Dividends button handles edit error gracefully
        print("Test 4: Dividends button handles edit error gracefully")
        await test_case.test_dividends_button_handles_edit_error_gracefully()
        print("✅ Test 4 passed")
        
        print("\n🎉 All tests passed! Info buttons fix is working correctly.")
    
    asyncio.run(run_async_tests())

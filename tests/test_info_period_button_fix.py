#!/usr/bin/env python3
"""
Test for info period button fix - ensuring buttons are removed from old message
when switching between periods (1Y, 5Y, Max) in /info command
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

class TestInfoPeriodButtonFix(unittest.TestCase):
    """Test cases for info period button fix"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
        self.bot.logger = Mock()
        
    @patch('bot.ok.Asset')
    @patch('bot.ShansAi._get_asset_key_metrics')
    @patch('bot.ShansAi._get_chart_for_period')
    @patch('bot.ShansAi._send_photo_safe')
    @patch('bot.ShansAi._send_ephemeral_message')
    async def test_info_period_button_removes_old_buttons(self, mock_ephemeral, mock_send_photo, 
                                                         mock_get_chart, mock_get_metrics, mock_asset):
        """Test that buttons are removed from old message when switching periods"""
        
        # Setup mocks
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_update.callback_query = mock_callback_query
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        
        mock_asset_instance = Mock()
        mock_asset.return_value = mock_asset_instance
        
        mock_get_metrics.return_value = {"return": 0.1, "volatility": 0.15}
        mock_get_chart.return_value = b"fake_chart_data"
        mock_send_photo.return_value = None
        mock_ephemeral.return_value = None
        
        # Test the function
        await self.bot._handle_info_period_button(mock_update, mock_context, "AAPL", "5Y")
        
        # Verify that edit_message_reply_markup was called to remove buttons
        mock_callback_query.edit_message_reply_markup.assert_called_once_with(reply_markup=None)
        
        # Verify that new message was sent with chart
        mock_send_photo.assert_called_once()
        
    @patch('bot.ok.Asset')
    @patch('bot.ShansAi._get_asset_key_metrics')
    @patch('bot.ShansAi._get_chart_for_period')
    @patch('bot.ShansAi._send_message_safe')
    @patch('bot.ShansAi._send_ephemeral_message')
    async def test_info_period_button_handles_edit_error_gracefully(self, mock_ephemeral, mock_send_message,
                                                                   mock_get_chart, mock_get_metrics, mock_asset):
        """Test that function handles edit_message_reply_markup errors gracefully"""
        
        # Setup mocks
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_update.callback_query = mock_callback_query
        mock_callback_query.edit_message_reply_markup = AsyncMock(side_effect=Exception("Edit failed"))
        
        mock_asset_instance = Mock()
        mock_asset.return_value = mock_asset_instance
        
        mock_get_metrics.return_value = {"return": 0.1, "volatility": 0.15}
        mock_get_chart.return_value = None  # No chart data
        mock_send_message.return_value = None
        mock_ephemeral.return_value = None
        
        # Test the function
        await self.bot._handle_info_period_button(mock_update, mock_context, "AAPL", "MAX")
        
        # Verify that edit_message_reply_markup was called (even though it failed)
        mock_callback_query.edit_message_reply_markup.assert_called_once_with(reply_markup=None)
        
        # Verify that warning was logged
        self.bot.logger.warning.assert_called()
        
        # Verify that new message was sent
        mock_send_message.assert_called_once()

if __name__ == '__main__':
    # Run the async tests
    import asyncio
    
    async def run_async_tests():
        test_case = TestInfoPeriodButtonFix()
        test_case.setUp()
        
        print("Testing info period button fix...")
        
        # Test 1: Buttons are removed from old message
        print("Test 1: Buttons are removed from old message")
        await test_case.test_info_period_button_removes_old_buttons()
        print("✅ Test 1 passed")
        
        # Test 2: Handles edit error gracefully
        print("Test 2: Handles edit error gracefully")
        await test_case.test_info_period_button_handles_edit_error_gracefully()
        print("✅ Test 2 passed")
        
        print("\n🎉 All tests passed! Info period button fix is working correctly.")
    
    asyncio.run(run_async_tests())

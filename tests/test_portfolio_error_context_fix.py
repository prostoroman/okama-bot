#!/usr/bin/env python3
"""
Test for portfolio error context fix.

This test verifies that when a portfolio command fails, the user context is properly cleared
to prevent fallback to compare command.
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the parent directory to the path to import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the config before importing bot
with patch.dict(os.environ, {
    'TELEGRAM_BOT_TOKEN': 'test_token',
    'YANDEX_API_KEY': 'test_key',
    'YANDEX_FOLDER_ID': 'test_folder'
}):
    from bot import ShansAi


class TestPortfolioErrorContextFix(unittest.TestCase):
    """Test portfolio error context clearing"""
    
    def setUp(self):
        """Set up test fixtures"""
        with patch.dict(os.environ, {
            'TELEGRAM_BOT_TOKEN': 'test_token',
            'YANDEX_API_KEY': 'test_key',
            'YANDEX_FOLDER_ID': 'test_folder'
        }):
            self.bot = ShansAi()
        self.bot.logger = Mock()
        self.bot.context_store = Mock()
        self.bot.user_sessions = {}
        
        # Mock the context store methods
        self.bot.context_store.get_user_context.return_value = {}
        self.bot.context_store.update_user_context.return_value = {}
        
        # Mock the _send_message_safe method
        self.bot._send_message_safe = AsyncMock()
        
        # Mock the _get_user_context method
        self.bot._get_user_context = Mock(return_value={})
        
        # Mock the _update_user_context method
        self.bot._update_user_context = Mock()
    
    def test_portfolio_command_error_clears_context(self):
        """Test that portfolio command error clears user context"""
        # Create a mock update object
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 12345
        
        # Create a mock context object
        context = Mock()
        context.args = ['GMKN.MOEX:0.4', 'AFKS.MOEX:0.5', 'CHMF.MOEX:0.1']
        
        # Mock the portfolio creation to raise an exception
        with patch.object(self.bot, '_create_portfolio_from_args', side_effect=Exception("Test error")):
            # Run the portfolio command
            import asyncio
            asyncio.run(self.bot.portfolio_command(update, context))
        
        # Verify that _update_user_context was called to clear the context
        self.bot._update_user_context.assert_called_with(
            12345,
            waiting_for_portfolio=False,
            waiting_for_portfolio_weights=False,
            waiting_for_compare=False,
            portfolio_tickers=None,
            portfolio_base_symbols=None
        )
        
        # Verify that error message was sent
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        self.assertIn("❌ Ошибка при выполнении команды портфеля", call_args[0][1])
    
    def test_portfolio_input_handler_error_clears_context(self):
        """Test that portfolio input handler error clears user context"""
        # Create a mock update object
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 12345
        
        # Create a mock context object
        context = Mock()
        
        # Mock the portfolio creation to raise an exception
        with patch.object(self.bot, '_create_portfolio_from_args', side_effect=Exception("Test error")):
            # Run the portfolio input handler
            import asyncio
            asyncio.run(self.bot._handle_portfolio_input(update, context, "GMKN.MOEX:0.4 AFKS.MOEX:0.5 CHMF.MOEX:0.1"))
        
        # Verify that _update_user_context was called to clear the context
        self.bot._update_user_context.assert_called_with(
            12345,
            waiting_for_portfolio=False,
            waiting_for_portfolio_weights=False,
            waiting_for_compare=False,
            portfolio_tickers=None,
            portfolio_base_symbols=None
        )
        
        # Verify that error message was sent
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        self.assertIn("❌ Ошибка при обработке ввода портфеля", call_args[0][1])
    
    def test_portfolio_weights_input_handler_error_clears_context(self):
        """Test that portfolio weights input handler error clears user context"""
        # Create a mock update object
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 12345
        
        # Create a mock context object
        context = Mock()
        
        # Mock the portfolio creation to raise an exception
        with patch.object(self.bot, '_create_portfolio_from_args', side_effect=Exception("Test error")):
            # Run the portfolio weights input handler
            import asyncio
            asyncio.run(self.bot._handle_portfolio_weights_input(update, context, "0.4 0.5 0.1"))
        
        # Verify that _update_user_context was called to clear the context
        self.bot._update_user_context.assert_called_with(
            12345,
            waiting_for_portfolio=False,
            waiting_for_portfolio_weights=False,
            waiting_for_compare=False,
            portfolio_tickers=None,
            portfolio_base_symbols=None
        )
        
        # Verify that error message was sent
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        self.assertIn("❌ Ошибка при обработке ввода портфеля", call_args[0][1])
    
    def test_portfolio_tickers_weights_input_handler_error_clears_context(self):
        """Test that portfolio tickers weights input handler error clears user context"""
        # Create a mock update object
        update = Mock()
        update.effective_user = Mock()
        update.effective_user.id = 12345
        
        # Create a mock context object
        context = Mock()
        
        # Mock the portfolio creation to raise an exception
        with patch.object(self.bot, '_create_portfolio_from_args', side_effect=Exception("Test error")):
            # Run the portfolio tickers weights input handler
            import asyncio
            asyncio.run(self.bot._handle_portfolio_tickers_weights_input(update, context, "0.4 0.5 0.1"))
        
        # Verify that _update_user_context was called to clear the context
        self.bot._update_user_context.assert_called_with(
            12345,
            waiting_for_portfolio=False,
            waiting_for_portfolio_weights=False,
            waiting_for_compare=False,
            portfolio_tickers=None,
            portfolio_base_symbols=None
        )
        
        # Verify that error message was sent
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        self.assertIn("❌ Ошибка при обработке ввода весов портфеля", call_args[0][1])


if __name__ == '__main__':
    unittest.main()

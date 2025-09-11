#!/usr/bin/env python3
"""
Test script for compare command soft handling functionality.
Tests the new soft handling logic for single symbol input.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes
from services.context_store import InMemoryUserContextStore
from bot import ShansAi


class TestCompareSoftHandling:
    """Test class for compare command soft handling"""
    
    def setup_method(self):
        """Setup test environment"""
        self.context_store = InMemoryUserContextStore()
        self.bot = ShansAi()
        self.bot.context_store = self.context_store
        
        # Mock user and chat
        self.user = User(id=12345, first_name="Test", is_bot=False)
        self.chat = Chat(id=67890, type="private")
        
        # Create mock update
        self.update = Mock(spec=Update)
        self.update.effective_user = self.user
        self.update.effective_chat = self.chat
        
        # Create mock context
        self.context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        self.context.args = []
        
        # Mock the _send_message_safe method
        self.bot._send_message_safe = AsyncMock()
    
    async def test_empty_compare_command_resets_context(self):
        """Test that empty /compare command resets the context"""
        # Set up initial context with stored symbol
        self.context_store.update_user_context(12345, compare_first_symbol="AAPL.US")
        
        # Call compare_command with no args
        await self.bot.compare_command(self.update, self.context)
        
        # Check that context was reset
        user_context = self.context_store.get_user_context(12345)
        assert user_context['compare_first_symbol'] is None
        assert user_context['waiting_for_compare'] is True
        
        # Check that help message was sent
        self.bot._send_message_safe.assert_called_once()
    
    async def test_single_symbol_first_input(self):
        """Test handling of first single symbol input"""
        # Set up context for compare input
        self.context_store.update_user_context(12345, waiting_for_compare=True)
        
        # Call _handle_compare_input with single symbol
        await self.bot._handle_compare_input(self.update, self.context, "AAPL.US")
        
        # Check that symbol was stored
        user_context = self.context_store.get_user_context(12345)
        assert user_context['compare_first_symbol'] == "AAPL.US"
        assert user_context['waiting_for_compare'] is False
        
        # Check that appropriate message was sent
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args[0]
        assert "Вы указали только 1 символ" in call_args[1]
    
    async def test_single_symbol_second_input(self):
        """Test handling of second single symbol input when first is stored"""
        # Set up context with stored first symbol
        self.context_store.update_user_context(12345, 
                                              compare_first_symbol="AAPL.US",
                                              waiting_for_compare=True)
        
        # Mock compare_command to avoid full execution
        with patch.object(self.bot, 'compare_command', new_callable=AsyncMock) as mock_compare:
            # Call _handle_compare_input with second symbol
            await self.bot._handle_compare_input(self.update, self.context, "MSFT.US")
            
            # Check that stored symbol was cleared
            user_context = self.context_store.get_user_context(12345)
            assert user_context['compare_first_symbol'] is None
            
            # Check that compare_command was called with combined symbols
            mock_compare.assert_called_once()
            call_args = mock_compare.call_args[0]
            assert call_args[1].args == ["AAPL.US", "MSFT.US"]
    
    async def test_multiple_symbols_input(self):
        """Test handling of multiple symbols input"""
        # Set up context with stored first symbol
        self.context_store.update_user_context(12345, 
                                              compare_first_symbol="AAPL.US",
                                              waiting_for_compare=True)
        
        # Mock compare_command to avoid full execution
        with patch.object(self.bot, 'compare_command', new_callable=AsyncMock) as mock_compare:
            # Call _handle_compare_input with multiple symbols
            await self.bot._handle_compare_input(self.update, self.context, "MSFT.US GOOGL.US")
            
            # Check that stored symbol was cleared
            user_context = self.context_store.get_user_context(12345)
            assert user_context['compare_first_symbol'] is None
            
            # Check that compare_command was called with the new symbols (not combined)
            mock_compare.assert_called_once()
            call_args = mock_compare.call_args[0]
            assert call_args[1].args == ["MSFT.US", "GOOGL.US"]
    
    async def test_empty_input_clears_context(self):
        """Test that empty input clears the stored context"""
        # Set up context with stored first symbol
        self.context_store.update_user_context(12345, 
                                              compare_first_symbol="AAPL.US",
                                              waiting_for_compare=True)
        
        # Call _handle_compare_input with empty input
        await self.bot._handle_compare_input(self.update, self.context, "")
        
        # Check that stored symbol was cleared
        user_context = self.context_store.get_user_context(12345)
        assert user_context['compare_first_symbol'] is None
        
        # Check that error message was sent
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args[0]
        assert "Необходимо указать минимум 2 символа" in call_args[1]
    
    async def test_compare_command_with_stored_symbol(self):
        """Test compare_command with stored symbol and single input"""
        # Set up context with stored first symbol
        self.context_store.update_user_context(12345, compare_first_symbol="AAPL.US")
        
        # Set up context args
        self.context.args = ["MSFT.US"]
        
        # Mock the rest of compare_command to avoid full execution
        with patch.object(self.bot, '_parse_currency_and_period') as mock_parse:
            mock_parse.return_value = (["MSFT.US"], None, None)
            
            with patch.object(self.bot, '_send_message_safe', new_callable=AsyncMock):
                # This should raise an exception due to mocking, but we can check the logic
                try:
                    await self.bot.compare_command(self.update, self.context)
                except:
                    pass
                
                # Check that stored symbol was cleared
                user_context = self.context_store.get_user_context(12345)
                assert user_context['compare_first_symbol'] is None


async def run_tests():
    """Run all tests"""
    test_instance = TestCompareSoftHandling()
    
    tests = [
        test_instance.test_empty_compare_command_resets_context,
        test_instance.test_single_symbol_first_input,
        test_instance.test_single_symbol_second_input,
        test_instance.test_multiple_symbols_input,
        test_instance.test_empty_input_clears_context,
        test_instance.test_compare_command_with_stored_symbol,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test_instance.setup_method()
            await test()
            print(f"✅ {test.__name__} - PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} - FAILED: {e}")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Test script for compare button fix functionality.
Tests the integration between info compare button and soft handling logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes
from services.context_store import InMemoryUserContextStore
from bot import ShansAi


class TestCompareButtonFix:
    """Test class for compare button fix"""
    
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
        self.bot._send_callback_message = AsyncMock()
    
    async def test_info_compare_button_sets_base_symbol(self):
        """Test that info compare button sets compare_base_symbol"""
        # Call _handle_info_compare_button
        await self.bot._handle_info_compare_button(self.update, self.context, "CL.COMM")
        
        # Check that compare_base_symbol was set
        user_context = self.context_store.get_user_context(12345)
        assert user_context['compare_base_symbol'] == "CL.COMM"
        assert user_context['waiting_for_compare'] is True
        
        # Check that callback message was sent
        self.bot._send_callback_message.assert_called_once()
    
    async def test_compare_input_with_base_symbol(self):
        """Test compare input when base symbol is set from info button"""
        # Set up context with base symbol from info button
        self.context_store.update_user_context(12345, 
                                              compare_base_symbol="CL.COMM",
                                              waiting_for_compare=True)
        
        # Mock compare_command to avoid full execution
        with patch.object(self.bot, 'compare_command', new_callable=AsyncMock) as mock_compare:
            # Call _handle_compare_input with single symbol
            await self.bot._handle_compare_input(self.update, self.context, "BND.US")
            
            # Check that base symbol was cleared
            user_context = self.context_store.get_user_context(12345)
            assert user_context['compare_base_symbol'] is None
            
            # Check that compare_command was called with combined symbols
            mock_compare.assert_called_once()
            call_args = mock_compare.call_args[0]
            # The args should be set in context.args
            assert call_args[1].args == ["CL.COMM", "BND.US"]
    
    async def test_compare_input_with_random_examples(self):
        """Test that random examples are generated for single symbol input"""
        # Set up context for compare input (no base symbol)
        self.context_store.update_user_context(12345, waiting_for_compare=True)
        
        # Mock get_random_examples to return predictable results
        with patch.object(self.bot, 'get_random_examples') as mock_random:
            mock_random.return_value = ["AAPL.US", "MSFT.US", "GOOGL.US"]
            
            # Call _handle_compare_input with single symbol
            await self.bot._handle_compare_input(self.update, self.context, "SPY.US")
            
            # Check that symbol was stored
            user_context = self.context_store.get_user_context(12345)
            assert user_context['compare_first_symbol'] == "SPY.US"
            
            # Check that message with random examples was sent
            self.bot._send_message_safe.assert_called_once()
            call_args = self.bot._send_message_safe.call_args[0]
            message_text = call_args[1]
            assert "Вы указали только 1 символ" in message_text
            assert "`AAPL.US`" in message_text
            assert "`MSFT.US`" in message_text
            assert "`GOOGL.US`" in message_text
    
    async def test_compare_command_with_base_symbol(self):
        """Test compare_command with base symbol from info button"""
        # Set up context with base symbol
        self.context_store.update_user_context(12345, compare_base_symbol="CL.COMM")
        
        # Set up context args
        self.context.args = ["BND.US"]
        
        # Mock the rest of compare_command to avoid full execution
        with patch.object(self.bot, '_parse_currency_and_period') as mock_parse:
            mock_parse.return_value = (["BND.US"], None, None)
            
            with patch.object(self.bot, '_send_message_safe', new_callable=AsyncMock):
                # This should raise an exception due to mocking, but we can check the logic
                try:
                    await self.bot.compare_command(self.update, self.context)
                except:
                    pass
                
                # Check that base symbol was cleared
                user_context = self.context_store.get_user_context(12345)
                assert user_context['compare_base_symbol'] is None
    
    async def test_empty_compare_command_clears_both_symbols(self):
        """Test that empty compare command clears both stored symbols"""
        # Set up context with both symbols
        self.context_store.update_user_context(12345, 
                                              compare_first_symbol="AAPL.US",
                                              compare_base_symbol="CL.COMM")
        
        # Call compare_command with no args
        await self.bot.compare_command(self.update, self.context)
        
        # Check that both symbols were cleared
        user_context = self.context_store.get_user_context(12345)
        assert user_context['compare_first_symbol'] is None
        assert user_context['compare_base_symbol'] is None
        assert user_context['waiting_for_compare'] is True
    
    async def test_multiple_symbols_input_clears_both_symbols(self):
        """Test that multiple symbols input clears both stored symbols"""
        # Set up context with both symbols
        self.context_store.update_user_context(12345, 
                                              compare_first_symbol="AAPL.US",
                                              compare_base_symbol="CL.COMM",
                                              waiting_for_compare=True)
        
        # Mock compare_command to avoid full execution
        with patch.object(self.bot, 'compare_command', new_callable=AsyncMock) as mock_compare:
            # Call _handle_compare_input with multiple symbols
            await self.bot._handle_compare_input(self.update, self.context, "MSFT.US GOOGL.US")
            
            # Check that both symbols were cleared
            user_context = self.context_store.get_user_context(12345)
            assert user_context['compare_first_symbol'] is None
            assert user_context['compare_base_symbol'] is None
            
            # Check that compare_command was called with the new symbols (not combined)
            mock_compare.assert_called_once()
            call_args = mock_compare.call_args[0]
            assert call_args[1].args == ["MSFT.US", "GOOGL.US"]


async def run_tests():
    """Run all tests"""
    test_instance = TestCompareButtonFix()
    
    tests = [
        test_instance.test_info_compare_button_sets_base_symbol,
        test_instance.test_compare_input_with_base_symbol,
        test_instance.test_compare_input_with_random_examples,
        test_instance.test_compare_command_with_base_symbol,
        test_instance.test_empty_compare_command_clears_both_symbols,
        test_instance.test_multiple_symbols_input_clears_both_symbols,
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

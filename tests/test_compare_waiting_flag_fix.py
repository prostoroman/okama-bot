#!/usr/bin/env python3
"""
Test script for compare waiting flag fix.
Tests that waiting_for_compare flag is properly managed during compare flow.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes
from services.context_store import InMemoryUserContextStore
from bot import ShansAi


class TestCompareWaitingFlagFix:
    """Test class for compare waiting flag fix"""
    
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
    
    async def test_first_symbol_keeps_waiting_flag(self):
        """Test that first symbol input keeps waiting_for_compare=True"""
        # Set up context for compare input (no stored symbols)
        self.context_store.update_user_context(12345, waiting_for_compare=True)
        
        # Mock get_random_examples to return predictable results
        with patch.object(self.bot, 'get_random_examples') as mock_random:
            mock_random.return_value = ["AAPL.US", "MSFT.US", "GOOGL.US"]
            
            # Call _handle_compare_input with single symbol
            await self.bot._handle_compare_input(self.update, self.context, "SPY.US")
            
            # Check that symbol was stored and waiting flag remains True
            user_context = self.context_store.get_user_context(12345)
            assert user_context['compare_first_symbol'] == "SPY.US"
            assert user_context['waiting_for_compare'] is True
            
            print("✅ First symbol keeps waiting_for_compare=True")
    
    async def test_second_symbol_clears_waiting_flag(self):
        """Test that second symbol input clears waiting_for_compare=False"""
        # Set up context with stored first symbol
        self.context_store.update_user_context(12345, 
                                              compare_first_symbol="SPY.US",
                                              waiting_for_compare=True)
        
        # Mock compare_command to avoid full execution
        with patch.object(self.bot, 'compare_command', new_callable=AsyncMock) as mock_compare:
            # Call _handle_compare_input with second symbol
            await self.bot._handle_compare_input(self.update, self.context, "QQQ.US")
            
            # Check that waiting flag was cleared
            user_context = self.context_store.get_user_context(12345)
            assert user_context['waiting_for_compare'] is False
            
            print("✅ Second symbol clears waiting_for_compare=False")
    
    async def test_base_symbol_from_button_works(self):
        """Test that base symbol from compare button works correctly"""
        # Set up context with base symbol from compare button
        self.context_store.update_user_context(12345, 
                                              compare_base_symbol="CL.COMM",
                                              waiting_for_compare=True)
        
        # Mock compare_command to avoid full execution
        with patch.object(self.bot, 'compare_command', new_callable=AsyncMock) as mock_compare:
            # Call _handle_compare_input with single symbol
            await self.bot._handle_compare_input(self.update, self.context, "BND.US")
            
            # Check that waiting flag was cleared and symbols were combined
            user_context = self.context_store.get_user_context(12345)
            assert user_context['waiting_for_compare'] is False
            assert user_context['compare_base_symbol'] is None
            
            print("✅ Base symbol from button works correctly")
    
    async def test_multiple_symbols_clear_waiting_flag(self):
        """Test that multiple symbols input clears waiting flag"""
        # Set up context with waiting flag
        self.context_store.update_user_context(12345, waiting_for_compare=True)
        
        # Mock compare_command to avoid full execution
        with patch.object(self.bot, 'compare_command', new_callable=AsyncMock) as mock_compare:
            # Call _handle_compare_input with multiple symbols
            await self.bot._handle_compare_input(self.update, self.context, "SPY.US QQQ.US")
            
            # Check that waiting flag was cleared
            user_context = self.context_store.get_user_context(12345)
            assert user_context['waiting_for_compare'] is False
            
            print("✅ Multiple symbols clear waiting flag")


async def run_tests():
    """Run all tests"""
    test_instance = TestCompareWaitingFlagFix()
    
    tests = [
        test_instance.test_first_symbol_keeps_waiting_flag,
        test_instance.test_second_symbol_clears_waiting_flag,
        test_instance.test_base_symbol_from_button_works,
        test_instance.test_multiple_symbols_clear_waiting_flag,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test_instance.setup_method()
            await test()
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

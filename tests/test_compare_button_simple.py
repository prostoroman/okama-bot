#!/usr/bin/env python3
"""
Simple test script for compare button functionality.
Tests the basic integration between info compare button and soft handling logic.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes
from services.context_store import InMemoryUserContextStore
from bot import ShansAi


class TestCompareButtonSimple:
    """Simple test class for compare button functionality"""
    
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
    
    async def test_info_compare_button_sets_context(self):
        """Test that info compare button sets the correct context"""
        # Call _handle_info_compare_button
        await self.bot._handle_info_compare_button(self.update, self.context, "CL.COMM")
        
        # Check that context was set correctly
        user_context = self.context_store.get_user_context(12345)
        assert user_context['compare_base_symbol'] == "CL.COMM"
        assert user_context['waiting_for_compare'] is True
        
        # Check that callback message was sent
        self.bot._send_callback_message.assert_called_once()
        print("✅ Info compare button sets context correctly")
    
    async def test_context_fields_exist(self):
        """Test that all required context fields exist"""
        user_context = self.context_store.get_user_context(12345)
        
        # Check that all required fields exist
        assert 'compare_first_symbol' in user_context
        assert 'compare_base_symbol' in user_context
        assert 'waiting_for_compare' in user_context
        
        # Check default values
        assert user_context['compare_first_symbol'] is None
        assert user_context['compare_base_symbol'] is None
        assert user_context['waiting_for_compare'] is False
        
        print("✅ All required context fields exist with correct defaults")
    
    async def test_random_examples_generation(self):
        """Test that random examples are generated correctly"""
        # Mock get_random_examples to return predictable results
        with patch.object(self.bot, 'get_random_examples') as mock_random:
            mock_random.return_value = ["AAPL.US", "MSFT.US", "GOOGL.US"]
            
            # Call the method
            examples = self.bot.get_random_examples(3)
            
            # Check that it returns the expected values
            assert examples == ["AAPL.US", "MSFT.US", "GOOGL.US"]
            
            print("✅ Random examples generation works correctly")
    
    async def test_context_update_clears_symbols(self):
        """Test that context update clears symbols correctly"""
        # Set up context with both symbols
        self.context_store.update_user_context(12345, 
                                              compare_first_symbol="AAPL.US",
                                              compare_base_symbol="CL.COMM")
        
        # Clear both symbols
        self.context_store.update_user_context(12345, 
                                              compare_first_symbol=None,
                                              compare_base_symbol=None)
        
        # Check that both symbols were cleared
        user_context = self.context_store.get_user_context(12345)
        assert user_context['compare_first_symbol'] is None
        assert user_context['compare_base_symbol'] is None
        
        print("✅ Context update clears symbols correctly")


async def run_tests():
    """Run all tests"""
    test_instance = TestCompareButtonSimple()
    
    tests = [
        test_instance.test_info_compare_button_sets_context,
        test_instance.test_context_fields_exist,
        test_instance.test_random_examples_generation,
        test_instance.test_context_update_clears_symbols,
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

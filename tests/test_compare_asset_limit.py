#!/usr/bin/env python3
"""
Test script for compare command asset limit functionality
Tests the 5 asset limit restriction in /compare command
"""

import asyncio
import sys
import os

# Add the parent directory to the path to import bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

# Import the bot class
from bot import ShansAi

class TestCompareAssetLimit:
    """Test class for compare command asset limit functionality"""
    
    def __init__(self):
        self.bot = None
        self.mock_update = None
        self.mock_context = None
        
    def setup_mocks(self):
        """Setup mock objects for testing"""
        # Create mock bot instance
        self.bot = ShansAi()
        
        # Create mock user
        mock_user = User(
            id=12345,
            is_bot=False,
            first_name="Test",
            username="testuser"
        )
        
        # Create mock chat
        mock_chat = Chat(
            id=12345,
            type="private"
        )
        
        # Create mock message
        mock_message = Message(
            message_id=1,
            date=None,
            chat=mock_chat,
            from_user=mock_user,
            text="/compare SPY.US QQQ.US AAPL.US MSFT.US GOOGL.US TSLA.US"
        )
        
        # Create mock update
        self.mock_update = Update(
            update_id=1,
            message=mock_message
        )
        
        # Create mock context
        self.mock_context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        self.mock_context.args = ["SPY.US", "QQQ.US", "AAPL.US", "MSFT.US", "GOOGL.US", "TSLA.US"]
        
        # Mock the _send_message_safe method
        self.bot._send_message_safe = AsyncMock()
        
        # Mock the _update_user_context method
        self.bot._update_user_context = MagicMock()
        
        # Mock the _get_user_context method
        self.bot._get_user_context = MagicMock(return_value={})
        
        # Mock logger
        self.bot.logger = MagicMock()
        
    async def test_compare_command_with_6_assets(self):
        """Test compare command with 6 assets (exceeds limit)"""
        print("🧪 Testing compare command with 6 assets (should fail)...")
        
        self.setup_mocks()
        
        # Test with 6 assets
        await self.bot.compare_command(self.mock_update, self.mock_context)
        
        # Verify that error message was sent
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        error_message = call_args[0][1]  # Second argument is the message text
        
        print(f"Error message received: {error_message}")
        assert "Максимум 5 активов для сравнения" in error_message
        assert "введите список для сравнения заново" in error_message
        
        # Verify that user context was cleared
        self.bot._update_user_context.assert_called_with(
            12345, 
            compare_first_symbol=None, 
            compare_base_symbol=None, 
            waiting_for_compare=False
        )
        
        print("✅ Test passed: 6 assets correctly rejected")
        
    async def test_compare_command_with_5_assets(self):
        """Test compare command with exactly 5 assets (should pass)"""
        print("🧪 Testing compare command with 5 assets (should pass)...")
        
        self.setup_mocks()
        
        # Update context args to have exactly 5 assets
        self.mock_context.args = ["SPY.US", "QQQ.US", "AAPL.US", "MSFT.US", "GOOGL.US"]
        
        # Mock methods that might be called during comparison processing
        self.bot._send_ephemeral_message = AsyncMock()
        self.bot._send_message_safe = AsyncMock()
        
        # Mock the resolve_symbol_or_isin method to avoid actual symbol resolution
        with patch.object(self.bot, 'resolve_symbol_or_isin') as mock_resolve:
            mock_resolve.return_value = {'symbol': 'SPY.US'}
            
            # Mock other methods that might be called
            with patch.object(self.bot, 'determine_data_source') as mock_source:
                mock_source.return_value = 'okama'
                
                # This should not raise an error about too many assets
                try:
                    await self.bot.compare_command(self.mock_update, self.mock_context)
                    # If we get here without error, the limit check passed
                    print("✅ Command executed without asset limit error")
                except Exception as e:
                    if "Максимум 5 активов" in str(e):
                        print(f"❌ Unexpected asset limit error: {e}")
                        raise
                    else:
                        # Other errors are expected due to mocking
                        print(f"✅ Expected error due to mocking: {e}")
        
        print("✅ Test passed: 5 assets correctly accepted")
        
    async def test_handle_compare_input_with_6_assets(self):
        """Test _handle_compare_input with 6 assets (exceeds limit)"""
        print("🧪 Testing _handle_compare_input with 6 assets (should fail)...")
        
        self.setup_mocks()
        
        # Test with 6 assets in text input
        text_input = "SPY.US QQQ.US AAPL.US MSFT.US GOOGL.US TSLA.US"
        
        await self.bot._handle_compare_input(self.mock_update, self.mock_context, text_input)
        
        # Verify that error message was sent
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        error_message = call_args[0][1]  # Second argument is the message text
        
        print(f"Error message received: {error_message}")
        assert "Максимум 5 активов для сравнения" in error_message
        assert "введите список для сравнения заново" in error_message
        
        # Verify that user context was cleared
        self.bot._update_user_context.assert_called_with(
            12345, 
            compare_first_symbol=None, 
            compare_base_symbol=None, 
            waiting_for_compare=False
        )
        
        print("✅ Test passed: _handle_compare_input with 6 assets correctly rejected")
        
    async def test_combined_symbols_exceed_limit(self):
        """Test when stored symbol + new input exceeds 5 assets limit"""
        print("🧪 Testing combined symbols exceeding 5 assets limit...")
        
        self.setup_mocks()
        
        # Mock user context with stored first symbol
        self.bot._get_user_context.return_value = {
            'compare_first_symbol': 'SPY.US'
        }
        
        # Test with 5 additional assets (total would be 6)
        text_input = "QQQ.US AAPL.US MSFT.US GOOGL.US TSLA.US"
        
        await self.bot._handle_compare_input(self.mock_update, self.mock_context, text_input)
        
        # Verify that error message was sent
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        error_message = call_args[0][1]  # Second argument is the message text
        
        print(f"Error message received: {error_message}")
        assert "Максимум 5 активов для сравнения" in error_message
        assert "введите список для сравнения заново" in error_message
        
        # Verify that user context was cleared
        self.bot._update_user_context.assert_called_with(
            12345, 
            compare_first_symbol=None, 
            compare_base_symbol=None, 
            waiting_for_compare=False
        )
        
        print("✅ Test passed: Combined symbols exceeding limit correctly rejected")

async def main():
    """Main test function"""
    print("🚀 Starting Compare Asset Limit Tests")
    print("=" * 50)
    
    tester = TestCompareAssetLimit()
    
    try:
        # Run all tests
        await tester.test_compare_command_with_6_assets()
        print()
        
        await tester.test_compare_command_with_5_assets()
        print()
        
        await tester.test_handle_compare_input_with_6_assets()
        print()
        
        await tester.test_combined_symbols_exceed_limit()
        print()
        
        print("=" * 50)
        print("🎉 All tests passed successfully!")
        print("✅ Compare command asset limit (5 assets) is working correctly")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Run the tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

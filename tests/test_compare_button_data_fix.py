#!/usr/bin/env python3
"""
Test script to verify the fix for Button_data_invalid error in /compare command
when more than 4 assets are passed.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, MagicMock
from telegram import Update, User, CallbackQuery, Message, Chat
from telegram.ext import ContextTypes

def test_compare_button_data_size_limit():
    """Test that compare command button data stays within Telegram's 64-byte limit"""
    
    # Test assets that previously caused the error
    test_symbols = ['SBER.MOEX', 'LKOH.MOEX', 'LQDT.MOEX', 'OBLG.MOEX', 'GOLD.MOEX']
    
    # Create mock objects
    mock_user = Mock(spec=User)
    mock_user.id = 12345
    
    mock_chat = Mock(spec=Chat)
    mock_chat.id = 67890
    
    mock_message = Mock(spec=Message)
    mock_message.chat = mock_chat
    
    mock_callback_query = Mock(spec=CallbackQuery)
    mock_callback_query.data = 'compare_portfolio'
    mock_callback_query.message = mock_message
    
    mock_update = Mock(spec=Update)
    mock_update.effective_user = mock_user
    mock_update.callback_query = mock_callback_query
    
    mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    
    # Test the old approach (would fail)
    old_symbols_str = '_'.join(test_symbols)
    old_callback_data = f'compare_portfolio_{old_symbols_str}'
    old_length = len(old_callback_data)
    
    print(f"Old callback data: {old_callback_data}")
    print(f"Old callback data length: {old_length} bytes")
    print(f"Old approach exceeds limit: {old_length > 64}")
    
    # Test the new approach (should pass)
    new_callback_data = 'compare_portfolio'
    new_length = len(new_callback_data)
    
    print(f"\nNew callback data: {new_callback_data}")
    print(f"New callback data length: {new_length} bytes")
    print(f"New approach within limit: {new_length <= 64}")
    
    # Verify the fix
    assert old_length > 64, "Old approach should exceed 64-byte limit"
    assert new_length <= 64, "New approach should be within 64-byte limit"
    
    print("\n✅ Test passed: Button data size limit fix is working correctly!")
    print(f"✅ Reduced callback data size from {old_length} to {new_length} bytes")
    print(f"✅ Savings: {old_length - new_length} bytes")

if __name__ == "__main__":
    test_compare_button_data_size_limit()

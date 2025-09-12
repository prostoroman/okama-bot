#!/usr/bin/env python3
"""
Test for info command routing fix
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import bot
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

class TestInfoRoutingFix(unittest.TestCase):
    """Test that info command routing works correctly"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
        
    def test_info_command_sets_waiting_flag(self):
        """Test that info command without args sets waiting_for_info flag"""
        # Mock update and context
        update = Mock()
        update.effective_user.id = 12345
        context = Mock()
        context.args = []  # No arguments
        
        # Mock the _update_user_context method
        with patch.object(self.bot, '_update_user_context') as mock_update_context:
            with patch.object(self.bot, '_send_message_safe') as mock_send_message:
                # Run the info command
                import asyncio
                asyncio.run(self.bot.info_command(update, context))
                
                # Check that waiting_for_info flag was set
                mock_update_context.assert_called_with(12345, waiting_for_info=True)
                
                # Check that help message was sent
                mock_send_message.assert_called_once()
                call_args = mock_send_message.call_args[0]
                self.assertIn("📊", call_args[1])
                self.assertIn("Информация об активе", call_args[1])
    
    def test_handle_message_processes_info_input(self):
        """Test that handle_message processes input as info when waiting_for_info is True"""
        # Mock update and context
        update = Mock()
        update.message = Mock()
        update.message.text = "HSBA.LSE"
        update.effective_user.id = 12345
        context = Mock()
        
        # Mock user context with waiting_for_info=True
        mock_user_context = {'waiting_for_info': True}
        
        with patch.object(self.bot, '_get_user_context', return_value=mock_user_context):
            with patch.object(self.bot, '_update_user_context') as mock_update_context:
                with patch.object(self.bot, 'info_command') as mock_info_command:
                    # Run handle_message
                    import asyncio
                    asyncio.run(self.bot.handle_message(update, context))
                    
                    # Check that waiting_for_info flag was cleared
                    mock_update_context.assert_called_with(12345, waiting_for_info=False)
                    
                    # Check that info_command was called with the symbol
                    mock_info_command.assert_called_once()
                    call_args = mock_info_command.call_args[0]
                    self.assertEqual(call_args[1].args, ["HSBA.LSE"])
    
    def test_handle_message_ignores_info_when_not_waiting(self):
        """Test that handle_message doesn't process as info when not waiting"""
        # Mock update and context
        update = Mock()
        update.message = Mock()
        update.message.text = "HSBA.LSE"
        update.effective_user.id = 12345
        context = Mock()
        
        # Mock user context without waiting_for_info
        mock_user_context = {'waiting_for_info': False}
        
        with patch.object(self.bot, '_get_user_context', return_value=mock_user_context):
            with patch.object(self.bot, 'info_command') as mock_info_command:
                # Run handle_message
                import asyncio
                asyncio.run(self.bot.handle_message(update, context))
                
                # Check that info_command was NOT called
                mock_info_command.assert_not_called()

if __name__ == '__main__':
    unittest.main()

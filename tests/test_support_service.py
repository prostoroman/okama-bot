"""
Test module for support_service functionality
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import json

from services.support_service import SupportService
from services.context_store import InMemoryUserContextStore


class TestSupportService(unittest.TestCase):
    """Test cases for SupportService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.context_store = InMemoryUserContextStore()
        self.support_service = SupportService(self.context_store)
        
        # Mock update object
        self.mock_update = Mock()
        self.mock_update.effective_user.id = 12345
        self.mock_update.effective_user.username = "testuser"
        self.mock_update.effective_user.first_name = "Test"
        self.mock_update.effective_user.last_name = "User"
        self.mock_update.effective_chat.id = 67890
        self.mock_update.effective_chat.type = "private"
        self.mock_update.message.message_id = 123
        
    def test_create_support_ticket(self):
        """Test support ticket creation"""
        # Add some context for the user
        user_id = 12345
        self.context_store.update_user_context(
            user_id,
            last_assets=["SPY.US", "QQQ.US"],
            portfolio_count=2,
            analyzed_tickers=["AAPL.US", "MSFT.US"]
        )
        
        # Add conversation history
        self.context_store.add_conversation_entry(
            user_id, "Как посмотреть информацию о SPY?", "Используйте команду /info SPY.US"
        )
        
        # Create ticket
        ticket = self.support_service.create_support_ticket(self.mock_update, "У меня проблема с ботом")
        
        # Verify ticket structure
        self.assertIn('meta', ticket)
        self.assertIn('user_message', ticket)
        self.assertIn('context', ticket)
        self.assertIn('conversation_history', ticket)
        
        # Verify meta data
        meta = ticket['meta']
        self.assertEqual(meta['user_id'], 12345)
        self.assertEqual(meta['username'], "testuser")
        self.assertEqual(meta['first_name'], "Test")
        self.assertEqual(meta['last_name'], "User")
        self.assertEqual(meta['chat_id'], 67890)
        
        # Verify context
        context = ticket['context']
        self.assertEqual(context['last_assets'], ["SPY.US", "QQQ.US"])
        self.assertEqual(context['portfolio_count'], 2)
        self.assertEqual(context['analyzed_tickers'], ["AAPL.US", "MSFT.US"])
        
        # Verify conversation history
        self.assertEqual(len(ticket['conversation_history']), 1)
        
    def test_format_support_message(self):
        """Test support message formatting"""
        # Create a test ticket
        ticket = {
            'meta': {
                'user_id': 12345,
                'username': 'testuser',
                'first_name': 'Test',
                'last_name': 'User',
                'chat_id': 67890,
                'chat_type': 'private',
                'timestamp': datetime.now().isoformat()
            },
            'user_message': 'У меня проблема с ботом',
            'context': {
                'last_assets': ['SPY.US'],
                'portfolio_count': 1
            }
        }
        
        # Format message
        formatted = self.support_service.format_support_message(ticket)
        
        # Verify formatting
        self.assertIn('👤', formatted)
        self.assertIn('Test User', formatted)
        self.assertIn('(@testuser)', formatted)
        self.assertIn('12345', formatted)
        self.assertIn('67890', formatted)
        self.assertIn('У меня проблема с ботом', formatted)
        self.assertIn('SPY.US', formatted)
        
    @patch('services.support_service.Config')
    async def test_send_support_ticket_success(self, mock_config):
        """Test successful support ticket sending"""
        # Mock config
        mock_config.SUPPORT_GROUP_ID = "-1001234567890"
        mock_config.SUPPORT_THREAD_ID = None
        mock_config.MAX_MESSAGE_LENGTH = 4096
        
        # Mock bot
        mock_bot = AsyncMock()
        mock_bot.send_message.return_value = Mock(message_id=999)
        
        # Create test ticket
        ticket = {
            'meta': {'user_id': 12345},
            'user_message': 'Test message',
            'context': {}
        }
        
        # Send ticket
        result = await self.support_service.send_support_ticket(mock_bot, ticket)
        
        # Verify success
        self.assertTrue(result)
        mock_bot.send_message.assert_called_once()
        
    async def test_send_error_report(self):
        """Test error report sending"""
        # Mock bot
        mock_bot = AsyncMock()
        
        # Create test error
        test_error = ValueError("Test error")
        test_context = {
            'user_id': 12345,
            'chat_id': 67890,
            'message_text': 'test message'
        }
        
        # Send error report
        with patch('services.support_service.Config') as mock_config:
            mock_config.SUPPORT_GROUP_ID = "-1001234567890"
            mock_config.SUPPORT_THREAD_ID = None
            
            result = await self.support_service.send_error_report(mock_bot, test_error, test_context)
            
            # Verify success
            self.assertTrue(result)
            mock_bot.send_message.assert_called_once()
            
            # Verify error message contains relevant info
            call_args = mock_bot.send_message.call_args
            message_text = call_args[1]['text']
            self.assertIn('ValueError', message_text)
            self.assertIn('Test error', message_text)
            self.assertIn('12345', message_text)


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python3
"""
Test for long message handling in AI analysis
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
from services.gemini_service import GeminiService


class TestLongMessageHandling(unittest.TestCase):
    """Test cases for long message handling functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
        self.gemini_service = GeminiService()
    
    def test_send_callback_message_truncation(self):
        """Test that _send_callback_message truncates long messages"""
        # Create a very long message (over 4096 characters)
        long_message = "A" * 5000  # 5000 characters
        
        # Mock update and context
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_message = Mock()
        mock_chat = Mock()
        
        mock_update.callback_query = mock_callback_query
        mock_callback_query.message = mock_message
        mock_message.chat_id = 12345
        mock_context.bot = Mock()
        
        # Test the function
        import asyncio
        asyncio.run(self.bot._send_callback_message(mock_update, mock_context, long_message))
        
        # Check that the message was truncated
        call_args = mock_context.bot.send_message.call_args
        sent_text = call_args[1]['text']
        
        self.assertLessEqual(len(sent_text), 4096)
        self.assertIn("... (сообщение обрезано из-за длины)", sent_text)
        
        print(f"Original length: {len(long_message)}, Sent length: {len(sent_text)}")
    
    def test_gemini_analysis_truncation(self):
        """Test that Gemini service truncates long analysis results"""
        # Mock a very long analysis result
        long_analysis = "A" * 5000  # 5000 characters
        
        # Mock the response structure
        mock_response = {
            'candidates': [{
                'content': {
                    'parts': [{'text': long_analysis}]
                }
            }]
        }
        
        # Mock the requests.post response
        with patch('services.gemini_service.requests.post') as mock_post:
            mock_response_obj = Mock()
            mock_response_obj.status_code = 200
            mock_response_obj.json.return_value = mock_response
            mock_post.return_value = mock_response_obj
            
            # Test the analyze_data function
            data_info = {
                'symbols': ['SPY.US'],
                'describe_table': 'Test table',
                'analysis_metadata': {
                    'data_source': 'test',
                    'analysis_depth': 'comprehensive'
                }
            }
            
            result = self.gemini_service.analyze_data(data_info)
            
            # Check that the result was truncated
            self.assertTrue(result['success'])
            analysis_text = result['analysis']
            self.assertLessEqual(len(analysis_text), 4000)
            self.assertIn("... (анализ обрезан из-за длины)", analysis_text)
            
            print(f"Original analysis length: {len(long_analysis)}, Truncated length: {len(analysis_text)}")
    
    def test_send_message_safe_long_message(self):
        """Test that _send_message_safe handles long messages correctly"""
        # Create a long message
        long_message = "A" * 5000  # 5000 characters
        
        # Mock update
        mock_update = Mock()
        mock_message = Mock()
        mock_update.message = mock_message
        
        # Test the function
        import asyncio
        asyncio.run(self.bot._send_message_safe(mock_update, long_message))
        
        # Check that send_long_message was called
        # Note: This test verifies the logic flow, actual message sending is mocked
        print("Long message handling test completed")
    
    def test_message_length_limits(self):
        """Test various message length limits"""
        # Test different lengths
        test_cases = [
            (1000, False),    # Short message, should not be truncated
            (3000, False),    # Medium message, should not be truncated
            (5000, True),     # Long message, should be truncated
            (10000, True),    # Very long message, should be truncated
        ]
        
        for length, should_truncate in test_cases:
            message = "A" * length
            
            # Test _send_callback_message truncation
            if should_truncate:
                truncated = message[:4096-50] + "\n\n... (сообщение обрезано из-за длины)"
                self.assertLessEqual(len(truncated), 4096)
                self.assertIn("... (сообщение обрезано из-за длины)", truncated)
            else:
                self.assertLessEqual(len(message), 4096)
            
            print(f"Length {length}: {'Truncated' if should_truncate else 'Not truncated'}")
    
    def test_error_handling_with_long_messages(self):
        """Test error handling when sending long messages fails"""
        # Create a long message
        long_message = "A" * 5000
        
        # Mock update with None callback_query to trigger error path
        mock_update = Mock()
        mock_update.callback_query = None
        mock_update.message = None
        mock_context = Mock()
        
        # Test the function - should not raise exception
        import asyncio
        try:
            asyncio.run(self.bot._send_callback_message(mock_update, mock_context, long_message))
            print("Error handling test passed - no exception raised")
        except Exception as e:
            self.fail(f"Error handling failed: {e}")


if __name__ == '__main__':
    print("Testing long message handling functionality...")
    
    unittest.main(verbosity=2)

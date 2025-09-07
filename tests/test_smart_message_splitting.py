#!/usr/bin/env python3
"""
Test for smart message splitting functionality
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestSmartMessageSplitting(unittest.TestCase):
    """Test cases for smart message splitting functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    def test_split_text_smart_single_message(self):
        """Test that short messages are not split"""
        short_text = "This is a short message"
        parts = self.bot._split_text_smart(short_text)
        
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], short_text)
        
        print(f"Short message test: {len(parts)} part(s)")
    
    def test_split_text_smart_multiple_parts(self):
        """Test that long messages are split into multiple parts"""
        # Create a long message (over 4000 characters)
        long_text = "Line " + "\n".join([f"Line {i}" for i in range(1000)])
        
        parts = self.bot._split_text_smart(long_text)
        
        self.assertGreater(len(parts), 1)
        
        # Check that each part is within limits
        for i, part in enumerate(parts):
            self.assertLessEqual(len(part), 4000, f"Part {i+1} is too long: {len(part)} chars")
        
        print(f"Long message test: {len(parts)} parts")
        for i, part in enumerate(parts):
            print(f"  Part {i+1}: {len(part)} characters")
    
    def test_split_text_smart_preserves_structure(self):
        """Test that splitting preserves text structure"""
        structured_text = """# Header 1
This is paragraph 1.

## Header 2
This is paragraph 2 with multiple lines.
Line 2 of paragraph 2.
Line 3 of paragraph 2.

### Header 3
This is paragraph 3.

## Another Header
This is another paragraph with a very long line that might need to be split because it contains a lot of text and could potentially exceed the maximum length limit for a single message part.

Final paragraph."""
        
        parts = self.bot._split_text_smart(structured_text)
        
        # Check that splitting preserves line breaks
        for part in parts:
            self.assertIn('\n', part)  # Each part should contain line breaks
        
        # Reconstruct and check that structure is preserved
        reconstructed = '\n'.join(parts)
        self.assertIn("# Header 1", reconstructed)
        self.assertIn("## Header 2", reconstructed)
        self.assertIn("### Header 3", reconstructed)
        
        print(f"Structure preservation test: {len(parts)} parts")
    
    def test_split_text_smart_long_line(self):
        """Test splitting of very long lines"""
        # Create a very long line (over 4000 characters)
        long_line = "This is a very long line with many words " * 100  # ~4000+ characters
        
        parts = self.bot._split_text_smart(long_line)
        
        self.assertGreater(len(parts), 1)
        
        # Check that each part is within limits
        for i, part in enumerate(parts):
            self.assertLessEqual(len(part), 4000, f"Part {i+1} is too long: {len(part)} chars")
        
        print(f"Long line test: {len(parts)} parts")
    
    def test_split_text_smart_mixed_content(self):
        """Test splitting of mixed content (short and long lines)"""
        mixed_text = """Short line
Another short line

""" + "Very long line with many words " * 200 + """

Short line again
Another short line

""" + "Another very long line " * 150 + """

Final short line"""
        
        parts = self.bot._split_text_smart(mixed_text)
        
        self.assertGreater(len(parts), 1)
        
        # Check that each part is within limits
        for i, part in enumerate(parts):
            self.assertLessEqual(len(part), 4000, f"Part {i+1} is too long: {len(part)} chars")
        
        print(f"Mixed content test: {len(parts)} parts")
    
    def test_split_text_smart_empty_and_whitespace(self):
        """Test handling of empty and whitespace-only content"""
        # Test empty string
        parts = self.bot._split_text_smart("")
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], "")
        
        # Test whitespace-only string
        parts = self.bot._split_text_smart("   \n\n   ")
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], "   \n\n   ")
        
        print("Empty and whitespace test passed")
    
    def test_split_text_smart_boundary_cases(self):
        """Test boundary cases around the 4000 character limit"""
        # Test exactly 4000 characters
        exact_text = "A" * 4000
        parts = self.bot._split_text_smart(exact_text)
        self.assertEqual(len(parts), 1)
        self.assertEqual(len(parts[0]), 4000)
        
        # Test 4001 characters
        over_text = "A" * 4001
        parts = self.bot._split_text_smart(over_text)
        self.assertEqual(len(parts), 2)
        self.assertEqual(len(parts[0]), 4000)
        self.assertEqual(len(parts[1]), 1)
        
        print("Boundary cases test passed")
    
    async def test_send_long_callback_message(self):
        """Test sending long callback messages"""
        # Create a long message
        long_message = "Line " + "\n".join([f"Line {i}" for i in range(1000)])
        
        # Mock update and context
        mock_update = Mock()
        mock_context = Mock()
        mock_callback_query = Mock()
        mock_message = Mock()
        mock_bot = AsyncMock()
        
        mock_update.callback_query = mock_callback_query
        mock_callback_query.message = mock_message
        mock_message.chat_id = 12345
        mock_context.bot = mock_bot
        
        # Test the function
        await self.bot._send_long_callback_message(mock_update, mock_context, long_message)
        
        # Check that multiple messages were sent
        self.assertGreater(mock_bot.send_message.call_count, 1)
        
        print(f"Long callback message test: {mock_bot.send_message.call_count} messages sent")
    
    def test_send_long_callback_message_sync(self):
        """Test sending long callback messages (synchronous wrapper)"""
        import asyncio
        
        async def run_test():
            await self.test_send_long_callback_message()
        
        asyncio.run(run_test())
    
    def test_split_text_smart_performance(self):
        """Test performance with very large text"""
        import time
        
        # Create a very large text (10000+ characters)
        large_text = "This is a test line with some content. " * 500  # ~20,000 characters
        
        start_time = time.time()
        parts = self.bot._split_text_smart(large_text)
        end_time = time.time()
        
        # Should complete quickly (under 1 second)
        self.assertLess(end_time - start_time, 1.0)
        
        # Should create multiple parts
        self.assertGreater(len(parts), 1)
        
        print(f"Performance test: {len(parts)} parts in {end_time - start_time:.3f} seconds")


if __name__ == '__main__':
    print("Testing smart message splitting functionality...")
    
    unittest.main(verbosity=2)

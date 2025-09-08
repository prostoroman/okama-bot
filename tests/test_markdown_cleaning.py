#!/usr/bin/env python3
"""
Test for Markdown cleaning functionality
"""

import unittest
import sys
import os

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestMarkdownCleaning(unittest.TestCase):
    """Test cases for Markdown cleaning functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    def test_clean_unclosed_bold_markers(self):
        """Test cleaning of unclosed bold markers"""
        # Test case 1: Unclosed bold marker
        text_with_unclosed_bold = "This is **bold text without closing"
        cleaned_text = self.bot._clean_markdown(text_with_unclosed_bold)
        
        # Should remove the unclosed **
        expected = "This is bold text without closing"
        self.assertEqual(cleaned_text, expected)
        print(f"✅ Unclosed bold marker test passed: '{cleaned_text}'")
        
        # Test case 2: Multiple unclosed bold markers
        text_with_multiple_unclosed = "**First** **Second without closing **Third**"
        cleaned_text = self.bot._clean_markdown(text_with_multiple_unclosed)
        
        # Should remove the unclosed ** (the one before "Third")
        expected = "**First** **Second without closing Third**"
        self.assertEqual(cleaned_text, expected)
        print(f"✅ Multiple unclosed bold markers test passed: '{cleaned_text}'")
    
    def test_clean_unclosed_italic_markers(self):
        """Test cleaning of unclosed italic markers"""
        # Test case 1: Unclosed italic marker
        text_with_unclosed_italic = "This is *italic text without closing"
        cleaned_text = self.bot._clean_markdown(text_with_unclosed_italic)
        
        # Should remove the unclosed *
        expected = "This is italic text without closing"
        self.assertEqual(cleaned_text, expected)
        print(f"✅ Unclosed italic marker test passed: '{cleaned_text}'")
    
    def test_clean_unclosed_code_blocks(self):
        """Test cleaning of unclosed code blocks"""
        # Test case 1: Unclosed code block
        text_with_unclosed_code = "Here is some code:\n```python\nprint('hello')\n# Missing closing ```"
        cleaned_text = self.bot._clean_markdown(text_with_unclosed_code)
        
        # Should remove the unclosed ``` and everything after it
        expected = "Here is some code:\nprint('hello')\n# Missing closing"
        self.assertEqual(cleaned_text, expected)
        print(f"✅ Unclosed code block test passed: '{cleaned_text}'")
    
    def test_clean_unclosed_inline_code(self):
        """Test cleaning of unclosed inline code"""
        # Test case 1: Unclosed inline code
        text_with_unclosed_inline = "Use the `function without closing"
        cleaned_text = self.bot._clean_markdown(text_with_unclosed_inline)
        
        # Should remove the unclosed `
        expected = "Use the function without closing"
        self.assertEqual(cleaned_text, expected)
        print(f"✅ Unclosed inline code test passed: '{cleaned_text}'")
    
    def test_clean_problematic_sequences(self):
        """Test cleaning of problematic sequences"""
        # Test case 1: Multiple asterisks
        text_with_multiple_asterisks = "This is ****very**** bold"
        cleaned_text = self.bot._clean_markdown(text_with_multiple_asterisks)
        
        # Should reduce to **
        expected = "This is **very** bold"
        self.assertEqual(cleaned_text, expected)
        print(f"✅ Multiple asterisks test passed: '{cleaned_text}'")
        
        # Test case 2: Three asterisks
        text_with_three_asterisks = "This is ***very*** bold"
        cleaned_text = self.bot._clean_markdown(text_with_three_asterisks)
        
        # Should reduce to **
        expected = "This is **very** bold"
        self.assertEqual(cleaned_text, expected)
        print(f"✅ Three asterisks test passed: '{cleaned_text}'")
    
    def test_clean_underscores(self):
        """Test cleaning of underscores"""
        # Test case 1: Underscores that are not part of markdown
        text_with_underscores = "This is a_function_call() and another_function"
        cleaned_text = self.bot._clean_markdown(text_with_underscores)
        
        # Should escape underscores
        expected = "This is a\\_function\\_call() and another\\_function"
        self.assertEqual(cleaned_text, expected)
        print(f"✅ Underscores test passed: '{cleaned_text}'")
    
    def test_clean_valid_markdown(self):
        """Test that valid markdown is preserved"""
        # Test case 1: Valid markdown
        valid_markdown = "**Bold text** and *italic text* and `inline code`"
        cleaned_text = self.bot._clean_markdown(valid_markdown)
        
        # Should remain unchanged
        self.assertEqual(cleaned_text, valid_markdown)
        print(f"✅ Valid markdown preservation test passed: '{cleaned_text}'")
        
        # Test case 2: Valid code block
        valid_code_block = "Here is code:\n```python\nprint('hello')\n```\nEnd of code"
        cleaned_text = self.bot._clean_markdown(valid_code_block)
        
        # Should remain unchanged
        self.assertEqual(cleaned_text, valid_code_block)
        print(f"✅ Valid code block preservation test passed")
    
    def test_clean_complex_markdown(self):
        """Test cleaning of complex markdown with multiple issues"""
        # Complex text with multiple issues
        complex_text = """
        **Analysis Results:**

        **Asset Performance:**
        - **SPY.US:** 12.5% return
        - **QQQ.US:** 15.2% return

        **Risk Metrics:**
        - Sharpe Ratio: **0.85**
        - Sortino Ratio: *0.92*

        **Code Example:**
        ```python
        def calculate_return(prices):
            return (prices[-1] / prices[0]) - 1
        # Missing closing ```

        **Conclusion:** This is a `function_call() with underscore
        """
        
        cleaned_text = self.bot._clean_markdown(complex_text)
        
        # Should fix the issues but preserve valid markdown
        self.assertNotIn("```python", cleaned_text)  # Should remove unclosed code block
        self.assertNotIn("`function_call() with underscore", cleaned_text)  # Should remove unclosed inline code
        self.assertIn("**Analysis Results:**", cleaned_text)  # Should preserve valid bold
        self.assertIn("**SPY.US:**", cleaned_text)  # Should preserve valid bold
        
        print(f"✅ Complex markdown cleaning test passed")
        print(f"Cleaned text length: {len(cleaned_text)}")
    
    def test_clean_error_handling(self):
        """Test error handling in markdown cleaning"""
        # Test case 1: None input
        try:
            cleaned_text = self.bot._clean_markdown(None)
            self.fail("Should have handled None input")
        except Exception as e:
            print(f"✅ None input handling test passed: {e}")
        
        # Test case 2: Empty string
        cleaned_text = self.bot._clean_markdown("")
        self.assertEqual(cleaned_text, "")
        print(f"✅ Empty string test passed: '{cleaned_text}'")


if __name__ == '__main__':
    print("Testing Markdown cleaning functionality...")
    
    unittest.main(verbosity=2)

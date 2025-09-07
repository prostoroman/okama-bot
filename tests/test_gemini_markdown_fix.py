#!/usr/bin/env python3
"""
Test for Gemini analysis Markdown error fix
"""

import unittest
import sys
import os

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestGeminiAnalysisMarkdownFix(unittest.TestCase):
    """Test cases for Gemini analysis Markdown error fix"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.bot = ShansAi()
    
    def test_safe_markdown_simple(self):
        """Test safe markdown cleaning - simple cases"""
        # Test case 1: Unclosed bold
        text = "This is **bold without closing"
        cleaned = self.bot._safe_markdown(text)
        expected = "This is bold without closing"
        self.assertEqual(cleaned, expected)
        print(f"✅ Safe markdown unclosed bold test passed: '{cleaned}'")
        
        # Test case 2: Unclosed italic
        text = "This is *italic without closing"
        cleaned = self.bot._safe_markdown(text)
        expected = "This is italic without closing"
        self.assertEqual(cleaned, expected)
        print(f"✅ Safe markdown unclosed italic test passed: '{cleaned}'")
        
        # Test case 3: Unclosed inline code
        text = "This is `code without closing"
        cleaned = self.bot._safe_markdown(text)
        expected = "This is code without closing"
        self.assertEqual(cleaned, expected)
        print(f"✅ Safe markdown unclosed inline code test passed: '{cleaned}'")
    
    def test_safe_markdown_valid_preserved(self):
        """Test that valid markdown is preserved"""
        valid_text = "**Bold** and *italic* and `code` work fine"
        cleaned = self.bot._safe_markdown(valid_text)
        self.assertEqual(cleaned, valid_text)
        print(f"✅ Safe markdown valid preservation test passed: '{cleaned}'")
    
    def test_safe_markdown_complex_ai_response(self):
        """Test safe markdown with AI-like response"""
        ai_response = """
**📊 Анализ портфеля:**

**Активы:**
- **SPY.US:** S&P 500 ETF (доходность: 12.5%)
- **QQQ.US:** NASDAQ-100 ETF (доходность: 15.2%

**Метрики риска:**
- Sharpe Ratio: **0.85**
- Sortino Ratio: *0.92*

**Рекомендации:**
Портфель показывает хорошую производительность, но рекомендуется диверсификация в `fixed_income` активы для снижения волатильности.
        """
        
        cleaned = self.bot._safe_markdown(ai_response)
        
        # Should preserve valid markdown and fix unclosed ones
        self.assertIn("**📊 Анализ портфеля:**", cleaned)
        self.assertIn("**SPY.US:**", cleaned)
        self.assertIn("**QQQ.US:**", cleaned)
        self.assertIn("**Метрики риска:**", cleaned)
        self.assertIn("**0.85**", cleaned)
        self.assertIn("*0.92*", cleaned)
        self.assertIn("`fixed\\_income`", cleaned)  # Escaped underscore
        
        # Should not contain unclosed markdown
        bold_count = cleaned.count('**')
        self.assertEqual(bold_count % 2, 0, "Bold markers should be balanced")
        
        italic_count = cleaned.count('*')
        self.assertEqual(italic_count % 2, 0, "Italic markers should be balanced")
        
        code_count = cleaned.count('`')
        self.assertEqual(code_count % 2, 0, "Code markers should be balanced")
        
        print(f"✅ Complex AI response test passed")
        print(f"Cleaned text length: {len(cleaned)}")
    
    def test_safe_markdown_error_handling(self):
        """Test error handling in safe markdown"""
        # Test None input
        cleaned = self.bot._safe_markdown(None)
        self.assertEqual(cleaned, "")
        print(f"✅ None input handling test passed: '{cleaned}'")
        
        # Test empty string
        cleaned = self.bot._safe_markdown("")
        self.assertEqual(cleaned, "")
        print(f"✅ Empty string test passed: '{cleaned}'")
        
        # Test non-string input
        cleaned = self.bot._safe_markdown(123)
        self.assertEqual(cleaned, 123)  # Returns original non-string input
        print(f"✅ Non-string input test passed: '{cleaned}'")
    
    def test_gemini_analysis_simulation(self):
        """Test simulation of Gemini analysis response"""
        # Simulate a problematic Gemini response that caused the original error
        problematic_response = """
**📈 Финансовый анализ активов**

**Основные метрики:**

| Актив | Доходность | Волатильность | Sharpe Ratio |
|-------|------------|---------------|--------------|
| SPY.US | 12.5% | 15.8% | **0.79** |
| QQQ.US | 15.2% | 18.3% | *0.83* |

**Анализ корреляций:**
Корреляция между активами составляет `0.85`, что указывает на высокую связанность.

**Рекомендации:**
1. **Диверсификация:** Рассмотрите добавление `bond_etf` для снижения волатильности
2. **Ребалансировка:** Проводите ребалансировку каждые `6_months`
3. **Мониторинг:** Отслеживайте изменения в `market_conditions
        """
        
        # This text has unclosed markdown that would cause parsing errors
        cleaned = self.bot._safe_markdown(problematic_response)
        
        # Should be cleanable without errors
        self.assertIsInstance(cleaned, str)
        self.assertGreater(len(cleaned), 0)
        
        # Check that main content is preserved
        self.assertIn("Финансовый анализ", cleaned)
        self.assertIn("SPY.US", cleaned)
        self.assertIn("QQQ.US", cleaned)
        self.assertIn("Диверсификация", cleaned)
        
        # Check that problematic parts are fixed
        self.assertIn("market\\_conditions", cleaned)  # Fixed underscore
        
        print(f"✅ Gemini analysis simulation test passed")
        print(f"Original length: {len(problematic_response)}")
        print(f"Cleaned length: {len(cleaned)}")


if __name__ == '__main__':
    print("Testing Gemini analysis Markdown error fix...")
    
    unittest.main(verbosity=2)

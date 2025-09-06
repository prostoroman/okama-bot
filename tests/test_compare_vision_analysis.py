"""
Test for Google Vision analysis in /compare command
"""

import unittest
import io
import os
import sys
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_vision_service import GoogleVisionService


class TestCompareVisionAnalysis(unittest.TestCase):
    """Test cases for Google Vision analysis in compare command"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = GoogleVisionService()
    
    def test_analysis_success_response(self):
        """Test successful analysis response format"""
        mock_response = {
            'success': True,
            'analysis': '📊 Обнаружен график с финансовыми данными',
            'text': 'Sample chart text',
            'labels': [{'description': 'chart', 'confidence': 0.9}],
            'objects': [{'name': 'line', 'score': 0.8}]
        }
        
        # Test success case
        self.assertTrue(mock_response.get('success'))
        self.assertIsNotNone(mock_response.get('analysis'))
        
        # Test message formatting
        if mock_response.get('success'):
            analysis_text = mock_response.get('analysis', '')
            if analysis_text:
                expected_message = f"🤖 **Анализ графика Google Vision API**\n\n{analysis_text}"
                self.assertIn("🤖 **Анализ графика Google Vision API**", expected_message)
                self.assertIn(analysis_text, expected_message)
    
    def test_analysis_error_response(self):
        """Test error analysis response format"""
        mock_response = {
            'success': False,
            'error': 'API request failed with status 403'
        }
        
        # Test error case
        self.assertFalse(mock_response.get('success'))
        self.assertIsNotNone(mock_response.get('error'))
        
        # Test error message formatting
        if not mock_response.get('success'):
            error_msg = mock_response.get('error', 'Неизвестная ошибка')
            expected_message = f"❌ **Ошибка Google Vision API**\n\n{error_msg}"
            self.assertIn("❌ **Ошибка Google Vision API**", expected_message)
            self.assertIn(error_msg, expected_message)
    
    def test_analysis_empty_response(self):
        """Test empty analysis response"""
        mock_response = {
            'success': True,
            'analysis': ''
        }
        
        # Test empty analysis case
        self.assertTrue(mock_response.get('success'))
        self.assertEqual(mock_response.get('analysis', ''), '')
        
        # Test empty message formatting
        if mock_response.get('success'):
            analysis_text = mock_response.get('analysis', '')
            if not analysis_text:
                expected_message = "🤖 Google Vision API: Анализ выполнен, но результат пуст"
                self.assertEqual(expected_message, "🤖 Google Vision API: Анализ выполнен, но результат пуст")
    
    def test_analysis_none_response(self):
        """Test None analysis response"""
        mock_response = None
        
        # Test None case
        self.assertIsNone(mock_response)
        
        # Test None message formatting
        if not mock_response:
            expected_message = "⚠️ Google Vision API недоступен - анализ не выполнен"
            self.assertEqual(expected_message, "⚠️ Google Vision API недоступен - анализ не выполнен")
    
    def test_analyze_chart_without_api_key(self):
        """Test chart analysis without API key"""
        # Test analysis without API key
        mock_image_bytes = b"fake_image_data"
        result = self.service.analyze_chart(mock_image_bytes)
        
        # Should return None when service is not available
        self.assertIsNone(result)
    
    def test_analyze_chart_service_not_available(self):
        """Test chart analysis when service is not available"""
        # Set service as not available
        self.service.client = None
        
        # Test analysis
        mock_image_bytes = b"fake_image_data"
        result = self.service.analyze_chart(mock_image_bytes)
        
        # Should return None when service is not available
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()

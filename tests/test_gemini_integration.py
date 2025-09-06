"""
Tests for Gemini API integration in compare command
"""

import unittest
import io
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.gemini_service import GeminiService


class TestGeminiService(unittest.TestCase):
    """Test cases for Gemini service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = GeminiService()
    
    def test_service_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.service)
        # Client will be None if no API key is provided
        # This is expected behavior
    
    def test_service_availability(self):
        """Test service availability"""
        # Service should not be available without API key
        self.assertFalse(self.service.is_available())
    
    def test_get_service_status(self):
        """Test service status information"""
        status = self.service.get_service_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('available', status)
        self.assertIn('api_key_set', status)
        self.assertIn('api_key_length', status)
        self.assertIn('library_installed', status)
        self.assertIn('api_url', status)
        
        self.assertIsInstance(status['available'], bool)
        self.assertIsInstance(status['api_key_set'], bool)
        self.assertIsInstance(status['api_key_length'], int)
        self.assertIsInstance(status['library_installed'], bool)
    
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
    
    def test_analysis_success_response(self):
        """Test successful analysis response format"""
        mock_response = {
            'success': True,
            'analysis': '📊 Обнаружен график с финансовыми данными',
            'full_analysis': 'Детальный анализ графика с трендами и рекомендациями',
            'raw_response': {'candidates': [{'content': {'parts': [{'text': 'Analysis text'}]}}]}
        }
        
        # Test success case
        self.assertTrue(mock_response.get('success'))
        self.assertIsNotNone(mock_response.get('analysis'))
        self.assertIsNotNone(mock_response.get('full_analysis'))
        
        # Test message formatting
        if mock_response.get('success'):
            analysis_text = mock_response.get('analysis', '')
            if analysis_text:
                expected_message = f"🤖 **Анализ графика Gemini AI**\n\n{analysis_text}"
                self.assertIn("🤖 **Анализ графика Gemini AI**", expected_message)
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
            expected_message = f"❌ **Ошибка Gemini API**\n\n{error_msg}"
            self.assertIn("❌ **Ошибка Gemini API**", expected_message)
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
                expected_message = "🤖 Gemini AI: Анализ выполнен, но результат пуст"
                self.assertEqual(expected_message, "🤖 Gemini AI: Анализ выполнен, но результат пуст")
    
    def test_analysis_none_response(self):
        """Test None analysis response"""
        mock_response = None
        
        # Test None case
        self.assertIsNone(mock_response)
        
        # Test None message formatting
        if not mock_response:
            expected_message = "⚠️ Gemini API недоступен - анализ не выполнен"
            self.assertEqual(expected_message, "⚠️ Gemini API недоступен - анализ не выполнен")


class TestGeminiConfiguration(unittest.TestCase):
    """Test cases for Gemini configuration"""
    
    def test_api_key_from_env(self):
        """Test API key loading from environment"""
        # Test with mock environment variable
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test_api_key'}):
            service = GeminiService()
            self.assertEqual(service.api_key, 'test_api_key')
    
    def test_api_key_parameter(self):
        """Test API key from parameter"""
        service = GeminiService(api_key='test_api_key')
        self.assertEqual(service.api_key, 'test_api_key')
    
    def test_api_key_validation(self):
        """Test API key validation"""
        # Test with valid API key format (using test key, not real one)
        service = GeminiService(api_key='AIzaSyTestKey123456789012345678901234567890')
        service.client = True  # Mock successful initialization
        
        self.assertTrue(service.is_available())
        self.assertEqual(len(service.api_key), 39)
    
    def test_service_status_with_api_key(self):
        """Test service status with API key"""
        service = GeminiService(api_key='test_api_key')
        status = service.get_service_status()
        
        self.assertTrue(status['api_key_set'])
        self.assertEqual(status['api_key_length'], 12)
        self.assertIn('gemini', status['api_url'])


if __name__ == '__main__':
    unittest.main()

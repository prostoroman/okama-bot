"""
Tests for Google Vision API integration in compare command
"""

import unittest
import io
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import tempfile

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.google_vision_service import GoogleVisionService


class TestGoogleVisionService(unittest.TestCase):
    """Test cases for Google Vision service"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = GoogleVisionService()
    
    def test_service_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.service)
        # Client will be None if no API key is provided
        # This is expected behavior
    
    def test_is_available(self):
        """Test service availability check"""
        # This will depend on actual credentials
        availability = self.service.is_available()
        self.assertIsInstance(availability, bool)
    
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
    
    def test_analyze_chart_with_mock(self):
        """Test chart analysis with mocked Google Vision API"""
        # Create a mock image
        mock_image_bytes = b"fake_image_data"
        
        # Mock the Google Vision API response
        mock_api_response = {
            "responses": [
                {
                    "textAnnotations": [
                        {
                            "description": "Sample chart text"
                        }
                    ],
                    "labelAnnotations": [
                        {
                            "description": "chart",
                            "score": 0.9
                        }
                    ],
                    "localizedObjectAnnotations": [
                        {
                            "name": "line",
                            "score": 0.8
                        }
                    ]
                }
            ]
        }
        
        # Mock requests.post
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response
        
        # Patch requests.post and set up API key
        with patch('requests.post', return_value=mock_response):
            with patch.object(self.service, 'api_key', 'test_api_key'):
                with patch.object(self.service, 'client', True):  # Mark as available
                    result = self.service.analyze_chart(mock_image_bytes)
        
        self.assertIsNotNone(result)
        self.assertIn('success', result)
        self.assertIn('text', result)
        self.assertIn('labels', result)
        self.assertIn('objects', result)
        self.assertIn('analysis', result)
    
    def test_analyze_chart_without_client(self):
        """Test chart analysis when client is not available"""
        # Set client to None
        self.service.client = None
        
        result = self.service.analyze_chart(b"fake_image_data")
        
        self.assertIsNone(result)
    
    def test_generate_analysis_summary(self):
        """Test analysis summary generation"""
        text = "Price: $100, Return: 5%, Growth: 10%"
        labels = [
            {'description': 'chart', 'confidence': 0.9},
            {'description': 'graph', 'confidence': 0.8}
        ]
        objects = [
            {'name': 'line', 'confidence': 0.8},
            {'name': 'axis', 'confidence': 0.7}
        ]
        
        summary = self.service._generate_analysis_summary(text, labels, objects)
        
        self.assertIsInstance(summary, str)
        self.assertIn('Анализ графика', summary)
        self.assertIn('chart', summary.lower())
        self.assertIn('line', summary.lower())
    
    def test_generate_analysis_summary_empty(self):
        """Test analysis summary generation with empty inputs"""
        summary = self.service._generate_analysis_summary("", [], [])
        
        self.assertIsInstance(summary, str)
        self.assertIn('Обнаружен график', summary)


class TestGoogleVisionIntegration(unittest.TestCase):
    """Test cases for Google Vision integration in bot"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock the bot class
        self.mock_bot = Mock()
        self.mock_bot.google_vision_service = Mock()
        self.mock_bot.google_vision_service.is_available.return_value = True
        self.mock_bot.google_vision_service.analyze_chart.return_value = {
            'success': True,
            'text': 'Sample chart text',
            'labels': [{'description': 'chart', 'confidence': 0.9}],
            'objects': [{'name': 'line', 'confidence': 0.8}],
            'analysis': 'Test analysis summary'
        }
    
    def test_chart_analysis_integration(self):
        """Test chart analysis integration in compare command"""
        # Mock image bytes
        mock_img_bytes = b"fake_chart_image"
        
        # Test the analysis call
        result = self.mock_bot.google_vision_service.analyze_chart(mock_img_bytes)
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertIn('text', result)
        self.assertIn('analysis', result)
    
    def test_service_unavailable(self):
        """Test behavior when Google Vision service is unavailable"""
        self.mock_bot.google_vision_service.is_available.return_value = False
        
        # Service should not be used when unavailable
        self.assertFalse(self.mock_bot.google_vision_service.is_available())
    
    def test_analysis_error_handling(self):
        """Test error handling in chart analysis"""
        # Mock an error response
        self.mock_bot.google_vision_service.analyze_chart.return_value = {
            'success': False,
            'error': 'Test error message'
        }
        
        result = self.mock_bot.google_vision_service.analyze_chart(b"fake_image")
        
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestGoogleVisionConfiguration(unittest.TestCase):
    """Test cases for Google Vision configuration"""
    
    def test_api_key_from_env(self):
        """Test API key from environment variable"""
        with patch.dict(os.environ, {'GOOGLE_VISION_API_KEY': 'test_api_key_123'}):
            service = GoogleVisionService()
            self.assertEqual(service.api_key, 'test_api_key_123')
    
    def test_api_key_parameter(self):
        """Test API key from parameter"""
        test_key = 'custom_api_key_456'
        service = GoogleVisionService(api_key=test_key)
        self.assertEqual(service.api_key, test_key)
    
    def test_api_key_validation(self):
        """Test API key validation"""
        # Test with valid API key
        service = GoogleVisionService(api_key='valid_key_123')
        self.assertTrue(service.api_key)
        
        # Test with empty API key
        service = GoogleVisionService(api_key='')
        self.assertFalse(service.api_key)
        
        # Test with None API key
        service = GoogleVisionService(api_key=None)
        self.assertIsNone(service.api_key)
    
    def test_service_status_with_api_key(self):
        """Test service status with API key"""
        service = GoogleVisionService(api_key='test_key_789')
        status = service.get_service_status()
        
        # Check if API key status is properly set
        self.assertIn('api_key_set', status)
        self.assertIn('api_key_length', status)
        
        # Should have API key set
        self.assertTrue(status['api_key_set'])
        self.assertEqual(status['api_key_length'], 12)  # Length of 'test_key_789'


if __name__ == '__main__':
    unittest.main()

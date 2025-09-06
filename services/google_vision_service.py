"""
Google Vision API service for chart analysis
"""

import logging
import io
import base64
from typing import Optional, Dict, Any
import os

try:
    from google.cloud import vision
except ImportError:
    vision = None

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class GoogleVisionService:
    """Service for analyzing charts using Google Vision API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Vision service
        
        Args:
            api_key: Google Cloud Vision API key
        """
        self.client = None
        self.api_key = api_key or os.getenv('GOOGLE_VISION_API_KEY')
        self.api_url = "https://vision.googleapis.com/v1/images:annotate"
        
        if requests is None:
            logger.warning("Requests library not installed. Chart analysis will be disabled.")
            return
            
        try:
            self._initialize_client()
        except Exception as e:
            logger.error(f"Failed to initialize Google Vision client: {e}")
            self.client = None
    
    def _initialize_client(self):
        """Initialize Google Vision client with API key"""
        if not self.api_key:
            logger.warning("Google Vision API key not provided")
            return
        
        # Validate API key format (should be a string)
        if not isinstance(self.api_key, str) or len(self.api_key.strip()) == 0:
            logger.warning("Invalid Google Vision API key format")
            return
        
        # Check if requests library is available
        if requests is None:
            logger.warning("Requests library not available")
            return
        
        # Simple validation - just check format
        if len(self.api_key) >= 20 and self.api_key.startswith('AIza'):
            self.client = True  # Mark as initialized
            logger.info("Google Vision API key format validated successfully")
        else:
            logger.warning("Google Vision API key format appears invalid")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Google Vision service is available"""
        return self.client is not None
    
    def analyze_chart(self, image_bytes: bytes) -> Optional[Dict[str, Any]]:
        """
        Analyze chart image using Google Vision API
        
        Args:
            image_bytes: Chart image as bytes
            
        Returns:
            Dictionary with analysis results or None if failed
        """
        if not self.is_available():
            logger.warning("Google Vision service not available")
            return None
        
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare API request payload
            payload = {
                "requests": [
                    {
                        "image": {
                            "content": image_base64
                        },
                        "features": [
                            {
                                "type": "TEXT_DETECTION",
                                "maxResults": 1
                            },
                            {
                                "type": "LABEL_DETECTION",
                                "maxResults": 10
                            },
                            {
                                "type": "OBJECT_LOCALIZATION",
                                "maxResults": 10
                            }
                        ]
                    }
                ]
            }
            
            # Make API request
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Google Vision API request failed: {response.status_code}")
                return {
                    'error': f"API request failed with status {response.status_code}",
                    'success': False
                }
            
            result = response.json()
            
            if 'responses' not in result or not result['responses']:
                logger.error("Invalid response from Google Vision API")
                return {
                    'error': "Invalid API response",
                    'success': False
                }
            
            response_data = result['responses'][0]
            
            # Extract text content
            detected_text = ""
            if 'textAnnotations' in response_data and response_data['textAnnotations']:
                detected_text = response_data['textAnnotations'][0].get('description', '')
            
            # Extract chart-related labels
            chart_labels = []
            if 'labelAnnotations' in response_data:
                for label in response_data['labelAnnotations']:
                    if label.get('score', 0) > 0.7:  # High confidence labels only
                        chart_labels.append({
                            'description': label.get('description', ''),
                            'confidence': label.get('score', 0)
                        })
            
            # Extract objects (potential chart elements)
            chart_objects = []
            if 'localizedObjectAnnotations' in response_data:
                for obj in response_data['localizedObjectAnnotations']:
                    if obj.get('score', 0) > 0.7:  # High confidence objects only
                        chart_objects.append({
                            'name': obj.get('name', ''),
                            'confidence': obj.get('score', 0)
                        })
            
            # Generate analysis summary
            analysis = self._generate_analysis_summary(
                detected_text, chart_labels, chart_objects
            )
            
            logger.info(f"Chart analysis completed: {len(detected_text)} chars, {len(chart_labels)} labels, {len(chart_objects)} objects")
            
            return {
                'text': detected_text,
                'labels': chart_labels,
                'objects': chart_objects,
                'analysis': analysis,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing chart with Google Vision: {e}")
            return {
                'error': str(e),
                'success': False
            }
    
    def _generate_analysis_summary(self, text: str, labels: list, objects: list) -> str:
        """
        Generate a brief analysis summary based on detected elements
        
        Args:
            text: Detected text content
            labels: Detected labels
            objects: Detected objects
            
        Returns:
            Brief analysis summary in Russian
        """
        summary_parts = []
        
        # Analyze labels for chart type
        chart_types = []
        for label in labels:
            label_desc = label['description'].lower()
            if any(keyword in label_desc for keyword in ['chart', 'graph', 'diagram', 'plot']):
                chart_types.append(label['description'])
        
        if chart_types:
            summary_parts.append(f"📊 Тип графика: {', '.join(chart_types[:2])}")
        
        # Analyze text for financial data
        financial_keywords = ['price', 'value', 'return', 'yield', 'profit', 'loss', 'growth', 'decline']
        detected_keywords = []
        
        text_lower = text.lower()
        for keyword in financial_keywords:
            if keyword in text_lower:
                detected_keywords.append(keyword)
        
        if detected_keywords:
            summary_parts.append(f"💰 Финансовые показатели: {', '.join(detected_keywords[:3])}")
        
        # Analyze objects for chart elements
        chart_elements = []
        for obj in objects:
            obj_name = obj['name'].lower()
            if any(element in obj_name for element in ['line', 'bar', 'point', 'axis', 'grid']):
                chart_elements.append(obj['name'])
        
        if chart_elements:
            summary_parts.append(f"📈 Элементы графика: {', '.join(chart_elements[:3])}")
        
        # Extract numbers and percentages from text
        import re
        numbers = re.findall(r'\d+\.?\d*%?', text)
        if numbers:
            summary_parts.append(f"🔢 Обнаружены числовые значения: {len(numbers)} значений")
        
        # Generate final summary
        if summary_parts:
            return "Анализ графика:\n" + "\n".join(summary_parts)
        else:
            return "📊 Обнаружен график с финансовыми данными"
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get service status information
        
        Returns:
            Dictionary with service status
        """
        return {
            'available': self.is_available(),
            'api_key_set': bool(self.api_key),
            'api_key_length': len(self.api_key) if self.api_key else 0,
            'library_installed': requests is not None,
            'api_url': self.api_url
        }

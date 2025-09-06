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
    from google.oauth2 import service_account
except ImportError:
    vision = None
    service_account = None

logger = logging.getLogger(__name__)


class GoogleVisionService:
    """Service for analyzing charts using Google Vision API"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Vision service
        
        Args:
            credentials_path: Path to Google Cloud service account JSON file
        """
        self.client = None
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if vision is None:
            logger.warning("Google Cloud Vision library not installed. Chart analysis will be disabled.")
            return
            
        try:
            self._initialize_client()
        except Exception as e:
            logger.error(f"Failed to initialize Google Vision client: {e}")
            self.client = None
    
    def _initialize_client(self):
        """Initialize Google Vision client with credentials"""
        # First, try to find credentials file in config_files directory
        config_credentials_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config_files',
            'google_vision_credentials.json'
        )
        
        # Priority order: parameter -> env var -> config file
        credentials_file = None
        if self.credentials_path and os.path.exists(self.credentials_path):
            credentials_file = self.credentials_path
            logger.info(f"Using provided credentials file: {credentials_file}")
        elif os.path.exists(config_credentials_path):
            credentials_file = config_credentials_path
            logger.info(f"Using config credentials file: {credentials_file}")
        elif os.getenv('GOOGLE_APPLICATION_CREDENTIALS') and os.path.exists(os.getenv('GOOGLE_APPLICATION_CREDENTIALS')):
            credentials_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            logger.info(f"Using environment credentials file: {credentials_file}")
        
        if credentials_file:
            # Use service account file
            credentials = service_account.Credentials.from_service_account_file(
                credentials_file,
                scopes=['https://www.googleapis.com/auth/cloud-vision']
            )
            self.client = vision.ImageAnnotatorClient(credentials=credentials)
            logger.info("Google Vision client initialized with service account file")
        else:
            # Try to use default credentials (environment variable or metadata server)
            self.client = vision.ImageAnnotatorClient()
            logger.info("Google Vision client initialized with default credentials")
    
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
            # Create image object
            image = vision.Image(content=image_bytes)
            
            # Perform text detection (OCR)
            text_response = self.client.text_detection(image=image)
            texts = text_response.text_annotations
            
            # Perform object detection to identify chart elements
            objects_response = self.client.object_localization(image=image)
            objects = objects_response.localized_object_annotations
            
            # Perform label detection for general chart identification
            labels_response = self.client.label_detection(image=image)
            labels = labels_response.label_annotations
            
            # Extract text content
            detected_text = ""
            if texts:
                detected_text = texts[0].description if texts[0].description else ""
            
            # Extract chart-related labels
            chart_labels = []
            for label in labels:
                if label.score > 0.7:  # High confidence labels only
                    chart_labels.append({
                        'description': label.description,
                        'confidence': label.score
                    })
            
            # Extract objects (potential chart elements)
            chart_objects = []
            for obj in objects:
                if obj.score > 0.7:  # High confidence objects only
                    chart_objects.append({
                        'name': obj.name,
                        'confidence': obj.score
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
        # Check for config credentials file
        config_credentials_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config_files',
            'google_vision_credentials.json'
        )
        
        return {
            'available': self.is_available(),
            'credentials_path': self.credentials_path,
            'credentials_exist': os.path.exists(self.credentials_path) if self.credentials_path else False,
            'config_credentials_exist': os.path.exists(config_credentials_path),
            'config_credentials_path': config_credentials_path,
            'library_installed': vision is not None
        }

"""
Gemini API service for chart analysis
"""

import logging
import io
import base64
from typing import Optional, Dict, Any
import os

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for analyzing charts using Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service
        
        Args:
            api_key: Google AI Studio API key for Gemini
        """
        self.client = None
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
        if requests is None:
            logger.warning("Requests library not installed. Chart analysis will be disabled.")
            return
            
        try:
            self._initialize_client()
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.client = None
    
    def _initialize_client(self):
        """Initialize Gemini client with API key"""
        if not self.api_key:
            logger.warning("Gemini API key not provided")
            return
        
        # Validate API key format (should be a string)
        if not isinstance(self.api_key, str) or len(self.api_key.strip()) == 0:
            logger.warning("Invalid Gemini API key format")
            return
        
        # Check if requests library is available
        if requests is None:
            logger.warning("Requests library not available")
            return
        
        # Simple validation - Gemini API keys typically start with different patterns
        if len(self.api_key) >= 20:
            self.client = True  # Mark as initialized
            logger.info("Gemini API key format validated successfully")
        else:
            logger.warning("Gemini API key format appears invalid")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Gemini service is available"""
        return self.client is not None
    
    def analyze_chart(self, image_bytes: bytes, prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze chart image using Gemini API
        
        Args:
            image_bytes: Chart image as bytes
            prompt: Optional custom prompt for analysis
            
        Returns:
            Dictionary with analysis results or None if failed
        """
        if not self.is_available():
            logger.warning("Gemini service not available")
            return None
        
        # Default prompt for financial chart analysis
        if not prompt:
            prompt = """Ты — ИИ-финансовый аналитик. Проанализируй представленный график, сфокусировавшись на ключевых трендах и метриках. 
            Опиши содержание графика, указав временной период, показанные инструменты и значительные ценовые движения. 
            Заверши кратким резюме общего рыночного настроения или ключевым выводом. 
            Не используй никакого форматирования, маркированных или нумерованных списков. 
            Предоставь один абзац не более пяти предложений. 
            Ответ должен быть прямым анализом без каких-либо оговорок или спекулятивных формулировок."""
        
        try:
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare API request payload
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            },
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": image_base64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.5,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                }
            }
            
            # Make API request
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Gemini API request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', f'API request failed with status {response.status_code}')
                    
                    # Check for specific error types
                    if 'location is not supported' in error_message.lower():
                        error_message = "Gemini API недоступен в вашем регионе. Попробуйте использовать VPN или другой AI сервис."
                    elif 'quota' in error_message.lower():
                        error_message = "Превышена квота Gemini API. Попробуйте позже."
                    elif 'invalid' in error_message.lower() and 'key' in error_message.lower():
                        error_message = "Неверный API ключ Gemini. Проверьте настройки."
                    
                    return {
                        'error': error_message,
                        'success': False
                    }
                except:
                    return {
                        'error': f"API request failed with status {response.status_code}",
                        'success': False
                    }
            
            result = response.json()
            
            if 'candidates' not in result or not result['candidates']:
                logger.error("Invalid response from Gemini API")
                return {
                    'error': "Invalid API response",
                    'success': False
                }
            
            candidate = result['candidates'][0]
            
            if 'content' not in candidate or 'parts' not in candidate['content']:
                logger.error("No content in Gemini API response")
                return {
                    'error': "No content in API response",
                    'success': False
                }
            
            # Extract analysis text
            analysis_text = ""
            for part in candidate['content']['parts']:
                if 'text' in part:
                    analysis_text += part['text']
            
            if not analysis_text:
                logger.warning("Empty analysis from Gemini API")
                return {
                    'error': "Empty analysis result",
                    'success': False
                }
            
            # Generate analysis summary
            analysis = self._generate_analysis_summary(analysis_text)
            
            return {
                'success': True,
                'analysis': analysis,
                'full_analysis': analysis_text,
                'raw_response': result
            }
            
        except Exception as e:
            logger.error(f"Error analyzing chart with Gemini: {e}")
            return {
                'error': f"Analysis failed: {str(e)}",
                'success': False
            }
    
    def _generate_analysis_summary(self, full_analysis: str) -> str:
        """
        Generate a brief analysis summary from full analysis
        
        Args:
            full_analysis: Full analysis text from Gemini
            
        Returns:
            Brief analysis summary in Russian
        """
        # For Gemini, we can use the full analysis as it's already well-structured
        # Just ensure it's not too long for Telegram
        if len(full_analysis) > 2000:
            # Truncate but keep important parts
            summary = full_analysis[:1900] + "\n\n... (анализ продолжается)"
        else:
            summary = full_analysis
        
        return summary
    
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
    
    def analyze_data(self, data_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze financial data using Gemini API (text-only analysis)
        
        Args:
            data_info: Dictionary containing financial data information
            
        Returns:
            Dictionary with analysis results or None if failed
        """
        if not self.is_available():
            logger.warning("Gemini service not available")
            return None
        
        try:
            # Prepare data description for Gemini
            data_description = self._prepare_data_description(data_info)
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"""Проанализируй следующие финансовые данные и дай подробный анализ:

{data_description}

Пожалуйста, предоставь:
1. Общую оценку производительности активов
2. Сравнительный анализ между активами
3. Анализ рисков и волатильности
4. Рекомендации по инвестированию
5. Выводы о трендах и паттернах

Отвечай на русском языке, структурированно и подробно."""
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                }
            }
            
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                logger.error(f"Gemini API request failed: {response.status_code}")
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', f'API request failed with status {response.status_code}')
                    
                    # Check for specific error types
                    if 'location is not supported' in error_message.lower():
                        error_message = "Gemini API недоступен в вашем регионе. Попробуйте использовать VPN или другой AI сервис."
                    elif 'quota' in error_message.lower():
                        error_message = "Превышена квота Gemini API. Попробуйте позже."
                    elif 'invalid' in error_message.lower() and 'key' in error_message.lower():
                        error_message = "Неверный API ключ Gemini. Проверьте настройки."
                    
                    return {
                        'error': error_message,
                        'success': False
                    }
                except:
                    return {
                        'error': f"API request failed with status {response.status_code}",
                        'success': False
                    }
            
            result = response.json()
            
            if 'candidates' not in result or not result['candidates']:
                logger.error("Invalid response from Gemini API: No candidates found")
                return {
                    'error': "Invalid API response: No candidates found",
                    'success': False
                }
            
            first_candidate = result['candidates'][0]
            if 'content' not in first_candidate or 'parts' not in first_candidate['content']:
                logger.error("Invalid response from Gemini API: No content parts found")
                return {
                    'error': "Invalid API response: No content parts found",
                    'success': False
                }
            
            full_analysis_text = ""
            for part in first_candidate['content']['parts']:
                if 'text' in part:
                    full_analysis_text += part['text'] + "\n"
            
            return {
                'success': True,
                'analysis': full_analysis_text.strip(),
                'full_analysis': full_analysis_text.strip(),
                'analysis_type': 'data'
            }
            
        except requests.exceptions.Timeout:
            logger.error("Gemini API request timed out")
            return {
                'error': "Gemini API request timed out",
                'success': False
            }
        except Exception as e:
            logger.error(f"Failed to analyze data with Gemini API: {e}")
            return {
                'error': f"Failed to analyze data: {e}",
                'success': False
            }
    
    def _prepare_data_description(self, data_info: Dict[str, Any]) -> str:
        """
        Prepare data description for Gemini analysis
        
        Args:
            data_info: Dictionary containing financial data information
            
        Returns:
            Formatted data description string
        """
        description_parts = []
        
        # Basic info
        if 'symbols' in data_info:
            description_parts.append(f"**Анализируемые активы:** {', '.join(data_info['symbols'])}")
        
        if 'currency' in data_info:
            description_parts.append(f"**Валюта:** {data_info['currency']}")
        
        if 'period' in data_info:
            description_parts.append(f"**Период анализа:** {data_info['period']}")
        
        # Performance metrics
        if 'performance' in data_info:
            perf = data_info['performance']
            description_parts.append("\n**Метрики производительности:**")
            
            for symbol, metrics in perf.items():
                description_parts.append(f"\n**{symbol}:**")
                if 'total_return' in metrics:
                    description_parts.append(f"  • Общая доходность: {metrics['total_return']:.2%}")
                if 'annual_return' in metrics:
                    description_parts.append(f"  • Годовая доходность: {metrics['annual_return']:.2%}")
                if 'volatility' in metrics:
                    description_parts.append(f"  • Волатильность: {metrics['volatility']:.2%}")
                if 'sharpe_ratio' in metrics:
                    description_parts.append(f"  • Коэффициент Шарпа: {metrics['sharpe_ratio']:.2f}")
                if 'max_drawdown' in metrics:
                    description_parts.append(f"  • Максимальная просадка: {metrics['max_drawdown']:.2%}")
        
        # Correlation matrix
        if 'correlations' in data_info:
            description_parts.append("\n**Корреляционная матрица:**")
            for i, symbol1 in enumerate(data_info['symbols']):
                for j, symbol2 in enumerate(data_info['symbols']):
                    if i < j:  # Only upper triangle
                        corr = data_info['correlations'][i][j]
                        description_parts.append(f"  • {symbol1} ↔ {symbol2}: {corr:.3f}")
        
        # Additional data
        if 'additional_info' in data_info:
            description_parts.append(f"\n**Дополнительная информация:** {data_info['additional_info']}")
        
        return "\n".join(description_parts)

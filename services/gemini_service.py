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
        
        # Централизованные промпты
        self._initialize_prompts()
        
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
    
    def _initialize_prompts(self):
        """Initialize centralized prompts for different analysis types"""
        
        # Базовый промпт - общая часть для всех типов анализа
        self.base_prompt = """Ты — финансовый аналитик уровня ведущих инвестиционных банков.
Твоя задача — провести комплексный анализ выбранных активов или портфеля.
Используй строгий профессиональный тон, глубокую аналитику и структуру."""
        
        # Общие атрибуты для всех типов анализа
        self.common_attributes = {
            'role': 'ведущий финансовый аналитик уровня крупнейших инвестиционных банков',
            'style': 'профессиональный язык, конкретные цифры и обоснованные выводы',
            'disclaimer': 'Добавь сноску о том, что анализ не учитывает макроэкономические факторы, политическую ситуацию и пр, не является инвестиционной рекомендацией'
        }
        
        # Кастомные промпты для разных типов анализа
        self.custom_prompts = {
            'chart': {
                'task': 'провести комплексный анализ представленного графика',
                'focus': 'ключевые тренды и метрики',
                'format': 'один абзац не более пяти предложений без форматирования',
                'restrictions': 'Не комментируй инфляцию (USD.INFL, EUR.INFL и т.д.) - анализируй только сравниваемые активы',
                'style': 'прямой анализ без оговорок или спекулятивных формулировок'  # Переопределяет общий стиль
            },
            
            'data_comparison': {
                'task': 'провести комплексный анализ выбранных активов',
                'focus': 'сравнительный анализ активов по всем метрикам',
                'requirements': [
                    'СРАВНИТЕЛЬНЫЙ АНАЛИЗ АКТИВОВ: Сравни каждый актив по доступным метрикам, выдели лидеров и аутсайдеров',
                    'АНАЛИЗ РИСК-ДОХОДНОСТЬ: Оцени соотношение риск-доходность для каждого актива',
                    'КОРРЕЛЯЦИОННЫЙ АНАЛИЗ: Оцени степень корреляции между активами, определи возможности диверсификации',
                    'ИНВЕСТИЦИОННЫЕ РЕКОМЕНДАЦИИ: Дай конкретные рекомендации по каждому активу'
                ],
                'format': 'Структурированный отчет с подзаголовками, четкий язык, профессиональные термины с пояснениями не более 4000 символов'
            },
            
            'portfolio': {
                'task': 'провести комплексный анализ портфеля и предоставить профессиональные рекомендации по оптимизации',
                'requirements': [
                    'АНАЛИЗ ТЕКУЩЕГО ПОРТФЕЛЯ: Оцени общую эффективность портфеля с учетом доступных метрик',
                    'АНАЛИЗ СОСТАВА ПОРТФЕЛЯ: Оцени текущие веса активов, проанализируй вклад каждого актива',
                    'РЕКОМЕНДАЦИИ ПО РЕБАЛАНСИРОВКЕ: Сравни текущий портфель с оптимальными портфелями',
                    'ИНВЕСТИЦИОННЫЕ РЕКОМЕНДАЦИИ: Дай конкретные рекомендации по каждому активу'
                ],
                'format': 'Структурированный отчет с подзаголовками, четкий язык, профессиональные термины с пояснениями не более 4000 символов'
            }
        }
    
    def _build_prompt(self, analysis_type: str, custom_data: str = "") -> str:
        """
        Build complete prompt for specific analysis type
        
        Args:
            analysis_type: Type of analysis ('chart', 'data_comparison', 'portfolio')
            custom_data: Custom data to append to the prompt
            
        Returns:
            Complete formatted prompt
        """
        if analysis_type not in self.custom_prompts:
            raise ValueError(f"Unknown analysis type: {analysis_type}")
        
        prompt_config = self.custom_prompts[analysis_type]
        prompt_parts = [self.base_prompt]
        
        # Объединяем общие атрибуты с специфичными для типа анализа
        # Специфичные атрибуты переопределяют общие
        merged_config = {**self.common_attributes, **prompt_config}
        
        # Добавляем роль и задачу
        prompt_parts.append(f"Твоя роль: {merged_config['role']}")
        prompt_parts.append(f"Твоя задача: {merged_config['task']}")
        
        # Добавляем кастомные данные если есть
        if custom_data:
            prompt_parts.append(f"\n{custom_data}")
        
        # Добавляем требования к анализу
        if 'requirements' in merged_config:
            prompt_parts.append("\n**ТРЕБОВАНИЯ К АНАЛИЗУ:**")
            for i, requirement in enumerate(merged_config['requirements'], 1):
                prompt_parts.append(f"\n{i}. **{requirement}**")
        
        # Добавляем формат ответа
        if 'format' in merged_config:
            prompt_parts.append(f"\n**ФОРМАТ ОТВЕТА:**")
            prompt_parts.append(merged_config['format'])
        
        # Добавляем стиль
        if 'style' in merged_config:
            prompt_parts.append(f"\n**СТИЛЬ:**")
            prompt_parts.append(merged_config['style'])
        
        # Добавляем ограничения
        if 'restrictions' in merged_config:
            prompt_parts.append(f"\n**ВАЖНО:** {merged_config['restrictions']}")
        
        # Добавляем дисклеймер
        if 'disclaimer' in merged_config:
            prompt_parts.append(f"\n**ДИСКЛЕЙМЕР:** {merged_config['disclaimer']}")
        
        # Добавляем язык ответа
        prompt_parts.append("\nОтвечай на русском языке, профессионально и детально.")
        
        return "\n".join(prompt_parts)
    
    def is_available(self) -> bool:
        """Check if Gemini service is available"""
        return self.client is not None
    
    def analyze_chart(self, image_bytes: bytes, prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze chart image using Gemini API
        
        Args:
            image_bytes: Chart image as bytes
            prompt: Optional custom prompt for analysis (if None, uses centralized chart prompt)
            
        Returns:
            Dictionary with analysis results or None if failed
        """
        if not self.is_available():
            logger.warning("Gemini service not available")
            return None
        
        # Use centralized prompt if no custom prompt provided
        if not prompt:
            chart_data = """Проанализируй представленный график, сфокусировавшись на ключевых трендах и метриках. 
Опиши содержание графика, указав временной период, показанные инструменты и значительные ценовые движения. 
Заверши кратким резюме общего рыночного настроения или ключевым выводом."""
            prompt = self._build_prompt('chart', chart_data)
        
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
            
            # Build centralized prompt for data comparison
            prompt = self._build_prompt('data_comparison', f"Проанализируй следующие финансовые данные и предоставь детальный профессиональный анализ:\n\n{data_description}")
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 3000,  # Увеличено для более детального анализа
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
            
            # Не обрезаем анализ - позволяем отправлять по частям
            analysis_text = full_analysis_text.strip()
            
            return {
                'success': True,
                'analysis': analysis_text,
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
        Prepare comprehensive data description for Gemini analysis
        
        Args:
            data_info: Dictionary containing financial data information
            
        Returns:
            Formatted data description string with detailed comparison parameters
        """
        # Handle None or invalid input
        if not data_info or not isinstance(data_info, dict):
            return "**Ошибка:** Данные для анализа недоступны\n\n" + "="*50 + "\n**ИНСТРУКЦИИ ДЛЯ АНАЛИЗА:**\nИспользуй все предоставленные данные для комплексного анализа:\n1. Сравни активы по всем метрикам из таблицы describe\n2. Проанализируй соотношение риск-доходность\n3. Оцени корреляции между активами\n4. Дай рекомендации по инвестированию\n5. Выдели сильные и слабые стороны каждого актива"
        
        description_parts = []
        
        # Basic info
        if 'symbols' in data_info:
            symbols = data_info['symbols']
            asset_names = data_info.get('asset_names', {})
            
            # Create list with asset names if available
            assets_with_names = []
            for symbol in symbols:
                if symbol in asset_names and asset_names[symbol] != symbol:
                    assets_with_names.append(f"{symbol} ({asset_names[symbol]})")
                else:
                    assets_with_names.append(symbol)
            
            symbols_list = ', '.join(assets_with_names)
            description_parts.append(f"**Анализируемые активы:** {symbols_list}")

        
        if 'analysis_type' in data_info:
            description_parts.append(f"**Тип анализа:** {data_info['analysis_type']}")
        
        if 'currency' in data_info:
            description_parts.append(f"**Валюта:** {data_info['currency']}")
        
        if 'period' in data_info:
            description_parts.append(f"**Период анализа:** {data_info['period']}")
        
        # Analysis metadata
        if 'analysis_metadata' in data_info:
            metadata = data_info['analysis_metadata']
            description_parts.append(f"**Источник данных:** {metadata.get('data_source', 'unknown')}")
            description_parts.append(f"**Глубина анализа:** {metadata.get('analysis_depth', 'basic')}")
            description_parts.append(f"**Включает корреляции:** {'Да' if metadata.get('includes_correlations', False) else 'Нет'}")
            description_parts.append(f"**Включает таблицу describe:** {'Да' if metadata.get('includes_describe_table', False) else 'Нет'}")
        
        # Summary metrics table - основная таблица метрик с периодом инвестиций
        if 'summary_metrics_table' in data_info and data_info['summary_metrics_table']:
            description_parts.append("\n**📊 ОСНОВНЫЕ МЕТРИКИ АКТИВОВ:**")
            description_parts.append(data_info['summary_metrics_table'])
        
        # Describe table data - дополнительная статистика из okama
        if 'describe_table' in data_info and data_info['describe_table']:
            description_parts.append("\n**📊 ДОПОЛНИТЕЛЬНАЯ СТАТИСТИКА (okama.AssetList.describe):**")
            description_parts.append(data_info['describe_table'])
        
        # Performance metrics удалены - все метрики теперь в основной таблице
        # Это исключает дублирование данных в анализе Gemini
        
        # Correlation matrix
        if 'correlations' in data_info and data_info['correlations']:
            description_parts.append("\n**🔗 КОРРЕЛЯЦИОННАЯ МАТРИЦА:**")
            symbols = data_info.get('symbols', [])
            asset_names = data_info.get('asset_names', {})
            
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols):
                    if i < j:  # Only upper triangle
                        corr = data_info['correlations'][i][j]
                        
                        # Use asset names if available
                        name1 = symbol1
                        if symbol1 in asset_names and asset_names[symbol1] != symbol1:
                            name1 = f"{symbol1} ({asset_names[symbol1]})"
                        
                        name2 = symbol2
                        if symbol2 in asset_names and asset_names[symbol2] != symbol2:
                            name2 = f"{symbol2} ({asset_names[symbol2]})"
                        
                        description_parts.append(f"  • {name1} ↔ {name2}: {corr:.3f}")
        
        # Efficient frontier data
        if 'efficient_frontier' in data_info and data_info['efficient_frontier']:
            ef_data = data_info['efficient_frontier']
            description_parts.append("\n**📈 ДАННЫЕ ЭФФЕКТИВНОЙ ГРАНИЦЫ (okama.EfficientFrontier):**")
            description_parts.append(f"**Валюта:** {ef_data.get('currency', 'USD')}")
            description_parts.append(f"**Активы:** {', '.join(ef_data.get('asset_names', []))}")
            
            # Min risk portfolio
            min_risk = ef_data.get('min_risk_portfolio', {})
            if min_risk.get('risk') is not None and min_risk.get('return') is not None:
                description_parts.append(f"\n**🎯 ПОРТФЕЛЬ МИНИМАЛЬНОГО РИСКА:**")
                description_parts.append(f"  • Риск: {min_risk['risk']:.2%}")
                description_parts.append(f"  • Доходность: {min_risk['return']:.2%}")
                if min_risk.get('weights'):
                    weights_str = []
                    for i, weight in enumerate(min_risk['weights']):
                        asset_name = ef_data.get('asset_names', [])[i] if i < len(ef_data.get('asset_names', [])) else f"Asset_{i}"
                        weights_str.append(f"{asset_name}: {weight:.1%}")
                    description_parts.append(f"  • Веса: {', '.join(weights_str)}")
            
            # Max return portfolio
            max_return = ef_data.get('max_return_portfolio', {})
            if max_return.get('risk') is not None and max_return.get('return') is not None:
                description_parts.append(f"\n**🚀 ПОРТФЕЛЬ МАКСИМАЛЬНОЙ ДОХОДНОСТИ:**")
                description_parts.append(f"  • Риск: {max_return['risk']:.2%}")
                description_parts.append(f"  • Доходность: {max_return['return']:.2%}")
                if max_return.get('weights'):
                    weights_str = []
                    for i, weight in enumerate(max_return['weights']):
                        asset_name = ef_data.get('asset_names', [])[i] if i < len(ef_data.get('asset_names', [])) else f"Asset_{i}"
                        weights_str.append(f"{asset_name}: {weight:.1%}")
                    description_parts.append(f"  • Веса: {', '.join(weights_str)}")
            
            # Max Sharpe portfolio
            max_sharpe = ef_data.get('max_sharpe_portfolio', {})
            if max_sharpe.get('risk') is not None and max_sharpe.get('return') is not None:
                description_parts.append(f"\n**⭐ ПОРТФЕЛЬ МАКСИМАЛЬНОГО КОЭФФИЦИЕНТА ШАРПА:**")
                description_parts.append(f"  • Риск: {max_sharpe['risk']:.2%}")
                description_parts.append(f"  • Доходность: {max_sharpe['return']:.2%}")
                description_parts.append(f"  • Коэффициент Шарпа: {max_sharpe.get('sharpe_ratio', 'N/A')}")
                if max_sharpe.get('weights'):
                    weights_str = []
                    for i, weight in enumerate(max_sharpe['weights']):
                        asset_name = ef_data.get('asset_names', [])[i] if i < len(ef_data.get('asset_names', [])) else f"Asset_{i}"
                        weights_str.append(f"{asset_name}: {weight:.1%}")
                    description_parts.append(f"  • Веса: {', '.join(weights_str)}")

        # Additional data
        if 'additional_info' in data_info and data_info['additional_info']:
            description_parts.append(f"\n**ℹ️ ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:** {data_info['additional_info']}")
        
        # Добавляем инструкции для AI
        description_parts.append("\n" + "="*50)
        description_parts.append("**ИНСТРУКЦИИ ДЛЯ АНАЛИЗА:**")
        description_parts.append("Используй все предоставленные данные для комплексного анализа:")
        description_parts.append("1. Проанализируй основные метрики (период инвестиций, CAGR, волатильность, Sharpe, Sortino, просадки)")
        description_parts.append("2. Сравни активы по всем метрикам")
        description_parts.append("3. Проанализируй соотношение риск-доходность с учетом реальных безрисковых ставок")
        description_parts.append("4. Оцени корреляции между активами")
        description_parts.append("5. Проанализируй данные эффективной границы и дай рекомендации по конкретным весам активов")
        description_parts.append("6. Учти период инвестиций при анализе - разные активы могут иметь разную историю")
        description_parts.append("Добавь юридически правильный дисклеймер о том, что анализ не учитывает макроэкономические факторы, политическую ситуацию и пр, не является инвестиционной рекомендацией")
        
        return "\n".join(description_parts)
    
    def analyze_portfolio(self, portfolio_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze portfolio data using Gemini API with specialized portfolio analysis prompt
        
        Args:
            portfolio_data: Dictionary containing portfolio-specific data
            
        Returns:
            Dictionary with analysis results or None if failed
        """
        if not self.is_available():
            logger.warning("Gemini service not available")
            return None
        
        try:
            # Prepare portfolio-specific data description
            portfolio_description = self._prepare_portfolio_description(portfolio_data)
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Build centralized prompt for portfolio analysis
            prompt = self._build_prompt('portfolio', f"Проанализируй следующие данные портфеля:\n\n{portfolio_description}")
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.6,  # Немного ниже для более консервативных рекомендаций
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 4000,  # Увеличено для детального анализа портфеля
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
            
            analysis_text = full_analysis_text.strip()
            
            return {
                'success': True,
                'analysis': analysis_text,
                'full_analysis': full_analysis_text.strip(),
                'analysis_type': 'portfolio'
            }
            
        except requests.exceptions.Timeout:
            logger.error("Gemini API request timed out")
            return {
                'error': "Gemini API request timed out",
                'success': False
            }
        except Exception as e:
            logger.error(f"Failed to analyze portfolio with Gemini API: {e}")
            return {
                'error': f"Failed to analyze portfolio: {e}",
                'success': False
            }
    
    def _prepare_portfolio_description(self, portfolio_data: Dict[str, Any]) -> str:
        """
        Prepare comprehensive portfolio description for Gemini analysis
        
        Args:
            portfolio_data: Dictionary containing portfolio-specific data
            
        Returns:
            Formatted portfolio description string
        """
        if not portfolio_data or not isinstance(portfolio_data, dict):
            return "**Ошибка:** Данные портфеля недоступны"
        
        description_parts = []
        
        # Basic portfolio info
        if 'symbols' in portfolio_data:
            symbols = portfolio_data['symbols']
            weights = portfolio_data.get('weights', [])
            asset_names = portfolio_data.get('asset_names', {})
            
            # Create portfolio composition
            composition = []
            for i, symbol in enumerate(symbols):
                weight = weights[i] if i < len(weights) else 0
                asset_name = asset_names.get(symbol, symbol)
                composition.append(f"{asset_name}: {weight:.1%}")
            
            description_parts.append(f"**Состав портфеля:** {', '.join(composition)}")
        
        if 'currency' in portfolio_data:
            description_parts.append(f"**Валюта:** {portfolio_data['currency']}")
        
        if 'period' in portfolio_data:
            description_parts.append(f"**Период анализа:** {portfolio_data['period']}")
        
        # Portfolio metrics table - основная таблица метрик портфеля
        if 'portfolio_metrics_table' in portfolio_data and portfolio_data['portfolio_metrics_table']:
            description_parts.append("\n**📊 МЕТРИКИ ПОРТФЕЛЯ:**")
            description_parts.append(portfolio_data['portfolio_metrics_table'])
        
        # Individual assets metrics for comparison
        if 'individual_assets_metrics' in portfolio_data and portfolio_data['individual_assets_metrics']:
            description_parts.append("\n**📈 МЕТРИКИ ОТДЕЛЬНЫХ АКТИВОВ (для сравнения):**")
            description_parts.append(portfolio_data['individual_assets_metrics'])
        
        # Correlation matrix
        if 'correlations' in portfolio_data and portfolio_data['correlations']:
            description_parts.append("\n**🔗 КОРРЕЛЯЦИОННАЯ МАТРИЦА:**")
            symbols = portfolio_data.get('symbols', [])
            asset_names = portfolio_data.get('asset_names', {})
            
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols):
                    if i < j:  # Only upper triangle
                        corr = portfolio_data['correlations'][i][j]
                        
                        # Use asset names if available
                        name1 = asset_names.get(symbol1, symbol1)
                        name2 = asset_names.get(symbol2, symbol2)
                        
                        description_parts.append(f"  • {name1} ↔ {name2}: {corr:.3f}")
        
        # Efficient frontier data
        if 'efficient_frontier' in portfolio_data and portfolio_data['efficient_frontier']:
            ef_data = portfolio_data['efficient_frontier']
            description_parts.append("\n**📈 ДАННЫЕ ЭФФЕКТИВНОЙ ГРАНИЦЫ (okama.EfficientFrontier):**")
            description_parts.append(f"**Валюта:** {ef_data.get('currency', 'USD')}")
            description_parts.append(f"**Активы:** {', '.join(ef_data.get('asset_names', []))}")
            
            # Min risk portfolio
            min_risk = ef_data.get('min_risk_portfolio', {})
            if min_risk.get('risk') is not None and min_risk.get('return') is not None:
                description_parts.append(f"\n**🎯 ПОРТФЕЛЬ МИНИМАЛЬНОГО РИСКА:**")
                description_parts.append(f"  • Риск: {min_risk['risk']:.2%}")
                description_parts.append(f"  • Доходность: {min_risk['return']:.2%}")
                if min_risk.get('weights'):
                    weights_str = []
                    for i, weight in enumerate(min_risk['weights']):
                        asset_name = ef_data.get('asset_names', [])[i] if i < len(ef_data.get('asset_names', [])) else f"Asset_{i}"
                        weights_str.append(f"{asset_name}: {weight:.1%}")
                    description_parts.append(f"  • Веса: {', '.join(weights_str)}")
            
            # Max return portfolio
            max_return = ef_data.get('max_return_portfolio', {})
            if max_return.get('risk') is not None and max_return.get('return') is not None:
                description_parts.append(f"\n**🚀 ПОРТФЕЛЬ МАКСИМАЛЬНОЙ ДОХОДНОСТИ:**")
                description_parts.append(f"  • Риск: {max_return['risk']:.2%}")
                description_parts.append(f"  • Доходность: {max_return['return']:.2%}")
                if max_return.get('weights'):
                    weights_str = []
                    for i, weight in enumerate(max_return['weights']):
                        asset_name = ef_data.get('asset_names', [])[i] if i < len(ef_data.get('asset_names', [])) else f"Asset_{i}"
                        weights_str.append(f"{asset_name}: {weight:.1%}")
                    description_parts.append(f"  • Веса: {', '.join(weights_str)}")
            
            # Max Sharpe portfolio
            max_sharpe = ef_data.get('max_sharpe_portfolio', {})
            if max_sharpe.get('risk') is not None and max_sharpe.get('return') is not None:
                description_parts.append(f"\n**⭐ ПОРТФЕЛЬ МАКСИМАЛЬНОГО КОЭФФИЦИЕНТА ШАРПА:**")
                description_parts.append(f"  • Риск: {max_sharpe['risk']:.2%}")
                description_parts.append(f"  • Доходность: {max_sharpe['return']:.2%}")
                description_parts.append(f"  • Коэффициент Шарпа: {max_sharpe.get('sharpe_ratio', 'N/A')}")
                if max_sharpe.get('weights'):
                    weights_str = []
                    for i, weight in enumerate(max_sharpe['weights']):
                        asset_name = ef_data.get('asset_names', [])[i] if i < len(ef_data.get('asset_names', [])) else f"Asset_{i}"
                        weights_str.append(f"{asset_name}: {weight:.1%}")
                    description_parts.append(f"  • Веса: {', '.join(weights_str)}")
        
        # Additional portfolio info
        if 'additional_info' in portfolio_data and portfolio_data['additional_info']:
            description_parts.append(f"\n**ℹ️ ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:** {portfolio_data['additional_info']}")
        
        # Add instructions for AI
        description_parts.append("\n" + "="*50)
        description_parts.append("**ИНСТРУКЦИИ ДЛЯ АНАЛИЗА ПОРТФЕЛЯ:**")
        description_parts.append("Используй все предоставленные данные для комплексного анализа портфеля:")
        description_parts.append("1. Проанализируй метрики портфеля целиком (CAGR, волатильность, Sharpe, Sortino, просадки)")
        description_parts.append("2. Сравни текущий портфель с оптимальными портфелями из эффективной границы")
        description_parts.append("3. Оцени корреляции между активами и качество диверсификации")
        description_parts.append("4. Дай конкретные рекомендации по ребалансировке с указанием новых весов")
        description_parts.append("5. Предложи стратегические улучшения портфеля")
        description_parts.append("6. Оцени риски и предложи меры по их снижению")
        description_parts.append("Добавь юридически правильный дисклеймер о том, что анализ не является инвестиционной рекомендацией")
        
        return "\n".join(description_parts)

"""
Okama Financial Brain

Ядро интеллектуальной системы для финансового анализа, управляющее полным циклом
обработки запроса пользователя: от анализа текста до генерации аналитических выводов.

Этап 1: Декомпозиция запроса и планирование получения данных
Этап 2: Анализ отчета и формирование финального ответа
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from services.intent_parser import IntentParser, ParsedIntent
from services.asset_resolver import AssetResolver
from services.okama_handler import OkamaHandler
from services.report_builder import ReportBuilder
from services.analysis_engine import AnalysisEngine
from yandexgpt_service import YandexGPTService

logger = logging.getLogger(__name__)


@dataclass
class FinancialQuery:
    """Структурированный запрос для финансового анализа"""
    intent: str  # single_asset_info, asset_comparison, portfolio_analysis, inflation_info, macro_info
    assets: List[str]  # Нормализованные тикеры okama
    asset_classes: List[str]  # Классы активов (US, MOEX, COMM, INDX, FX, INFL)
    weights: Optional[List[float]] = None  # Веса для портфеля
    currency: Optional[str] = None  # Валюта отчета
    period: Optional[str] = None  # Период анализа
    user_message: str = ""  # Оригинальное сообщение пользователя


@dataclass
class AnalysisResult:
    """Результат анализа с данными и метриками"""
    query: FinancialQuery
    data_report: Dict[str, Any]  # Структурированный отчет от Okama
    charts: List[bytes]  # Сгенерированные изображения
    ai_insights: str  # Аналитические выводы от AI
    recommendations: str  # Рекомендации


class OkamaFinancialBrain:
    """
    Okama Financial Brain - ядро интеллектуальной системы для финансового анализа
    
    Управляет полным циклом обработки запроса пользователя:
    1. Декомпозиция запроса и планирование получения данных
    2. Анализ отчета и формирование финального ответа
    """
    
    def __init__(self):
        """Инициализация сервисов"""
        self.intent_parser = IntentParser()
        self.asset_resolver = AssetResolver()
        self.okama_handler = OkamaHandler()
        self.report_builder = ReportBuilder()
        self.analysis_engine = AnalysisEngine()
        self.yandexgpt = YandexGPTService()
        
        # Маппинг намерений на типы анализа
        self.intent_mapping = {
            'asset_single': 'single_asset_info',
            'asset_compare': 'asset_comparison', 
            'portfolio': 'portfolio_analysis',
            'inflation': 'inflation_info',
            'macro': 'macro_info',
            'chat': 'chat'
        }
        
        # Маппинг классов активов
        self.asset_class_mapping = {
            'US': 'US',
            'MOEX': 'MOEX', 
            'COMM': 'COMM',
            'INDX': 'INDX',
            'FX': 'FX',
            'INFL': 'INFL'
        }
    
    def process_query(self, user_message: str) -> AnalysisResult:
        """
        Основной метод обработки запроса пользователя
        
        Args:
            user_message: Текст запроса от пользователя
            
        Returns:
            AnalysisResult: Полный результат анализа
        """
        try:
            # Этап 1: Декомпозиция запроса и планирование получения данных
            query = self._decompose_query(user_message)
            logger.info(f"Query decomposed: {query}")
            
            # Этап 2: Получение данных и построение отчетов
            data_report = self._execute_data_retrieval(query)
            logger.info(f"Data retrieved for {len(query.assets)} assets")
            
            # Этап 3: Построение отчетов и графиков
            report_text, charts = self._build_reports(query, data_report)
            
            # Этап 4: AI анализ и формирование выводов
            ai_insights = self._generate_ai_insights(query, data_report, user_message)
            recommendations = self._generate_recommendations(query, data_report)
            
            # Формирование финального результата
            result = AnalysisResult(
                query=query,
                data_report=data_report,
                charts=charts,
                ai_insights=ai_insights,
                recommendations=recommendations
            )
            
            logger.info("Analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise
    
    def _decompose_query(self, user_message: str) -> FinancialQuery:
        """
        Этап 1: Декомпозиция запроса и планирование получения данных
        
        Определяет намерение, извлекает активы, нормализует их и формирует план действий
        """
        # Парсинг намерения
        parsed_intent = self.intent_parser.parse(user_message)
        
        # Маппинг на стандартные типы
        intent = self.intent_mapping.get(parsed_intent.intent, 'chat')
        
        # Разрешение активов
        resolved_assets = []
        asset_classes = []
        
        if parsed_intent.raw_assets:
            resolved = self.asset_resolver.resolve(parsed_intent.raw_assets)
            resolved_assets = [r.ticker for r in resolved if r.valid]
            asset_classes = [r.asset_class for r in resolved if r.valid]
        
        # Извлечение весов для портфеля
        weights = None
        if intent == 'portfolio_analysis' and len(resolved_assets) > 1:
            weights = self._extract_weights(user_message, len(resolved_assets))
        
        # Определение валюты отчета
        currency = self._extract_currency(user_message, parsed_intent.options)
        
        # Определение периода анализа
        period = self._extract_period(user_message, parsed_intent.options)
        
        return FinancialQuery(
            intent=intent,
            assets=resolved_assets,
            asset_classes=asset_classes,
            weights=weights,
            currency=currency,
            period=period,
            user_message=user_message
        )
    
    def _extract_weights(self, message: str, num_assets: int) -> List[float]:
        """Извлечение весов из сообщения пользователя"""
        message_lower = message.lower()
        
        # Поиск явно указанных весов
        import re
        weight_patterns = [
            r'(\d+(?:\.\d+)?)\s*%?\s*(?:вес|weight)',
            r'вес[аы]?\s*(\d+(?:\.\d+)?)\s*%?',
            r'weight[s]?\s*(\d+(?:\.\d+)?)\s*%?',
            r'(\d+(?:\.\d+)?)\s*%?\s*(?:акции|облигации|золото|серебро|нефть)',
            r'веса[аы]?\s*(\d+(?:\.\d+)?)\s*и\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*%\s*и\s*(\d+(?:\.\d+)?)\s*%'
        ]
        
        weights = []
        for pattern in weight_patterns:
            matches = re.findall(pattern, message_lower)
            if matches:
                if isinstance(matches[0], tuple):
                    # Для паттернов с несколькими группами
                    for match in matches:
                        weights.extend([float(w) / 100.0 for w in match])
                else:
                    # Для простых паттернов
                    weights.extend([float(w) / 100.0 for w in matches])
        
        # Если веса найдены и их достаточно
        if len(weights) >= num_assets:
            return weights[:num_assets]
        
        # Если веса не указаны или недостаточно, распределяем поровну
        return [1.0 / num_assets] * num_assets
    
    def _extract_currency(self, message: str, options: Dict[str, str]) -> Optional[str]:
        """Извлечение валюты отчета"""
        # Сначала проверяем опции из парсера
        if options.get('base_currency'):
            return options['base_currency']
        
        # Поиск в тексте
        message_lower = message.lower()
        currency_patterns = {
            'USD': ['usd', 'доллар', 'доллары', '$'],
            'EUR': ['eur', 'евро', '€'],
            'RUB': ['rub', 'рубль', 'рубли', '₽', 'р']
        }
        
        for currency, patterns in currency_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return currency
        
        return None  # Будет определена автоматически
    
    def _extract_period(self, message: str, options: Dict[str, str]) -> Optional[str]:
        """Извлечение периода анализа"""
        # Сначала проверяем опции из парсера
        if options.get('period'):
            return options['period']
        
        # Поиск в тексте
        message_lower = message.lower()
        period_patterns = {
            '1Y': ['1 год', '1 г', '1y', 'год'],
            '3Y': ['3 года', '3 г', '3y', '3 года'],
            '5Y': ['5 лет', '5 л', '5y', '5 лет'],
            '10Y': ['10 лет', '10 л', '10y', '10 лет'],
            'YTD': ['ytd', 'с начала года', 'год к дате']
        }
        
        for period, patterns in period_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return period
        
        return None  # Будет использован период по умолчанию
    
    def _execute_data_retrieval(self, query: FinancialQuery) -> Dict[str, Any]:
        """Выполнение получения данных согласно плану"""
        try:
            if query.intent == 'single_asset_info':
                if not query.assets:
                    raise ValueError("Не указаны активы для анализа")
                return self.okama_handler.get_single_asset(
                    query.assets[0], 
                    base_currency=query.currency
                )
            
            elif query.intent == 'asset_comparison':
                if len(query.assets) < 2:
                    # Если только один актив, обрабатываем как single_asset
                    if len(query.assets) == 1:
                        return self.okama_handler.get_single_asset(
                            query.assets[0], 
                            base_currency=query.currency
                        )
                    else:
                        raise ValueError("Для сравнения необходимо минимум 2 актива")
                return self.okama_handler.get_multiple_assets(query.assets)
            
            elif query.intent == 'portfolio_analysis':
                if len(query.assets) < 2:
                    raise ValueError("Для анализа портфеля необходимо минимум 2 актива")
                return self.okama_handler.get_portfolio(
                    query.assets, 
                    weights=query.weights
                )
            
            elif query.intent == 'inflation_info':
                return self.okama_handler.get_inflation()
            
            elif query.intent == 'macro_info':
                # Для макро-анализа используем сравнение активов
                if len(query.assets) >= 2:
                    return self.okama_handler.get_multiple_assets(query.assets)
                elif len(query.assets) == 1:
                    return self.okama_handler.get_single_asset(
                        query.assets[0], 
                        base_currency=query.currency
                    )
                else:
                    raise ValueError("Для макро-анализа необходимо указать активы")
            
            else:
                raise ValueError(f"Неподдерживаемый тип анализа: {query.intent}")
                
        except Exception as e:
            logger.error(f"Error in data retrieval: {e}")
            raise
    
    def _build_reports(self, query: FinancialQuery, data_report: Dict[str, Any]) -> Tuple[str, List[bytes]]:
        """Построение отчетов и графиков"""
        try:
            if query.intent == 'single_asset_info':
                return self.report_builder.build_single_asset_report(data_report)
            
            elif query.intent == 'asset_comparison':
                return self.report_builder.build_multi_asset_report(data_report)
            
            elif query.intent == 'portfolio_analysis':
                return self.report_builder.build_portfolio_report(data_report)
            
            elif query.intent == 'inflation_info':
                return self.report_builder.build_inflation_report(data_report)
            
            elif query.intent == 'macro_info':
                # Для макро-анализа используем multi-asset отчет
                if len(query.assets) >= 2:
                    return self.report_builder.build_multi_asset_report(data_report)
                else:
                    return self.report_builder.build_single_asset_report(data_report)
            
            else:
                return "Отчет не может быть построен", []
                
        except Exception as e:
            logger.error(f"Error building reports: {e}")
            return f"Ошибка построения отчета: {str(e)}", []
    
    def _generate_ai_insights(self, query: FinancialQuery, data_report: Dict[str, Any], user_message: str) -> str:
        """Генерация AI аналитических выводов"""
        try:
            # Определение типа анализа для AI
            analysis_type = query.intent
            
            # Формирование контекста для AI
            context = {
                "query_type": query.intent,
                "assets": query.assets,
                "asset_classes": query.asset_classes,
                "currency": query.currency,
                "period": query.period,
                "user_message": user_message
            }
            
            # Вызов AI для анализа
            if analysis_type == 'single_asset_info':
                return self.analysis_engine.summarize('single_asset', data_report, user_message)
            elif analysis_type == 'asset_comparison':
                return self.analysis_engine.summarize('asset_compare', data_report, user_message)
            elif analysis_type == 'portfolio_analysis':
                return self.analysis_engine.summarize('portfolio', data_report, user_message)
            elif analysis_type == 'inflation_info':
                return self.analysis_engine.summarize('inflation', data_report, user_message)
            elif analysis_type == 'macro_info':
                return self.analysis_engine.summarize('macro', data_report, user_message)
            else:
                return "Анализ завершен успешно."
                
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return "Анализ завершен успешно. AI анализ временно недоступен."
    
    def _generate_recommendations(self, query: FinancialQuery, data_report: Dict[str, Any]) -> str:
        """Генерация рекомендаций на основе анализа"""
        try:
            # Формирование промпта для рекомендаций
            prompt = f"""
            На основе анализа {query.intent} для активов {', '.join(query.assets)} 
            предоставьте 2-3 конкретные, практические рекомендации.
            
            Контекст:
            - Тип анализа: {query.intent}
            - Классы активов: {', '.join(query.asset_classes)}
            - Валюта: {query.currency or 'автоматически'}
            - Период: {query.period or 'по умолчанию'}
            
            Фокус на:
            - Диверсификации портфеля
            - Управлении рисками
            - Оптимизации доходности
            - Практических действиях
            
            Каждая рекомендация должна быть в одном предложении.
            """
            
            response = self.yandexgpt.ask_question(prompt)
            return response if response else "Рекомендации временно недоступны."
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return "Рекомендации временно недоступны."
    
    def format_final_response(self, result: AnalysisResult) -> str:
        """Формирование финального ответа для пользователя"""
        try:
            response_parts = []
            
            # Заголовок
            intent_titles = {
                'single_asset_info': '📊 Анализ актива',
                'asset_comparison': '⚖️ Сравнение активов',
                'portfolio_analysis': '💼 Анализ портфеля',
                'inflation_info': '📈 Анализ инфляции',
                'macro_info': '🌍 Макроэкономический анализ'
            }
            
            title = intent_titles.get(result.query.intent, '📊 Финансовый анализ')
            response_parts.append(f"**{title}**")
            response_parts.append("")
            
            # Информация о запросе
            if result.query.assets:
                response_parts.append(f"**Активы:** {', '.join(result.query.assets)}")
            
            if result.query.currency:
                response_parts.append(f"**Валюта:** {result.query.currency}")
            
            if result.query.period:
                response_parts.append(f"**Период:** {result.query.period}")
            
            response_parts.append("")
            
            # Основные метрики из отчета
            if 'metrics' in result.data_report:
                metrics = result.data_report['metrics']
                if isinstance(metrics, dict):
                    response_parts.append("**Ключевые метрики:**")
                    for asset, metric_data in metrics.items():
                        if isinstance(metric_data, dict):
                            response_parts.append(f"• {asset}:")
                            if metric_data.get('cagr') is not None:
                                response_parts.append(f"  - CAGR: {metric_data['cagr']*100:.2f}%")
                            if metric_data.get('volatility') is not None:
                                response_parts.append(f"  - Волатильность: {metric_data['volatility']*100:.2f}%")
                            if metric_data.get('sharpe') is not None:
                                response_parts.append(f"  - Sharpe: {metric_data['sharpe']:.2f}")
                elif isinstance(metrics, dict) and 'cagr' in metrics:
                    # Для одиночного актива
                    response_parts.append("**Ключевые метрики:**")
                    if metrics.get('cagr') is not None:
                        response_parts.append(f"• CAGR: {metrics['cagr']*100:.2f}%")
                    if metrics.get('volatility') is not None:
                        response_parts.append(f"• Волатильность: {metrics['volatility']*100:.2f}%")
                    if metrics.get('sharpe') is not None:
                        response_parts.append(f"• Sharpe: {metrics['sharpe']:.2f}")
            
            response_parts.append("")
            
            # AI аналитические выводы
            if result.ai_insights:
                response_parts.append("**🤖 AI Анализ:**")
                response_parts.append(result.ai_insights)
                response_parts.append("")
            
            # Рекомендации
            if result.recommendations:
                response_parts.append("**💡 Рекомендации:**")
                response_parts.append(result.recommendations)
                response_parts.append("")
            
            # Информация о графиках
            if result.charts:
                response_parts.append(f"**📊 Графики:** Сгенерировано {len(result.charts)} график(ов)")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error formatting final response: {e}")
            return f"Анализ завершен. Ошибка форматирования: {str(e)}"
    
    def get_analysis_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Получение краткого резюме анализа"""
        return {
            "intent": result.query.intent,
            "assets": result.query.assets,
            "asset_classes": result.query.asset_classes,
            "currency": result.query.currency,
            "period": result.query.period,
            "charts_count": len(result.charts),
            "has_ai_insights": bool(result.ai_insights),
            "has_recommendations": bool(result.recommendations),
            "timestamp": datetime.now().isoformat()
        }

"""
Enhanced Okama Financial Brain

Полнофункциональная интеллектуальная система для финансового анализа с:
- Улучшенным парсингом намерений
- Расширенным резолвингом активов
- Поддержкой конвертации валют и периодов
- Улучшенной визуализацией и отчетами
- Специализированным AI-анализом
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from services.intent_parser_enhanced import EnhancedIntentParser
from services.asset_resolver_enhanced import EnhancedAssetResolver
from services.okama_handler_enhanced import EnhancedOkamaHandler
from services.report_builder_enhanced import EnhancedReportBuilder
from services.analysis_engine_enhanced import EnhancedAnalysisEngine
from yandexgpt_service import YandexGPTService

logger = logging.getLogger(__name__)

@dataclass
class EnhancedFinancialQuery:
    """Расширенный структурированный запрос для финансового анализа"""
    intent: str  # asset_single, asset_compare, portfolio_analysis, inflation_data, macro_data
    assets: List[str]  # Нормализованные тикеры okama
    asset_classes: List[str]  # Классы активов
    weights: Optional[List[float]] = None  # Веса для портфеля
    currency: Optional[str] = None  # Валюта отчета
    period: Optional[str] = None  # Период анализа
    since_date: Optional[str] = None  # Дата начала
    to_date: Optional[str] = None  # Дата окончания
    convert_to: Optional[str] = None  # Валюта для конвертации
    country: Optional[str] = None  # Страна для инфляции
    user_message: str = ""  # Оригинальное сообщение пользователя

@dataclass
class EnhancedAnalysisResult:
    """Расширенный результат анализа"""
    query: EnhancedFinancialQuery
    data_report: Dict[str, Any]  # Структурированный отчет от Okama
    charts: List[bytes]  # Сгенерированные изображения
    ai_insights: str  # Аналитические выводы от AI
    recommendations: str  # Рекомендации
    csv_report: Optional[str] = None  # CSV отчет

class EnhancedOkamaFinancialBrain:
    """
    Enhanced Okama Financial Brain - интеллектуальная система для финансового анализа
    
    Управляет полным циклом обработки запроса пользователя:
    1. Декомпозиция запроса и планирование получения данных
    2. Анализ отчета и формирование финального ответа
    """
    
    def __init__(self):
        """Инициализация сервисов"""
        self.intent_parser = EnhancedIntentParser()
        self.asset_resolver = EnhancedAssetResolver()
        self.okama_handler = EnhancedOkamaHandler()
        self.report_builder = EnhancedReportBuilder()
        self.analysis_engine = EnhancedAnalysisEngine()
        self.yandexgpt = YandexGPTService()
        
        # Маппинг намерений на стандартные типы
        self.intent_mapping = {
            'asset_single': 'asset_single',
            'asset_compare': 'asset_compare',
            'portfolio_analysis': 'portfolio_analysis',
            'inflation_data': 'inflation_data',
            'macro_data': 'macro_data'
        }
    
    def process_query(self, user_message: str) -> EnhancedAnalysisResult:
        """
        Основной метод обработки запроса пользователя
        
        Args:
            user_message: Текст запроса от пользователя
            
        Returns:
            EnhancedAnalysisResult: Полный результат анализа
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
            
            # Этап 5: Создание CSV отчета
            csv_report = self._create_csv_report(query, data_report)
            
            # Формирование финального результата
            result = EnhancedAnalysisResult(
                query=query,
                data_report=data_report,
                charts=charts,
                ai_insights=ai_insights,
                recommendations=recommendations,
                csv_report=csv_report
            )
            
            logger.info("Analysis completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise
    
    def _decompose_query(self, user_message: str) -> EnhancedFinancialQuery:
        """
        Этап 1: Декомпозиция запроса и планирование получения данных
        
        Определяет намерение, извлекает активы, нормализует их и формирует план действий
        """
        # Парсинг намерения
        parsed_intent = self.intent_parser.parse(user_message)
        
        # Маппинг на стандартные типы
        intent = self.intent_mapping.get(parsed_intent.intent, 'asset_single')
        
        # Разрешение активов
        resolved_assets = []
        asset_classes = []
        
        if parsed_intent.assets:
            resolved = self.asset_resolver.resolve(parsed_intent.assets)
            resolved_assets = [r.ticker for r in resolved if r.valid]
            asset_classes = [r.asset_class for r in resolved if r.valid]
            
            # Проверяем валидность активов
            if not resolved_assets:
                raise ValueError("Не удалось разрешить ни один актив. Проверьте названия.")
        
        # Извлечение весов для портфеля
        weights = None
        if intent == 'portfolio_analysis' and len(resolved_assets) > 1:
            weights = parsed_intent.weights or self._distribute_weights_equally(len(resolved_assets))
        
        # Определение валюты отчета
        currency = parsed_intent.currency or self._get_default_currency(resolved_assets)
        
        # Определение периода анализа
        period = parsed_intent.period or self.intent_parser.get_default_period()
        
        return EnhancedFinancialQuery(
            intent=intent,
            assets=resolved_assets,
            asset_classes=asset_classes,
            weights=weights,
            currency=currency,
            period=period,
            since_date=parsed_intent.since_date,
            to_date=parsed_intent.to_date,
            convert_to=parsed_intent.convert_to,
            country=parsed_intent.country,
            user_message=user_message
        )
    
    def _distribute_weights_equally(self, num_assets: int) -> List[float]:
        """Распределяет веса поровну между активами"""
        return [1.0 / num_assets] * num_assets
    
    def _get_default_currency(self, assets: List[str]) -> str:
        """Определяет валюту по умолчанию"""
        if not assets:
            return 'USD'
        
        # Определяем валюту по первому активу
        asset = assets[0]
        if asset.endswith('.MOEX'):
            return 'RUB'
        elif asset.endswith('.US') or asset.endswith('.INDX') or asset.endswith('.COMM'):
            return 'USD'
        elif asset.endswith('.FX'):
            return 'USD'
        else:
            return 'USD'
    
    def _execute_data_retrieval(self, query: EnhancedFinancialQuery) -> Dict[str, Any]:
        """Выполнение получения данных согласно плану"""
        try:
            # Подготавливаем параметры для Okama Handler
            kwargs = {
                'period': query.period,
                'currency': query.currency,
                'convert_to': query.convert_to,
                'since_date': query.since_date,
                'to_date': query.to_date,
                'country': query.country
            }
            
            if query.intent == 'portfolio_analysis':
                kwargs['weights'] = query.weights
            
            # Выполняем запрос
            result = self.okama_handler.process_request(
                intent=query.intent,
                assets=query.assets,
                **kwargs
            )
            
            # Проверяем на ошибки
            if 'error' in result:
                raise ValueError(result['error'])
            
            return result
            
        except Exception as e:
            logger.error(f"Error in data retrieval: {e}")
            raise
    
    def _build_reports(self, query: EnhancedFinancialQuery, data_report: Dict[str, Any]) -> Tuple[str, List[bytes]]:
        """Построение отчетов и графиков"""
        try:
            return self.report_builder.build_report(
                intent=query.intent,
                data=data_report,
                user_query=query.user_message
            )
        except Exception as e:
            logger.error(f"Error building reports: {e}")
            return f"Ошибка построения отчета: {str(e)}", []
    
    def _generate_ai_insights(self, query: EnhancedFinancialQuery, data_report: Dict[str, Any], user_message: str) -> str:
        """Генерация AI аналитических выводов"""
        try:
            return self.analysis_engine.analyze(
                intent=query.intent,
                data=data_report,
                user_query=user_message
            )
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return "Анализ завершен успешно. AI анализ временно недоступен."
    
    def _generate_recommendations(self, query: EnhancedFinancialQuery, data_report: Dict[str, Any]) -> str:
        """Генерация рекомендаций на основе анализа"""
        try:
            return self.analysis_engine.get_recommendations(
                intent=query.intent,
                data=data_report
            )
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return "Рекомендации временно недоступны."
    
    def _create_csv_report(self, query: EnhancedFinancialQuery, data_report: Dict[str, Any]) -> Optional[str]:
        """Создание CSV отчета"""
        try:
            return self.report_builder.create_csv_report(
                data=data_report,
                intent=query.intent
            )
        except Exception as e:
            logger.error(f"Error creating CSV report: {e}")
            return None
    
    def format_final_response(self, result: EnhancedAnalysisResult) -> str:
        """Формирование финального ответа для пользователя"""
        try:
            response_parts = []
            
            # Заголовок
            intent_titles = {
                'asset_single': '📊 Анализ актива',
                'asset_compare': '⚖️ Сравнение активов',
                'portfolio_analysis': '💼 Анализ портфеля',
                'inflation_data': '📈 Анализ инфляции',
                'macro_data': '🌍 Макроэкономический анализ'
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
            
            if result.query.convert_to and result.query.convert_to != result.query.currency:
                response_parts.append(f"**Конвертация в:** {result.query.convert_to}")
            
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
                            if metric_data.get('max_drawdown') is not None:
                                response_parts.append(f"  - Макс. просадка: {metric_data['max_drawdown']*100:.2f}%")
                elif isinstance(metrics, dict) and 'cagr' in metrics:
                    # Для одиночного актива
                    response_parts.append("**Ключевые метрики:**")
                    if metrics.get('cagr') is not None:
                        response_parts.append(f"• CAGR: {metrics['cagr']*100:.2f}%")
                    if metrics.get('volatility') is not None:
                        response_parts.append(f"• Волатильность: {metrics['volatility']*100:.2f}%")
                    if metrics.get('sharpe') is not None:
                        response_parts.append(f"• Sharpe: {metrics['sharpe']:.2f}")
                    if metrics.get('max_drawdown') is not None:
                        response_parts.append(f"• Макс. просадка: {metrics['max_drawdown']*100:.2f}%")
            
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
            
            # Информация о CSV отчете
            if result.csv_report:
                response_parts.append("**📄 CSV отчет:** Доступен для скачивания")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error formatting final response: {e}")
            return f"Анализ завершен. Ошибка форматирования: {str(e)}"
    
    def get_analysis_summary(self, result: EnhancedAnalysisResult) -> Dict[str, Any]:
        """Получение краткого резюме анализа"""
        return {
            "intent": result.query.intent,
            "assets": result.query.assets,
            "asset_classes": result.query.asset_classes,
            "currency": result.query.currency,
            "period": result.query.period,
            "convert_to": result.query.convert_to,
            "country": result.query.country,
            "charts_count": len(result.charts),
            "has_ai_insights": bool(result.ai_insights),
            "has_recommendations": bool(result.recommendations),
            "has_csv_report": bool(result.csv_report),
            "timestamp": datetime.now().isoformat()
        }
    
    def validate_query(self, user_message: str) -> Tuple[bool, Optional[str]]:
        """Проверяет корректность запроса пользователя"""
        try:
            # Пытаемся разобрать запрос
            parsed = self.intent_parser.parse(user_message)
            
            if parsed.intent == 'unknown':
                return False, "Не удалось определить намерение. Попробуйте переформулировать запрос."
            
            if not parsed.assets:
                return False, "Не указаны активы для анализа. Укажите названия или тикеры активов."
            
            # Проверяем активы
            resolved = self.asset_resolver.resolve(parsed.assets)
            invalid_assets = [r.original for r in resolved if not r.valid]
            
            if invalid_assets:
                suggestions = []
                for asset in invalid_assets:
                    asset_suggestions = self.asset_resolver.get_suggestions(asset)
                    if asset_suggestions:
                        suggestions.append(f"'{asset}' -> {', '.join(asset_suggestions)}")
                
                if suggestions:
                    return False, f"Нераспознанные активы: {', '.join(invalid_assets)}. Возможные варианты: {'; '.join(suggestions)}"
                else:
                    return False, f"Нераспознанные активы: {', '.join(invalid_assets)}. Проверьте названия."
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating query: {e}")
            return False, f"Ошибка валидации запроса: {str(e)}"

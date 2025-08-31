"""
Enhanced Analysis Engine

Улучшенный аналитический движок на LLM для финансового анализа с:
- Специализированными промптами для каждого типа анализа
- Контекстными рекомендациями
- Учетом типа актива и макросреды
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import logging

from yandexgpt_service import YandexGPTService

logger = logging.getLogger(__name__)

class EnhancedAnalysisEngine:
    """Улучшенный аналитический движок для финансового анализа"""
    
    def __init__(self):
        self.yandexgpt = YandexGPTService()
        
        # Специализированные промпты для каждого типа анализа
        self.analysis_prompts = {
            'asset_single': self._get_single_asset_prompt(),
            'asset_compare': self._get_comparison_prompt(),
            'portfolio_analysis': self._get_portfolio_prompt(),
            'inflation_data': self._get_inflation_prompt(),
            'macro_data': self._get_macro_prompt()
        }
    
    def analyze(self, intent: str, data: Dict[str, Any], user_query: str) -> str:
        """
        Основной метод анализа данных
        
        Args:
            intent: Тип анализа
            data: Данные для анализа
            user_query: Оригинальный запрос пользователя
            
        Returns:
            str: Аналитический вывод
        """
        try:
            # Получаем специализированный промпт
            prompt = self.analysis_prompts.get(intent, self._get_generic_prompt())
            
            # Формируем контекст для анализа
            context = self._build_analysis_context(intent, data, user_query)
            
            # Выполняем анализ через LLM
            analysis = self.yandexgpt.ask_question(prompt + "\n\n" + context)
            
            if not analysis:
                return self._get_fallback_analysis(intent, data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in analysis engine: {e}")
            return self._get_fallback_analysis(intent, data)
    
    def analyze_asset(self, symbol: str, price_history: Any, period: str) -> Dict[str, Any]:
        """
        Анализ одного актива
        
        Args:
            symbol: Символ актива
            price_history: История цен
            period: Период анализа
            
        Returns:
            Dict[str, Any]: Результат анализа или ошибка
        """
        try:
            # Формируем данные для анализа
            data = {
                'symbol': symbol,
                'price_history': price_history,
                'period': period,
                'type': 'asset_single'
            }
            
            # Выполняем анализ
            analysis_result = self.analyze('asset_single', data, f"Анализ актива {symbol} за период {period}")
            
            return {
                'analysis': analysis_result,
                'symbol': symbol,
                'period': period
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_asset for {symbol}: {e}")
            return {
                'error': f"Ошибка анализа: {str(e)}"
            }
    
    def _get_single_asset_prompt(self) -> str:
        """Промпт для анализа одного актива"""
        return """Ты - опытный финансовый аналитик. Проанализируй данные по активу и предоставь краткий, но содержательный анализ.

Фокус анализа:
1. Интерпретация ключевых метрик (CAGR, волатильность, Sharpe, просадка)
2. Оценка риска и доходности
3. Контекстные выводы о качестве актива
4. Практические рекомендации

Стиль: Профессиональный, но понятный. 3-5 предложений. На русском языке.

Структура ответа:
- Краткая оценка актива
- Ключевые сильные и слабые стороны
- Рекомендация для инвестора"""
    
    def _get_comparison_prompt(self) -> str:
        """Промпт для сравнения активов"""
        return """Ты - опытный финансовый аналитик. Сравни активы и предоставь сравнительный анализ.

Фокус анализа:
1. Сравнение доходности и рисков
2. Анализ корреляций между активами
3. Выявление лучшего актива по разным критериям
4. Рекомендации по диверсификации

Стиль: Аналитический, сравнительный. 4-6 предложений. На русском языке.

Структура ответа:
- Сравнительная оценка активов
- Анализ рисков и доходности
- Рекомендации по выбору"""
    
    def _get_portfolio_prompt(self) -> str:
        """Промпт для анализа портфеля"""
        return """Ты - опытный финансовый аналитик. Проанализируй портфель и предоставь рекомендации.

Фокус анализа:
1. Оценка общего риска и доходности портфеля
2. Анализ диверсификации
3. Оценка эффективности распределения весов
4. Рекомендации по оптимизации

Стиль: Консультативный, практический. 4-6 предложений. На русском языке.

Структура ответа:
- Оценка качества портфеля
- Анализ диверсификации
- Конкретные рекомендации по улучшению"""
    
    def _get_inflation_prompt(self) -> str:
        """Промпт для анализа инфляции"""
        return """Ты - опытный макроэкономист. Проанализируй данные по инфляции и их значение.

Фокус анализа:
1. Интерпретация динамики CPI
2. Сравнение с историческими уровнями
3. Влияние на экономику и инвестиции
4. Прогнозные оценки

Стиль: Макроэкономический, аналитический. 3-5 предложений. На русском языке.

Структура ответа:
- Анализ динамики инфляции
- Значение для экономики
- Рекомендации для инвесторов"""
    
    def _get_macro_prompt(self) -> str:
        """Промпт для макроэкономического анализа"""
        return """Ты - опытный макроэкономист. Проанализируй макроэкономические данные и их значение.

Фокус анализа:
1. Интерпретация макроэкономических показателей
2. Связь с экономическими циклами
3. Влияние на финансовые рынки
4. Инвестиционные выводы

Стиль: Макроэкономический, стратегический. 4-6 предложений. На русском языке.

Структура ответа:
- Анализ макроэкономической ситуации
- Связь с финансовыми рынками
- Стратегические рекомендации"""
    
    def _get_generic_prompt(self) -> str:
        """Общий промпт для анализа"""
        return """Ты - опытный финансовый аналитик. Проанализируй предоставленные данные и сделай выводы.

Фокус анализа:
1. Интерпретация ключевых показателей
2. Выявление основных трендов
3. Практические выводы
4. Рекомендации

Стиль: Профессиональный, понятный. 3-4 предложения. На русском языке."""
    
    def _build_analysis_context(self, intent: str, data: Dict[str, Any], user_query: str) -> str:
        """Формирует контекст для анализа"""
        context_parts = []
        
        # Основная информация
        context_parts.append(f"Запрос пользователя: {user_query}")
        context_parts.append(f"Тип анализа: {intent}")
        
        # Данные по активам
        if 'tickers' in data:
            context_parts.append(f"Анализируемые активы: {', '.join(data['tickers'])}")
        
        if 'ticker' in data:
            context_parts.append(f"Анализируемый актив: {data['ticker']}")
        
        # Метрики
        if 'metrics' in data:
            metrics = data['metrics']
            if isinstance(metrics, dict):
                context_parts.append("Ключевые метрики:")
                for asset, metric_data in metrics.items():
                    if isinstance(metric_data, dict):
                        asset_metrics = []
                        if metric_data.get('cagr') is not None:
                            asset_metrics.append(f"CAGR: {metric_data['cagr']*100:.2f}%")
                        if metric_data.get('volatility') is not None:
                            asset_metrics.append(f"Волатильность: {metric_data['volatility']*100:.2f}%")
                        if metric_data.get('sharpe') is not None:
                            asset_metrics.append(f"Sharpe: {metric_data['sharpe']:.2f}")
                        if metric_data.get('max_drawdown') is not None:
                            asset_metrics.append(f"Макс. просадка: {metric_data['max_drawdown']*100:.2f}%")
                        
                        if asset_metrics:
                            context_parts.append(f"  {asset}: {', '.join(asset_metrics)}")
            else:
                # Для одиночного актива
                if isinstance(metrics, dict):
                    asset_metrics = []
                    if metrics.get('cagr') is not None:
                        asset_metrics.append(f"CAGR: {metrics['cagr']*100:.2f}%")
                    if metrics.get('volatility') is not None:
                        asset_metrics.append(f"Волатильность: {metrics['volatility']*100:.2f}%")
                    if metrics.get('sharpe') is not None:
                        asset_metrics.append(f"Sharpe: {metrics['sharpe']:.2f}")
                    if asset_metrics:
                        context_parts.append(f"Ключевые метрики: {', '.join(asset_metrics)}")
        
        # Корреляции
        if 'correlation' in data:
            try:
                if isinstance(data['correlation'], pd.DataFrame):
                    context_parts.append("Корреляции между активами:")
                    correlation_text = data['correlation'].round(3).to_string()
                    context_parts.append(correlation_text)
            except ImportError:
                # pandas не доступен, пропускаем корреляции
                pass
        
        # Дополнительная информация
        if 'period' in data:
            context_parts.append(f"Период анализа: {data['period']}")
        
        if 'currency' in data:
            context_parts.append(f"Валюта: {data['currency']}")
        
        if 'weights' in data:
            weights = data['weights']
            if weights:
                weights_text = ', '.join([f"{w*100:.1f}%" for w in weights])
                context_parts.append(f"Веса портфеля: {weights_text}")
        
        return "\n".join(context_parts)
    
    def _get_fallback_analysis(self, intent: str, data: Dict[str, Any]) -> str:
        """Возвращает fallback анализ при ошибке LLM"""
        if intent == 'asset_single':
            return self._get_single_asset_fallback(data)
        elif intent == 'asset_compare':
            return self._get_comparison_fallback(data)
        elif intent == 'portfolio_analysis':
            return self._get_portfolio_fallback(data)
        elif intent == 'inflation_data':
            return self._get_inflation_fallback(data)
        elif intent == 'macro_data':
            return self._get_macro_fallback(data)
        else:
            return "Анализ завершен успешно. Рекомендуется рассмотреть ключевые метрики для принятия инвестиционных решений."
    
    def _get_single_asset_fallback(self, data: Dict[str, Any]) -> str:
        """Fallback анализ для одного актива"""
        metrics = data.get('metrics', {})
        if not metrics:
            return "Анализ актива завершен. Рекомендуется изучить динамику цены и ключевые метрики."
        
        # Простая интерпретация метрик
        analysis_parts = []
        
        if metrics.get('cagr') is not None:
            cagr = metrics['cagr']
            if cagr > 0.15:
                analysis_parts.append("Актив показывает высокую доходность")
            elif cagr > 0.08:
                analysis_parts.append("Актив демонстрирует хорошую доходность")
            elif cagr > 0:
                analysis_parts.append("Актив имеет положительную доходность")
            else:
                analysis_parts.append("Актив показывает отрицательную доходность")
        
        if metrics.get('volatility') is not None:
            vol = metrics['volatility']
            if vol > 0.25:
                analysis_parts.append("Высокая волатильность указывает на значительные риски")
            elif vol > 0.15:
                analysis_parts.append("Умеренная волатильность")
            else:
                analysis_parts.append("Низкая волатильность обеспечивает стабильность")
        
        if not analysis_parts:
            analysis_parts.append("Анализ завершен успешно")
        
        return ". ".join(analysis_parts) + "."
    
    def _get_comparison_fallback(self, data: Dict[str, Any]) -> str:
        """Fallback анализ для сравнения активов"""
        metrics = data.get('metrics', {})
        if not metrics:
            return "Сравнительный анализ завершен. Рекомендуется изучить метрики каждого актива."
        
        # Простое сравнение
        best_cagr = None
        best_asset = None
        
        for asset, metric_data in metrics.items():
            if isinstance(metric_data, dict) and metric_data.get('cagr') is not None:
                if best_cagr is None or metric_data['cagr'] > best_cagr:
                    best_cagr = metric_data['cagr']
                    best_asset = asset
        
        if best_asset and best_cagr:
            return f"По доходности лидирует {best_asset} (CAGR: {best_cagr*100:.2f}%). Рекомендуется проанализировать риски каждого актива для принятия решения."
        
        return "Сравнительный анализ завершен. Рекомендуется изучить соотношение риск-доходность."
    
    def _get_portfolio_fallback(self, data: Dict[str, Any]) -> str:
        """Fallback анализ для портфеля"""
        metrics = data.get('metrics', {})
        weights = data.get('weights', [])
        
        if not metrics:
            return "Анализ портфеля завершен. Рекомендуется изучить общие метрики и структуру."
        
        analysis_parts = []
        
        if metrics.get('cagr') is not None:
            cagr = metrics['cagr']
            if cagr > 0.10:
                analysis_parts.append("Портфель показывает хорошую доходность")
            elif cagr > 0:
                analysis_parts.append("Портфель имеет положительную доходность")
            else:
                analysis_parts.append("Портфель показывает отрицательную доходность")
        
        if weights and len(weights) > 1:
            analysis_parts.append("Портфель диверсифицирован по нескольким активам")
        
        if not analysis_parts:
            analysis_parts.append("Анализ портфеля завершен успешно")
        
        return ". ".join(analysis_parts) + "."
    
    def _get_inflation_fallback(self, data: Dict[str, Any]) -> str:
        """Fallback анализ для инфляции"""
        metrics = data.get('metrics', {})
        if not metrics:
            return "Анализ инфляции завершен. Рекомендуется изучить динамику CPI."
        
        if metrics.get('cagr') is not None:
            cagr = metrics['cagr']
            if cagr > 0.05:
                return f"Высокий уровень инфляции ({cagr*100:.2f}% годовых) требует внимания к защите от обесценивания."
            elif cagr > 0.02:
                return f"Умеренная инфляция ({cagr*100:.2f}% годовых) находится в нормальных пределах."
            else:
                return f"Низкая инфляция ({cagr*100:.2f}% годовых) благоприятна для экономики."
        
        return "Анализ инфляции завершен. Рекомендуется мониторить динамику цен."
    
    def _get_macro_fallback(self, data: Dict[str, Any]) -> str:
        """Fallback анализ для макроэкономических данных"""
        return "Макроэкономический анализ завершен. Рекомендуется изучить ключевые показатели и их влияние на рынки."
    
    def get_recommendations(self, intent: str, data: Dict[str, Any]) -> str:
        """Генерирует рекомендации на основе анализа"""
        try:
            prompt = f"""
            На основе анализа {intent} предоставь 2-3 конкретные, практические рекомендации.
            
            Контекст:
            - Тип анализа: {intent}
            - Данные: {str(data)[:500]}...
            
            Фокус на:
            - Диверсификации портфеля
            - Управлении рисками
            - Оптимизации доходности
            - Практических действиях
            
            Каждая рекомендация должна быть в одном предложении.
            Ответ на русском языке.
            """
            
            response = self.yandexgpt.ask_question(prompt)
            return response if response else "Рекомендации временно недоступны."
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return "Рекомендации временно недоступны."

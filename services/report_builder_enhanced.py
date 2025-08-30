"""
Enhanced Report Builder

Улучшенный генератор отчетов для финансового анализа с:
- Расширенной визуализацией
- Красивыми таблицами
- Поддержкой всех типов намерений
- Конвертацией валют
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Any, Optional
import io
import logging

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from yandexgpt_service import YandexGPTService

logger = logging.getLogger(__name__)

class EnhancedReportBuilder:

    def _add_copyright_signature(self, ax):
        """Добавить копирайт подпись к графику"""
        ax.text(0.02, -0.15, '________________________________________________________________________________________________________________',
               transform=ax.transAxes, color='grey', alpha=0.7, fontsize=10)
        ax.text(0.02, -0.25, '   ©Цбот                                                                               Source: okama   ',
               transform=ax.transAxes, fontsize=12, color='grey', alpha=0.7)
    """Улучшенный генератор отчетов для финансового анализа"""
    
    def __init__(self):
        # Настройки стиля
        plt.style.use('default')
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        # Инициализация AI сервиса для анализа графиков
        self.yandexgpt = YandexGPTService()
        
    def build_report(self, intent: str, data: Dict[str, Any], user_query: str) -> Tuple[str, List[bytes], List[str]]:
        """Основной метод построения отчета с возвратом анализов графиков"""
        try:
            if intent == 'asset_single':
                return self._build_single_asset_report(data, user_query)
            elif intent == 'asset_compare':
                return self._build_comparison_report(data, user_query)
            elif intent == 'portfolio_analysis':
                return self._build_portfolio_report(data, user_query)
            elif intent == 'inflation_data':
                return self._build_inflation_report(data, user_query)
            elif intent == 'macro_data':
                return self._build_macro_report(data, user_query)
            else:
                return self._build_generic_report(data, user_query)
                
        except Exception as e:
            logger.error(f"Error building report: {e}")
            return f"Ошибка построения отчета: {str(e)}", [], []
    
    # Методы-обертки для совместимости с bot.py
    def build_single_asset_report(self, data: Dict[str, Any]) -> Tuple[str, List[bytes]]:
        """Совместимость с bot.py"""
        try:
            report_text, charts, _ = self._build_single_asset_report(data, "")
            return report_text, charts
        except Exception as e:
            logger.error(f"Error in build_single_asset_report: {e}")
            return f"Ошибка построения отчета: {str(e)}", []
    
    def build_multi_asset_report(self, data: Dict[str, Any]) -> Tuple[str, List[bytes]]:
        """Совместимость с bot.py"""
        try:
            report_text, charts, _ = self._build_comparison_report(data, "")
            return report_text, charts
        except Exception as e:
            logger.error(f"Error in build_multi_asset_report: {e}")
            return f"Ошибка построения отчета: {str(e)}", []
    
    def build_portfolio_report(self, data: Dict[str, Any]) -> Tuple[str, List[bytes]]:
        """Совместимость с bot.py"""
        try:
            report_text, charts, _ = self._build_portfolio_report(data, "")
            return report_text, charts
        except Exception as e:
            logger.error(f"Error in build_portfolio_report: {e}")
            return f"Ошибка построения отчета: {str(e)}", []
    
    def build_inflation_report(self, data: Dict[str, Any]) -> Tuple[str, List[bytes]]:
        """Совместимость с bot.py"""
        try:
            report_text, charts, _ = self._build_inflation_report(data, "")
            return report_text, charts
        except Exception as e:
            logger.error(f"Error in build_inflation_report: {e}")
            return f"Ошибка построения отчета: {str(e)}", []
    
    def _build_single_asset_report(self, data: Dict[str, Any], user_query: str) -> Tuple[str, List[bytes], List[str]]:
        """Строит отчет по одному активу"""
        ticker = data.get('ticker', 'Unknown')
        name = data.get('name', ticker)
        currency = data.get('currency', 'Unknown')
        period = data.get('period', 'Unknown')
        metrics = data.get('metrics', {})
        prices = data.get('prices')
        
        # Текстовый отчет
        report_text = f"📊 **Анализ актива: {name} ({ticker})**\n\n"
        
        # Основная информация об активе (как в команде /asset)
        if data.get('country'):
            report_text += f"**Страна:** {data.get('country')}\n"
        if data.get('exchange'):
            report_text += f"**Биржа:** {data.get('exchange')}\n"
        report_text += f"**Валюта:** {currency}\n"
        if data.get('type'):
            report_text += f"**Тип:** {data.get('type')}\n"
        if data.get('isin'):
            report_text += f"**ISIN:** {data.get('isin')}\n"
        if data.get('first_date'):
            report_text += f"**Первый день:** {data.get('first_date')}\n"
        if data.get('last_date'):
            report_text += f"**Последний день:** {data.get('last_date')}\n"
        if data.get('period_length'):
            report_text += f"**Длина периода:** {data.get('period_length')}\n"
        report_text += f"**Период анализа:** {period}\n\n"
        
        # Текущая цена
        if data.get('current_price'):
            report_text += f"**Текущая цена:** {data.get('current_price')} {currency}\n"
        
        # Метрики производительности (как в команде /asset)
        if data.get('annual_return') and data.get('annual_return') != 'N/A':
            report_text += f"**Годовая доходность:** {data.get('annual_return')}\n"
        if data.get('total_return') and data.get('total_return') != 'N/A':
            report_text += f"**Общая доходность:** {data.get('total_return')}\n"
        if data.get('volatility') and data.get('volatility') != 'N/A':
            report_text += f"**Волатильность:** {data.get('volatility')}\n"
        
        # Дополнительные метрики из enhanced анализа
        if metrics:
            report_text += "\n**📈 Аналитические метрики:**\n"
            if metrics.get('cagr') is not None:
                report_text += f"• CAGR: {metrics['cagr']*100:.2f}%\n"
            if metrics.get('volatility') is not None:
                report_text += f"• Волатильность: {metrics['volatility']*100:.2f}%\n"
            if metrics.get('sharpe') is not None:
                report_text += f"• Sharpe Ratio: {metrics['sharpe']:.2f}\n"
            if metrics.get('max_drawdown') is not None:
                report_text += f"• Макс. просадка: {metrics['max_drawdown']*100:.2f}%\n"
            if metrics.get('total_return') is not None:
                report_text += f"• Общая доходность: {metrics['total_return']*100:.2f}%\n"
        
        # Диагностика данных
        if prices is not None:
            report_text += f"\n**🔍 Диагностика данных:**\n"
            report_text += f"• Тип prices: {type(prices).__name__}\n"
            if hasattr(prices, 'shape'):
                report_text += f"• Размер: {prices.shape}\n"
            elif hasattr(prices, '__len__'):
                report_text += f"• Длина: {len(prices)}\n"
            else:
                report_text += f"• Значение: {prices}\n"
        
        # Графики с AI-анализом
        charts = []
        chart_analyses = []
        
        # 1. График изменения цен (если есть данные)
        if prices is not None and hasattr(prices, 'empty') and isinstance(prices, pd.Series) and not prices.empty:
            plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
            
            # График цены
            ax1.plot(prices.index, prices.values, color=self.colors[0], linewidth=2)
            ax1.set_title(f'Динамика цены: {name} ({ticker})', fontsize=14, fontweight='bold')
            ax1.set_ylabel(f'Цена ({currency})', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # График доходности
            returns = prices.pct_change().dropna()
            cumulative_returns = (1 + returns).cumprod()
            ax2.plot(cumulative_returns.index, cumulative_returns.values, color=self.colors[1], linewidth=2)
            ax2.set_title('Накопленная доходность', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Доходность (разы)', fontsize=12)
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Создаем график с анализом
            asset_info = {'ticker': ticker, 'name': name}
            chart_bytes, analysis = self._fig_to_png_with_analysis(fig, "График динамики цен и доходности", asset_info)
            charts.append(chart_bytes)
            chart_analyses.append(analysis)
        
        # 2. График из asset_service (если есть)
        if data.get('chart'):
            charts.append(data['chart'])
            chart_analyses.append("График из asset_service")
        
        # 3. Дополнительные графики для анализа
        if prices is not None and hasattr(prices, 'empty') and isinstance(prices, pd.Series) and not prices.empty and len(prices) > 20:
            # График волатильности (скользящее окно)
            fig, ax = plt.subplots(figsize=(10, 4))
            window_size = min(30, len(prices) // 4)
            rolling_vol = prices.pct_change().rolling(window=window_size).std() * np.sqrt(252)
            ax.plot(rolling_vol.index, rolling_vol.values, color=self.colors[2], linewidth=1.5)
            ax.set_title(f'Скользящая волатильность ({window_size} дней)', fontsize=12)
            ax.set_ylabel('Волатильность (годовая)', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            
            # Создаем график с анализом
            chart_bytes, analysis = self._fig_to_png_with_analysis(fig, f"График скользящей волатильности ({window_size} дней)", asset_info)
            charts.append(chart_bytes)
            chart_analyses.append(analysis)
            
            # График просадок
            fig, ax = plt.subplots(figsize=(10, 4))
            cummax = prices.cummax()
            drawdowns = (prices - cummax) / cummax * 100
            ax.fill_between(drawdowns.index, drawdowns.values, 0, color='red', alpha=0.3)
            ax.plot(drawdowns.index, drawdowns.values, color='red', linewidth=1)
            ax.set_title('История просадок', fontsize=12)
            ax.set_ylabel('Просадка (%)', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            
            # Создаем график с анализом
            chart_bytes, analysis = self._fig_to_png_with_analysis(fig, "График истории просадок", asset_info)
            charts.append(chart_bytes)
            chart_analyses.append(analysis)
        
        # Добавляем анализы графиков в текстовый отчет
        if chart_analyses:
            report_text += "\n**🧠 AI-анализ графиков:**\n"
            for i, analysis in enumerate(chart_analyses):
                if analysis != "График из asset_service":  # Пропускаем системные графики
                    report_text += f"• График {i+1}: {analysis}\n"
        
        return report_text, charts
    
    def _build_comparison_report(self, data: Dict[str, Any], user_query: str) -> Tuple[str, List[bytes]]:
        """Строит отчет по сравнению активов"""
        tickers = data.get('tickers', [])
        metrics = data.get('metrics', {})
        correlation = data.get('correlation')
        prices = data.get('prices')
        period = data.get('period', 'Unknown')
        currency = data.get('currency', 'Unknown')
        
        # Диагностика данных
        logger.info(f"Building comparison report for tickers: {tickers}")
        logger.info(f"Metrics keys: {list(metrics.keys()) if metrics else 'No metrics'}")
        logger.info(f"Metrics structure: {metrics}")
        logger.info(f"Prices shape: {prices.shape if hasattr(prices, 'shape') else 'No prices'}")
        
        # Текстовый отчет
        report_text = f"⚖️ **Сравнение активов**\n\n"
        report_text += f"**Активы:** {', '.join(tickers)}\n"
        report_text += f"**Период:** {period}\n"
        report_text += f"**Валюта:** {currency}\n\n"
        
        # Если доступны человекочитаемые имена
        names = data.get('names') or {}
        if isinstance(names, dict) and names:
            try:
                pretty_names = [f"{t} — {names.get(t, t)}" for t in tickers]
                report_text += "**Названия активов:**\n" + "\n".join([f"• {s}" for s in pretty_names]) + "\n\n"
            except Exception:
                pass
        
        # Таблица метрик
        if metrics:
            report_text += "**📊 Сравнительная таблица метрик:**\n"
            metrics_table = self._create_metrics_table(metrics)
            report_text += metrics_table + "\n\n"
        else:
            report_text += "**⚠️ Метрики:** Не удалось получить метрики для сравнения\n\n"
            # Попробуем создать простые метрики из prices
            if prices is not None and hasattr(prices, 'empty') and isinstance(prices, pd.DataFrame) and not prices.empty:
                try:
                    simple_metrics = {}
                    for ticker in tickers:
                        if ticker in prices:
                            ticker_prices = prices[ticker].dropna()
                            if len(ticker_prices) > 1:
                                simple_metrics[ticker] = self._compute_simple_metrics(ticker_prices)
                    
                    if simple_metrics:
                        report_text += "**📈 Простые метрики (из цен):**\n"
                        for ticker, ticker_metrics in simple_metrics.items():
                            report_text += f"**{ticker}:**\n"
                            if ticker_metrics.get('total_return') is not None:
                                report_text += f"• Общая доходность: {ticker_metrics['total_return']*100:.2f}%\n"
                            if ticker_metrics.get('volatility') is not None:
                                report_text += f"• Волатильность: {ticker_metrics['volatility']*100:.2f}%\n"
                            report_text += "\n"
                except Exception as e:
                    logger.warning(f"Error computing simple metrics: {e}")
        
        # Корреляции
        if correlation is not None and hasattr(correlation, 'empty') and isinstance(correlation, pd.DataFrame) and not correlation.empty:
            report_text += "**🔗 Корреляции между активами:**\n"
            try:
                correlation_text = correlation.round(3).to_string()
                report_text += correlation_text + "\n\n"
            except Exception as e:
                report_text += f"Ошибка отображения корреляций: {str(e)}\n\n"
        
        # Добавим краткий вывод describe, если есть
        describe_df = data.get('describe')
        if describe_df is not None and hasattr(describe_df, 'empty') and isinstance(describe_df, pd.DataFrame) and not describe_df.empty:
            try:
                # Покажем только ключевые строки (CAGR и Max drawdowns) если найдены
                subset = describe_df.copy()
                key_rows = subset[subset['property'].isin(['CAGR', 'Max drawdowns'])]
                if hasattr(key_rows, 'empty') and key_rows.empty:
                    key_rows = subset.head(5)
                report_text += "**📋 Краткое описание (describe):**\n"
                report_text += key_rows.to_string(index=False) + "\n\n"
            except Exception:
                pass
        
        # Графики
        charts = []
        
        # 1) Нормализованные цены и накопленная доходность (fallback по prices)
        if prices is not None and hasattr(prices, 'empty') and isinstance(prices, pd.DataFrame) and not prices.empty:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            for i, ticker in enumerate(tickers):
                if ticker in prices:
                    normalized_prices = prices[ticker] / prices[ticker].iloc[0] * 100
                    ax1.plot(normalized_prices.index, normalized_prices.values, 
                            label=ticker, color=self.colors[i % len(self.colors)], linewidth=2)
            ax1.set_title('Нормализованные цены (база = 100)', fontsize=14, fontweight='bold')
            ax1.set_ylabel('Цена (нормализованная)', fontsize=12)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            returns = prices.pct_change().dropna()
            cumulative_returns = (1 + returns).cumprod()
            for i, ticker in enumerate(tickers):
                if ticker in cumulative_returns:
                    ax2.plot(cumulative_returns.index, cumulative_returns[ticker].values,
                            label=ticker, color=self.colors[i % len(self.colors)], linewidth=2)
            ax2.set_title('Накопленная доходность', fontsize=14, fontweight='bold')
            ax2.set_ylabel('Доходность (разы)', fontsize=12)
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            charts.append(self._fig_to_png(fig))
        
        # 2) Wealth indexes из AssetList
        wealth_indexes = data.get('wealth_indexes')
        if wealth_indexes is not None and hasattr(wealth_indexes, 'empty') and isinstance(wealth_indexes, pd.DataFrame) and not wealth_indexes.empty:
            plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
            fig, ax = plt.subplots(figsize=(12, 6))
            for i, ticker in enumerate(tickers):
                if ticker in wealth_indexes:
                    ax.plot(wealth_indexes.index, wealth_indexes[ticker].values, 
                            label=ticker, color=self.colors[i % len(self.colors)], linewidth=2)
            ax.set_title('Wealth Indexes (накопленная стоимость, base=1)', fontsize=14, fontweight='bold')
            ax.set_ylabel('Индекс богатства (раз)')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            charts.append(self._fig_to_png(fig))
        
        # 3) История просадок
        drawdowns = data.get('drawdowns')
        if drawdowns is not None and hasattr(drawdowns, 'empty') and isinstance(drawdowns, pd.DataFrame) and not drawdowns.empty:
            plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
            fig, ax = plt.subplots(figsize=(12, 6))
            for i, ticker in enumerate(tickers):
                if ticker in drawdowns:
                    ax.plot(drawdowns.index, drawdowns[ticker].values, 
                            label=ticker, color=self.colors[i % len(self.colors)], linewidth=1.5)
            ax.set_title('Просадки (Drawdowns)', fontsize=14, fontweight='bold')
            ax.set_ylabel('Просадка')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            charts.append(self._fig_to_png(fig))
        
        # 4) Дивидендная доходность
        dividend_yield = data.get('dividend_yield')
        if dividend_yield is not None and hasattr(dividend_yield, 'empty') and isinstance(dividend_yield, pd.DataFrame) and not dividend_yield.empty:
            plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
            fig, ax = plt.subplots(figsize=(12, 6))
            for i, ticker in enumerate(tickers):
                if ticker in dividend_yield:
                    ax.plot(dividend_yield.index, dividend_yield[ticker].values, 
                            label=ticker, color=self.colors[i % len(self.colors)], linewidth=1.5)
            ax.set_title('Дивидендная доходность (история)', fontsize=14, fontweight='bold')
            ax.set_ylabel('Див. доходность')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            charts.append(self._fig_to_png(fig))
        
        # 5) Скользящая корреляция с бенчмарком
        index_corr = data.get('index_corr')
        if index_corr is not None and hasattr(index_corr, 'empty') and isinstance(index_corr, pd.DataFrame) and not index_corr.empty:
            plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
            fig, ax = plt.subplots(figsize=(12, 6))
            for i, col in enumerate(index_corr.columns):
                ax.plot(index_corr.index, index_corr[col].values, 
                        label=col, color=self.colors[i % len(self.colors)], linewidth=1.5)
            ax.set_title('Скользящая корреляция с бенчмарком (первый актив)', fontsize=14, fontweight='bold')
            ax.set_ylabel('Корреляция')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            charts.append(self._fig_to_png(fig))
        
        return report_text, charts
    
    def _build_portfolio_report(self, data: Dict[str, Any], user_query: str) -> Tuple[str, List[bytes]]:
        """Строит отчет по анализу портфеля"""
        tickers = data.get('tickers', [])
        weights = data.get('weights', [])
        metrics = data.get('metrics', {})
        portfolio_prices = data.get('portfolio_prices')
        frontier = data.get('frontier')
        period = data.get('period', 'Unknown')
        currency = data.get('currency', 'Unknown')
        
        # Текстовый отчет
        report_text = f"💼 **Анализ портфеля**\n\n"
        report_text += f"**Активы:** {', '.join(tickers)}\n"
        report_text += f"**Веса:** {', '.join([f'{w*100:.1f}%' for w in weights])}\n"
        report_text += f"**Период:** {period}\n"
        report_text += f"**Валюта:** {currency}\n\n"
        
        # Метрики портфеля
        if metrics:
            report_text += "**Метрики портфеля:**\n"
            if metrics.get('cagr') is not None:
                report_text += f"• CAGR: {metrics['cagr']*100:.2f}%\n"
            if metrics.get('volatility') is not None:
                report_text += f"• Волатильность: {metrics['volatility']*100:.2f}%\n"
            if metrics.get('sharpe') is not None:
                report_text += f"• Sharpe Ratio: {metrics['sharpe']:.2f}\n"
            if metrics.get('max_drawdown') is not None:
                report_text += f"• Макс. просадка: {metrics['max_drawdown']*100:.2f}%\n"
        
        # Графики
        charts = []
        
        # График стоимости портфеля
        if portfolio_prices is not None and hasattr(portfolio_prices, 'empty') and isinstance(portfolio_prices, pd.Series) and not portfolio_prices.empty:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Стоимость портфеля
            ax1.plot(portfolio_prices.index, portfolio_prices.values, 
                    color=self.colors[0], linewidth=2)
            ax1.set_title('Стоимость портфеля', fontsize=14, fontweight='bold')
            ax1.set_ylabel(f'Стоимость ({currency})', fontsize=12)
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # Круговая диаграмма весов
            if weights:
                ax2.pie(weights, labels=tickers, autopct='%1.1f%%', 
                       colors=self.colors[:len(weights)], startangle=90)
                ax2.set_title('Структура портфеля', fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            charts.append(self._fig_to_png(fig))
        
        # Efficient Frontier
        if frontier is not None and hasattr(frontier, 'empty') and isinstance(frontier, pd.DataFrame) and not frontier.empty and 'vol' in frontier.columns and 'ret' in frontier.columns:
            plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.scatter(frontier['vol'], frontier['ret'], s=20, alpha=0.6, color=self.colors[0])
            ax.set_xlabel('Риск (волатильность)', fontsize=12)
            ax.set_ylabel('Доходность', fontsize=12)
            ax.set_title('Efficient Frontier', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            charts.append(self._fig_to_png(fig))
        
        return report_text, charts
    
    def _build_inflation_report(self, data: Dict[str, Any], user_query: str) -> Tuple[str, List[bytes]]:
        """Строит отчет по инфляции"""
        ticker = data.get('ticker', 'Unknown')
        country = data.get('country', 'Unknown')
        name = data.get('name', 'CPI')
        currency = data.get('currency', 'Unknown')
        period = data.get('period', 'Unknown')
        cpi_data = data.get('cpi_data')  # Изменено с 'cpi' на 'cpi_data'
        metrics = data.get('metrics', {})
        
        # Текстовый отчет
        report_text = f"📈 **Анализ инфляции**\n\n"
        report_text += f"**Страна:** {country}\n"
        report_text += f"**Индикатор:** {name}\n"
        report_text += f"**Тикер:** {ticker}\n"
        report_text += f"**Валюта:** {currency}\n"
        report_text += f"**Период анализа:** {period}\n"
        
        # Добавляем информацию о периоде данных
        if data.get('first_date') and data.get('first_date') != 'N/A':
            report_text += f"**Первый день:** {data.get('first_date')}\n"
        if data.get('last_date') and data.get('last_date') != 'N/A':
            report_text += f"**Последний день:** {data.get('last_date')}\n"
        if data.get('period_length') and data.get('period_length') != 'N/A':
            report_text += f"**Длина периода:** {data.get('period_length')}\n"
        
        report_text += "\n"
        
        # Метрики
        if metrics:
            report_text += "**📊 Ключевые показатели:**\n"
            if metrics.get('cagr') is not None:
                report_text += f"• Среднегодовой рост: {metrics['cagr']*100:.2f}%\n"
            if metrics.get('volatility') is not None:
                report_text += f"• Волатильность: {metrics['volatility']*100:.2f}%\n"
            if metrics.get('sharpe') is not None:
                report_text += f"• Sharpe Ratio: {metrics['sharpe']:.2f}\n"
            if metrics.get('max_drawdown') is not None:
                report_text += f"• Макс. просадка: {metrics['max_drawdown']*100:.2f}%\n"
            if metrics.get('total_return') is not None:
                report_text += f"• Общая доходность: {metrics['total_return']*100:.2f}%\n"
        
        # Графики
        charts = []
        
        # 1. График из okama_handler (если есть)
        if data.get('chart'):
            charts.append(data['chart'])
        
        # 2. Дополнительный график CPI (если есть данные)
        if cpi_data is not None and hasattr(cpi_data, 'empty') and isinstance(cpi_data, pd.Series) and not cpi_data.empty:
            plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(cpi_data.index, cpi_data.values, color=self.colors[0], linewidth=2)
            ax.set_title(f'{name} - Динамика CPI ({country})', fontsize=14, fontweight='bold')
            ax.set_ylabel(f'CPI ({currency})', fontsize=12)
            ax.set_xlabel('Дата', fontsize=12)
            ax.grid(True, alpha=0.3)
            ax.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            charts.append(self._fig_to_png(fig))
            
            # 3. График годового изменения CPI
            if len(cpi_data) > 12:  # Если есть достаточно данных для годового изменения
                plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
                fig, ax = plt.subplots(figsize=(10, 4))
                yearly_change = cpi_data.pct_change(12).dropna() * 100  # Годовое изменение в %
                ax.plot(yearly_change.index, yearly_change.values, color=self.colors[1], linewidth=2)
                ax.set_title(f'{name} - Годовое изменение CPI ({country})', fontsize=12)
                ax.set_ylabel('Изменение CPI (%)', fontsize=10)
                ax.set_xlabel('Дата', fontsize=10)
                ax.grid(True, alpha=0.3)
                ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                ax.tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                charts.append(self._fig_to_png(fig))
        
        return report_text, charts
    
    def _build_macro_report(self, data: Dict[str, Any], user_query: str) -> Tuple[str, List[bytes]]:
        """Строит отчет по макроэкономическим данным"""
        # Для макро-данных используем сравнение активов
        return self._build_comparison_report(data, user_query)
    
    def _build_generic_report(self, data: Dict[str, Any], user_query: str) -> Tuple[str, List[bytes]]:
        """Строит общий отчет"""
        report_text = f"📊 **Финансовый анализ**\n\n"
        report_text += f"**Запрос:** {user_query}\n\n"
        
        if 'error' in data:
            report_text += f"❌ **Ошибка:** {data['error']}\n"
        else:
            report_text += "✅ Анализ завершен успешно\n"
        
        return report_text, []
    
    def _create_metrics_table(self, metrics: Dict[str, Dict[str, Any]]) -> str:
        """Создает таблицу метрик"""
        if not metrics:
            return "Нет данных о метриках"
        
        # Диагностика структуры метрик
        logger.info(f"Metrics structure: {metrics}")
        
        # Создаем DataFrame
        rows = []
        for ticker, metric_data in metrics.items():
            logger.info(f"Processing metrics for {ticker}: {metric_data}")
            
            # Безопасное извлечение значений с проверкой типов
            cagr = metric_data.get('cagr')
            volatility = metric_data.get('volatility')
            sharpe = metric_data.get('sharpe')
            max_drawdown = metric_data.get('max_drawdown')
            total_return = metric_data.get('total_return')
            
            # Форматируем значения с проверкой на None
            row = {
                'Тикер': ticker,
                'CAGR (%)': f"{cagr*100:.2f}" if cagr is not None else "N/A",
                'Волатильность (%)': f"{volatility*100:.2f}" if volatility is not None else "N/A",
                'Sharpe': f"{sharpe:.2f}" if sharpe is not None else "N/A",
                'Макс. просадка (%)': f"{max_drawdown*100:.2f}" if max_drawdown is not None else "N/A",
                'Общая доходность (%)': f"{total_return*100:.2f}" if total_return is not None else "N/A"
            }
            rows.append(row)
        
        if not rows:
            return "Не удалось создать таблицу метрик"
        
        try:
            df = pd.DataFrame(rows)
            return df.to_string(index=False)
        except Exception as e:
            logger.error(f"Error creating metrics table: {e}")
            # Fallback - простой текстовый формат
            result = "**Метрики по активам:**\n\n"
            for row in rows:
                result += f"**{row['Тикер']}:**\n"
                result += f"• CAGR: {row['CAGR (%)']}\n"
                result += f"• Волатильность: {row['Волатильность (%)']}\n"
                result += f"• Sharpe: {row['Sharpe']}\n"
                result += f"• Макс. просадка: {row['Макс. просадка (%)']}\n"
                result += f"• Общая доходность: {row['Общая доходность (%)']}\n\n"
            return result
    
    def _fig_to_png(self, fig) -> bytes:
        """Конвертирует matplotlib figure в PNG bytes"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    
    def _fig_to_png_with_analysis(self, fig, chart_type: str, asset_info: Dict[str, Any] = None) -> Tuple[bytes, str]:
        """
        Конвертирует matplotlib figure в PNG bytes и добавляет AI-анализ
        
        Args:
            fig: matplotlib figure
            chart_type: тип графика для анализа
            asset_info: информация об активе для контекста
            
        Returns:
            Tuple[bytes, str]: (PNG bytes, AI анализ)
        """
        # Сначала конвертируем в PNG
        png_bytes = self._fig_to_png(fig)
        
        # Создаем детальное описание графика для анализа
        if asset_info:
            ticker = asset_info.get('ticker', 'Unknown')
            name = asset_info.get('name', ticker)
            
            # Улучшенное описание графика с техническими деталями
            if "Ежедневный график цен" in chart_type:
                chart_desc = f"""Ежедневный график цен акции {ticker} ({name}) за последний год. 
График показывает динамику изменения цены акции по дням, включая открытие, максимум, минимум и закрытие.
Масштаб: дневные свечи, временной период: 1 год."""
            elif "Месячный график цен" in chart_type:
                chart_desc = f"""Месячный график цен акции {ticker} ({name}) за 10 лет. 
График отображает месячные изменения цены, показывая долгосрочные тренды и циклы.
Масштаб: месячные свечи, временной период: 10 лет."""
            elif "Волатильность" in chart_type:
                chart_desc = f"""График волатильности акции {ticker} ({name}). 
Показывает изменение волатильности цены во времени, рассчитанной как скользящее стандартное отклонение доходности.
Высокая волатильность указывает на нестабильность, низкая - на стабильность."""
            elif "Просадки" in chart_type:
                chart_desc = f"""График просадок акции {ticker} ({name}). 
Отображает максимальные потери от пиковых значений цены.
Показывает риск-метрики и периоды восстановления после падений."""
            else:
                chart_desc = f"""{chart_type} для {ticker} ({name}). 
Финансовый график, показывающий различные аспекты поведения цены акции."""
        else:
            chart_desc = f"""{chart_type}. 
Финансовый график для анализа цен и технических индикаторов."""
        
        analysis_prompt = f"""Проанализируй финансовый график: {chart_desc}

Задача: Опиши конкретно то, что видишь на графике:
1. Тренд (восходящий/нисходящий/боковой)
2. Ключевые уровни поддержки и сопротивления
3. Волатильность (высокая/средняя/низкая)

Анализ должен быть кратким и конкретным на русском языке (2-3 предложения)."""
        
        try:
            # Анализируем график с помощью Vision AI
            ai_response = self.yandexgpt.ask_question_with_vision(
                analysis_prompt,
                png_bytes,
                chart_desc
            )
            
            if ai_response and not ai_response.startswith("Ошибка") and not ai_response.startswith("Не удалось"):
                return png_bytes, ai_response
            else:
                return png_bytes, "⚠️ Не удалось проанализировать график"
                    
        except Exception as e:
            logger.error(f"Error analyzing chart: {e}")
            return png_bytes, f"⚠️ Ошибка анализа: {str(e)}"
    
    def create_csv_report(self, data: Dict[str, Any], intent: str) -> str:
        """Создает CSV отчет"""
        try:
            if intent == 'asset_single':
                return self._create_single_asset_csv(data)
            elif intent == 'asset_compare':
                return self._create_comparison_csv(data)
            elif intent == 'portfolio_analysis':
                return self._create_portfolio_csv(data)
            else:
                return self._create_generic_csv(data)
        except Exception as e:
            logger.error(f"Error creating CSV report: {e}")
            return ""
    
    def _create_single_asset_csv(self, data: Dict[str, Any]) -> str:
        """Создает CSV для одного актива"""
        prices = data.get('prices')
        if prices is None or not hasattr(prices, 'empty') or not isinstance(prices, pd.Series) or prices.empty:
            return ""
        
        csv_data = prices.reset_index()
        csv_data.columns = ['Date', 'Price']
        return csv_data.to_csv(index=False)
    
    def _create_comparison_csv(self, data: Dict[str, Any]) -> str:
        """Создает CSV для сравнения активов"""
        prices = data.get('prices')
        if prices is None or not hasattr(prices, 'empty') or not isinstance(prices, pd.DataFrame) or prices.empty:
            return ""
        
        csv_data = prices.reset_index()
        return csv_data.to_csv(index=False)
    
    def _create_portfolio_csv(self, data: Dict[str, Any]) -> str:
        """Создает CSV для портфеля"""
        portfolio_prices = data.get('portfolio_prices')
        if portfolio_prices is None or not hasattr(portfolio_prices, 'empty') or not isinstance(portfolio_prices, pd.Series) or portfolio_prices.empty:
            return ""
        
        csv_data = portfolio_prices.reset_index()
        csv_data.columns = ['Date', 'Portfolio_Value']
        return csv_data.to_csv(index=False)
    
    def _create_generic_csv(self, data: Dict[str, Any]) -> str:
        """Создает общий CSV"""
        return "No data available for CSV export"

    def _compute_simple_metrics(self, prices: pd.Series) -> Dict[str, Any]:
        """Вычисляет простые метрики из цен"""
        try:
            if len(prices) < 2:
                return {}
            
            # Общая доходность
            total_return = (prices.iloc[-1] / prices.iloc[0]) - 1.0
            
            # Волатильность (годовая)
            returns = prices.pct_change().dropna()
            if len(returns) > 1:
                # Определяем частоту данных
                if len(returns) > 200:  # Дневные данные
                    periods_per_year = 252
                elif len(returns) > 20:  # Месячные данные
                    periods_per_year = 12
                else:  # Квартальные или годовые
                    periods_per_year = 4
                
                volatility = float(np.std(returns, ddof=1)) * np.sqrt(periods_per_year)
            else:
                volatility = None
            
            return {
                'total_return': total_return,
                'volatility': volatility
            }
            
        except Exception as e:
            logger.warning(f"Error computing simple metrics: {e}")
            return {}

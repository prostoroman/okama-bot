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

logger = logging.getLogger(__name__)

class EnhancedReportBuilder:
    """Улучшенный генератор отчетов для финансового анализа"""
    
    def __init__(self):
        # Настройки стиля
        plt.style.use('default')
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
    def build_report(self, intent: str, data: Dict[str, Any], user_query: str) -> Tuple[str, List[bytes]]:
        """Основной метод построения отчета"""
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
            return f"Ошибка построения отчета: {str(e)}", []
    
    def _build_single_asset_report(self, data: Dict[str, Any], user_query: str) -> Tuple[str, List[bytes]]:
        """Строит отчет по одному активу"""
        ticker = data.get('ticker', 'Unknown')
        name = data.get('name', ticker)
        currency = data.get('currency', 'Unknown')
        period = data.get('period', 'Unknown')
        metrics = data.get('metrics', {})
        prices = data.get('prices')
        
        # Текстовый отчет
        report_text = f"📊 **Анализ актива: {name} ({ticker})**\n\n"
        report_text += f"**Валюта:** {currency}\n"
        report_text += f"**Период:** {period}\n\n"
        
        # Метрики
        if metrics:
            report_text += "**Ключевые метрики:**\n"
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
        
        # Графики
        charts = []
        if isinstance(prices, pd.Series) and not prices.empty:
            # График цены
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
            charts.append(self._fig_to_png(fig))
        
        return report_text, charts
    
    def _build_comparison_report(self, data: Dict[str, Any], user_query: str) -> Tuple[str, List[bytes]]:
        """Строит отчет по сравнению активов"""
        tickers = data.get('tickers', [])
        metrics = data.get('metrics', {})
        correlation = data.get('correlation')
        prices = data.get('prices')
        period = data.get('period', 'Unknown')
        currency = data.get('currency', 'Unknown')
        
        # Текстовый отчет
        report_text = f"⚖️ **Сравнение активов**\n\n"
        report_text += f"**Активы:** {', '.join(tickers)}\n"
        report_text += f"**Период:** {period}\n"
        report_text += f"**Валюта:** {currency}\n\n"
        
        # Таблица метрик
        if metrics:
            report_text += "**Сравнительная таблица метрик:**\n"
            metrics_table = self._create_metrics_table(metrics)
            report_text += metrics_table + "\n"
        
        # Корреляции
        if isinstance(correlation, pd.DataFrame) and not correlation.empty:
            report_text += "**Корреляции между активами:**\n"
            try:
                correlation_text = correlation.round(3).to_string()
                report_text += correlation_text + "\n"
            except Exception as e:
                report_text += f"Ошибка отображения корреляций: {str(e)}\n"
        
        # Графики
        charts = []
        if isinstance(prices, pd.DataFrame) and not prices.empty:
            # Нормализованные цены
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # График цен
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
            
            # График доходности
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
        if isinstance(portfolio_prices, pd.Series) and not portfolio_prices.empty:
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
        if isinstance(frontier, pd.DataFrame) and not frontier.empty and 'vol' in frontier.columns and 'ret' in frontier.columns:
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
        cpi_data = data.get('cpi')
        period = data.get('period', 'Unknown')
        metrics = data.get('metrics', {})
        
        # Текстовый отчет
        report_text = f"📈 **Анализ инфляции**\n\n"
        report_text += f"**Страна:** {country}\n"
        report_text += f"**Тикер:** {ticker}\n"
        report_text += f"**Период:** {period}\n\n"
        
        # Метрики
        if metrics:
            report_text += "**Ключевые показатели:**\n"
            if metrics.get('cagr') is not None:
                report_text += f"• Среднегодовой рост: {metrics['cagr']*100:.2f}%\n"
            if metrics.get('volatility') is not None:
                report_text += f"• Волатильность: {metrics['volatility']*100:.2f}%\n"
        
        # Графики
        charts = []
        if isinstance(cpi_data, pd.Series) and not cpi_data.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(cpi_data.index, cpi_data.values, color=self.colors[0], linewidth=2)
            ax.set_title(f'Индекс потребительских цен (CPI) - {country}', fontsize=14, fontweight='bold')
            ax.set_ylabel('CPI', fontsize=12)
            ax.set_xlabel('Дата', fontsize=12)
            ax.grid(True, alpha=0.3)
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
            return "Нет данных"
        
        # Создаем DataFrame
        rows = []
        for ticker, metric_data in metrics.items():
            row = {
                'Тикер': ticker,
                'CAGR (%)': f"{(metric_data.get('cagr') or 0)*100:.2f}",
                'Волатильность (%)': f"{(metric_data.get('volatility') or 0)*100:.2f}",
                'Sharpe': f"{(metric_data.get('sharpe') or 0):.2f}",
                'Макс. просадка (%)': f"{(metric_data.get('max_drawdown') or 0)*100:.2f}"
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        return df.to_string(index=False)
    
    def _fig_to_png(self, fig) -> bytes:
        """Конвертирует matplotlib figure в PNG bytes"""
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    
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
        if not isinstance(prices, pd.Series) or prices.empty:
            return ""
        
        csv_data = prices.reset_index()
        csv_data.columns = ['Date', 'Price']
        return csv_data.to_csv(index=False)
    
    def _create_comparison_csv(self, data: Dict[str, Any]) -> str:
        """Создает CSV для сравнения активов"""
        prices = data.get('prices')
        if not isinstance(prices, pd.DataFrame) or prices.empty:
            return ""
        
        csv_data = prices.reset_index()
        return csv_data.to_csv(index=False)
    
    def _create_portfolio_csv(self, data: Dict[str, Any]) -> str:
        """Создает CSV для портфеля"""
        portfolio_prices = data.get('portfolio_prices')
        if not isinstance(portfolio_prices, pd.Series) or portfolio_prices.empty:
            return ""
        
        csv_data = portfolio_prices.reset_index()
        csv_data.columns = ['Date', 'Portfolio_Value']
        return csv_data.to_csv(index=False)
    
    def _create_generic_csv(self, data: Dict[str, Any]) -> str:
        """Создает общий CSV"""
        return "No data available for CSV export"

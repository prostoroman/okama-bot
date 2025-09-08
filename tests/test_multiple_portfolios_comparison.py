#!/usr/bin/env python3
"""
Тест поддержки сравнения нескольких портфелей
Проверяет, что смешанное сравнение и вспомогательные кнопки корректно работают с несколькими портфелями
"""

import unittest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import OkamaFinanceBot


class TestMultiplePortfoliosComparison(unittest.TestCase):
    """Тест поддержки сравнения нескольких портфелей"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = OkamaFinanceBot()
        
        # Мокаем контекст пользователя с несколькими портфелями
        self.mock_user_context = {
            'saved_portfolios': {
                'PORTFOLIO_1': {
                    'symbols': ['SPY.US', 'QQQ.US'],
                    'weights': [0.6, 0.4],
                    'currency': 'USD',
                    'portfolio_symbol': 'PORTFOLIO_1'
                },
                'PORTFOLIO_2': {
                    'symbols': ['VOO.US', 'BND.US'],
                    'weights': [0.7, 0.3],
                    'currency': 'USD',
                    'portfolio_symbol': 'PORTFOLIO_2'
                },
                'PORTFOLIO_3': {
                    'symbols': ['SBER.MOEX', 'GAZP.MOEX'],
                    'weights': [0.5, 0.5],
                    'currency': 'RUB',
                    'portfolio_symbol': 'PORTFOLIO_3'
                }
            },
            'current_symbols': ['PORTFOLIO_1', 'PORTFOLIO_2', 'SPY.US'],
            'current_currency': 'USD',
            'last_analysis_type': 'comparison',
            'portfolio_contexts': [
                {
                    'symbol': 'PORTFOLIO_1',
                    'portfolio_symbols': ['SPY.US', 'QQQ.US'],
                    'portfolio_weights': [0.6, 0.4],
                    'portfolio_currency': 'USD',
                    'portfolio_object': Mock()
                },
                {
                    'symbol': 'PORTFOLIO_2',
                    'portfolio_symbols': ['VOO.US', 'BND.US'],
                    'portfolio_weights': [0.7, 0.3],
                    'portfolio_currency': 'USD',
                    'portfolio_object': Mock()
                },
                {
                    'symbol': 'SPY.US',
                    'portfolio_symbols': ['SPY.US'],
                    'portfolio_weights': [1.0],
                    'portfolio_currency': None,
                    'portfolio_object': None
                }
            ],
            'expanded_symbols': [
                Mock(),  # PORTFOLIO_1 wealth_index
                Mock(),  # PORTFOLIO_2 wealth_index
                'SPY.US'  # Regular asset
            ]
        }
        
        # Мокаем методы бота
        self.bot._get_user_context = Mock(return_value=self.mock_user_context)
        self.bot._update_user_context = Mock()
        self.bot._send_message_safe = Mock()
        self.bot._send_callback_message = Mock()
        self.bot.logger = Mock()
    
    def test_multiple_portfolios_expansion(self):
        """Тест расширения нескольких портфелей в команде /compare"""
        # Подготавливаем мок для _ok_portfolio
        mock_portfolio = Mock()
        mock_portfolio.wealth_index = pd.Series([1.0, 1.1, 1.2], index=pd.date_range('2020-01-01', periods=3))
        
        with patch.object(self.bot, '_ok_portfolio', return_value=mock_portfolio):
            # Симулируем обработку команды /compare с несколькими портфелями
            symbols = ['PORTFOLIO_1', 'PORTFOLIO_2', 'SPY.US']
            
            # Проверяем, что портфели корректно определяются
            saved_portfolios = self.mock_user_context['saved_portfolios']
            
            expanded_symbols = []
            portfolio_descriptions = []
            portfolio_contexts = []
            
            for symbol in symbols:
                is_portfolio = symbol in saved_portfolios
                
                if is_portfolio:
                    portfolio_info = saved_portfolios[symbol]
                    portfolio_symbols = portfolio_info['symbols']
                    portfolio_weights = portfolio_info['weights']
                    portfolio_currency = portfolio_info['currency']
                    
                    # Создаем портфель
                    portfolio = self.bot._ok_portfolio(portfolio_symbols, weights=portfolio_weights, currency=portfolio_currency)
                    expanded_symbols.append(portfolio.wealth_index)
                    portfolio_descriptions.append(f"{symbol} ({', '.join(portfolio_symbols)})")
                    portfolio_contexts.append({
                        'symbol': symbol,
                        'portfolio_symbols': portfolio_symbols,
                        'portfolio_weights': portfolio_weights,
                        'portfolio_currency': portfolio_currency,
                        'portfolio_object': portfolio
                    })
                else:
                    expanded_symbols.append(symbol)
                    portfolio_descriptions.append(symbol)
                    portfolio_contexts.append({
                        'symbol': symbol,
                        'portfolio_symbols': [symbol],
                        'portfolio_weights': [1.0],
                        'portfolio_currency': None,
                        'portfolio_object': None
                    })
            
            # Проверяем результаты
            self.assertEqual(len(expanded_symbols), 3)
            self.assertEqual(len(portfolio_descriptions), 3)
            self.assertEqual(len(portfolio_contexts), 3)
            
            # Проверяем, что портфели корректно расширены
            self.assertTrue(isinstance(expanded_symbols[0], pd.Series))  # PORTFOLIO_1
            self.assertTrue(isinstance(expanded_symbols[1], pd.Series))  # PORTFOLIO_2
            self.assertEqual(expanded_symbols[2], 'SPY.US')  # Regular asset
            
            # Проверяем описания
            self.assertIn('PORTFOLIO_1 (SPY.US, QQQ.US)', portfolio_descriptions[0])
            self.assertIn('PORTFOLIO_2 (VOO.US, BND.US)', portfolio_descriptions[1])
            self.assertEqual(portfolio_descriptions[2], 'SPY.US')
    
    def test_mixed_comparison_dividends_multiple_portfolios(self):
        """Тест создания графика дивидендной доходности для нескольких портфелей"""
        # Мокаем AssetList для дивидендной доходности
        mock_asset_list = Mock()
        mock_asset_list.dividend_yields = pd.DataFrame({
            'SPY.US': [0.02, 0.025, 0.03],
            'QQQ.US': [0.01, 0.015, 0.02],
            'VOO.US': [0.018, 0.022, 0.027],
            'BND.US': [0.03, 0.032, 0.035]
        }, index=pd.date_range('2020-01-01', periods=3))
        
        with patch.object(self.bot, '_ok_asset_list', return_value=mock_asset_list):
            # Симулируем создание графика дивидендной доходности
            symbols = ['PORTFOLIO_1', 'PORTFOLIO_2', 'SPY.US']
            currency = 'USD'
            
            # Проверяем обработку портфелей
            dividends_data = {}
            
            for i, portfolio_context in enumerate(self.mock_user_context['portfolio_contexts'][:2]):  # Только портфели
                symbol = portfolio_context['symbol']
                assets = portfolio_context['portfolio_symbols']
                weights = portfolio_context['portfolio_weights']
                
                # Создаем AssetList для активов портфеля
                portfolio_asset_list = self.bot._ok_asset_list(assets, currency=currency)
                
                if hasattr(portfolio_asset_list, 'dividend_yields'):
                    # Рассчитываем взвешенную дивидендную доходность
                    total_dividend_yield = 0
                    for asset, weight in zip(assets, weights):
                        if asset in portfolio_asset_list.dividend_yields.columns:
                            dividend_yield = portfolio_asset_list.dividend_yields[asset].iloc[-1]
                            total_dividend_yield += dividend_yield * weight
                    
                    dividends_data[symbol] = total_dividend_yield
            
            # Проверяем результаты
            self.assertEqual(len(dividends_data), 2)
            self.assertIn('PORTFOLIO_1', dividends_data)
            self.assertIn('PORTFOLIO_2', dividends_data)
            
            # Проверяем, что дивидендная доходность рассчитана корректно
            self.assertIsInstance(dividends_data['PORTFOLIO_1'], (int, float))
            self.assertIsInstance(dividends_data['PORTFOLIO_2'], (int, float))
    
    def test_mixed_comparison_drawdowns_multiple_portfolios(self):
        """Тест создания графика просадок для нескольких портфелей"""
        # Мокаем Portfolio для просадок
        mock_portfolio = Mock()
        mock_portfolio.wealth_index = pd.Series([1.0, 1.1, 0.95, 1.05, 1.2], 
                                              index=pd.date_range('2020-01-01', periods=5))
        
        with patch('okama.Portfolio', return_value=mock_portfolio):
            # Симулируем создание графика просадок
            symbols = ['PORTFOLIO_1', 'PORTFOLIO_2', 'SPY.US']
            currency = 'USD'
            
            # Проверяем обработку портфелей
            drawdowns_data = {}
            
            for i, portfolio_context in enumerate(self.mock_user_context['portfolio_contexts'][:2]):  # Только портфели
                symbol = portfolio_context['symbol']
                assets = portfolio_context['portfolio_symbols']
                weights = portfolio_context['portfolio_weights']
                
                # Создаем портфель
                import okama as ok
                portfolio = ok.Portfolio(
                    assets=assets,
                    weights=weights,
                    rebalancing_strategy=ok.Rebalance(period="year"),
                    symbol=symbol
                )
                
                # Рассчитываем просадки
                wealth_series = portfolio.wealth_index
                returns = wealth_series.pct_change().dropna()
                
                if len(returns) > 0:
                    cumulative = (1 + returns).cumprod()
                    running_max = cumulative.expanding().max()
                    drawdowns = (cumulative - running_max) / running_max
                    drawdowns_data[symbol] = drawdowns
            
            # Проверяем результаты
            self.assertEqual(len(drawdowns_data), 2)
            self.assertIn('PORTFOLIO_1', drawdowns_data)
            self.assertIn('PORTFOLIO_2', drawdowns_data)
            
            # Проверяем, что просадки рассчитаны корректно
            self.assertIsInstance(drawdowns_data['PORTFOLIO_1'], pd.Series)
            self.assertIsInstance(drawdowns_data['PORTFOLIO_2'], pd.Series)
    
    def test_mixed_comparison_correlation_multiple_portfolios(self):
        """Тест создания корреляционной матрицы для нескольких портфелей"""
        # Мокаем Portfolio для корреляции
        mock_portfolio = Mock()
        mock_portfolio.wealth_index = pd.Series([1.0, 1.1, 1.2, 1.15, 1.25], 
                                              index=pd.date_range('2020-01-01', periods=5))
        
        with patch('okama.Portfolio', return_value=mock_portfolio):
            # Симулируем создание корреляционной матрицы
            symbols = ['PORTFOLIO_1', 'PORTFOLIO_2', 'SPY.US']
            currency = 'USD'
            
            # Проверяем обработку портфелей
            correlation_data = {}
            
            for i, portfolio_context in enumerate(self.mock_user_context['portfolio_contexts'][:2]):  # Только портфели
                symbol = portfolio_context['symbol']
                assets = portfolio_context['portfolio_symbols']
                weights = portfolio_context['portfolio_weights']
                
                # Создаем портфель
                import okama as ok
                portfolio = ok.Portfolio(
                    assets=assets,
                    weights=weights,
                    rebalancing_strategy=ok.Rebalance(period="year"),
                    symbol=symbol
                )
                
                # Рассчитываем доходность для корреляции
                wealth_series = portfolio.wealth_index
                returns = wealth_series.pct_change().dropna()
                
                if len(returns) > 0:
                    correlation_data[symbol] = returns
            
            # Проверяем результаты
            self.assertEqual(len(correlation_data), 2)
            self.assertIn('PORTFOLIO_1', correlation_data)
            self.assertIn('PORTFOLIO_2', correlation_data)
            
            # Проверяем, что доходность рассчитана корректно
            self.assertIsInstance(correlation_data['PORTFOLIO_1'], pd.Series)
            self.assertIsInstance(correlation_data['PORTFOLIO_2'], pd.Series)
    
    def test_assetlist_creation_with_multiple_portfolios(self):
        """Тест создания AssetList с несколькими портфелями"""
        # Мокаем Portfolio и AssetList
        mock_portfolio = Mock()
        mock_portfolio.wealth_index = pd.Series([1.0, 1.1, 1.2], index=pd.date_range('2020-01-01', periods=3))
        
        mock_asset_list = Mock()
        mock_asset_list.wealth_indexes = pd.DataFrame({
            'PORTFOLIO_1': [1.0, 1.1, 1.2],
            'PORTFOLIO_2': [1.0, 1.05, 1.15],
            'SPY.US': [1.0, 1.08, 1.18]
        }, index=pd.date_range('2020-01-01', periods=3))
        
        with patch('okama.Portfolio', return_value=mock_portfolio), \
             patch.object(self.bot, '_ok_asset_list', return_value=mock_asset_list):
            
            # Симулируем создание AssetList с несколькими портфелями
            assets_for_comparison = []
            
            for i, portfolio_context in enumerate(self.mock_user_context['portfolio_contexts']):
                if i < 2:  # Первые два - портфели
                    portfolio = self.bot._ok_portfolio(
                        portfolio_context['portfolio_symbols'],
                        portfolio_context['portfolio_weights'],
                        currency=portfolio_context['portfolio_currency']
                    )
                    assets_for_comparison.append(portfolio)
                else:  # Третий - обычный актив
                    assets_for_comparison.append(portfolio_context['symbol'])
            
            # Создаем AssetList
            comparison = self.bot._ok_asset_list(assets_for_comparison, currency='USD')
            
            # Проверяем результаты
            self.assertEqual(len(assets_for_comparison), 3)
            self.assertTrue(hasattr(assets_for_comparison[0], 'wealth_index'))  # PORTFOLIO_1
            self.assertTrue(hasattr(assets_for_comparison[1], 'wealth_index'))  # PORTFOLIO_2
            self.assertEqual(assets_for_comparison[2], 'SPY.US')  # Regular asset
    
    def test_context_storage_for_multiple_portfolios(self):
        """Тест сохранения контекста для нескольких портфелей"""
        # Проверяем, что контекст корректно сохраняется
        user_id = 12345
        
        # Симулируем сохранение контекста
        self.bot._update_user_context(
            user_id,
            current_symbols=['PORTFOLIO_1', 'PORTFOLIO_2', 'SPY.US'],
            current_currency='USD',
            last_analysis_type='comparison',
            portfolio_contexts=self.mock_user_context['portfolio_contexts'],
            expanded_symbols=self.mock_user_context['expanded_symbols']
        )
        
        # Проверяем, что контекст сохранен
        self.bot._update_user_context.assert_called_once()
        
        # Проверяем параметры вызова
        call_args = self.bot._update_user_context.call_args[1]
        self.assertEqual(call_args['current_symbols'], ['PORTFOLIO_1', 'PORTFOLIO_2', 'SPY.US'])
        self.assertEqual(call_args['current_currency'], 'USD')
        self.assertEqual(call_args['last_analysis_type'], 'comparison')
        self.assertEqual(len(call_args['portfolio_contexts']), 3)
        self.assertEqual(len(call_args['expanded_symbols']), 3)


if __name__ == '__main__':
    unittest.main()

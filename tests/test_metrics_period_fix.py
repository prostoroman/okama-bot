#!/usr/bin/env python3
"""
Тест для проверки исправления метрик по периодам в команде /info
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os
import pandas as pd
import numpy as np

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestMetricsPeriodFix(unittest.TestCase):
    """Тест исправления метрик по периодам"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        self.bot.logger = MagicMock()
        
        # Создаем мок актива с тестовыми данными
        self.mock_asset = MagicMock()
        
        # Создаем тестовые данные за 5 лет (1260 торговых дней)
        dates = pd.date_range(start='2019-01-01', end='2024-01-01', freq='D')
        # Фильтруем только рабочие дни (примерно 252 в год)
        dates = dates[dates.weekday < 5][:1260]
        
        # Создаем ценовые данные с трендом
        np.random.seed(42)
        base_price = 100
        trend = np.linspace(0, 0.5, len(dates))  # 50% рост за 5 лет
        noise = np.random.normal(0, 0.02, len(dates))  # 2% волатильность
        prices = base_price * (1 + trend + noise).cumprod()
        
        self.mock_asset.close_daily = pd.Series(prices, index=dates)
        self.mock_asset.name = "Test Asset"
        self.mock_asset.country = "Test Country"
        self.mock_asset.asset_type = "Stock"
        self.mock_asset.exchange = "TEST"
        self.mock_asset.currency = "USD"
        self.mock_asset.isin = "TEST123456789"
        self.mock_asset.dividend_yield = pd.Series([0.02] * len(dates), index=dates)
    
    def test_get_data_for_period_1y(self):
        """Тест: фильтрация данных за 1 год"""
        filtered_data, returns = self.bot._get_data_for_period(self.mock_asset, '1Y')
        
        # Проверяем, что данные отфильтрованы правильно
        self.assertIsNotNone(filtered_data)
        self.assertIsNotNone(returns)
        self.assertEqual(len(filtered_data), 252)  # 1 год = 252 торговых дня
        self.assertEqual(len(returns), 251)  # returns на 1 меньше чем prices
    
    def test_get_data_for_period_5y(self):
        """Тест: фильтрация данных за 5 лет"""
        filtered_data, returns = self.bot._get_data_for_period(self.mock_asset, '5Y')
        
        # Проверяем, что данные отфильтрованы правильно
        self.assertIsNotNone(filtered_data)
        self.assertIsNotNone(returns)
        self.assertEqual(len(filtered_data), 1260)  # 5 лет = 1260 торговых дней
        self.assertEqual(len(returns), 1259)  # returns на 1 меньше чем prices
    
    def test_get_data_for_period_max(self):
        """Тест: фильтрация данных за MAX период"""
        filtered_data, returns = self.bot._get_data_for_period(self.mock_asset, 'MAX')
        
        # Проверяем, что данные не фильтруются
        self.assertIsNotNone(filtered_data)
        self.assertIsNotNone(returns)
        self.assertEqual(len(filtered_data), 1260)  # Все данные
        self.assertEqual(len(returns), 1259)
    
    @patch('asyncio.sleep', return_value=None)
    async def test_metrics_different_periods(self, mock_sleep):
        """Тест: метрики различаются для разных периодов"""
        
        # Получаем метрики для 1 года
        metrics_1y = await self.bot._get_asset_key_metrics(self.mock_asset, "TEST.US", "1Y")
        
        # Получаем метрики для 5 лет
        metrics_5y = await self.bot._get_asset_key_metrics(self.mock_asset, "TEST.US", "5Y")
        
        # Получаем метрики для MAX
        metrics_max = await self.bot._get_asset_key_metrics(self.mock_asset, "TEST.US", "MAX")
        
        # Проверяем, что метрики содержат информацию о периоде
        self.assertEqual(metrics_1y.get('period'), '1Y')
        self.assertEqual(metrics_5y.get('period'), '5Y')
        self.assertEqual(metrics_max.get('period'), 'MAX')
        
        # Проверяем, что количество точек данных различается
        self.assertEqual(metrics_1y.get('data_points'), 252)
        self.assertEqual(metrics_5y.get('data_points'), 1260)
        self.assertEqual(metrics_max.get('data_points'), 1260)
        
        # Проверяем, что CAGR различается (из-за разных периодов)
        if metrics_1y.get('cagr') is not None and metrics_5y.get('cagr') is not None:
            # CAGR за 1 год и 5 лет должны быть разными
            self.assertNotEqual(metrics_1y['cagr'], metrics_5y['cagr'])
        
        print(f"✅ 1Y CAGR: {metrics_1y.get('cagr', 'N/A')}")
        print(f"✅ 5Y CAGR: {metrics_5y.get('cagr', 'N/A')}")
        print(f"✅ MAX CAGR: {metrics_max.get('cagr', 'N/A')}")
    
    @patch('asyncio.sleep', return_value=None)
    async def test_format_response_with_period(self, mock_sleep):
        """Тест: форматирование ответа с правильным периодом"""
        
        # Получаем метрики для 5 лет
        metrics_5y = await self.bot._get_asset_key_metrics(self.mock_asset, "TEST.US", "5Y")
        
        # Форматируем ответ
        response = self.bot._format_asset_info_response(self.mock_asset, "TEST.US", metrics_5y)
        
        # Проверяем, что в ответе указан правильный период
        self.assertIn("Ключевые показатели (за 5 лет)", response)
        self.assertNotIn("Ключевые показатели (за 1 год)", response)
        
        print(f"✅ Response contains correct period: '5 лет'")
        print(f"✅ Response preview: {response[:200]}...")


if __name__ == '__main__':
    # Запуск тестов
    unittest.main()

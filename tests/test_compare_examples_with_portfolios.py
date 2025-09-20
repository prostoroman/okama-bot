#!/usr/bin/env python3
"""
Тест для проверки логики примеров сравнения с учетом сохраненных портфелей
"""

import unittest
from services.examples_service import ExamplesService


class TestCompareExamplesWithPortfolios(unittest.TestCase):
    """Тест для проверки генерации примеров сравнения с портфелями"""
    
    def setUp(self):
        """Инициализация тестового сервиса"""
        self.examples_service = ExamplesService()
    
    def test_compare_examples_with_saved_portfolios(self):
        """Тест генерации примеров с сохраненными портфелями"""
        # Тестовые данные
        saved_portfolios = {
            'PORTFOLIO_1': {
                'symbols': ['SPY.US', 'QQQ.US'],
                'weights': [0.6, 0.4],
                'description': 'Тестовый портфель 1'
            },
            'PORTFOLIO_2': {
                'symbols': ['SBER.MOEX', 'GAZP.MOEX'],
                'weights': [0.5, 0.5],
                'description': 'Тестовый портфель 2'
            }
        }
        
        context_tickers = ['AAPL.US', 'MSFT.US']
        
        # Получаем примеры
        examples = self.examples_service.get_compare_examples(
            count=3, 
            context_tickers=context_tickers, 
            saved_portfolios=saved_portfolios
        )
        
        # Проверяем, что примеры сгенерированы
        self.assertGreater(len(examples), 0, "Должны быть сгенерированы примеры")
        
        # Проверяем, что есть примеры с портфелями
        portfolio_examples = [ex for ex in examples if 'PORTFOLIO_' in ex]
        self.assertGreater(len(portfolio_examples), 0, "Должны быть примеры с портфелями")
        
        # Проверяем формат примеров
        for example in examples:
            self.assertIn('`', example, "Пример должен содержать команду в бэктиках")
            self.assertIn(' - ', example, "Пример должен содержать описание")
    
    def test_compare_examples_portfolio_vs_asset(self):
        """Тест генерации примера сравнения портфеля с активом"""
        saved_portfolios = {
            'PORTFOLIO_1': {
                'symbols': ['SPY.US', 'QQQ.US'],
                'weights': [0.6, 0.4]
            }
        }
        
        context_tickers = ['AAPL.US']
        
        examples = self.examples_service.get_compare_examples(
            count=3,
            context_tickers=context_tickers,
            saved_portfolios=saved_portfolios
        )
        
        # Проверяем, что есть пример сравнения портфеля с активом
        portfolio_asset_examples = [
            ex for ex in examples 
            if 'PORTFOLIO_1' in ex and 'AAPL.US' in ex
        ]
        self.assertGreater(len(portfolio_asset_examples), 0, 
                          "Должен быть пример сравнения портфеля с активом")
    
    def test_compare_examples_two_portfolios(self):
        """Тест генерации примера сравнения двух портфелей"""
        saved_portfolios = {
            'PORTFOLIO_1': {
                'symbols': ['SPY.US', 'QQQ.US'],
                'weights': [0.6, 0.4]
            },
            'PORTFOLIO_2': {
                'symbols': ['SBER.MOEX', 'GAZP.MOEX'],
                'weights': [0.5, 0.5]
            },
            'PORTFOLIO_3': {
                'symbols': ['AAPL.US', 'MSFT.US'],
                'weights': [0.7, 0.3]
            }
        }
        
        examples = self.examples_service.get_compare_examples(
            count=3,
            context_tickers=None,
            saved_portfolios=saved_portfolios
        )
        
        # Проверяем, что есть пример сравнения двух портфелей
        portfolio_vs_portfolio_examples = [
            ex for ex in examples 
            if ex.count('PORTFOLIO_') >= 2
        ]
        self.assertGreater(len(portfolio_vs_portfolio_examples), 0,
                          "Должен быть пример сравнения двух портфелей")
    
    def test_compare_examples_portfolio_vs_popular_asset(self):
        """Тест генерации примера сравнения портфеля с популярным активом"""
        saved_portfolios = {
            'PORTFOLIO_1': {
                'symbols': ['SPY.US', 'QQQ.US'],
                'weights': [0.6, 0.4]
            }
        }
        
        examples = self.examples_service.get_compare_examples(
            count=3,
            context_tickers=None,
            saved_portfolios=saved_portfolios
        )
        
        # Проверяем, что есть пример сравнения портфеля с популярным активом
        portfolio_popular_examples = [
            ex for ex in examples 
            if 'PORTFOLIO_1' in ex and ('MOEX' in ex or '.US' in ex)
        ]
        self.assertGreater(len(portfolio_popular_examples), 0,
                          "Должен быть пример сравнения портфеля с популярным активом")
    
    def test_compare_examples_without_portfolios(self):
        """Тест генерации примеров без сохраненных портфелей (обратная совместимость)"""
        context_tickers = ['AAPL.US', 'MSFT.US']
        
        examples = self.examples_service.get_compare_examples(
            count=3,
            context_tickers=context_tickers,
            saved_portfolios=None
        )
        
        # Проверяем, что примеры все равно генерируются
        self.assertGreater(len(examples), 0, "Должны быть сгенерированы примеры")
        
        # Проверяем формат примеров
        for example in examples:
            self.assertIn('`', example, "Пример должен содержать команду в бэктиках")
            self.assertIn(' - ', example, "Пример должен содержать описание")
    
    def test_get_company_name_for_ticker(self):
        """Тест получения названия компании по тикеру"""
        # Тест с существующим тикером
        company_name = self.examples_service._get_company_name_for_ticker('AAPL.US')
        self.assertEqual(company_name, 'Apple', "Должно вернуться правильное название компании")
        
        # Тест с несуществующим тикером
        company_name = self.examples_service._get_company_name_for_ticker('NONEXISTENT.US')
        self.assertIsNone(company_name, "Должно вернуться None для несуществующего тикера")
        
        # Тест с тикером без биржи
        company_name = self.examples_service._get_company_name_for_ticker('INVALID')
        self.assertIsNone(company_name, "Должно вернуться None для невалидного тикера")


if __name__ == '__main__':
    unittest.main()

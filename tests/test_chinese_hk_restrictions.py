#!/usr/bin/env python3
"""
Тесты для проверки ограничений китайских и гонконгских активов
"""

import unittest
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.examples_service import ExamplesService


class TestChineseHKRestrictions(unittest.TestCase):
    """Тесты для проверки исключения китайских и гонконгских активов"""
    
    def setUp(self):
        """Инициализация тестового сервиса"""
        self.examples_service = ExamplesService()
    
    def test_portfolio_examples_exclude_chinese_hk(self):
        """Тест: портфельные примеры не должны содержать китайские и гонконгские активы"""
        examples = self.examples_service.get_portfolio_examples(10)
        
        # Проверяем, что ни один пример не содержит китайские или гонконгские активы
        chinese_hk_exchanges = ['SSE', 'SZSE', 'HKEX']
        
        for example in examples:
            # Извлекаем тикеры из примера (формат: `TICKER:WEIGHT TICKER:WEIGHT`)
            example_text = example.split('`')[1] if '`' in example else example
            tickers = example_text.split()
            
            for ticker_weight in tickers:
                if ':' in ticker_weight:
                    ticker = ticker_weight.split(':')[0]
                    exchange = ticker.split('.')[-1] if '.' in ticker else ''
                    
                    self.assertNotIn(exchange, chinese_hk_exchanges, 
                                   f"Пример содержит китайский/гонконгский актив: {ticker}")
    
    def test_info_examples_exclude_chinese_hk(self):
        """Тест: примеры для /info не должны содержать китайские и гонконгские активы"""
        examples = self.examples_service.get_info_examples(10)
        
        # Проверяем, что ни один пример не содержит китайские или гонконгские активы
        chinese_hk_exchanges = ['SSE', 'SZSE', 'HKEX']
        
        for example in examples:
            # Извлекаем тикер из примера (формат: `TICKER` - Company Name, Exchange)
            if '`' in example:
                ticker_part = example.split('`')[1]
                ticker = ticker_part.split(' - ')[0]
                exchange = ticker.split('.')[-1] if '.' in ticker else ''
                
                self.assertNotIn(exchange, chinese_hk_exchanges, 
                               f"Пример содержит китайский/гонконгский актив: {ticker}")
    
    def test_compare_examples_exclude_chinese_hk(self):
        """Тест: примеры для /compare не должны содержать китайские и гонконгские активы"""
        examples = self.examples_service.get_compare_examples(10)
        
        # Проверяем, что ни один пример не содержит китайские или гонконгские активы
        chinese_hk_exchanges = ['SSE', 'SZSE', 'HKEX']
        
        for example in examples:
            # Извлекаем тикеры из примера (формат: `TICKER1 TICKER2` - описание)
            if '`' in example:
                tickers_part = example.split('`')[1]
                tickers = tickers_part.split()
                
                for ticker in tickers:
                    exchange = ticker.split('.')[-1] if '.' in ticker else ''
                    
                    self.assertNotIn(exchange, chinese_hk_exchanges, 
                                   f"Пример содержит китайский/гонконгский актив: {ticker}")


if __name__ == '__main__':
    unittest.main()

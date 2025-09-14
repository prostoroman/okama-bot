#!/usr/bin/env python3
"""
Тест для исправления парсинга портфеля с пробелами вместо запятых
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import unittest
from unittest.mock import Mock


class TestDataConsistencyFixes(unittest.TestCase):
    """Тесты для исправления парсинга портфеля"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        # Мокаем logger чтобы избежать ошибок
        self.bot.logger = Mock()
    
    def test_space_separated_portfolio(self):
        """Тест портфеля с пробелами вместо запятых"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:0.4 LKOH.MOEX:0.3 LQDT.MOEX:0.3")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 3)
        
        # Проверяем символы
        symbols = [symbol for symbol, _ in result['portfolio_data']]
        self.assertIn('SBER.MOEX', symbols)
        self.assertIn('LKOH.MOEX', symbols)
        self.assertIn('LQDT.MOEX', symbols)
        
        # Проверяем веса
        portfolio_dict = dict(result['portfolio_data'])
        self.assertEqual(portfolio_dict['SBER.MOEX'], 0.4)
        self.assertEqual(portfolio_dict['LKOH.MOEX'], 0.3)
        self.assertEqual(portfolio_dict['LQDT.MOEX'], 0.3)
        
        # Проверяем сумму
        total_weight = sum(weight for _, weight in result['portfolio_data'])
        self.assertAlmostEqual(total_weight, 1.0, places=3)
    
    def test_space_separated_with_extra_spaces(self):
        """Тест портфеля с пробелами и лишними пробелами"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:0.4  LKOH.MOEX:0.3   LQDT.MOEX:0.3")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 3)
        
        # Проверяем символы
        symbols = [symbol for symbol, _ in result['portfolio_data']]
        self.assertIn('SBER.MOEX', symbols)
        self.assertIn('LKOH.MOEX', symbols)
        self.assertIn('LQDT.MOEX', symbols)
        
        # Проверяем веса
        portfolio_dict = dict(result['portfolio_data'])
        self.assertEqual(portfolio_dict['SBER.MOEX'], 0.4)
        self.assertEqual(portfolio_dict['LKOH.MOEX'], 0.3)
        self.assertEqual(portfolio_dict['LQDT.MOEX'], 0.3)
    
    def test_space_separated_mixed_with_symbols_only(self):
        """Тест смешанного формата с пробелами"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:0.4 LKOH.MOEX LQDT.MOEX:0.3")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 3)
        
        # Проверяем символы
        symbols = [symbol for symbol, _ in result['portfolio_data']]
        self.assertIn('SBER.MOEX', symbols)
        self.assertIn('LKOH.MOEX', symbols)
        self.assertIn('LQDT.MOEX', symbols)
        
        # Проверяем веса
        portfolio_dict = dict(result['portfolio_data'])
        self.assertEqual(portfolio_dict['SBER.MOEX'], 0.4)
        self.assertEqual(portfolio_dict['LQDT.MOEX'], 0.3)
        # LKOH.MOEX должен получить оставшийся вес (0.3)
        self.assertAlmostEqual(portfolio_dict['LKOH.MOEX'], 0.3, places=3)
        
        # Проверяем сумму
        total_weight = sum(weight for _, weight in result['portfolio_data'])
        self.assertAlmostEqual(total_weight, 1.0, places=3)
    
    def test_space_separated_with_comma_numbers(self):
        """Тест портфеля с пробелами и запятыми в числах (русская локаль)"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:0,4 LKOH.MOEX:0,3 LQDT.MOEX:0,3")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 3)
        
        # Проверяем символы
        symbols = [symbol for symbol, _ in result['portfolio_data']]
        self.assertIn('SBER.MOEX', symbols)
        self.assertIn('LKOH.MOEX', symbols)
        self.assertIn('LQDT.MOEX', symbols)
        
        # Проверяем веса
        portfolio_dict = dict(result['portfolio_data'])
        self.assertEqual(portfolio_dict['SBER.MOEX'], 0.4)
        self.assertEqual(portfolio_dict['LKOH.MOEX'], 0.3)
        self.assertEqual(portfolio_dict['LQDT.MOEX'], 0.3)
    
    def test_comma_separated_still_works(self):
        """Тест что запятые все еще работают"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:0.4, LKOH.MOEX:0.3, LQDT.MOEX:0.3")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 3)
        
        # Проверяем символы
        symbols = [symbol for symbol, _ in result['portfolio_data']]
        self.assertIn('SBER.MOEX', symbols)
        self.assertIn('LKOH.MOEX', symbols)
        self.assertIn('LQDT.MOEX', symbols)
        
        # Проверяем веса
        portfolio_dict = dict(result['portfolio_data'])
        self.assertEqual(portfolio_dict['SBER.MOEX'], 0.4)
        self.assertEqual(portfolio_dict['LKOH.MOEX'], 0.3)
        self.assertEqual(portfolio_dict['LQDT.MOEX'], 0.3)


if __name__ == '__main__':
    unittest.main()
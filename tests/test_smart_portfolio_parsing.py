#!/usr/bin/env python3
"""
Тест для умного парсинга ввода портфеля с прощением мелких ошибок
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import unittest
from unittest.mock import Mock


class TestSmartPortfolioParsing(unittest.TestCase):
    """Тесты для функции smart_parse_portfolio_input"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        # Мокаем logger чтобы избежать ошибок
        self.bot.logger = Mock()
    
    def test_standard_format(self):
        """Тест стандартного формата символ:доля"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:0.3, GAZP.MOEX:0.7")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 2)
        self.assertEqual(result['portfolio_data'][0], ('SBER.MOEX', 0.3))
        self.assertEqual(result['portfolio_data'][1], ('GAZP.MOEX', 0.7))
        self.assertEqual(len(result['suggestions']), 0)
    
    def test_list_of_symbols_equal_weights(self):
        """Тест списка символов без весов (равные доли)"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX, GAZP.MOEX, LKOH.MOEX")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 3)
        
        # Проверяем, что все доли равны
        weights = [weight for _, weight in result['portfolio_data']]
        self.assertAlmostEqual(weights[0], weights[1], places=3)
        self.assertAlmostEqual(weights[1], weights[2], places=3)
        self.assertAlmostEqual(sum(weights), 1.0, places=3)
        
        # Проверяем символы
        symbols = [symbol for symbol, _ in result['portfolio_data']]
        self.assertIn('SBER.MOEX', symbols)
        self.assertIn('GAZP.MOEX', symbols)
        self.assertIn('LKOH.MOEX', symbols)
    
    def test_mixed_format(self):
        """Тест смешанного формата (некоторые с весами, некоторые без)"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:0.3, GAZP.MOEX, LKOH.MOEX:0.2")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 3)
        
        # Проверяем сумму весов
        total_weight = sum(weight for _, weight in result['portfolio_data'])
        self.assertAlmostEqual(total_weight, 1.0, places=3)
        
        # Проверяем, что SBER имеет вес 0.3, LKOH - 0.2, GAZP - оставшийся вес
        portfolio_dict = dict(result['portfolio_data'])
        self.assertEqual(portfolio_dict['SBER.MOEX'], 0.3)
        self.assertEqual(portfolio_dict['LKOH.MOEX'], 0.2)
        self.assertAlmostEqual(portfolio_dict['GAZP.MOEX'], 0.5, places=3)
    
    def test_comma_in_number(self):
        """Тест замены запятой на точку в числах (русская локаль)"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:0,3, GAZP.MOEX:0,7")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 2)
        self.assertEqual(result['portfolio_data'][0], ('SBER.MOEX', 0.3))
        self.assertEqual(result['portfolio_data'][1], ('GAZP.MOEX', 0.7))
    
    def test_extra_spaces(self):
        """Тест обработки лишних пробелов"""
        result = self.bot.smart_parse_portfolio_input("  SBER.MOEX : 0.3  ,  GAZP.MOEX : 0.7  ")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 2)
        self.assertEqual(result['portfolio_data'][0], ('SBER.MOEX', 0.3))
        self.assertEqual(result['portfolio_data'][1], ('GAZP.MOEX', 0.7))
    
    def test_case_insensitive_symbols(self):
        """Тест регистронезависимых символов"""
        result = self.bot.smart_parse_portfolio_input("sber.moex:0.3, gazp.moex:0.7")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 2)
        self.assertEqual(result['portfolio_data'][0], ('SBER.MOEX', 0.3))
        self.assertEqual(result['portfolio_data'][1], ('GAZP.MOEX', 0.7))
    
    def test_weight_normalization(self):
        """Тест нормализации весов, если сумма близка к 1"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:0.2, GAZP.MOEX:0.3")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 2)
        
        # Проверяем, что сумма весов 0.5 (не нормализована, так как далека от 1.0)
        total_weight = sum(weight for _, weight in result['portfolio_data'])
        self.assertAlmostEqual(total_weight, 0.5, places=3)
        
        # Проверяем, что есть предложение о том, что сумма должна быть близка к 1.0
        self.assertTrue(any("должна быть близка к 1.0" in suggestion for suggestion in result['suggestions']))
    
    def test_weight_normalization_close_to_one(self):
        """Тест нормализации весов, если сумма близка к 1"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:0.4, GAZP.MOEX:0.7")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 2)
        
        # Проверяем, что веса нормализованы (сумма была 1.1, близко к 1.0)
        total_weight = sum(weight for _, weight in result['portfolio_data'])
        self.assertAlmostEqual(total_weight, 1.0, places=3)
        
        # Проверяем, что есть предложение о нормализации
        self.assertTrue(any("нормализованы" in suggestion for suggestion in result['suggestions']))
    
    def test_empty_input(self):
        """Тест пустого ввода"""
        result = self.bot.smart_parse_portfolio_input("")
        
        self.assertFalse(result['success'])
        self.assertEqual(len(result['portfolio_data']), 0)
        self.assertIn("Пустой ввод", result['message'])
        self.assertIn("Пример:", result['suggestions'][0])
    
    def test_invalid_weight(self):
        """Тест некорректного веса"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:abc")
        
        self.assertFalse(result['success'])
        self.assertEqual(len(result['portfolio_data']), 0)
        self.assertIn("Некорректная доля", result['suggestions'][0])
    
    def test_weight_out_of_range(self):
        """Тест веса вне диапазона 0-1"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX:1.5")
        
        self.assertFalse(result['success'])
        self.assertEqual(len(result['portfolio_data']), 0)
        self.assertTrue(any("должна быть от 0 до 1" in suggestion for suggestion in result['suggestions']))
    
    def test_original_user_case(self):
        """Тест оригинального случая пользователя"""
        result = self.bot.smart_parse_portfolio_input("SBER.MOEX, LKOH.MOEX, LQDT.MOEX, OBLG.MOEX, GOLD.MOEX, GAZP.MOEX")
        
        self.assertTrue(result['success'])
        self.assertEqual(len(result['portfolio_data']), 6)
        
        # Проверяем, что все символы присутствуют
        symbols = [symbol for symbol, _ in result['portfolio_data']]
        expected_symbols = ['SBER.MOEX', 'LKOH.MOEX', 'LQDT.MOEX', 'OBLG.MOEX', 'GOLD.MOEX', 'GAZP.MOEX']
        for expected_symbol in expected_symbols:
            self.assertIn(expected_symbol, symbols)
        
        # Проверяем, что все доли равны (1/6 ≈ 0.167)
        weights = [weight for _, weight in result['portfolio_data']]
        expected_weight = 1.0 / 6
        for weight in weights:
            self.assertAlmostEqual(weight, expected_weight, places=3)
        
        # Проверяем сумму
        self.assertAlmostEqual(sum(weights), 1.0, places=3)


if __name__ == '__main__':
    unittest.main()

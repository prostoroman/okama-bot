#!/usr/bin/env python3
"""
Тест для проверки исправления проблемы с нулевыми весами в примерах портфелей
"""

import sys
import os
import unittest

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.examples_service import ExamplesService


class TestPortfolioZeroWeightsFix(unittest.TestCase):
    """Тест для проверки отсутствия нулевых весов в примерах портфелей"""
    
    def setUp(self):
        """Инициализация тестового сервиса"""
        self.examples_service = ExamplesService()
    
    def test_generate_portfolio_weights_no_zeros(self):
        """Тест генерации весов без нулевых значений"""
        # Тестируем несколько раз для проверки стабильности
        for _ in range(100):
            weights = self.examples_service._generate_portfolio_weights(3)
            
            # Проверяем, что нет нулевых весов
            self.assertNotIn(0.0, weights, "Не должно быть нулевых весов")
            
            # Проверяем, что сумма равна 1.0
            self.assertEqual(sum(weights), 1.0, "Сумма весов должна быть равна 1.0")
            
            # Проверяем, что все веса положительные
            for weight in weights:
                self.assertGreater(weight, 0.0, "Все веса должны быть положительными")
    
    def test_generate_portfolio_weights_different_sizes(self):
        """Тест генерации весов для разного количества активов"""
        for num_assets in range(2, 6):  # От 2 до 5 активов
            weights = self.examples_service._generate_portfolio_weights(num_assets)
            
            # Проверяем количество весов
            self.assertEqual(len(weights), num_assets, f"Должно быть {num_assets} весов")
            
            # Проверяем отсутствие нулевых весов
            self.assertNotIn(0.0, weights, f"Не должно быть нулевых весов для {num_assets} активов")
            
            # Проверяем сумму
            self.assertEqual(sum(weights), 1.0, f"Сумма весов должна быть 1.0 для {num_assets} активов")
    
    def test_portfolio_examples_no_zero_weights(self):
        """Тест примеров портфелей без нулевых весов"""
        # Получаем примеры портфелей
        examples = self.examples_service.get_portfolio_examples(count=10)
        
        # Проверяем каждый пример
        for example in examples:
            # Извлекаем команду из примера (часть в обратных кавычках)
            if '`' in example:
                command_part = example.split('`')[1]
                
                # Проверяем, что нет весов 0.0
                self.assertNotIn(':0.0', command_part, f"Не должно быть весов 0.0 в команде: {command_part}")
                
                # Проверяем, что есть веса
                if ':' in command_part:
                    weights_str = command_part.split(':')
                    # Проверяем каждый вес
                    for weight_str in weights_str[1:]:  # Пропускаем первый элемент (тикер)
                        if ' ' in weight_str:
                            weight = float(weight_str.split(' ')[0])
                        else:
                            weight = float(weight_str)
                        self.assertGreater(weight, 0.0, f"Вес должен быть больше 0: {weight}")
    
    def test_portfolio_examples_with_context_no_zeros(self):
        """Тест примеров портфелей с контекстом без нулевых весов"""
        # Тестируем с MOEX контекстом
        context_tickers = ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']
        examples = self.examples_service.get_portfolio_examples(count=5, context_tickers=context_tickers)
        
        # Проверяем каждый пример
        for example in examples:
            if '`' in example:
                command_part = example.split('`')[1]
                self.assertNotIn(':0.0', command_part, f"Не должно быть весов 0.0 в команде: {command_part}")


if __name__ == '__main__':
    unittest.main()

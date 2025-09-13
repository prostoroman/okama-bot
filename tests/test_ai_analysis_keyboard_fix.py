#!/usr/bin/env python3
"""
Тест для проверки исправления проблемы с клавиатурой в AI-анализе команды /compare
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestAiAnalysisKeyboardFix(unittest.TestCase):
    """Тест исправления проблемы с клавиатурой в AI-анализе"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        self.bot.logger = Mock()
        
        # Мокаем сервисы
        self.bot.gemini_service = Mock()
        self.bot.gemini_service.is_available.return_value = True
        
        # Мокаем методы
        self.bot._get_user_context = Mock()
        self.bot._send_callback_message = AsyncMock()
        self.bot._send_callback_message_with_keyboard_removal = AsyncMock()
        self.bot._create_compare_command_keyboard = Mock()
        self.bot._prepare_data_for_analysis = AsyncMock()
        
    def test_data_analysis_compare_button_variables_initialized(self):
        """Тест что переменные symbols и currency инициализированы в начале функции"""
        # Проверяем, что функция _handle_data_analysis_compare_button существует
        self.assertTrue(hasattr(self.bot, '_handle_data_analysis_compare_button'))
        
        # Получаем исходный код функции
        import inspect
        source = inspect.getsource(self.bot._handle_data_analysis_compare_button)
        
        # Проверяем, что переменные инициализированы в начале функции
        self.assertIn('symbols = []', source)
        self.assertIn("currency = 'USD'", source)
        
        # Проверяем, что инициализация происходит до блока try
        lines = source.split('\n')
        symbols_init_line = None
        currency_init_line = None
        try_line = None
        
        for i, line in enumerate(lines):
            if 'symbols = []' in line:
                symbols_init_line = i
            elif "currency = 'USD'" in line:
                currency_init_line = i
            elif line.strip().startswith('try:'):
                try_line = i
                break
        
        self.assertIsNotNone(symbols_init_line, "symbols = [] не найден в коде")
        self.assertIsNotNone(currency_init_line, "currency = 'USD' не найден в коде")
        self.assertIsNotNone(try_line, "блок try не найден в коде")
        
        # Проверяем, что инициализация происходит до блока try
        self.assertLess(symbols_init_line, try_line, "symbols инициализируется после блока try")
        self.assertLess(currency_init_line, try_line, "currency инициализируется после блока try")
    
    def test_chart_analysis_compare_button_variables_initialized(self):
        """Тест что переменные symbols и currency инициализированы в функции анализа графика"""
        # Проверяем, что функция _handle_chart_analysis_compare_button существует
        self.assertTrue(hasattr(self.bot, '_handle_chart_analysis_compare_button'))
        
        # Получаем исходный код функции
        import inspect
        source = inspect.getsource(self.bot._handle_chart_analysis_compare_button)
        
        # Проверяем, что переменные инициализированы в начале функции
        self.assertIn('symbols = []', source)
        self.assertIn("currency = 'USD'", source)
    
    def test_yandexgpt_analysis_compare_button_variables_initialized(self):
        """Тест что переменные symbols и currency инициализированы в функции YandexGPT анализа"""
        # Проверяем, что функция _handle_yandexgpt_analysis_compare_button существует
        self.assertTrue(hasattr(self.bot, '_handle_yandexgpt_analysis_compare_button'))
        
        # Получаем исходный код функции
        import inspect
        source = inspect.getsource(self.bot._handle_yandexgpt_analysis_compare_button)
        
        # Проверяем, что переменные инициализированы в начале функции
        self.assertIn('symbols = []', source)
        self.assertIn("currency = 'USD'", source)


if __name__ == '__main__':
    unittest.main()

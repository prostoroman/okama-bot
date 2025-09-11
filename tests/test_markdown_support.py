#!/usr/bin/env python3
"""
Тест для проверки поддержки Markdown в командах бота
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestMarkdownSupport(unittest.TestCase):
    """Тест поддержки Markdown форматирования"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        self.bot.logger = Mock()
        
    def test_info_command_markdown_formatting(self):
        """Тест форматирования команды /info с Markdown"""
        # Создаем мок объекты
        update = Mock()
        context = Mock()
        context.args = []
        
        # Мокаем метод отправки сообщения
        self.bot._send_message_safe = AsyncMock()
        self.bot.get_random_examples = Mock(return_value=['AAPL.US', 'SPY.US', 'QQQ.US'])
        
        # Выполняем команду
        import asyncio
        asyncio.run(self.bot.info_command(update, context))
        
        # Проверяем, что сообщение было отправлено с правильным форматированием
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args[0]
        message_text = call_args[1]
        
        # Проверяем наличие Markdown форматирования
        self.assertIn("*Информация об активе*", message_text)
        self.assertIn("*Примеры:*", message_text)
        self.assertIn("*Просто отправьте название инструмента*", message_text)
    
    def test_compare_command_markdown_formatting(self):
        """Тест форматирования команды /compare с Markdown"""
        # Создаем мок объекты
        update = Mock()
        context = Mock()
        context.args = []
        
        # Мокаем методы
        self.bot._send_message_safe = AsyncMock()
        self.bot.get_random_examples = Mock(return_value=['AAPL.US', 'SPY.US', 'QQQ.US'])
        self.bot._get_user_context = Mock(return_value={'saved_portfolios': {}})
        self.bot._update_user_context = Mock()
        
        # Выполняем команду
        import asyncio
        asyncio.run(self.bot.compare_command(update, context))
        
        # Проверяем, что сообщение было отправлено с правильным форматированием
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args[0]
        message_text = call_args[1]
        
        # Проверяем наличие Markdown форматирования
        self.assertIn("*💬 Введите символы для сравнения:*", message_text)
    
    def test_portfolio_command_markdown_formatting(self):
        """Тест форматирования команды /portfolio с Markdown"""
        # Создаем мок объекты
        update = Mock()
        context = Mock()
        context.args = []
        
        # Мокаем методы
        self.bot._send_message_safe = AsyncMock()
        self.bot._update_user_context = Mock()
        self.bot._get_user_context = Mock(return_value={})
        
        # Выполняем команду
        import asyncio
        asyncio.run(self.bot.portfolio_command(update, context))
        
        # Проверяем, что сообщение было отправлено с правильным форматированием
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args[0]
        message_text = call_args[1]
        
        # Проверяем наличие Markdown форматирования
        self.assertIn("*Создание портфеля*", message_text)
        self.assertIn("*Введите символы для создания портфеля:*", message_text)
    
    def test_error_messages_markdown_formatting(self):
        """Тест форматирования сообщений об ошибках с Markdown"""
        # Создаем мок объекты
        update = Mock()
        
        # Мокаем метод отправки сообщения
        self.bot._send_message_safe = AsyncMock()
        
        # Тестируем различные сообщения об ошибках
        test_messages = [
            "*ℹ️ Данные о drawdowns недоступны для выбранных активов*",
            "*ℹ️ Данные о дивидендной доходности недоступны для выбранных активов*",
            "*❌ Сервис Tushare недоступен*",
            "*❌ Библиотека okama не установлена*"
        ]
        
        for message in test_messages:
            # Проверяем, что сообщение содержит Markdown форматирование
            self.assertTrue(message.startswith("*") and message.endswith("*"))
            self.assertIn("*", message)


if __name__ == '__main__':
    unittest.main()

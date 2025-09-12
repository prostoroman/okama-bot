#!/usr/bin/env python3
"""
Тест для проверки исправления markdown форматирования в сообщении портфеля
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestPortfolioMarkdownFix(unittest.TestCase):
    """Тест исправления markdown форматирования в сообщении портфеля"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        self.bot.logger = MagicMock()
        
    @patch('bot.ShansAi._update_user_context')
    @patch('bot.ShansAi._send_callback_message')
    async def test_portfolio_button_markdown_formatting(self, mock_send_callback, mock_update_context):
        """Тест правильного markdown форматирования в сообщении портфеля"""
        
        # Создаем мок объекты
        update = MagicMock()
        context = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.edit_message_reply_markup = AsyncMock()
        update.effective_user.id = 12345
        
        symbol = "AAPL.US"
        
        # Вызываем функцию
        await self.bot._handle_info_portfolio_button(update, context, symbol)
        
        # Проверяем, что _send_callback_message был вызван с parse_mode='Markdown'
        mock_send_callback.assert_called_once()
        call_args = mock_send_callback.call_args
        
        # Проверяем аргументы вызова
        self.assertEqual(call_args[0][0], update)  # update
        self.assertEqual(call_args[0][1], context)  # context
        self.assertIn("💼 **Добавить AAPL.US в портфель**", call_args[0][2])  # text содержит markdown
        self.assertEqual(call_args[0][3], 'Markdown')  # parse_mode
        
        # Проверяем, что текст содержит правильное markdown форматирование
        message_text = call_args[0][2]
        self.assertIn("**Добавить AAPL.US в портфель**", message_text)
        self.assertIn("**Примеры:**", message_text)
        self.assertIn("`AAPL.US:0.6 QQQ.US:0.4`", message_text)
        
    @patch('bot.ShansAi._update_user_context')
    @patch('bot.ShansAi._send_callback_message')
    async def test_portfolio_button_error_markdown_formatting(self, mock_send_callback, mock_update_context):
        """Тест markdown форматирования в сообщении об ошибке"""
        
        # Создаем мок объекты
        update = MagicMock()
        context = MagicMock()
        update.callback_query = MagicMock()
        update.callback_query.edit_message_reply_markup = AsyncMock()
        update.effective_user.id = 12345
        
        # Настраиваем мок для вызова исключения
        mock_update_context.side_effect = Exception("Test error")
        
        symbol = "AAPL.US"
        
        # Вызываем функцию
        await self.bot._handle_info_portfolio_button(update, context, symbol)
        
        # Проверяем, что _send_callback_message был вызван с parse_mode='Markdown' для ошибки
        mock_send_callback.assert_called_once()
        call_args = mock_send_callback.call_args
        
        # Проверяем аргументы вызова
        self.assertEqual(call_args[0][0], update)  # update
        self.assertEqual(call_args[0][1], context)  # context
        self.assertIn("❌ Ошибка при подготовке портфеля: Test error", call_args[0][2])  # text ошибки
        self.assertEqual(call_args[0][3], 'Markdown')  # parse_mode


if __name__ == '__main__':
    # Запуск тестов
    unittest.main()

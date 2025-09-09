#!/usr/bin/env python3
"""
Тест для проверки исправления отображения кнопок при ошибках в команде /info
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestInfoErrorButtonsFix(unittest.TestCase):
    """Тест исправления отображения кнопок при ошибках в /info"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        self.bot.logger = Mock()
        
        # Мокаем update и context
        self.update = Mock()
        self.update.effective_user.id = 12345
        self.update.message = Mock()
        self.update.message.text = "/info INVALID_SYMBOL"
        
        self.context = Mock()
        self.context.args = ["INVALID_SYMBOL"]
        
        # Мокаем методы отправки сообщений
        self.bot._send_message_safe = AsyncMock()
        self.bot._send_ephemeral_message = AsyncMock()
        self.bot._update_user_context = Mock()
        self.bot._get_user_context = Mock(return_value={})
        self.bot.resolve_symbol_or_isin = Mock(return_value={'symbol': 'INVALID_SYMBOL'})
        self.bot.determine_data_source = Mock(return_value='okama')
    
    @patch('okama.Asset')
    async def test_okama_info_error_no_buttons(self, mock_asset_class):
        """Тест: при ошибке в _handle_okama_info кнопки не отображаются"""
        # Настраиваем мок для вызова исключения
        mock_asset_class.side_effect = Exception("Asset not found")
        
        # Вызываем метод
        await self.bot._handle_okama_info(self.update, "INVALID_SYMBOL")
        
        # Проверяем, что сообщение отправлено без кнопок
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        
        # Проверяем, что сообщение содержит ошибку
        self.assertIn("Ошибка при получении информации об активе", call_args[0][1])
        
        # Проверяем, что reply_markup не передан (нет кнопок)
        self.assertEqual(len(call_args[1]), 0)  # Нет именованных аргументов
    
    @patch('okama.Asset')
    async def test_okama_info_success_with_buttons(self, mock_asset_class):
        """Тест: при успешном получении данных в _handle_okama_info кнопки отображаются"""
        # Настраиваем мок для успешного создания актива
        mock_asset = Mock()
        mock_asset.__str__ = Mock(return_value="Asset info")
        mock_asset_class.return_value = mock_asset
        
        # Вызываем метод
        await self.bot._handle_okama_info(self.update, "VALID_SYMBOL")
        
        # Проверяем, что сообщение отправлено с кнопками
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        
        # Проверяем, что сообщение содержит информацию об активе
        self.assertIn("Asset info", call_args[0][1])
        
        # Проверяем, что reply_markup передан (есть кнопки)
        self.assertIn('reply_markup', call_args[1])
        self.assertIsNotNone(call_args[1]['reply_markup'])
    
    async def test_tushare_info_error_with_buttons(self):
        """Тест: при ошибке в _handle_tushare_info кнопки отображаются для консистентности"""
        # Настраиваем мок для tushare_service
        self.bot.tushare_service = Mock()
        self.bot.tushare_service.get_symbol_info = Mock(return_value={'error': 'Symbol not found'})
        
        # Вызываем метод
        await self.bot._handle_tushare_info(self.update, "INVALID_SYMBOL")
        
        # Проверяем, что сообщение отправлено с кнопками
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        
        # Проверяем, что сообщение содержит ошибку
        self.assertIn("Ошибка:", call_args[0][1])
        
        # Проверяем, что reply_markup передан (есть кнопки)
        self.assertIn('reply_markup', call_args[1])
        self.assertIsNotNone(call_args[1]['reply_markup'])
    
    async def test_tushare_info_success_with_buttons(self):
        """Тест: при успешном получении данных в _handle_tushare_info кнопки отображаются"""
        # Настраиваем мок для tushare_service
        self.bot.tushare_service = Mock()
        self.bot.tushare_service.get_symbol_info = Mock(return_value={
            'name': 'Test Asset',
            'exchange': 'Test Exchange',
            'industry': 'Test Industry',
            'area': 'Test Area',
            'list_date': '2020-01-01'
        })
        
        # Вызываем метод
        await self.bot._handle_tushare_info(self.update, "VALID_SYMBOL")
        
        # Проверяем, что сообщение отправлено с кнопками
        self.bot._send_message_safe.assert_called_once()
        call_args = self.bot._send_message_safe.call_args
        
        # Проверяем, что сообщение содержит информацию об активе
        self.assertIn("Test Asset", call_args[0][1])
        
        # Проверяем, что reply_markup передан (есть кнопки)
        self.assertIn('reply_markup', call_args[1])
        self.assertIsNotNone(call_args[1]['reply_markup'])


if __name__ == '__main__':
    # Запуск тестов
    unittest.main()

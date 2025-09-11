#!/usr/bin/env python3
"""
Тест для проверки навигации по пространствам имен в команде /list
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
from telegram import Update, CallbackQuery, Message, User, Chat
from telegram.ext import ContextTypes


class TestNamespaceNavigation(unittest.TestCase):
    """Тест навигации по пространствам имен"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        
        # Создаем мок объекты
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 12345
        self.mock_user.username = "testuser"
        
        self.mock_chat = Mock(spec=Chat)
        self.mock_chat.id = 12345
        
        self.mock_message = Mock(spec=Message)
        self.mock_message.chat = self.mock_chat
        self.mock_message.chat_id = 12345
        
        self.mock_callback_query = Mock(spec=CallbackQuery)
        self.mock_callback_query.message = self.mock_message
        self.mock_callback_query.data = "nav_namespace_US_1"
        
        self.mock_update = Mock(spec=Update)
        self.mock_update.effective_user = self.mock_user
        self.mock_update.callback_query = self.mock_callback_query
        
        self.mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_message = AsyncMock()
    
    @patch('bot.ok')
    async def test_okama_namespace_navigation(self, mock_ok):
        """Тест навигации для okama пространств"""
        # Настраиваем мок для okama
        import pandas as pd
        
        # Создаем тестовые данные с большим количеством символов для тестирования пагинации
        test_symbols = []
        for i in range(50):  # 50 символов для тестирования пагинации
            test_symbols.append({
                'symbol': f'SYMBOL{i:03d}.US',
                'name': f'Test Company {i}'
            })
        
        mock_df = pd.DataFrame(test_symbols)
        mock_ok.symbols_in_namespace.return_value = mock_df
        
        # Тестируем первую страницу
        await self.bot._show_namespace_symbols(
            self.mock_update, 
            self.mock_context, 
            'US', 
            is_callback=True, 
            page=0
        )
        
        # Проверяем, что метод был вызван
        mock_ok.symbols_in_namespace.assert_called_with('US')
        
        # Проверяем, что сообщение было отправлено
        self.mock_context.bot.send_message.assert_called()
        
        # Получаем аргументы вызова
        call_args = self.mock_context.bot.send_message.call_args
        message_text = call_args[1]['text']
        reply_markup = call_args[1]['reply_markup']
        
        # Проверяем содержимое сообщения
        self.assertIn('📊 **US** - Всего символов: 50', message_text)
        self.assertIn('📋 **Навигация:** Показаны символы 1-20 из 50', message_text)
        self.assertIn('📄 Страница 1 из 3', message_text)
        
        # Проверяем наличие кнопок навигации
        keyboard = reply_markup.inline_keyboard
        self.assertEqual(len(keyboard), 2)  # Навигация + Excel
        
        # Проверяем кнопки навигации
        nav_buttons = keyboard[0]
        self.assertEqual(len(nav_buttons), 3)  # Назад, индикатор, вперед
        
        # Проверяем callback данные
        self.assertEqual(nav_buttons[0].callback_data, "nav_namespace_US_0")  # Назад (неактивна)
        self.assertEqual(nav_buttons[1].callback_data, "noop")  # Индикатор
        self.assertEqual(nav_buttons[2].callback_data, "nav_namespace_US_1")  # Вперед
    
    @patch('bot.tushare_service')
    async def test_tushare_namespace_navigation(self, mock_tushare_service):
        """Тест навигации для tushare пространств"""
        # Настраиваем мок для tushare
        mock_tushare_service.get_exchange_symbols.return_value = [
            {'symbol': f'00000{i}.SZ', 'name': f'Test Company {i}'} 
            for i in range(50)
        ]
        mock_tushare_service.get_exchange_symbols_count.return_value = 5000
        
        # Тестируем первую страницу
        await self.bot._show_tushare_namespace_symbols(
            self.mock_update, 
            self.mock_context, 
            'SZSE', 
            is_callback=True, 
            page=0
        )
        
        # Проверяем, что методы были вызваны
        mock_tushare_service.get_exchange_symbols.assert_called_with('SZSE')
        mock_tushare_service.get_exchange_symbols_count.assert_called_with('SZSE')
        
        # Проверяем, что сообщение было отправлено
        self.mock_context.bot.send_message.assert_called()
        
        # Получаем аргументы вызова
        call_args = self.mock_context.bot.send_message.call_args
        message_text = call_args[1]['text']
        reply_markup = call_args[1]['reply_markup']
        
        # Проверяем содержимое сообщения
        self.assertIn('📊 **Shenzhen Stock Exchange**', message_text)
        self.assertIn('📈 **Статистика:** Всего символов: 5,000', message_text)
        self.assertIn('📋 **Навигация:** Показаны символы 1-20 из 50', message_text)
        self.assertIn('📄 Страница 1 из 3', message_text)
        
        # Проверяем наличие кнопок навигации
        keyboard = reply_markup.inline_keyboard
        self.assertEqual(len(keyboard), 2)  # Навигация + Excel
        
        # Проверяем кнопки навигации
        nav_buttons = keyboard[0]
        self.assertEqual(len(nav_buttons), 3)  # Назад, индикатор, вперед
        
        # Проверяем callback данные
        self.assertEqual(nav_buttons[0].callback_data, "nav_tushare_SZSE_0")  # Назад (неактивна)
        self.assertEqual(nav_buttons[1].callback_data, "noop")  # Индикатор
        self.assertEqual(nav_buttons[2].callback_data, "nav_tushare_SZSE_1")  # Вперед
    
    async def test_navigation_callback_handlers(self):
        """Тест обработчиков callback для навигации"""
        # Тестируем обработку навигации для okama
        self.mock_callback_query.data = "nav_namespace_US_1"
        
        with patch.object(self.bot, '_show_namespace_symbols', new_callable=AsyncMock) as mock_show:
            await self.bot.button_callback(self.mock_update, self.mock_context)
            mock_show.assert_called_with(self.mock_update, self.mock_context, 'US', True, 1)
        
        # Тестируем обработку навигации для tushare
        self.mock_callback_query.data = "nav_tushare_SSE_2"
        
        with patch.object(self.bot, '_show_tushare_namespace_symbols', new_callable=AsyncMock) as mock_show_tushare:
            await self.bot.button_callback(self.mock_update, self.mock_context)
            mock_show_tushare.assert_called_with(self.mock_update, self.mock_context, 'SSE', True, 2)
    
    def test_pagination_calculation(self):
        """Тест расчета пагинации"""
        # Тестируем различные сценарии пагинации
        test_cases = [
            (50, 20, 3),   # 50 символов, 20 на страницу = 3 страницы
            (100, 20, 5),  # 100 символов, 20 на страницу = 5 страниц
            (15, 20, 1),   # 15 символов, 20 на страницу = 1 страница
            (0, 20, 0),    # 0 символов, 20 на страницу = 0 страниц
        ]
        
        for total_symbols, symbols_per_page, expected_pages in test_cases:
            total_pages = (total_symbols + symbols_per_page - 1) // symbols_per_page
            self.assertEqual(total_pages, expected_pages, 
                           f"Неверный расчет пагинации для {total_symbols} символов")


if __name__ == '__main__':
    unittest.main()

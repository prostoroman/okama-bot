#!/usr/bin/env python3
"""
Тест для проверки универсальной функции управления клавиатурой
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import io
from telegram import Update, CallbackQuery, Message, Chat, User, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

class TestKeyboardManagement(unittest.TestCase):
    """Тест для функции _send_message_with_keyboard_management"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        # Создаем мок-объекты
        self.mock_chat = Mock(spec=Chat)
        self.mock_chat.id = 12345
        
        self.mock_user = Mock(spec=User)
        self.mock_user.id = 67890
        
        self.mock_message = Mock(spec=Message)
        self.mock_message.chat_id = 12345
        self.mock_message.message_id = 1
        
        self.mock_callback_query = Mock(spec=CallbackQuery)
        self.mock_callback_query.message = self.mock_message
        
        self.mock_update = Mock(spec=Update)
        self.mock_update.effective_chat = self.mock_chat
        self.mock_update.effective_user = self.mock_user
        self.mock_update.callback_query = self.mock_callback_query
        
        self.mock_context = Mock(spec=ContextTypes.DEFAULT_TYPE)
        self.mock_context.bot = Mock()
        self.mock_context.bot.send_photo = AsyncMock()
        self.mock_context.bot.send_message = AsyncMock()
        self.mock_context.bot.send_document = AsyncMock()
        
        # Создаем тестовую клавиатуру
        self.test_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Тест", callback_data="test")]
        ])
        
        # Создаем тестовое изображение
        self.test_image = io.BytesIO(b"fake_image_data")
        
    @patch('bot.ShansAi._remove_keyboard_before_new_message')
    async def test_send_photo_with_keyboard(self, mock_remove_keyboard):
        """Тест отправки фото с клавиатурой"""
        # Создаем экземпляр бота (мок)
        bot_instance = Mock()
        bot_instance._remove_keyboard_before_new_message = AsyncMock()
        
        # Вызываем функцию
        await bot_instance._send_message_with_keyboard_management(
            self.mock_update,
            self.mock_context,
            message_type='photo',
            content=self.test_image,
            caption="Тестовая подпись",
            keyboard=self.test_keyboard
        )
        
        # Проверяем, что функция удаления клавиатуры была вызвана
        bot_instance._remove_keyboard_before_new_message.assert_called_once_with(
            self.mock_update, self.mock_context
        )
        
        # Проверяем, что send_photo был вызван с правильными параметрами
        self.mock_context.bot.send_photo.assert_called_once_with(
            chat_id=12345,
            photo=self.test_image,
            caption="Тестовая подпись",
            reply_markup=self.test_keyboard,
            parse_mode=None
        )
    
    @patch('bot.ShansAi._remove_keyboard_before_new_message')
    async def test_send_text_with_keyboard(self, mock_remove_keyboard):
        """Тест отправки текста с клавиатурой"""
        # Создаем экземпляр бота (мок)
        bot_instance = Mock()
        bot_instance._remove_keyboard_before_new_message = AsyncMock()
        
        # Вызываем функцию
        await bot_instance._send_message_with_keyboard_management(
            self.mock_update,
            self.mock_context,
            message_type='text',
            content="Тестовое сообщение",
            keyboard=self.test_keyboard,
            parse_mode='Markdown'
        )
        
        # Проверяем, что функция удаления клавиатуры была вызвана
        bot_instance._remove_keyboard_before_new_message.assert_called_once_with(
            self.mock_update, self.mock_context
        )
        
        # Проверяем, что send_message был вызван с правильными параметрами
        self.mock_context.bot.send_message.assert_called_once_with(
            chat_id=12345,
            text="Тестовое сообщение",
            reply_markup=self.test_keyboard,
            parse_mode='Markdown'
        )
    
    @patch('bot.ShansAi._remove_keyboard_before_new_message')
    async def test_send_document_with_keyboard(self, mock_remove_keyboard):
        """Тест отправки документа с клавиатурой"""
        # Создаем экземпляр бота (мок)
        bot_instance = Mock()
        bot_instance._remove_keyboard_before_new_message = AsyncMock()
        
        # Вызываем функцию
        await bot_instance._send_message_with_keyboard_management(
            self.mock_update,
            self.mock_context,
            message_type='document',
            content=self.test_image,
            caption="Тестовый документ",
            keyboard=self.test_keyboard
        )
        
        # Проверяем, что функция удаления клавиатуры была вызвана
        bot_instance._remove_keyboard_before_new_message.assert_called_once_with(
            self.mock_update, self.mock_context
        )
        
        # Проверяем, что send_document был вызван с правильными параметрами
        self.mock_context.bot.send_document.assert_called_once_with(
            chat_id=12345,
            document=self.test_image,
            caption="Тестовый документ",
            reply_markup=self.test_keyboard,
            parse_mode=None
        )
    
    @patch('bot.ShansAi._remove_keyboard_before_new_message')
    async def test_unsupported_message_type(self, mock_remove_keyboard):
        """Тест неподдерживаемого типа сообщения"""
        # Создаем экземпляр бота (мок)
        bot_instance = Mock()
        bot_instance._remove_keyboard_before_new_message = AsyncMock()
        bot_instance._send_callback_message = AsyncMock()
        
        # Вызываем функцию с неподдерживаемым типом
        await bot_instance._send_message_with_keyboard_management(
            self.mock_update,
            self.mock_context,
            message_type='unsupported',
            content="Тест"
        )
        
        # Проверяем, что функция удаления клавиатуры была вызвана
        bot_instance._remove_keyboard_before_new_message.assert_called_once_with(
            self.mock_update, self.mock_context
        )
        
        # Проверяем, что была вызвана функция отправки ошибки
        bot_instance._send_callback_message.assert_called_once_with(
            self.mock_update, self.mock_context, 
            "❌ Неподдерживаемый тип сообщения: unsupported"
        )

if __name__ == '__main__':
    unittest.main()

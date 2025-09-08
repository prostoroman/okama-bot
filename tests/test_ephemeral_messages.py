#!/usr/bin/env python3
"""
Тест для проверки работы исчезающих сообщений в боте
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestEphemeralMessages(unittest.TestCase):
    """Тест исчезающих сообщений"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        
        # Мокаем logger
        self.bot.logger = MagicMock()
        
        # Создаем мок объекты для update и context
        self.update = MagicMock()
        self.context = MagicMock()
        
        # Настраиваем мок для context.bot
        self.context.bot = AsyncMock()
        self.context.bot.send_message = AsyncMock()
        self.context.bot.delete_message = AsyncMock()
        
        # Настраиваем мок для update
        self.update.callback_query = MagicMock()
        self.update.callback_query.message = MagicMock()
        self.update.callback_query.message.chat_id = 12345
        self.update.callback_query.message.message_id = 67890
    
    def test_ephemeral_message_sends_and_deletes(self):
        """Тест отправки и удаления исчезающего сообщения"""
        
        async def run_test():
            # Мокаем возвращаемое сообщение
            mock_message = MagicMock()
            mock_message.message_id = 67890
            self.context.bot.send_message.return_value = mock_message
            
            # Отправляем исчезающее сообщение
            await self.bot._send_ephemeral_message(
                self.update, 
                self.context, 
                "Тестовое исчезающее сообщение",
                delete_after=1  # Удаляем через 1 секунду для быстрого теста
            )
            
            # Проверяем, что сообщение было отправлено
            self.context.bot.send_message.assert_called_once_with(
                chat_id=12345,
                text="Тестовое исчезающее сообщение",
                parse_mode=None
            )
            
            # Ждем немного больше времени удаления
            await asyncio.sleep(1.5)
            
            # Проверяем, что сообщение было удалено
            self.context.bot.delete_message.assert_called_once_with(
                chat_id=12345,
                message_id=67890
            )
        
        # Запускаем тест
        asyncio.run(run_test())
    
    def test_ephemeral_message_with_markdown(self):
        """Тест исчезающего сообщения с Markdown"""
        
        async def run_test():
            # Мокаем возвращаемое сообщение
            mock_message = MagicMock()
            mock_message.message_id = 67890
            self.context.bot.send_message.return_value = mock_message
            
            # Отправляем исчезающее сообщение с Markdown
            await self.bot._send_ephemeral_message(
                self.update, 
                self.context, 
                "**Жирный текст** и *курсив*",
                parse_mode='Markdown',
                delete_after=1
            )
            
            # Проверяем, что сообщение было отправлено с правильным parse_mode
            self.context.bot.send_message.assert_called_once_with(
                chat_id=12345,
                text="**Жирный текст** и *курсив*",
                parse_mode='Markdown'
            )
            
            # Ждем удаления
            await asyncio.sleep(1.5)
            
            # Проверяем удаление
            self.context.bot.delete_message.assert_called_once_with(
                chat_id=12345,
                message_id=67890
            )
        
        asyncio.run(run_test())
    
    def test_ephemeral_message_fallback_on_error(self):
        """Тест fallback при ошибке отправки исчезающего сообщения"""
        
        async def run_test():
            # Мокаем ошибку при отправке сообщения
            self.context.bot.send_message.side_effect = Exception("Ошибка отправки")
            
            # Мокаем _send_callback_message как fallback
            with patch.object(self.bot, '_send_callback_message', new_callable=AsyncMock) as mock_fallback:
                await self.bot._send_ephemeral_message(
                    self.update, 
                    self.context, 
                    "Тестовое сообщение",
                    delete_after=1
                )
                
                # Проверяем, что был вызван fallback
                mock_fallback.assert_called_once_with(
                    self.update, 
                    self.context, 
                    "Тестовое сообщение", 
                    None
                )
        
        asyncio.run(run_test())
    
    def test_ephemeral_message_with_regular_message_update(self):
        """Тест исчезающего сообщения с обычным update.message"""
        
        async def run_test():
            # Настраиваем update с message вместо callback_query
            self.update.callback_query = None
            self.update.message = MagicMock()
            self.update.message.chat_id = 54321
            
            # Мокаем возвращаемое сообщение
            mock_message = MagicMock()
            mock_message.message_id = 98765
            self.context.bot.send_message.return_value = mock_message
            
            # Отправляем исчезающее сообщение
            await self.bot._send_ephemeral_message(
                self.update, 
                self.context, 
                "Тестовое сообщение",
                delete_after=1
            )
            
            # Проверяем, что сообщение было отправлено с правильным chat_id
            self.context.bot.send_message.assert_called_once_with(
                chat_id=54321,
                text="Тестовое сообщение",
                parse_mode=None
            )
            
            # Ждем удаления
            await asyncio.sleep(1.5)
            
            # Проверяем удаление
            self.context.bot.delete_message.assert_called_once_with(
                chat_id=54321,
                message_id=98765
            )
        
        asyncio.run(run_test())
    
    def test_ephemeral_message_no_chat_id_error(self):
        """Тест обработки ошибки при отсутствии chat_id"""
        
        async def run_test():
            # Настраиваем update без callback_query и message
            self.update.callback_query = None
            self.update.message = None
            
            # Отправляем исчезающее сообщение
            await self.bot._send_ephemeral_message(
                self.update, 
                self.context, 
                "Тестовое сообщение",
                delete_after=1
            )
            
            # Проверяем, что сообщение не было отправлено
            self.context.bot.send_message.assert_not_called()
            
            # Проверяем, что была записана ошибка в лог
            self.bot.logger.error.assert_called_with("Cannot send ephemeral message: no chat_id available")
        
        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()

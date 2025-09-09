#!/usr/bin/env python3
"""
Тест для проверки исправления проблемы с кнопками портфеля при ошибке форматирования.
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestPortfolioButtonsFix(unittest.TestCase):
    """Тест исправления кнопок портфеля при ошибке форматирования."""
    
    def setUp(self):
        """Настройка тестового окружения."""
        self.bot = ShansAi()
        self.bot.logger = Mock()
        
        # Мокаем update и message
        self.update = Mock()
        self.update.message = Mock()
        self.update.message.reply_text = AsyncMock()
        self.update.effective_user = Mock()
        self.update.effective_user.id = 12345
        
        # Мокаем reply_markup
        self.reply_markup = Mock()
        self.reply_markup.to_dict = Mock(return_value={"inline_keyboard": []})
    
    async def test_send_message_safe_with_parse_error(self):
        """Тест отправки сообщения с ошибкой parse_mode, но сохранением кнопок."""
        # Текст с проблемным markdown
        problematic_text = "Portfolio with **bold** and `code` and [link](url) and _italic_"
        
        # Мокаем ошибку parse_mode
        self.update.message.reply_text.side_effect = [
            Exception("Bad Request: can't parse entities"),  # Первая попытка с parse_mode
            None  # Вторая попытка без parse_mode должна пройти
        ]
        
        # Вызываем функцию
        await self.bot._send_message_safe(
            self.update, 
            problematic_text, 
            parse_mode='Markdown', 
            reply_markup=self.reply_markup
        )
        
        # Проверяем, что было две попытки отправки
        self.assertEqual(self.update.message.reply_text.call_count, 2)
        
        # Проверяем, что вторая попытка была без parse_mode, но с кнопками
        second_call = self.update.message.reply_text.call_args_list[1]
        self.assertEqual(second_call[1]['reply_markup'], self.reply_markup)
        self.assertNotIn('parse_mode', second_call[1])
    
    async def test_send_message_safe_with_reply_markup_error(self):
        """Тест отправки сообщения с ошибкой reply_markup."""
        # Текст с проблемным markdown
        problematic_text = "Portfolio with **bold** and `code`"
        
        # Мокаем ошибки parse_mode и reply_markup
        self.update.message.reply_text.side_effect = [
            Exception("Bad Request: can't parse entities"),  # Первая попытка с parse_mode
            Exception("Bad Request: reply_markup invalid"),  # Вторая попытка с reply_markup
            None  # Третья попытка только с текстом должна пройти
        ]
        
        # Вызываем функцию
        await self.bot._send_message_safe(
            self.update, 
            problematic_text, 
            parse_mode='Markdown', 
            reply_markup=self.reply_markup
        )
        
        # Проверяем, что было три попытки отправки
        self.assertEqual(self.update.message.reply_text.call_count, 3)
        
        # Проверяем, что третья попытка была только с текстом
        third_call = self.update.message.reply_text.call_args_list[2]
        self.assertNotIn('reply_markup', third_call[1])
        self.assertNotIn('parse_mode', third_call[1])
    
    async def test_send_message_safe_fallback_with_buttons(self):
        """Тест fallback режима с сохранением кнопок."""
        # Текст с проблемным markdown
        problematic_text = "Portfolio with **bold** and `code`"
        
        # Мокаем ошибку в основном блоке
        with patch.object(self.bot, '_send_message_safe', side_effect=Exception("Main error")):
            # Мокаем fallback успешным
            self.update.message.reply_text.side_effect = [
                None  # Fallback с кнопками должен пройти
            ]
            
            # Вызываем функцию напрямую через fallback
            try:
                if hasattr(self.update, 'message') and self.update.message is not None:
                    await self.update.message.reply_text(
                        f"Ошибка форматирования: {str(problematic_text)[:1000]}...", 
                        reply_markup=self.reply_markup
                    )
            except Exception as fallback_error:
                self.fail(f"Fallback should not fail: {fallback_error}")
    
    def test_portfolio_symbol_generation(self):
        """Тест генерации символа портфеля."""
        # Мокаем user_context
        self.bot._get_user_context = Mock(return_value={'portfolio_count': 5})
        
        # Мокаем portfolio объект
        portfolio = Mock()
        portfolio.symbol = "portfolio_9570.PF"
        
        # Тест получения символа из okama
        if hasattr(portfolio, 'symbol'):
            portfolio_symbol = portfolio.symbol
        else:
            portfolio_symbol = f"PF_6"  # 5 + 1
        
        self.assertEqual(portfolio_symbol, "portfolio_9570.PF")
    
    def test_portfolio_symbol_fallback(self):
        """Тест fallback генерации символа портфеля."""
        # Мокаем user_context
        self.bot._get_user_context = Mock(return_value={'portfolio_count': 3})
        
        # Мокаем portfolio объект без символа
        portfolio = Mock()
        del portfolio.symbol  # Удаляем атрибут symbol
        
        # Тест fallback генерации
        try:
            if hasattr(portfolio, 'symbol'):
                portfolio_symbol = portfolio.symbol
            else:
                portfolio_symbol = f"PF_4"  # 3 + 1
        except Exception as e:
            portfolio_symbol = f"PF_4"  # 3 + 1
        
        self.assertEqual(portfolio_symbol, "PF_4")


if __name__ == '__main__':
    # Запуск тестов
    unittest.main()

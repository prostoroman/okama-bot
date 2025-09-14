#!/usr/bin/env python3
"""
Тест для проверки исправлений кнопки AI-анализ:
1. Добавление эмодзи мозг 🧠 к кнопке AI-анализ
2. Перенос кнопки AI-анализ в один ряд с эффективной границей
3. Проверка что клавиатура показывается после AI-анализа
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Добавляем путь к корневой директории проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestAIAnalysisKeyboardFix(unittest.TestCase):
    """Тест исправлений кнопки AI-анализ"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        
        # Мокаем необходимые сервисы
        self.bot.gemini_service = Mock()
        self.bot.gemini_service.is_available.return_value = True
        
        # Мокаем logger
        self.bot.logger = Mock()
        
        # Мокаем контекст пользователя
        self.bot._get_user_context = Mock()
        self.bot._get_user_context.return_value = {
            'current_symbols': ['AAPL', 'GOOGL'],
            'current_currency': 'USD',
            'expanded_symbols': ['AAPL', 'GOOGL'],
            'portfolio_contexts': []
        }
        
        # Мокаем функции отправки сообщений
        self.bot._send_ephemeral_message = AsyncMock()
        self.bot._send_callback_message_with_keyboard_removal = AsyncMock()
        self.bot._prepare_data_for_analysis = AsyncMock()
        
        # Мокаем анализ данных
        self.bot.gemini_service.analyze_data.return_value = {
            'success': True,
            'analysis': 'Тестовый AI-анализ данных'
        }
    
    def test_keyboard_structure_with_gemini_available(self):
        """Тест структуры клавиатуры когда Gemini доступен"""
        # Создаем мок объект update
        update = Mock()
        update.effective_user.id = 12345
        
        # Создаем клавиатуру
        keyboard = self.bot._create_compare_command_keyboard(['AAPL', 'GOOGL'], 'USD', update)
        
        # Проверяем структуру клавиатуры
        self.assertIsNotNone(keyboard)
        self.assertIsNotNone(keyboard.inline_keyboard)
        
        # Проверяем количество рядов
        self.assertEqual(len(keyboard.inline_keyboard), 4)  # 4 ряда кнопок
        
        # Проверяем первый ряд (Дивиденды и Просадки)
        first_row = keyboard.inline_keyboard[0]
        self.assertEqual(len(first_row), 2)
        self.assertEqual(first_row[0].text, "💰 Дивиденды")
        self.assertEqual(first_row[1].text, "📉 Просадки")
        
        # Проверяем второй ряд (Метрики и Корреляция)
        second_row = keyboard.inline_keyboard[1]
        self.assertEqual(len(second_row), 2)
        self.assertEqual(second_row[0].text, "📊 Метрики")
        self.assertEqual(second_row[1].text, "🔗 Корреляция")
        
        # Проверяем третий ряд (Эффективная граница и AI-анализ)
        third_row = keyboard.inline_keyboard[2]
        self.assertEqual(len(third_row), 2)
        self.assertEqual(third_row[0].text, "📈 Эффективная граница")
        self.assertEqual(third_row[1].text, "🧠 AI-анализ")  # Проверяем эмодзи мозг
        
        # Проверяем четвертый ряд (В Портфель)
        fourth_row = keyboard.inline_keyboard[3]
        self.assertEqual(len(fourth_row), 1)
        self.assertEqual(fourth_row[0].text, "💼 В Портфель")
    
    def test_keyboard_structure_without_gemini(self):
        """Тест структуры клавиатуры когда Gemini недоступен"""
        # Отключаем Gemini
        self.bot.gemini_service.is_available.return_value = False
        
        # Создаем мок объект update
        update = Mock()
        update.effective_user.id = 12345
        
        # Создаем клавиатуру
        keyboard = self.bot._create_compare_command_keyboard(['AAPL', 'GOOGL'], 'USD', update)
        
        # Проверяем структуру клавиатуры
        self.assertIsNotNone(keyboard)
        self.assertIsNotNone(keyboard.inline_keyboard)
        
        # Проверяем количество рядов (должно быть 4, но третий ряд содержит только одну кнопку)
        self.assertEqual(len(keyboard.inline_keyboard), 4)
        
        # Проверяем третий ряд (только Эффективная граница)
        third_row = keyboard.inline_keyboard[2]
        self.assertEqual(len(third_row), 1)
        self.assertEqual(third_row[0].text, "📈 Эффективная граница")
    
    @patch('bot.ShansAi._send_callback_message_with_keyboard_removal')
    async def test_ai_analysis_shows_keyboard(self, mock_send_message):
        """Тест что AI-анализ показывает клавиатуру"""
        # Создаем мок объекты
        update = Mock()
        context = Mock()
        
        # Вызываем функцию AI-анализа
        await self.bot._handle_data_analysis_compare_button(update, context)
        
        # Проверяем что функция отправки сообщения была вызвана
        self.assertTrue(mock_send_message.called)
        
        # Проверяем что в вызове был передан reply_markup (клавиатура)
        call_args = mock_send_message.call_args
        self.assertIn('reply_markup', call_args.kwargs)
        self.assertIsNotNone(call_args.kwargs['reply_markup'])
    
    def test_ai_analysis_button_callback_data(self):
        """Тест callback_data кнопки AI-анализ"""
        # Создаем мок объект update
        update = Mock()
        update.effective_user.id = 12345
        
        # Создаем клавиатуру
        keyboard = self.bot._create_compare_command_keyboard(['AAPL', 'GOOGL'], 'USD', update)
        
        # Находим кнопку AI-анализ
        ai_button = None
        for row in keyboard.inline_keyboard:
            for button in row:
                if button.text == "🧠 AI-анализ":
                    ai_button = button
                    break
        
        # Проверяем что кнопка найдена и имеет правильный callback_data
        self.assertIsNotNone(ai_button)
        self.assertEqual(ai_button.callback_data, "data_analysis_compare")


if __name__ == '__main__':
    unittest.main()
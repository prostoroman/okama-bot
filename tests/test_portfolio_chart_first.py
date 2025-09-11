#!/usr/bin/env python3
"""
Тест для проверки изменений команды /portfolio:
- Сначала выводится график накопленной доходности
- Информация о портфеле перенесена в caption
- Inline keyboard добавлен к графику
"""

import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi


class TestPortfolioChartFirst(unittest.TestCase):
    """Тест для проверки изменений команды /portfolio"""
    
    def setUp(self):
        """Настройка тестового окружения"""
        self.bot = ShansAi()
        self.bot.logger = Mock()
        
        # Мокаем контекст пользователя
        self.bot._get_user_context = Mock(return_value={
            'portfolio_count': 0,
            'saved_portfolios': {}
        })
        self.bot._update_user_context = Mock()
        
        # Мокаем отправку сообщений
        self.bot._send_ephemeral_message = AsyncMock()
        self.bot._send_message_safe = AsyncMock()
        self.bot._send_callback_message = AsyncMock()
        
        # Мокаем создание портфеля
        self.mock_portfolio = Mock()
        self.mock_portfolio.wealth_index = Mock()
        self.mock_portfolio.wealth_index.iloc = [-1]
        self.mock_portfolio.wealth_index.iloc[-1] = 1500.0
        self.mock_portfolio.period_length = "5 лет"
    
    def test_portfolio_command(self):
        """Тест команды /portfolio с новым поведением"""
        
        # Настраиваем update для команды portfolio
        update = Mock()
        update.message = Mock()
        update.message.text = "/portfolio AAPL:50% MSFT:50%"
        update.effective_user = Mock()
        update.effective_user.id = 12345
        update.effective_chat = Mock()
        update.effective_chat.id = 67890
        
        context = Mock()
        context.bot.send_photo = AsyncMock()
        context.args = ['AAPL:0.5', 'MSFT:0.5']
        
        # Мокаем _parse_currency_and_period чтобы вернуть правильные символы
        self.bot._parse_currency_and_period = Mock(return_value=(['AAPL:0.5', 'MSFT:0.5'], None, None))
        
        # Мокаем okama
        with patch('bot.ok') as mock_ok:
            mock_ok.Portfolio.return_value = self.mock_portfolio
            
            # Мокаем chart_styles
            with patch('bot.chart_styles') as mock_chart_styles:
                mock_fig = Mock()
                mock_ax = Mock()
                mock_chart_styles.create_portfolio_wealth_chart.return_value = (mock_fig, mock_ax)
                mock_chart_styles.save_figure = Mock()
                mock_chart_styles.cleanup_figure = Mock()
                
                # Мокаем io.BytesIO
                with patch('bot.io.BytesIO') as mock_bytesio:
                    mock_buffer = Mock()
                    mock_buffer.getvalue.return_value = b'fake_image_data'
                    mock_bytesio.return_value = mock_buffer
                    
                    # Мокаем дополнительные функции
                    self.bot._get_portfolio_basic_metrics = Mock(return_value="Test metrics")
                    self.bot._check_existing_portfolio = Mock(return_value=None)
                    self.bot._truncate_caption = Mock(side_effect=lambda x: x)
                    
                    # Вызываем команду portfolio
                    import asyncio
                    try:
                        print("Starting portfolio command...")
                        print(f"Context args: {context.args}")
                        asyncio.run(self.bot.portfolio_command(update, context))
                        print("Portfolio command completed")
                    except Exception as e:
                        print(f"Error in portfolio_command: {e}")
                        import traceback
                        traceback.print_exc()
                    
                    # Проверяем, что отправляется ephemeral сообщение
                    print(f"Ephemeral message called: {self.bot._send_ephemeral_message.called}")
                    print(f"Call count: {self.bot._send_ephemeral_message.call_count}")
                    if self.bot._send_ephemeral_message.called:
                        call_args = self.bot._send_ephemeral_message.call_args
                        print(f"Call args: {call_args}")
                    
                    # Проверяем, что send_message_safe НЕ вызывается (мы убрали отправку текстового сообщения)
                    print(f"Send message safe called: {self.bot._send_message_safe.called}")
                    print(f"Send message safe call count: {self.bot._send_message_safe.call_count}")
                    
                    # Проверяем, что send_photo вызывается
                    print(f"Send photo called: {context.bot.send_photo.called}")
                    print(f"Send photo call count: {context.bot.send_photo.call_count}")
                    
                    # Проверяем, что НЕ отправляется текстовое сообщение с кнопками
                    self.bot._send_message_safe.assert_not_called()
                    
                    # Проверяем, что вызывается новая функция _create_portfolio_wealth_chart_with_info
                    # (это проверяется через то, что send_photo вызывается с reply_markup)
                    context.bot.send_photo.assert_called_once()
                    send_photo_args = context.bot.send_photo.call_args
                    self.assertIn('reply_markup', send_photo_args[1])
                    
                    # Проверяем, что caption содержит информацию о портфеле
                    caption = send_photo_args[1]['caption']
                    self.assertIn("Накопленная доходность портфеля", caption)
                    self.assertIn("Состав портфеля", caption)
                    self.assertIn("Символ портфеля", caption)
                    self.assertIn("Используйте кнопки ниже", caption)
    
    def test_create_portfolio_wealth_chart_with_info(self):
        """Тест новой функции _create_portfolio_wealth_chart_with_info"""
        
        # Настраиваем моки
        update = Mock()
        update.effective_chat.id = 67890
        context = Mock()
        context.bot.send_photo = AsyncMock()
        
        portfolio = self.mock_portfolio
        symbols = ['AAPL', 'MSFT']
        currency = 'USD'
        weights = [0.5, 0.5]
        portfolio_symbol = 'PF_1'
        portfolio_text = "Test portfolio info"
        
        # Создаем mock reply_markup
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Test Button", callback_data="test")]
        ])
        
        # Мокаем chart_styles
        with patch('bot.chart_styles') as mock_chart_styles:
            mock_fig = Mock()
            mock_ax = Mock()
            mock_chart_styles.create_portfolio_wealth_chart.return_value = (mock_fig, mock_ax)
            mock_chart_styles.save_figure = Mock()
            mock_chart_styles.cleanup_figure = Mock()
            
            # Мокаем io.BytesIO
            with patch('bot.io.BytesIO') as mock_bytesio:
                mock_buffer = Mock()
                mock_buffer.getvalue.return_value = b'fake_image_data'
                mock_bytesio.return_value = mock_buffer
                
                # Вызываем функцию
                import asyncio
                asyncio.run(self.bot._create_portfolio_wealth_chart_with_info(
                    update, context, portfolio, symbols, currency, weights, 
                    portfolio_symbol, portfolio_text, reply_markup
                ))
                
                # Проверяем, что send_photo вызывается с правильными параметрами
                context.bot.send_photo.assert_called_once()
                call_args = context.bot.send_photo.call_args
                
                # Проверяем, что передан reply_markup
                self.assertIn('reply_markup', call_args[1])
                self.assertEqual(call_args[1]['reply_markup'], reply_markup)
                
                # Проверяем caption
                caption = call_args[1]['caption']
                self.assertIn("Накопленная доходность портфеля", caption)
                self.assertIn("AAPL (50.0%)", caption)
                self.assertIn("MSFT (50.0%)", caption)
                self.assertIn("PF_1", caption)
                self.assertIn("USD", caption)


if __name__ == '__main__':
    unittest.main()

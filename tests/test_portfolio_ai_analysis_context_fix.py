#!/usr/bin/env python3
"""
Test script for portfolio AI analysis context fix
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
from unittest.mock import Mock, AsyncMock, patch
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

async def test_portfolio_ai_analysis_context_fix():
    """Test the portfolio AI analysis context fix"""
    print("🧪 Тестирование исправления контекста AI анализа портфеля...")
    
    # Create bot instance
    bot = ShansAi()
    
    # Mock user and update
    user = User(id=12345, first_name="Test", is_bot=False)
    chat = Chat(id=12345, type="private")
    message = Message(message_id=1, date=None, chat=chat, from_user=user, text="▫️ AI-анализ")
    update = Update(update_id=1, message=message)
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    
    # Test scenario 1: User created portfolio, then comparison
    print("\n📋 Сценарий 1: Пользователь создал портфель, затем сравнение")
    
    # Mock user context with portfolio data and comparison as last action
    user_context = {
        'last_analysis_type': 'comparison',
        'saved_portfolios': {'test_portfolio': {'symbols': ['SPY.US', 'QQQ.US'], 'weights': [0.6, 0.4]}},
        'last_assets': ['AAPL.US', 'MSFT.US'],
        'current_symbols': ['AAPL.US', 'MSFT.US'],
        'current_currency': 'USD'
    }
    
    bot._get_user_context = lambda user_id: user_context
    
    # Mock the handlers
    bot._handle_portfolio_reply_keyboard_button = AsyncMock()
    bot._handle_compare_reply_keyboard_button = AsyncMock()
    bot._send_message_safe = AsyncMock()
    
    # Test the reply keyboard button handler
    await bot._handle_reply_keyboard_button(update, context, "▫️ AI-анализ")
    
    # Verify that compare handler was called (not portfolio)
    bot._handle_compare_reply_keyboard_button.assert_called_once()
    bot._handle_portfolio_reply_keyboard_button.assert_not_called()
    
    print("✅ Сценарий 1: Правильно выбран контекст сравнения")
    
    # Test scenario 2: User created comparison, then portfolio
    print("\n📋 Сценарий 2: Пользователь создал сравнение, затем портфель")
    
    # Mock user context with comparison data and portfolio as last action
    user_context = {
        'last_analysis_type': 'portfolio',
        'saved_portfolios': {'test_portfolio': {'symbols': ['SPY.US', 'QQQ.US'], 'weights': [0.6, 0.4]}},
        'last_assets': ['SPY.US', 'QQQ.US'],
        'current_symbols': ['SPY.US', 'QQQ.US'],
        'current_currency': 'USD'
    }
    
    bot._get_user_context = lambda user_id: user_context
    
    # Reset mocks
    bot._handle_portfolio_reply_keyboard_button.reset_mock()
    bot._handle_compare_reply_keyboard_button.reset_mock()
    
    # Test the reply keyboard button handler
    await bot._handle_reply_keyboard_button(update, context, "▫️ AI-анализ")
    
    # Verify that portfolio handler was called (not compare)
    bot._handle_portfolio_reply_keyboard_button.assert_called_once()
    bot._handle_compare_reply_keyboard_button.assert_not_called()
    
    print("✅ Сценарий 2: Правильно выбран контекст портфеля")
    
    # Test scenario 3: Only portfolio data
    print("\n📋 Сценарий 3: Только данные портфеля")
    
    # Mock user context with only portfolio data
    user_context = {
        'last_analysis_type': 'portfolio',
        'saved_portfolios': {'test_portfolio': {'symbols': ['SPY.US', 'QQQ.US'], 'weights': [0.6, 0.4]}},
        'last_assets': [],
        'current_symbols': ['SPY.US', 'QQQ.US'],
        'current_currency': 'USD'
    }
    
    bot._get_user_context = lambda user_id: user_context
    
    # Reset mocks
    bot._handle_portfolio_reply_keyboard_button.reset_mock()
    bot._handle_compare_reply_keyboard_button.reset_mock()
    
    # Test the reply keyboard button handler
    await bot._handle_reply_keyboard_button(update, context, "▫️ AI-анализ")
    
    # Verify that portfolio handler was called
    bot._handle_portfolio_reply_keyboard_button.assert_called_once()
    bot._handle_compare_reply_keyboard_button.assert_not_called()
    
    print("✅ Сценарий 3: Правильно выбран контекст портфеля")
    
    # Test scenario 4: Only comparison data
    print("\n📋 Сценарий 4: Только данные сравнения")
    
    # Mock user context with only comparison data
    user_context = {
        'last_analysis_type': 'comparison',
        'saved_portfolios': {},
        'last_assets': ['AAPL.US', 'MSFT.US'],
        'current_symbols': ['AAPL.US', 'MSFT.US'],
        'current_currency': 'USD'
    }
    
    bot._get_user_context = lambda user_id: user_context
    
    # Reset mocks
    bot._handle_portfolio_reply_keyboard_button.reset_mock()
    bot._handle_compare_reply_keyboard_button.reset_mock()
    
    # Test the reply keyboard button handler
    await bot._handle_reply_keyboard_button(update, context, "▫️ AI-анализ")
    
    # Verify that compare handler was called
    bot._handle_compare_reply_keyboard_button.assert_called_once()
    bot._handle_portfolio_reply_keyboard_button.assert_not_called()
    
    print("✅ Сценарий 4: Правильно выбран контекст сравнения")
    
    # Test scenario 5: No data available
    print("\n📋 Сценарий 5: Нет данных")
    
    # Mock user context with no data
    user_context = {
        'last_analysis_type': None,
        'saved_portfolios': {},
        'last_assets': [],
        'current_symbols': [],
        'current_currency': None
    }
    
    bot._get_user_context = lambda user_id: user_context
    
    # Reset mocks
    bot._handle_portfolio_reply_keyboard_button.reset_mock()
    bot._handle_compare_reply_keyboard_button.reset_mock()
    
    # Test the reply keyboard button handler
    await bot._handle_reply_keyboard_button(update, context, "▫️ AI-анализ")
    
    # Verify that error message was sent
    bot._send_message_safe.assert_called_once()
    bot._handle_portfolio_reply_keyboard_button.assert_not_called()
    bot._handle_compare_reply_keyboard_button.assert_not_called()
    
    print("✅ Сценарий 5: Правильно показано сообщение об ошибке")
    
    print("\n🎉 Все тесты пройдены успешно!")
    print("✅ Исправление контекста AI анализа портфеля работает корректно")

if __name__ == "__main__":
    asyncio.run(test_portfolio_ai_analysis_context_fix())

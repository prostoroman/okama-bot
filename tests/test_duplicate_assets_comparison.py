"""
Тесты для проверки обработки дубликатов при сравнении активов
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, Message, User, Chat
from telegram.ext import ContextTypes

from bot import OkamaBot


class TestDuplicateAssetsComparison:
    """Тесты для проверки обработки дубликатов при сравнении активов"""

    @pytest.fixture
    def bot(self):
        """Создание экземпляра бота для тестирования"""
        return OkamaBot()

    @pytest.fixture
    def mock_update(self):
        """Создание мок-объекта Update"""
        update = MagicMock(spec=Update)
        update.effective_user = MagicMock(spec=User)
        update.effective_user.id = 12345
        update.effective_chat = MagicMock(spec=Chat)
        update.effective_chat.id = 12345
        return update

    @pytest.fixture
    def mock_context(self):
        """Создание мок-объекта Context"""
        context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
        context.args = []
        return context

    @pytest.mark.asyncio
    async def test_duplicate_two_assets_error(self, bot, mock_update, mock_context):
        """Тест: ошибка при сравнении двух одинаковых активов"""
        # Настройка
        mock_context.args = ['SPY.US', 'SPY.US']
        
        # Мок для _send_message_safe
        bot._send_message_safe = AsyncMock()
        
        # Мок для _remove_portfolio_reply_keyboard
        bot._remove_portfolio_reply_keyboard = AsyncMock()
        
        # Мок для _get_user_context
        bot._get_user_context = MagicMock(return_value={})
        
        # Мок для _update_user_context
        bot._update_user_context = MagicMock()
        
        # Мок для _normalize_symbol_namespace
        bot._normalize_symbol_namespace = MagicMock(side_effect=lambda x: x)
        
        # Выполнение
        await bot.compare_command(mock_update, mock_context)
        
        # Проверка
        bot._send_message_safe.assert_called_with(
            mock_update, 
            "❌ Можно сравнивать только разные активы. Указаны одинаковые символы."
        )

    @pytest.mark.asyncio
    async def test_duplicate_three_assets_removal(self, bot, mock_update, mock_context):
        """Тест: удаление дубликатов при сравнении трех активов с повторами"""
        # Настройка
        mock_context.args = ['SPY.US', 'QQQ.US', 'SPY.US']
        
        # Мок для _send_message_safe
        bot._send_message_safe = AsyncMock()
        
        # Мок для _remove_portfolio_reply_keyboard
        bot._remove_portfolio_reply_keyboard = AsyncMock()
        
        # Мок для _get_user_context
        bot._get_user_context = MagicMock(return_value={'saved_portfolios': {}})
        
        # Мок для _update_user_context
        bot._update_user_context = MagicMock()
        
        # Мок для _normalize_symbol_namespace
        bot._normalize_symbol_namespace = MagicMock(side_effect=lambda x: x)
        
        # Мок для _parse_currency_and_period
        bot._parse_currency_and_period = MagicMock(return_value=(['SPY.US', 'QQQ.US', 'SPY.US'], None, None))
        
        # Мок для остальных методов, которые могут быть вызваны
        bot._create_asset_list = AsyncMock()
        bot._create_comparison_chart = AsyncMock()
        bot._send_chart_with_metrics = AsyncMock()
        
        # Выполнение
        await bot.compare_command(mock_update, mock_context)
        
        # Проверка
        bot._send_message_safe.assert_called_with(
            mock_update, 
            "⚠️ Обнаружены повторяющиеся активы. Исключены дубликаты из сравнения."
        )

    @pytest.mark.asyncio
    async def test_duplicate_four_assets_removal(self, bot, mock_update, mock_context):
        """Тест: удаление дубликатов при сравнении четырех активов с повторами"""
        # Настройка
        mock_context.args = ['SPY.US', 'QQQ.US', 'SPY.US', 'QQQ.US']
        
        # Мок для _send_message_safe
        bot._send_message_safe = AsyncMock()
        
        # Мок для _remove_portfolio_reply_keyboard
        bot._remove_portfolio_reply_keyboard = AsyncMock()
        
        # Мок для _get_user_context
        bot._get_user_context = MagicMock(return_value={'saved_portfolios': {}})
        
        # Мок для _update_user_context
        bot._update_user_context = MagicMock()
        
        # Мок для _normalize_symbol_namespace
        bot._normalize_symbol_namespace = MagicMock(side_effect=lambda x: x)
        
        # Мок для _parse_currency_and_period
        bot._parse_currency_and_period = MagicMock(return_value=(['SPY.US', 'QQQ.US', 'SPY.US', 'QQQ.US'], None, None))
        
        # Мок для остальных методов, которые могут быть вызваны
        bot._create_asset_list = AsyncMock()
        bot._create_comparison_chart = AsyncMock()
        bot._send_chart_with_metrics = AsyncMock()
        
        # Выполнение
        await bot.compare_command(mock_update, mock_context)
        
        # Проверка
        bot._send_message_safe.assert_called_with(
            mock_update, 
            "⚠️ Обнаружены повторяющиеся активы. Исключены дубликаты из сравнения."
        )

    @pytest.mark.asyncio
    async def test_no_duplicates_normal_comparison(self, bot, mock_update, mock_context):
        """Тест: нормальное сравнение без дубликатов"""
        # Настройка
        mock_context.args = ['SPY.US', 'QQQ.US', 'AAPL.US']
        
        # Мок для _send_message_safe
        bot._send_message_safe = AsyncMock()
        
        # Мок для _remove_portfolio_reply_keyboard
        bot._remove_portfolio_reply_keyboard = AsyncMock()
        
        # Мок для _get_user_context
        bot._get_user_context = MagicMock(return_value={'saved_portfolios': {}})
        
        # Мок для _update_user_context
        bot._update_user_context = MagicMock()
        
        # Мок для _normalize_symbol_namespace
        bot._normalize_symbol_namespace = MagicMock(side_effect=lambda x: x)
        
        # Мок для _parse_currency_and_period
        bot._parse_currency_and_period = MagicMock(return_value=(['SPY.US', 'QQQ.US', 'AAPL.US'], None, None))
        
        # Мок для остальных методов, которые могут быть вызваны
        bot._create_asset_list = AsyncMock()
        bot._create_comparison_chart = AsyncMock()
        bot._send_chart_with_metrics = AsyncMock()
        
        # Выполнение
        await bot.compare_command(mock_update, mock_context)
        
        # Проверка - не должно быть сообщения о дубликатах
        duplicate_message_calls = [
            call for call in bot._send_message_safe.call_args_list 
            if "Обнаружены повторяющиеся активы" in str(call)
        ]
        assert len(duplicate_message_calls) == 0

    @pytest.mark.asyncio
    async def test_duplicate_with_different_case(self, bot, mock_update, mock_context):
        """Тест: обработка дубликатов с разным регистром"""
        # Настройка
        mock_context.args = ['SPY.US', 'spy.us']
        
        # Мок для _send_message_safe
        bot._send_message_safe = AsyncMock()
        
        # Мок для _remove_portfolio_reply_keyboard
        bot._remove_portfolio_reply_keyboard = AsyncMock()
        
        # Мок для _get_user_context
        bot._get_user_context = MagicMock(return_value={})
        
        # Мок для _update_user_context
        bot._update_user_context = MagicMock()
        
        # Мок для _normalize_symbol_namespace - нормализует регистр
        bot._normalize_symbol_namespace = MagicMock(side_effect=lambda x: x.upper())
        
        # Выполнение
        await bot.compare_command(mock_update, mock_context)
        
        # Проверка - после нормализации регистра должны быть одинаковые символы
        bot._send_message_safe.assert_called_with(
            mock_update, 
            "❌ Можно сравнивать только разные активы. Указаны одинаковые символы."
        )

    def test_unique_symbols_preservation_order(self):
        """Тест: сохранение порядка символов при удалении дубликатов"""
        # Тестируем логику удаления дубликатов
        symbols = ['SPY.US', 'QQQ.US', 'SPY.US', 'AAPL.US', 'QQQ.US']
        unique_symbols = list(dict.fromkeys(symbols))
        
        # Проверяем, что порядок сохранен
        expected = ['SPY.US', 'QQQ.US', 'AAPL.US']
        assert unique_symbols == expected
        
        # Проверяем, что дубликаты действительно удалены
        assert len(unique_symbols) == 3
        assert len(symbols) == 5

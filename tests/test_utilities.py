#!/usr/bin/env python3
"""
Вспомогательные утилиты для тестирования okama-bot
"""

import sys
import os
import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

# Add the parent directory to the path to import bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    OKAMA_AVAILABLE = True
except ImportError:
    OKAMA_AVAILABLE = False


class TestDataGenerator:
    """Генератор тестовых данных для бота"""
    
    @staticmethod
    def create_mock_update(user_id: int = 12345, message_text: str = "", callback_data: str = None) -> Mock:
        """Создает mock объект Update для тестирования"""
        mock_update = Mock()
        mock_update.effective_user = Mock()
        mock_update.effective_user.id = user_id
        mock_update.effective_user.first_name = "TestUser"
        
        if message_text:
            mock_update.message = Mock()
            mock_update.message.text = message_text
        
        if callback_data:
            mock_update.callback_query = Mock()
            mock_update.callback_query.data = callback_data
            mock_update.callback_query.answer = AsyncMock()
        
        return mock_update
    
    @staticmethod
    def create_mock_context() -> Mock:
        """Создает mock объект Context для тестирования"""
        mock_context = Mock()
        mock_context.bot = Mock()
        mock_context.bot.send_message = AsyncMock()
        mock_context.bot.send_photo = AsyncMock()
        mock_context.bot.send_document = AsyncMock()
        mock_context.bot.edit_message_text = AsyncMock()
        mock_context.bot.edit_message_reply_markup = AsyncMock()
        return mock_context
    
    @staticmethod
    def create_test_price_data(symbol: str = "SPY.US", days: int = 100) -> pd.Series:
        """Создает тестовые данные цен"""
        dates = pd.date_range('2020-01-01', periods=days, freq='D')
        np.random.seed(42)  # Для воспроизводимости
        returns = np.random.normal(0.001, 0.02, days)
        prices = 100 * (1 + returns).cumprod()
        return pd.Series(prices, index=dates, name=symbol)
    
    @staticmethod
    def create_test_portfolio_data(symbols: List[str], weights: List[float]) -> Dict[str, Any]:
        """Создает тестовые данные портфеля"""
        return {
            'symbols': symbols,
            'weights': weights,
            'currency': 'USD',
            'created_at': datetime.now().isoformat()
        }
    
    @staticmethod
    def create_test_user_context() -> Dict[str, Any]:
        """Создает тестовый контекст пользователя"""
        return {
            'current_symbols': ['SPY.US', 'QQQ.US'],
            'last_analysis_type': 'compare',
            'saved_portfolios': {
                'test_portfolio_1': {
                    'symbols': ['SPY.US', 'QQQ.US'],
                    'weights': [0.6, 0.4],
                    'currency': 'USD'
                }
            }
        }


class MockOkamaAsset:
    """Mock класс для okama.Asset"""
    
    def __init__(self, symbol: str, price_data: pd.Series = None):
        self.symbol = symbol
        self._price_data = price_data or TestDataGenerator.create_test_price_data(symbol)
        self._dividend_data = None
    
    def close_prices(self) -> pd.Series:
        return self._price_data
    
    @property
    def dividends(self):
        if self._dividend_data is None:
            # Создаем тестовые дивиденды
            dates = self._price_data.index[::30]  # Каждый месяц
            amounts = np.random.uniform(0.5, 2.0, len(dates))
            self._dividend_data = pd.Series(amounts, index=dates)
        return self._dividend_data


class MockOkamaPortfolio:
    """Mock класс для okama.Portfolio"""
    
    def __init__(self, symbols: List[str], weights: List[float], currency: str = "USD"):
        self.symbols = symbols
        self.weights = weights
        self.currency = currency
        self._returns_data = None
        self._wealth_index = None
    
    @property
    def returns(self):
        if self._returns_data is None:
            # Создаем тестовые доходности
            dates = pd.date_range('2020-01-01', periods=100, freq='D')
            np.random.seed(42)
            returns = np.random.normal(0.001, 0.02, 100)
            self._returns_data = pd.Series(returns, index=dates)
        return self._returns_data
    
    @property
    def wealth_index(self):
        if self._wealth_index is None:
            # Создаем тестовый индекс благосостояния
            dates = pd.date_range('2020-01-01', periods=100, freq='D')
            np.random.seed(42)
            returns = np.random.normal(0.001, 0.02, 100)
            wealth = 100 * (1 + returns).cumprod()
            self._wealth_index = pd.Series(wealth, index=dates)
        return self._wealth_index
    
    @property
    def wealth_index_with_assets(self):
        # Возвращаем тот же индекс благосостояния
        return self.wealth_index


class TestRunner:
    """Утилита для запуска тестов"""
    
    @staticmethod
    def run_async_test(test_func, *args, **kwargs):
        """Запускает асинхронную тестовую функцию"""
        return asyncio.run(test_func(*args, **kwargs))
    
    @staticmethod
    def create_test_environment():
        """Создает тестовое окружение"""
        # Патчим okama для использования mock объектов
        if OKAMA_AVAILABLE:
            with patch('okama.Asset', MockOkamaAsset):
                with patch('okama.Portfolio', MockOkamaPortfolio):
                    yield
        else:
            yield


class TestAssertions:
    """Дополнительные утверждения для тестирования"""
    
    @staticmethod
    def assert_valid_telegram_message(message_text: str):
        """Проверяет, что сообщение соответствует ограничениям Telegram"""
        assert len(message_text) <= 4096, f"Message too long: {len(message_text)} characters"
        assert isinstance(message_text, str), "Message must be a string"
    
    @staticmethod
    def assert_valid_chart_data(chart_data: bytes):
        """Проверяет, что данные графика валидны"""
        assert isinstance(chart_data, bytes), "Chart data must be bytes"
        assert len(chart_data) > 0, "Chart data cannot be empty"
        # Проверяем, что это PNG (начинается с PNG signature)
        assert chart_data.startswith(b'\x89PNG'), "Chart data must be PNG format"
    
    @staticmethod
    def assert_valid_portfolio_data(portfolio_data: Dict[str, Any]):
        """Проверяет, что данные портфеля валидны"""
        required_keys = ['symbols', 'weights', 'currency']
        for key in required_keys:
            assert key in portfolio_data, f"Portfolio data missing key: {key}"
        
        assert isinstance(portfolio_data['symbols'], list), "Symbols must be a list"
        assert isinstance(portfolio_data['weights'], list), "Weights must be a list"
        assert len(portfolio_data['symbols']) == len(portfolio_data['weights']), "Symbols and weights must have same length"
        
        # Проверяем, что веса в сумме дают 1
        total_weight = sum(portfolio_data['weights'])
        assert abs(total_weight - 1.0) < 0.01, f"Weights must sum to 1.0, got {total_weight}"
    
    @staticmethod
    def assert_valid_symbol(symbol: str):
        """Проверяет, что символ валиден"""
        assert isinstance(symbol, str), "Symbol must be a string"
        assert len(symbol) > 0, "Symbol cannot be empty"
        assert '.' in symbol, "Symbol must contain a dot (e.g., SPY.US)"
    
    @staticmethod
    def assert_valid_weights(weights: List[float]):
        """Проверяет, что веса валидны"""
        assert isinstance(weights, list), "Weights must be a list"
        assert len(weights) > 0, "Weights cannot be empty"
        
        for weight in weights:
            assert isinstance(weight, (int, float)), "All weights must be numbers"
            assert 0 <= weight <= 1, f"Weight {weight} must be between 0 and 1"
        
        total_weight = sum(weights)
        assert abs(total_weight - 1.0) < 0.01, f"Weights must sum to 1.0, got {total_weight}"


class TestDataValidator:
    """Валидатор тестовых данных"""
    
    @staticmethod
    def validate_price_data(price_data: pd.Series) -> bool:
        """Валидирует данные цен"""
        if not isinstance(price_data, pd.Series):
            return False
        
        if len(price_data) == 0:
            return False
        
        if not isinstance(price_data.index, pd.DatetimeIndex):
            return False
        
        if not price_data.dtype in ['float64', 'int64']:
            return False
        
        if (price_data <= 0).any():
            return False
        
        return True
    
    @staticmethod
    def validate_returns_data(returns_data: pd.Series) -> bool:
        """Валидирует данные доходности"""
        if not isinstance(returns_data, pd.Series):
            return False
        
        if len(returns_data) == 0:
            return False
        
        if not isinstance(returns_data.index, pd.DatetimeIndex):
            return False
        
        if not returns_data.dtype in ['float64', 'int64']:
            return False
        
        return True
    
    @staticmethod
    def validate_portfolio_metrics(metrics: Dict[str, float]) -> bool:
        """Валидирует метрики портфеля"""
        required_metrics = [
            'annual_return', 'volatility', 'sharpe_ratio', 
            'sortino_ratio', 'max_drawdown', 'calmar_ratio'
        ]
        
        for metric in required_metrics:
            if metric not in metrics:
                return False
            
            if not isinstance(metrics[metric], (int, float)):
                return False
        
        return True


class TestReporter:
    """Репортер результатов тестирования"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def start_test_suite(self):
        """Начинает набор тестов"""
        self.start_time = datetime.now()
        print(f"🚀 Начало тестирования: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def end_test_suite(self):
        """Завершает набор тестов"""
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time
        
        print(f"\n🏁 Завершение тестирования: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ Общее время: {duration.total_seconds():.2f} секунд")
        
        # Статистика
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['status'] == 'passed')
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Результаты:")
        print(f"   Всего тестов: {total_tests}")
        print(f"   ✅ Пройдено: {passed_tests}")
        print(f"   ❌ Провалено: {failed_tests}")
        print(f"   📈 Успешность: {(passed_tests / total_tests * 100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Проваленные тесты:")
            for result in self.results:
                if result['status'] == 'failed':
                    print(f"   - {result['name']}: {result['error']}")
    
    def add_test_result(self, name: str, status: str, error: str = None, duration: float = None):
        """Добавляет результат теста"""
        self.results.append({
            'name': name,
            'status': status,
            'error': error,
            'duration': duration,
            'timestamp': datetime.now()
        })
        
        status_emoji = "✅" if status == "passed" else "❌"
        print(f"{status_emoji} {name}" + (f" ({duration:.2f}s)" if duration else ""))
        
        if error:
            print(f"   Ошибка: {error}")


# Глобальные утилиты для использования в тестах
def create_test_bot():
    """Создает экземпляр бота для тестирования"""
    from bot import ShansAi
    return ShansAi()


def create_test_environment():
    """Создает тестовое окружение с моками"""
    return TestRunner.create_test_environment()


def run_async_test(test_func, *args, **kwargs):
    """Запускает асинхронную тестовую функцию"""
    return TestRunner.run_async_test(test_func, *args, **kwargs)


if __name__ == '__main__':
    print("🧪 Утилиты для тестирования okama-bot")
    print(f"📚 Okama доступен: {OKAMA_AVAILABLE}")
    
    # Демонстрация использования
    print("\n🔧 Демонстрация утилит:")
    
    # Создание тестовых данных
    generator = TestDataGenerator()
    price_data = generator.create_test_price_data("SPY.US", 30)
    print(f"✅ Созданы тестовые данные цен: {len(price_data)} точек")
    
    # Валидация данных
    validator = TestDataValidator()
    is_valid = validator.validate_price_data(price_data)
    print(f"✅ Валидация данных цен: {'Пройдена' if is_valid else 'Провалена'}")
    
    # Создание mock объектов
    mock_update = generator.create_mock_update(12345, "/test SPY.US")
    mock_context = generator.create_mock_context()
    print(f"✅ Созданы mock объекты для тестирования")
    
    print("\n🎯 Утилиты готовы к использованию!")

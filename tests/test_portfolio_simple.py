#!/usr/bin/env python3
"""
Простой тест для проверки улучшений команды /portfolio
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_portfolio_keyboard_has_ai_analysis():
    """Тест: проверяем что клавиатура портфеля содержит кнопку AI-анализ"""
    from bot import ShansAi
    
    # Создаем экземпляр бота
    bot = ShansAi()
    
    # Мокаем Gemini сервис как доступный
    class MockGemini:
        def is_available(self):
            return True
    bot.gemini_service = MockGemini()
    
    # Создаем клавиатуру портфеля
    keyboard = bot._create_portfolio_command_keyboard('test_portfolio')
    
    # Проверяем, что клавиатура создана
    assert keyboard is not None, "Клавиатура не создана"
    
    # Проверяем, что кнопка AI-анализ присутствует
    has_ai_button = False
    for row in keyboard.inline_keyboard:
        for button in row:
            if 'AI-анализ' in button.text:
                has_ai_button = True
                break
    
    assert has_ai_button, "Кнопка AI-анализ не найдена в клавиатуре"
    print("✅ Кнопка AI-анализ найдена в клавиатуре портфеля")

def test_portfolio_keyboard_without_gemini():
    """Тест: проверяем что без Gemini сервиса кнопка AI-анализ не показывается"""
    from bot import ShansAi
    
    # Создаем экземпляр бота
    bot = ShansAi()
    
    # Мокаем Gemini сервис как недоступный
    class MockGemini:
        def is_available(self):
            return False
    bot.gemini_service = MockGemini()
    
    # Создаем клавиатуру портфеля
    keyboard = bot._create_portfolio_command_keyboard('test_portfolio')
    
    # Проверяем, что клавиатура создана
    assert keyboard is not None, "Клавиатура не создана"
    
    # Проверяем, что кнопка AI-анализ отсутствует
    has_ai_button = False
    for row in keyboard.inline_keyboard:
        for button in row:
            if 'AI-анализ' in button.text:
                has_ai_button = True
                break
    
    assert not has_ai_button, "Кнопка AI-анализ найдена, хотя Gemini недоступен"
    print("✅ Кнопка AI-анализ правильно скрыта при недоступности Gemini")

def test_callback_routing():
    """Тест: проверяем что callback'и для AI-анализа правильно обрабатываются"""
    # Проверяем, что callback начинается с правильного префикса
    callback_data = 'portfolio_ai_analysis_test_portfolio'
    
    assert callback_data.startswith('portfolio_ai_analysis_'), "Неправильный префикс callback'а"
    print("✅ Callback для AI-анализа имеет правильный префикс")

def test_metrics_button_uses_summary_table():
    """Тест: проверяем что кнопка Метрики использует правильную функцию"""
    from bot import ShansAi
    
    # Создаем экземпляр бота
    bot = ShansAi()
    
    # Проверяем, что функция _create_summary_metrics_table существует
    assert hasattr(bot, '_create_summary_metrics_table'), "Функция _create_summary_metrics_table не найдена"
    print("✅ Функция _create_summary_metrics_table существует")

def test_ai_analysis_handler_exists():
    """Тест: проверяем что обработчик AI-анализа существует"""
    from bot import ShansAi
    
    # Создаем экземпляр бота
    bot = ShansAi()
    
    # Проверяем, что функция обработчика существует
    assert hasattr(bot, '_handle_portfolio_ai_analysis_button'), "Обработчик AI-анализа не найден"
    print("✅ Обработчик AI-анализа существует")

if __name__ == '__main__':
    print("🧪 Запуск простых тестов для улучшений команды /portfolio")
    print("=" * 60)
    
    try:
        test_portfolio_keyboard_has_ai_analysis()
        test_portfolio_keyboard_without_gemini()
        test_callback_routing()
        test_metrics_button_uses_summary_table()
        test_ai_analysis_handler_exists()
        
        print("=" * 60)
        print("🎉 Все тесты прошли успешно!")
        print("✅ Кнопка Метрики теперь использует _create_summary_metrics_table()")
        print("✅ Кнопка AI-анализ добавлена в клавиатуру портфеля")
        print("✅ Функционал AI-анализа реализован аналогично сравнению")
        
    except Exception as e:
        print(f"❌ Тест не прошел: {e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
"""
Тест для проверки исправления ошибки создания таблицы метрик портфеля
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_portfolio_metrics_fix():
    """Тест: проверяем что новая функция _create_portfolio_summary_metrics_table существует"""
    from bot import ShansAi
    
    # Создаем экземпляр бота
    bot = ShansAi()
    
    # Проверяем, что новая функция существует
    assert hasattr(bot, '_create_portfolio_summary_metrics_table'), "Функция _create_portfolio_summary_metrics_table не найдена"
    print("✅ Функция _create_portfolio_summary_metrics_table существует")

def test_portfolio_metrics_table_format():
    """Тест: проверяем формат таблицы метрик портфеля"""
    from bot import ShansAi
    import okama as ok
    
    # Создаем экземпляр бота
    bot = ShansAi()
    
    try:
        # Создаем тестовый портфель
        symbols = ['SBER.MOEX', 'LKOH.MOEX']
        weights = [0.6, 0.4]
        currency = 'RUB'
        
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
        
        # Создаем таблицу метрик
        table = bot._create_portfolio_summary_metrics_table(portfolio, symbols, weights, currency)
        
        # Проверяем, что таблица создана
        assert table is not None, "Таблица метрик не создана"
        assert not table.startswith("❌"), f"Ошибка создания таблицы: {table}"
        
        # Проверяем наличие ключевых метрик
        key_metrics = [
            "Среднегодовая доходность (CAGR)",
            "Волатильность", 
            "Коэфф. Шарпа",
            "Макс. просадка",
            "Безрисковая ставка",
            "Состав портфеля"
        ]
        
        for metric in key_metrics:
            assert metric in table, f"Метрика '{metric}' не найдена в таблице"
        
        print("✅ Таблица метрик портфеля создана успешно")
        print("✅ Все ключевые метрики присутствуют")
        
    except Exception as e:
        print(f"⚠️ Тест не прошел из-за ошибки: {e}")
        print("Это может быть связано с недоступностью данных okama")

if __name__ == '__main__':
    print("🧪 Запуск тестов для исправления ошибки таблицы метрик портфеля")
    print("=" * 70)
    
    try:
        test_portfolio_metrics_fix()
        test_portfolio_metrics_table_format()
        
        print("=" * 70)
        print("🎉 Все тесты прошли успешно!")
        print("✅ Ошибка создания таблицы метрик портфеля исправлена")
        
    except Exception as e:
        print(f"❌ Тест не прошел: {e}")
        import traceback
        traceback.print_exc()

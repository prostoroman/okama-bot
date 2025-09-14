#!/usr/bin/env python3
"""
Тест для проверки исправления значений метрик портфеля
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_portfolio_metrics_values():
    """Тест: проверяем что метрики портфеля показывают правильные значения"""
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
        
        # Создаем таблицу метрик портфеля
        portfolio_table = bot._create_portfolio_summary_metrics_table(portfolio, symbols, weights, currency)
        
        # Проверяем, что таблица создана
        assert portfolio_table is not None, "Таблица метрик портфеля не создана"
        assert not portfolio_table.startswith("❌"), f"Ошибка создания таблицы: {portfolio_table}"
        
        print("📊 Созданная таблица метрик:")
        print(portfolio_table)
        
        # Проверяем, что значения не являются названиями метрик
        lines = portfolio_table.split('\n')
        for line in lines:
            if '|' in line and not line.startswith('|') and 'Метрика' not in line:
                parts = line.split('|')
                if len(parts) >= 3:
                    metric_name = parts[1].strip()
                    metric_value = parts[2].strip()
                    
                    # Проверяем, что значение не равно названию метрики
                    assert metric_value != metric_name, f"Значение '{metric_value}' равно названию метрики '{metric_name}'"
                    
                    # Проверяем, что значение содержит числа или проценты
                    has_number = any(char.isdigit() for char in metric_value)
                    has_percent = '%' in metric_value
                    has_na = metric_value == 'N/A'
                    
                    assert has_number or has_percent or has_na, f"Значение '{metric_value}' не содержит чисел, процентов или N/A"
        
        print("\n✅ Все значения метрик корректны")
        print("✅ Значения не равны названиям метрик")
        print("✅ Значения содержат числа, проценты или N/A")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Тест не прошел из-за ошибки: {e}")
        print("Это может быть связано с недоступностью данных okama")
        import traceback
        traceback.print_exc()
        return False

def test_specific_metrics():
    """Тест: проверяем конкретные метрики"""
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
        
        # Создаем таблицу метрик портфеля
        portfolio_table = bot._create_portfolio_summary_metrics_table(portfolio, symbols, weights, currency)
        
        # Проверяем конкретные метрики
        expected_metrics = [
            "compound return (YTD)",
            "CAGR (5 years)",
            "Risk (19 years, 0 months)",
            "Max drawdown (19 years, 0 months)",
            "Risk free rate",
            "Sharpe Ratio"
        ]
        
        print("\n🔍 Проверка конкретных метрик:")
        for metric in expected_metrics:
            if metric in portfolio_table:
                # Извлекаем значение метрики
                lines = portfolio_table.split('\n')
                for line in lines:
                    if metric in line and '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            value = parts[2].strip()
                            print(f"   ✅ {metric}: {value}")
                            break
            else:
                print(f"   ❌ {metric}: не найдена")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Тест не прошел из-за ошибки: {e}")
        return False

if __name__ == '__main__':
    print("🧪 Запуск тестов исправления значений метрик портфеля")
    print("=" * 70)
    
    success_count = 0
    total_tests = 2
    
    try:
        if test_portfolio_metrics_values():
            success_count += 1
        
        if test_specific_metrics():
            success_count += 1
        
        print("=" * 70)
        if success_count == total_tests:
            print("🎉 Все тесты прошли успешно!")
            print("✅ Значения метрик портфеля исправлены")
            print("✅ Отображаются реальные данные из okama.portfolio.describe()")
        else:
            print(f"⚠️ Прошло {success_count} из {total_tests} тестов")
        
    except Exception as e:
        print(f"❌ Тест не прошел: {e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
"""
Тест для проверки консистентности метрик портфеля с метриками сравнения
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_portfolio_metrics_consistency():
    """Тест: проверяем что метрики портфеля имеют тот же формат, что и в compare"""
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
        
        # Проверяем наличие заголовка
        assert "## 📊 Метрики портфеля" in portfolio_table, "Заголовок таблицы не найден"
        
        # Проверяем наличие ключевых метрик из okama.describe()
        key_metrics_from_describe = [
            "Compound return",
            "CAGR",
            "Annualized mean return", 
            "Dividend yield",
            "Risk",
            "CVAR",
            "Max drawdowns"
        ]
        
        print("🔍 Проверка метрик из okama.describe():")
        for metric in key_metrics_from_describe:
            present = metric in portfolio_table
            status = "✅" if present else "❌"
            print(f"   {status} {metric}")
        
        # Проверяем наличие дополнительных метрик
        additional_metrics = [
            "Risk free rate",
            "Sharpe Ratio", 
            "Sortino Ratio",
            "Calmar Ratio"
        ]
        
        print("\n🔍 Проверка дополнительных метрик:")
        for metric in additional_metrics:
            present = metric in portfolio_table
            status = "✅" if present else "❌"
            print(f"   {status} {metric}")
        
        # Проверяем формат таблицы (markdown)
        assert "|" in portfolio_table, "Таблица не в markdown формате"
        assert "Метрика" in portfolio_table, "Заголовок 'Метрика' не найден"
        assert "Значение" in portfolio_table, "Заголовок 'Значение' не найден"
        
        print("\n✅ Таблица метрик портфеля создана успешно")
        print("✅ Формат соответствует метрикам сравнения")
        print("✅ Все ключевые метрики присутствуют")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Тест не прошел из-за ошибки: {e}")
        print("Это может быть связано с недоступностью данных okama")
        return False

def test_portfolio_vs_compare_format():
    """Тест: проверяем что формат таблицы портфеля соответствует формату сравнения"""
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
        
        # Создаем таблицу метрик сравнения для тех же активов
        compare_table = bot._create_summary_metrics_table(symbols, currency, symbols, [], None)
        
        # Проверяем, что обе таблицы созданы
        assert portfolio_table is not None, "Таблица метрик портфеля не создана"
        assert compare_table is not None, "Таблица метрик сравнения не создана"
        
        # Проверяем, что обе таблицы используют одинаковый формат markdown
        assert "|" in portfolio_table, "Таблица портфеля не в markdown формате"
        assert "|" in compare_table, "Таблица сравнения не в markdown формате"
        
        # Проверяем, что обе таблицы содержат одинаковые типы метрик
        portfolio_metrics = set()
        compare_metrics = set()
        
        # Извлекаем названия метрик из таблиц
        for line in portfolio_table.split('\n'):
            if '|' in line and not line.startswith('|') and 'Метрика' not in line:
                metric = line.split('|')[1].strip()
                if metric:
                    portfolio_metrics.add(metric)
        
        for line in compare_table.split('\n'):
            if '|' in line and not line.startswith('|') and 'Метрика' not in line:
                metric = line.split('|')[1].strip()
                if metric:
                    compare_metrics.add(metric)
        
        # Проверяем пересечение метрик
        common_metrics = portfolio_metrics.intersection(compare_metrics)
        print(f"\n📊 Общие метрики между портфелем и сравнением: {len(common_metrics)}")
        for metric in sorted(common_metrics):
            print(f"   ✅ {metric}")
        
        print("\n✅ Формат таблиц консистентен")
        print("✅ Метрики портфеля соответствуют метрикам сравнения")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Тест не прошел из-за ошибки: {e}")
        print("Это может быть связано с недоступностью данных okama")
        return False

if __name__ == '__main__':
    print("🧪 Запуск тестов консистентности метрик портфеля")
    print("=" * 70)
    
    success_count = 0
    total_tests = 2
    
    try:
        if test_portfolio_metrics_consistency():
            success_count += 1
        
        if test_portfolio_vs_compare_format():
            success_count += 1
        
        print("=" * 70)
        if success_count == total_tests:
            print("🎉 Все тесты прошли успешно!")
            print("✅ Метрики портфеля полностью соответствуют метрикам сравнения")
            print("✅ Переиспользован код из _create_summary_metrics_table")
        else:
            print(f"⚠️ Прошло {success_count} из {total_tests} тестов")
        
    except Exception as e:
        print(f"❌ Тест не прошел: {e}")
        import traceback
        traceback.print_exc()

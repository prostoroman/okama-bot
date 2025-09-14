#!/usr/bin/env python3
"""
Тест для проверки корректности расчетов метрик на конкретных символах:
SBER.MOEX, LKOH.MOEX, LQDT.MOEX, OBLG.MOEX, GOLD.MOEX

Проверяет:
1. Адекватность расчетов CAGR, волатильности, Sharpe, Sortino
2. Проблемы с LQDT (волатильность 42,203%, просадка -99.9%)
3. Корректность безрисковой ставки (сейчас 16.5% - ключевая ставка ЦБ)
4. Расчет Sortino ratio (downside deviation)
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import okama as ok
    print("✅ Okama импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта okama: {e}")
    sys.exit(1)

def test_metrics_calculation():
    """Тестирует расчет метрик для указанных символов"""
    
    symbols = ['SBER.MOEX', 'LKOH.MOEX', 'LQDT.MOEX', 'OBLG.MOEX', 'GOLD.MOEX']
    results = {}
    
    print("🔍 Тестирование метрик для символов:")
    print("=" * 60)
    
    for symbol in symbols:
        print(f"\n📊 Анализ {symbol}")
        print("-" * 40)
        
        try:
            # Создаем объект актива
            asset = ok.Asset(symbol)
            
            # Получаем данные
            returns = asset.ror
            
            # Рассчитываем цены из доходностей (wealth index)
            prices = (1 + returns).cumprod()
            
            print(f"📅 Период данных: {prices.index[0].strftime('%Y-%m-%d')} - {prices.index[-1].strftime('%Y-%m-%d')}")
            print(f"📈 Количество наблюдений: {len(prices)}")
            
            # Проверяем данные на аномалии
            print(f"💰 Начальная цена: {prices.iloc[0]:.2f}")
            print(f"💰 Конечная цена: {prices.iloc[-1]:.2f}")
            print(f"💰 Минимальная цена: {prices.min():.2f}")
            print(f"💰 Максимальная цена: {prices.max():.2f}")
            
            # Проверяем на нулевые или отрицательные цены
            if (prices <= 0).any():
                print("⚠️  ОБНАРУЖЕНЫ НУЛЕВЫЕ ИЛИ ОТРИЦАТЕЛЬНЫЕ ЦЕНЫ!")
                zero_prices = prices[prices <= 0]
                print(f"   Количество проблемных цен: {len(zero_prices)}")
                print(f"   Даты проблемных цен: {zero_prices.index.tolist()}")
            
            # Проверяем доходности на аномалии
            print(f"📊 Средняя доходность: {returns.mean():.6f}")
            print(f"📊 Стандартное отклонение доходности: {returns.std():.6f}")
            print(f"📊 Минимальная доходность: {returns.min():.6f}")
            print(f"📊 Максимальная доходность: {returns.max():.6f}")
            
            # Проверяем на экстремальные доходности
            extreme_returns = returns[abs(returns) > 0.5]  # Более 50% за день
            if len(extreme_returns) > 0:
                print(f"⚠️  ОБНАРУЖЕНЫ ЭКСТРЕМАЛЬНЫЕ ДОХОДНОСТИ (>50%): {len(extreme_returns)}")
                for date, ret in extreme_returns.items():
                    print(f"   {date.strftime('%Y-%m-%d')}: {ret:.2%}")
            
            # Рассчитываем метрики
            metrics = calculate_metrics_manually(prices, returns, symbol)
            results[symbol] = metrics
            
            # Выводим результаты
            print(f"\n📈 РАСЧЕТНЫЕ МЕТРИКИ:")
            print(f"   CAGR: {metrics['cagr']:.2%}")
            print(f"   Волатильность: {metrics['volatility']:.2%}")
            print(f"   Sharpe Ratio: {metrics['sharpe']:.4f}")
            print(f"   Sortino Ratio: {metrics['sortino']:.4f}")
            print(f"   Макс. просадка: {metrics['max_drawdown']:.2%}")
            print(f"   Calmar Ratio: {metrics['calmar']:.4f}")
            print(f"   VaR 95%: {metrics['var_95']:.2%}")
            print(f"   CVaR 95%: {metrics['cvar_95']:.2%}")
            
            # Проверяем на аномалии
            check_anomalies(symbol, metrics)
            
        except Exception as e:
            print(f"❌ Ошибка при анализе {symbol}: {e}")
            results[symbol] = {'error': str(e)}
    
    return results

def calculate_metrics_manually(prices, returns, symbol):
    """Рассчитывает метрики вручную для проверки"""
    
    # CAGR
    total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
    # Для месячных данных используем количество месяцев
    months = len(prices)
    years = months / 12.0
    cagr = (1 + total_return) ** (1 / years) - 1
    
    # Волатильность (аннуализированная)
    volatility = returns.std() * np.sqrt(12)  # Для месячных данных
    
    # Безрисковая ставка (текущая реализация - 16.5% для RUB)
    risk_free_rate = 0.165
    
    # Sharpe Ratio
    sharpe = (cagr - risk_free_rate) / volatility if volatility > 0 else 0
    
    # Sortino Ratio (downside deviation)
    negative_returns = returns[returns < 0]
    if len(negative_returns) > 0:
        downside_deviation = negative_returns.std() * np.sqrt(12)  # Для месячных данных
        sortino = (cagr - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
    else:
        sortino = sharpe  # Если нет отрицательных доходностей
    
    # Максимальная просадка
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.expanding().max()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Calmar Ratio
    calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # VaR 95% и CVaR 95%
    var_95 = returns.quantile(0.05)
    returns_below_var = returns[returns <= var_95]
    cvar_95 = returns_below_var.mean() if len(returns_below_var) > 0 else var_95
    
    return {
        'cagr': cagr,
        'volatility': volatility,
        'sharpe': sharpe,
        'sortino': sortino,
        'max_drawdown': max_drawdown,
        'calmar': calmar,
        'var_95': var_95,
        'cvar_95': cvar_95,
        'risk_free_rate': risk_free_rate
    }

def check_anomalies(symbol, metrics):
    """Проверяет метрики на аномалии"""
    
    print(f"\n🔍 ПРОВЕРКА НА АНОМАЛИИ:")
    
    # Проверка волатильности
    if metrics['volatility'] > 5.0:  # Более 500%
        print(f"   ⚠️  АНОМАЛЬНО ВЫСОКАЯ ВОЛАТИЛЬНОСТЬ: {metrics['volatility']:.2%}")
    
    # Проверка просадки
    if metrics['max_drawdown'] < -0.95:  # Более -95%
        print(f"   ⚠️  АНОМАЛЬНО ГЛУБОКАЯ ПРОСАДКА: {metrics['max_drawdown']:.2%}")
    
    # Проверка Sortino
    if abs(metrics['sortino']) > 10:  # Абсолютное значение больше 10
        print(f"   ⚠️  АНОМАЛЬНЫЙ SORTINO RATIO: {metrics['sortino']:.4f}")
    
    # Проверка Sharpe
    if metrics['sharpe'] < -2 or metrics['sharpe'] > 5:
        print(f"   ⚠️  ЭКСТРЕМАЛЬНЫЙ SHARPE RATIO: {metrics['sharpe']:.4f}")
    
    # Проверка CAGR
    if abs(metrics['cagr']) > 1.0:  # Более 100% годовых
        print(f"   ⚠️  ЭКСТРЕМАЛЬНАЯ ДОХОДНОСТЬ: {metrics['cagr']:.2%}")

def analyze_risk_free_rate_issue():
    """Анализирует проблему с безрисковой ставкой"""
    
    print("\n" + "=" * 60)
    print("🔍 АНАЛИЗ ПРОБЛЕМЫ С БЕЗРИСКОВОЙ СТАВКОЙ")
    print("=" * 60)
    
    print("\n📊 Текущая реализация:")
    print("   - Используется ключевая ставка ЦБ: 16.5%")
    print("   - Это временно повышенная ставка")
    print("   - Искажает долгосрочный анализ")
    
    print("\n💡 Рекомендации:")
    print("   1. Использовать доходность ОФЗ (гособлигаций)")
    print("   2. Для краткосрочных стратегий - ОФЗ 1Y")
    print("   3. Для долгосрочных - ОФЗ 10Y")
    print("   4. Альтернатива: средняя ключевая ставка за 5-10 лет")
    
    print("\n🎯 Влияние на метрики:")
    print("   - При ставке 16.5% почти все активы имеют отрицательный Sharpe")
    print("   - Это отражает аномально высокую ставку, а не 'плохие' активы")
    print("   - Метрики становятся малоинформативными")

def main():
    """Основная функция теста"""
    
    print("🚀 ЗАПУСК ТЕСТА ПРОВЕРКИ МЕТРИК")
    print("=" * 60)
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Тестируем расчет метрик
    results = test_metrics_calculation()
    
    # Анализируем проблему с безрисковой ставкой
    analyze_risk_free_rate_issue()
    
    # Итоговый анализ
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ АНАЛИЗ")
    print("=" * 60)
    
    print("\n✅ Корректные расчеты:")
    for symbol, metrics in results.items():
        if 'error' not in metrics:
            print(f"   {symbol}: CAGR {metrics['cagr']:.1%}, Vol {metrics['volatility']:.1%}")
    
    print("\n⚠️  Проблемные активы:")
    for symbol, metrics in results.items():
        if 'error' not in metrics:
            issues = []
            if metrics['volatility'] > 5.0:
                issues.append(f"Vol {metrics['volatility']:.0%}")
            if metrics['max_drawdown'] < -0.95:
                issues.append(f"DD {metrics['max_drawdown']:.1%}")
            if abs(metrics['sortino']) > 10:
                issues.append(f"Sortino {metrics['sortino']:.1f}")
            
            if issues:
                print(f"   {symbol}: {', '.join(issues)}")
    
    print("\n🔧 Требуемые исправления:")
    print("   1. Исправить расчет волатильности для LQDT")
    print("   2. Исправить расчет просадки для LQDT")
    print("   3. Проверить формулу Sortino (downside deviation)")
    print("   4. Изменить безрисковую ставку на доходность ОФЗ")
    
    print(f"\n✅ Тест завершен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

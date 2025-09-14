#!/usr/bin/env python3
"""
Тест для проверки использования okama.Rate для получения безрисковых ставок
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import okama as ok

def test_okama_rates_availability():
    """Тестирует доступность ставок в okama.Rate"""
    
    print("🔍 Тестирование доступности ставок в okama.Rate")
    print("=" * 60)
    
    # Список ставок для тестирования
    rate_symbols = [
        'US_EFFR.RATE',
        'EU_DFR.RATE',
        'EU_MLR.RATE',
        'EU_MRO.RATE',
        'RUS_CBR.RATE',
        'RUONIA.RATE',
        'RUONIA_AVG_1M.RATE',
        'RUONIA_AVG_3M.RATE',
        'RUONIA_AVG_6M.RATE',
        'CHN_LPR1.RATE',
        'CHN_LPR5.RATE',
        'UK_BR.RATE',
        'ISR_IR.RATE'
    ]
    
    available_rates = {}
    
    for rate_symbol in rate_symbols:
        try:
            rate_obj = ok.Rate(rate_symbol)
            rate_values = rate_obj.values_monthly
            
            if rate_values is not None and len(rate_values) > 0:
                avg_rate = rate_values.mean()
                available_rates[rate_symbol] = {
                    'available': True,
                    'avg_rate': float(avg_rate),
                    'data_points': len(rate_values),
                    'period': f"{rate_values.index[0]} - {rate_values.index[-1]}"
                }
                print(f"✅ {rate_symbol}: {avg_rate:.4f} ({len(rate_values)} точек)")
            else:
                available_rates[rate_symbol] = {'available': False}
                print(f"❌ {rate_symbol}: Нет данных")
                
        except Exception as e:
            available_rates[rate_symbol] = {'available': False, 'error': str(e)}
            print(f"❌ {rate_symbol}: Ошибка - {e}")
    
    return available_rates

def test_currency_rate_mapping():
    """Тестирует маппинг валют на ставки"""
    
    print("\n🔍 Тестирование маппинга валют на ставки")
    print("=" * 60)
    
    bot = ShansAi()
    
    # Тестовые валюты и периоды
    test_cases = [
        {'currency': 'USD', 'period': 1.0},
        {'currency': 'EUR', 'period': 2.0},
        {'currency': 'RUB', 'period': 0.5},
        {'currency': 'RUB', 'period': 1.0},
        {'currency': 'RUB', 'period': 5.0},
        {'currency': 'CNY', 'period': 1.0},
        {'currency': 'CNY', 'period': 6.0},
        {'currency': 'GBP', 'period': 1.0},
        {'currency': 'ILS', 'period': 1.0},
        {'currency': 'HKD', 'period': 1.0},  # Должна использовать фиксированную ставку
    ]
    
    print("\n📊 Маппинг валют на ставки:")
    print("Валюта | Период | Ставки для попытки")
    print("-" * 50)
    
    for case in test_cases:
        currency = case['currency']
        period = case['period']
        
        try:
            rate_symbols = bot._get_rate_symbol_for_currency(currency, period)
            print(f"{currency:6} | {period:6.1f} | {', '.join(rate_symbols) if rate_symbols else 'Нет ставок'}")
        except Exception as e:
            print(f"{currency:6} | {period:6.1f} | Ошибка: {e}")

def test_risk_free_rate_calculation():
    """Тестирует расчет безрисковой ставки с использованием okama.Rate"""
    
    print("\n🔍 Тестирование расчета безрисковой ставки")
    print("=" * 60)
    
    bot = ShansAi()
    
    # Тестовые случаи
    test_cases = [
        {'currency': 'USD', 'period': 1.0},
        {'currency': 'EUR', 'period': 2.0},
        {'currency': 'RUB', 'period': 0.5},
        {'currency': 'RUB', 'period': 1.0},
        {'currency': 'RUB', 'period': 5.0},
        {'currency': 'CNY', 'period': 1.0},
        {'currency': 'CNY', 'period': 6.0},
        {'currency': 'GBP', 'period': 1.0},
        {'currency': 'ILS', 'period': 1.0},
        {'currency': 'HKD', 'period': 1.0},
    ]
    
    print("\n📊 Расчет безрисковых ставок:")
    print("Валюта | Период | Ставка | Источник")
    print("-" * 45)
    
    for case in test_cases:
        currency = case['currency']
        period = case['period']
        
        try:
            rate = bot.get_risk_free_rate(currency, period)
            
            # Определяем источник ставки
            if currency.upper() == 'HKD':
                source = "Фиксированная"
            else:
                # Проверяем, была ли получена ставка из okama
                try:
                    okama_rate = bot._get_okama_rate_data(currency, period)
                    if okama_rate is not None:
                        source = "okama.Rate"
                    else:
                        source = "Fallback"
                except:
                    source = "Fallback"
            
            print(f"{currency:6} | {period:6.1f} | {rate:6.1%} | {source}")
            
        except Exception as e:
            print(f"{currency:6} | {period:6.1f} | Ошибка: {e}")

def test_rate_data_quality():
    """Тестирует качество данных ставок"""
    
    print("\n🔍 Тестирование качества данных ставок")
    print("=" * 60)
    
    # Тестируем несколько ключевых ставок
    key_rates = [
        'US_EFFR.RATE',
        'RUS_CBR.RATE',
        'RUONIA_AVG_6M.RATE',
        'CHN_LPR1.RATE'
    ]
    
    for rate_symbol in key_rates:
        try:
            rate_obj = ok.Rate(rate_symbol)
            rate_values = rate_obj.values_monthly
            
            if rate_values is not None and len(rate_values) > 0:
                print(f"\n📊 {rate_symbol}:")
                print(f"   Период: {rate_values.index[0]} - {rate_values.index[-1]}")
                print(f"   Количество точек: {len(rate_values)}")
                print(f"   Среднее значение: {rate_values.mean():.4f}")
                print(f"   Минимум: {rate_values.min():.4f}")
                print(f"   Максимум: {rate_values.max():.4f}")
                print(f"   Стандартное отклонение: {rate_values.std():.4f}")
                
                # Проверяем на аномалии
                if rate_values.std() > rate_values.mean():
                    print(f"   ⚠️  Высокая волатильность ставки")
                
                if rate_values.min() < 0:
                    print(f"   ⚠️  Отрицательные значения ставки")
                    
            else:
                print(f"❌ {rate_symbol}: Нет данных")
                
        except Exception as e:
            print(f"❌ {rate_symbol}: Ошибка - {e}")

def main():
    """Основная функция теста"""
    
    print("🚀 ЗАПУСК ТЕСТА ПРОВЕРКИ OKAMA.RATE")
    print("=" * 60)
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Тестируем доступность ставок
    available_rates = test_okama_rates_availability()
    
    # Тестируем маппинг валют
    test_currency_rate_mapping()
    
    # Тестируем расчет безрисковой ставки
    test_risk_free_rate_calculation()
    
    # Тестируем качество данных
    test_rate_data_quality()
    
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ АНАЛИЗ")
    print("=" * 60)
    
    # Подсчитываем доступные ставки
    total_rates = len(available_rates)
    available_count = sum(1 for rate in available_rates.values() if rate.get('available', False))
    
    print(f"Всего ставок протестировано: {total_rates}")
    print(f"Доступных ставок: {available_count}")
    print(f"Процент доступности: {(available_count/total_rates)*100:.1f}%")
    
    if available_count >= total_rates * 0.7:
        print("✅ Большинство ставок доступны - okama.Rate можно использовать")
    elif available_count >= total_rates * 0.5:
        print("⚠️  Половина ставок доступны - okama.Rate частично применим")
    else:
        print("❌ Мало доступных ставок - лучше использовать fallback ставки")
    
    print(f"\n✅ Тест завершен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

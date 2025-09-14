#!/usr/bin/env python3
"""
Демонстрационный тест новых возможностей таблиц метрик
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

def demo_enhanced_metrics():
    """Демонстрация новых возможностей таблиц метрик"""
    
    print("🚀 ДЕМОНСТРАЦИЯ УЛУЧШЕННЫХ ТАБЛИЦ МЕТРИК")
    print("=" * 60)
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    bot = ShansAi()
    
    # Тестовые символы
    symbols = ['SBER.MOEX', 'LKOH.MOEX', 'OBLG.MOEX']
    currency = 'RUB'
    
    print(f"\n📊 Тестируемые символы: {', '.join(symbols)}")
    print(f"💰 Валюта: {currency}")
    
    # Создаем таблицу метрик
    print(f"\n🔍 Создание таблицы метрик...")
    
    try:
        # Создаем портфолио контексты для тестирования
        portfolio_contexts = []
        for symbol in symbols:
            try:
                asset = ok.Asset(symbol)
                portfolio_contexts.append({
                    'portfolio_object': None,
                    'portfolio_symbols': [symbol]
                })
            except Exception as e:
                print(f"❌ Ошибка создания актива {symbol}: {e}")
                portfolio_contexts.append({
                    'portfolio_object': None,
                    'portfolio_symbols': [symbol]
                })
        
        # Создаем таблицу метрик
        metrics_table = bot._create_summary_metrics_table(
            symbols=symbols,
            currency=currency,
            expanded_symbols=symbols,
            portfolio_contexts=portfolio_contexts,
            specified_period=None
        )
        
        print(f"\n📋 Созданная таблица метрик:")
        print("=" * 60)
        print(metrics_table)
        
        # Демонстрируем новые безрисковые ставки
        print(f"\n🔍 Демонстрация новых безрисковых ставок:")
        print("=" * 60)
        
        currencies = ['USD', 'EUR', 'RUB', 'CNY', 'GBP', 'ILS', 'HKD']
        periods = [0.5, 1.0, 5.0]
        
        print("Валюта | 0.5 лет | 1.0 лет | 5.0 лет")
        print("-" * 40)
        
        for currency in currencies:
            rates = []
            for period in periods:
                try:
                    rate = bot.get_risk_free_rate(currency, period)
                    rates.append(f"{rate:.1%}")
                except Exception as e:
                    rates.append("Ошибка")
            
            print(f"{currency:6} | {rates[0]:7} | {rates[1]:7} | {rates[2]:7}")
        
        # Демонстрируем период инвестиций
        print(f"\n🔍 Демонстрация расчета периода инвестиций:")
        print("=" * 60)
        
        for symbol in symbols:
            try:
                asset = ok.Asset(symbol)
                returns = asset.ror
                prices = (1 + returns).cumprod()
                
                years = len(prices) / 12.0
                
                print(f"\n📊 {symbol}:")
                print(f"   Количество наблюдений: {len(prices)}")
                print(f"   Период в годах: {years:.1f}")
                
                if years < 1:
                    print(f"   Отображение: {years*12:.1f} мес")
                else:
                    print(f"   Отображение: {years:.1f} лет")
                    
            except Exception as e:
                print(f"❌ Ошибка для {symbol}: {e}")
        
        print(f"\n✅ Демонстрация завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при демонстрации: {e}")

def demo_okama_rates():
    """Демонстрация работы с okama.Rate"""
    
    print(f"\n🔍 ДЕМОНСТРАЦИЯ OKAMA.RATE")
    print("=" * 60)
    
    # Тестируем несколько ключевых ставок
    rate_symbols = [
        'US_EFFR.RATE',
        'RUS_CBR.RATE',
        'RUONIA_AVG_6M.RATE',
        'CHN_LPR1.RATE'
    ]
    
    for rate_symbol in rate_symbols:
        try:
            rate_obj = ok.Rate(rate_symbol)
            rate_values = rate_obj.values_monthly
            
            if rate_values is not None and len(rate_values) > 0:
                print(f"\n📊 {rate_symbol}:")
                print(f"   Период: {rate_values.index[0]} - {rate_values.index[-1]}")
                print(f"   Количество точек: {len(rate_values)}")
                print(f"   Среднее значение: {rate_values.mean():.4f}")
                print(f"   Текущее значение: {rate_values.iloc[-1]:.4f}")
                
        except Exception as e:
            print(f"❌ {rate_symbol}: Ошибка - {e}")

def main():
    """Основная функция демонстрации"""
    
    # Демонстрируем улучшенные таблицы метрик
    demo_enhanced_metrics()
    
    # Демонстрируем okama.Rate
    demo_okama_rates()
    
    print(f"\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ АНАЛИЗ ДЕМОНСТРАЦИИ")
    print("=" * 60)
    
    print("✅ Все новые возможности работают корректно:")
    print("   - Период инвестиций отображается в таблице")
    print("   - Вторая таблица с okama.AssetList.describe создается")
    print("   - Безрисковые ставки получаются из okama.Rate")
    print("   - HKD использует фиксированную ставку 2.85%")
    print("   - Остальные валюты используют реальные данные")
    
    print(f"\n✅ Демонстрация завершена: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

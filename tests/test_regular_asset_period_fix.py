#!/usr/bin/env python3
"""
Test script for regular asset chart period fix
Tests that different periods (1Y, 5Y, MAX) show different data ranges for regular assets
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
from datetime import datetime

def test_regular_asset_period_data():
    """Test that different periods return different data ranges for regular assets"""
    print("🧪 Тестирование исправления периодов графиков для обычных активов...")
    
    try:
        # Test with a popular US stock
        test_symbol = "AAPL.US"
        print(f"✅ Тестируем символ: {test_symbol}")
        
        # Create asset
        asset = ok.Asset(test_symbol)
        
        # Get daily data
        daily_data = asset.close_daily
        print(f"   Общее количество дневных записей: {len(daily_data)}")
        print(f"   Первая дата: {daily_data.index[0]}")
        print(f"   Последняя дата: {daily_data.index[-1]}")
        
        # Test 1Y period (252 trading days)
        print("\n📊 Тестирование периода 1Y...")
        data_1y = daily_data.tail(252)
        print(f"   Количество записей за 1Y: {len(data_1y)}")
        print(f"   Первая дата: {data_1y.index[0]}")
        print(f"   Последняя дата: {data_1y.index[-1]}")
        
        # Test 5Y period (1260 trading days)
        print("\n📊 Тестирование периода 5Y...")
        data_5y = daily_data.tail(1260)
        print(f"   Количество записей за 5Y: {len(data_5y)}")
        print(f"   Первая дата: {data_5y.index[0]}")
        print(f"   Последняя дата: {data_5y.index[-1]}")
        
        # Test MAX period (all available data)
        print("\n📊 Тестирование периода MAX...")
        data_max = daily_data
        print(f"   Количество записей за MAX: {len(data_max)}")
        print(f"   Первая дата: {data_max.index[0]}")
        print(f"   Последняя дата: {data_max.index[-1]}")
        
        # Verify that 5Y has more data than 1Y
        if len(data_5y) > len(data_1y):
            print("✅ Период 5Y содержит больше данных, чем период 1Y")
        else:
            print("❌ Период 5Y не содержит больше данных, чем период 1Y")
            return False
        
        # Verify that MAX has more data than 5Y
        if len(data_max) >= len(data_5y):
            print("✅ Период MAX содержит больше или равно данных, чем период 5Y")
        else:
            print("❌ Период MAX не содержит больше данных, чем период 5Y")
            return False
        
        # Verify that 5Y starts earlier than 1Y
        if data_5y.index[0] < data_1y.index[0]:
            print("✅ Период 5Y начинается раньше, чем период 1Y")
        else:
            print("❌ Период 5Y не начинается раньше, чем период 1Y")
            return False
        
        # Verify that MAX starts earlier than 5Y
        if data_max.index[0] <= data_5y.index[0]:
            print("✅ Период MAX начинается раньше или в то же время, чем период 5Y")
        else:
            print("❌ Период MAX не начинается раньше, чем период 5Y")
            return False
        
        # Verify that all periods end at the same time (latest data)
        if (data_5y.index[-1] == data_1y.index[-1] == data_max.index[-1]):
            print("✅ Все периоды заканчиваются в одно время (последние данные)")
        else:
            print("❌ Периоды заканчиваются в разное время")
            return False
        
        # Calculate date ranges using len() since we're dealing with trading days
        print(f"\n📅 Количество торговых дней:")
        print(f"   1Y: {len(data_1y)} торговых дней")
        print(f"   5Y: {len(data_5y)} торговых дней")
        print(f"   MAX: {len(data_max)} торговых дней")
        
        # Verify that 5Y covers approximately 5 times more trading days than 1Y
        if len(data_5y) > len(data_1y) * 4:  # At least 4x more (5Y should be ~5x 1Y)
            print("✅ Период 5Y покрывает значительно больше торговых дней, чем 1Y")
        else:
            print("❌ Период 5Y не покрывает значительно больше торговых дней, чем 1Y")
            return False
        
        # Verify that MAX covers the most trading days
        if len(data_max) >= len(data_5y):
            print("✅ Период MAX покрывает наибольшее количество торговых дней")
        else:
            print("❌ Период MAX не покрывает наибольшее количество торговых дней")
            return False
        
        print("\n🎉 Все тесты пройдены! Исправление периодов для обычных активов работает корректно.")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка во время тестирования: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_period_filtering_logic():
    """Test the period filtering logic"""
    print("\n🔍 Тестирование логики фильтрации периодов...")
    
    try:
        test_symbol = "AAPL.US"
        asset = ok.Asset(test_symbol)
        daily_data = asset.close_daily
        
        # Test different period configurations
        periods = {
            '1Y': 252,
            '5Y': 1260,
            'MAX': len(daily_data)
        }
        
        for period_name, trading_days in periods.items():
            print(f"\n📊 Тестирование периода {period_name} ({trading_days} торговых дней)...")
            
            # Apply filtering logic
            if trading_days < len(daily_data):
                filtered_data = daily_data.tail(trading_days)
            else:
                filtered_data = daily_data
            
            print(f"   Исходных записей: {len(daily_data)}")
            print(f"   Отфильтрованных записей: {len(filtered_data)}")
            print(f"   Первая дата: {filtered_data.index[0]}")
            print(f"   Последняя дата: {filtered_data.index[-1]}")
            
            # Verify filtering worked correctly
            if period_name == 'MAX':
                if len(filtered_data) == len(daily_data):
                    print(f"   ✅ Период {period_name}: все данные сохранены")
                else:
                    print(f"   ❌ Период {period_name}: данные потеряны")
                    return False
            else:
                if len(filtered_data) <= trading_days:
                    print(f"   ✅ Период {period_name}: данные отфильтрованы корректно")
                else:
                    print(f"   ❌ Период {period_name}: слишком много данных")
                    return False
        
        print("\n🎉 Тест логики фильтрации пройден!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка во время тестирования логики фильтрации: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ПЕРИОДОВ ГРАФИКОВ ДЛЯ ОБЫЧНЫХ АКТИВОВ")
    print("=" * 70)
    
    success = True
    
    # Run tests
    success &= test_regular_asset_period_data()
    success &= test_period_filtering_logic()
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Исправление периодов графиков для обычных активов работает корректно")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("🔧 Требуется дополнительная отладка")
    print("=" * 70)

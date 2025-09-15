#!/usr/bin/env python3
"""
Test script for chart period fix
Tests that different periods (1Y, 5Y) show different data ranges
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tushare_service import TushareService
import pandas as pd
from datetime import datetime

def test_chart_period_data():
    """Test that different periods return different data ranges"""
    print("🧪 Тестирование исправления периодов графиков...")
    
    try:
        # Initialize Tushare service
        tushare_service = TushareService()
        
        # Test with a popular Chinese stock
        test_symbol = "000001.SZ"  # Ping An Bank
        symbol_info = tushare_service.get_symbol_info(test_symbol)
        
        if 'error' in symbol_info:
            print(f"❌ Ошибка получения информации о символе {test_symbol}: {symbol_info['error']}")
            return False
        
        ts_code = symbol_info['ts_code']
        print(f"✅ Тестируем символ: {test_symbol} (ts_code: {ts_code})")
        
        # Test 1Y period
        print("\n📊 Тестирование периода 1Y...")
        data_1y = tushare_service.get_daily_data_by_days(ts_code, 252)
        
        if data_1y.empty:
            print("❌ Нет данных для периода 1Y")
            return False
        
        print(f"   Количество записей за 1Y: {len(data_1y)}")
        print(f"   Первая дата: {data_1y['trade_date'].min()}")
        print(f"   Последняя дата: {data_1y['trade_date'].max()}")
        
        # Test 5Y period
        print("\n📊 Тестирование периода 5Y...")
        data_5y = tushare_service.get_daily_data_by_days(ts_code, 1260)
        
        if data_5y.empty:
            print("❌ Нет данных для периода 5Y")
            return False
        
        print(f"   Количество записей за 5Y: {len(data_5y)}")
        print(f"   Первая дата: {data_5y['trade_date'].min()}")
        print(f"   Последняя дата: {data_5y['trade_date'].max()}")
        
        # Verify that 5Y has more data than 1Y
        if len(data_5y) > len(data_1y):
            print("✅ Период 5Y содержит больше данных, чем период 1Y")
        else:
            print("❌ Период 5Y не содержит больше данных, чем период 1Y")
            return False
        
        # Verify that 5Y starts earlier than 1Y
        if data_5y['trade_date'].min() < data_1y['trade_date'].min():
            print("✅ Период 5Y начинается раньше, чем период 1Y")
        else:
            print("❌ Период 5Y не начинается раньше, чем период 1Y")
            return False
        
        # Verify that both periods end at the same time (latest data)
        if data_5y['trade_date'].max() == data_1y['trade_date'].max():
            print("✅ Оба периода заканчиваются в одно время (последние данные)")
        else:
            print("❌ Периоды заканчиваются в разное время")
            return False
        
        # Calculate date ranges
        date_range_1y = (data_1y['trade_date'].max() - data_1y['trade_date'].min()).days
        date_range_5y = (data_5y['trade_date'].max() - data_5y['trade_date'].min()).days
        
        print(f"\n📅 Диапазон дат:")
        print(f"   1Y: {date_range_1y} календарных дней")
        print(f"   5Y: {date_range_5y} календарных дней")
        
        # Verify that 5Y covers approximately 5 times more calendar days
        if date_range_5y > date_range_1y * 3:  # At least 3x more (allowing for weekends/holidays)
            print("✅ Период 5Y покрывает значительно больший диапазон дат")
        else:
            print("❌ Период 5Y не покрывает значительно больший диапазон дат")
            return False
        
        print("\n🎉 Все тесты пройдены! Исправление периодов работает корректно.")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка во время тестирования: {e}")
        return False

def test_period_consistency():
    """Test that the same period returns consistent results"""
    print("\n🔄 Тестирование консистентности периодов...")
    
    try:
        tushare_service = TushareService()
        test_symbol = "000001.SZ"
        symbol_info = tushare_service.get_symbol_info(test_symbol)
        
        if 'error' in symbol_info:
            print(f"❌ Ошибка получения информации о символе: {symbol_info['error']}")
            return False
        
        ts_code = symbol_info['ts_code']
        
        # Get 1Y data twice
        data_1y_1 = tushare_service.get_daily_data_by_days(ts_code, 252)
        data_1y_2 = tushare_service.get_daily_data_by_days(ts_code, 252)
        
        # Check if both calls return the same number of records
        if len(data_1y_1) == len(data_1y_2):
            print("✅ Консистентность количества записей для периода 1Y")
        else:
            print(f"❌ Несоответствие количества записей: {len(data_1y_1)} vs {len(data_1y_2)}")
            return False
        
        # Check if both calls return the same date range
        if (data_1y_1['trade_date'].min() == data_1y_2['trade_date'].min() and 
            data_1y_1['trade_date'].max() == data_1y_2['trade_date'].max()):
            print("✅ Консистентность диапазона дат для периода 1Y")
        else:
            print("❌ Несоответствие диапазона дат для периода 1Y")
            return False
        
        print("🎉 Тест консистентности пройден!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка во время тестирования консистентности: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ ПЕРИОДОВ ГРАФИКОВ")
    print("=" * 60)
    
    success = True
    
    # Run tests
    success &= test_chart_period_data()
    success &= test_period_consistency()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Исправление периодов графиков работает корректно")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("🔧 Требуется дополнительная отладка")
    print("=" * 60)

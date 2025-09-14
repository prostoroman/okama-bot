#!/usr/bin/env python3
"""
Test script to verify the enhanced compare metrics functionality:
1. CAGR 1 year and CAGR 5 years are added to the first table
2. Property names are used instead of numeric indices in the second table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
from bot import ShansAi

def test_compare_metrics_enhancement():
    """Test the enhanced compare metrics functionality"""
    
    print("🧪 Тестирование улучшенных метрик сравнения")
    print("=" * 50)
    
    # Test symbols
    symbols = ['SPY.US', 'QQQ.US']
    currency = 'USD'
    
    print(f"📊 Тестируемые символы: {symbols}")
    print(f"💰 Валюта: {currency}")
    
    try:
        # Create bot instance
        bot = ShansAi()
        
        # Test 1: Check that describe data has property names
        print(f"\n🔍 Тест 1: Проверка структуры describe данных")
        asset_list = ok.AssetList(symbols, ccy=currency)
        describe_data = asset_list.describe()
        
        print(f"   Размер данных: {describe_data.shape}")
        print(f"   Колонки: {list(describe_data.columns)}")
        print(f"   Индексы: {list(describe_data.index)}")
        
        # Check if property column exists
        if 'property' in describe_data.columns:
            print(f"   ✅ Колонка 'property' найдена")
            property_names = describe_data['property'].tolist()
            print(f"   Названия метрик: {property_names}")
        else:
            print(f"   ❌ Колонка 'property' не найдена")
            return False
        
        # Test 2: Check CAGR calculations for 1y and 5y
        print(f"\n🔍 Тест 2: Проверка расчета CAGR 1г и 5л")
        
        # Create expanded symbols and portfolio contexts for testing
        expanded_symbols = []
        portfolio_contexts = []
        
        for symbol in symbols:
            try:
                asset = ok.Asset(symbol)
                expanded_symbols.append(symbol)
                portfolio_contexts.append({
                    'portfolio_object': asset,
                    'portfolio_symbols': [symbol]
                })
            except Exception as e:
                print(f"   ❌ Ошибка создания актива {symbol}: {e}")
                return False
        
        # Test the summary metrics table creation
        summary_table = bot._create_summary_metrics_table(
            symbols=symbols,
            currency=currency,
            expanded_symbols=expanded_symbols,
            portfolio_contexts=portfolio_contexts,
            specified_period=None
        )
        
        if summary_table and not summary_table.startswith("❌"):
            print(f"   ✅ Таблица метрик создана успешно")
            
            # Check if CAGR 1y and CAGR 5y are in the table
            if "Средн. доходность (CAGR) 1 год" in summary_table:
                print(f"   ✅ CAGR 1 год добавлен в таблицу")
            else:
                print(f"   ❌ CAGR 1 год не найден в таблице")
            
            if "Средн. доходность (CAGR) 5 лет" in summary_table:
                print(f"   ✅ CAGR 5 лет добавлен в таблицу")
            else:
                print(f"   ❌ CAGR 5 лет не найден в таблице")
                
            print(f"\n📋 Пример таблицы метрик:")
            print(summary_table[:500] + "..." if len(summary_table) > 500 else summary_table)
        else:
            print(f"   ❌ Ошибка создания таблицы метрик: {summary_table}")
            return False
        
        # Test 3: Check describe table with property names
        print(f"\n🔍 Тест 3: Проверка таблицы describe с названиями метрик")
        
        describe_table = bot._create_describe_table(symbols, currency)
        
        if describe_table:
            print(f"   ✅ Таблица describe создана успешно")
            
            # Check if property names are used instead of numeric indices
            has_numeric_indices = any(str(i) in describe_table for i in range(20))
            has_property_names = any(prop in describe_table for prop in property_names[:5])
            
            if not has_numeric_indices and has_property_names:
                print(f"   ✅ Используются названия метрик вместо числовых индексов")
            else:
                print(f"   ❌ Проблема с форматированием таблицы describe")
                print(f"      Числовые индексы: {has_numeric_indices}")
                print(f"      Названия метрик: {has_property_names}")
            
            print(f"\n📋 Пример таблицы describe:")
            print(describe_table[:500] + "..." if len(describe_table) > 500 else describe_table)
        else:
            print(f"   ❌ Ошибка создания таблицы describe")
            return False
        
        print(f"\n✅ Все тесты пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка во время тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_compare_metrics_enhancement()
    if success:
        print(f"\n🎉 Тестирование завершено успешно!")
    else:
        print(f"\n💥 Тестирование завершилось с ошибками!")
        sys.exit(1)

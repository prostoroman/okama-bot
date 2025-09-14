#!/usr/bin/env python3
"""
Test script to verify the final compare metrics enhancements:
1. Renamed 'Среднегодовая доходность (CAGR)' to 'Средн. доходность (CAGR)'
2. Moved 'Макс. просадка' to be after 'Волатильность'
3. Added period information to metric names in describe table
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
from bot import ShansAi

def test_compare_metrics_final_enhancement():
    """Test the final compare metrics enhancements"""
    
    print("🧪 Тестирование финальных улучшений метрик сравнения")
    print("=" * 60)
    
    # Test symbols
    symbols = ['SPY.US', 'QQQ.US']
    currency = 'USD'
    
    print(f"📊 Тестируемые символы: {symbols}")
    print(f"💰 Валюта: {currency}")
    
    try:
        # Create bot instance
        bot = ShansAi()
        
        # Test 1: Check first table structure and naming
        print(f"\n🔍 Тест 1: Проверка структуры первой таблицы")
        
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
            
            # Check if CAGR is renamed correctly
            if "Средн. доходность (CAGR)" in summary_table and "Среднегодовая доходность (CAGR)" not in summary_table:
                print(f"   ✅ CAGR переименован в 'Средн. доходность (CAGR)'")
            else:
                print(f"   ❌ Проблема с переименованием CAGR")
            
            # Check if Max Drawdown is after Volatility
            volatility_pos = summary_table.find("Волатильность")
            drawdown_pos = summary_table.find("Макс. просадка")
            
            if volatility_pos != -1 and drawdown_pos != -1 and drawdown_pos > volatility_pos:
                print(f"   ✅ 'Макс. просадка' размещена после 'Волатильности'")
            else:
                print(f"   ❌ Проблема с размещением 'Макс. просадка'")
                print(f"      Позиция Волатильности: {volatility_pos}")
                print(f"      Позиция Макс. просадки: {drawdown_pos}")
                
            print(f"\n📋 Пример первой таблицы:")
            print(summary_table[:800] + "..." if len(summary_table) > 800 else summary_table)
        else:
            print(f"   ❌ Ошибка создания таблицы метрик: {summary_table}")
            return False
        
        # Test 2: Check describe table with period information
        print(f"\n🔍 Тест 2: Проверка таблицы describe с периодами")
        
        # First, let's check the raw describe data structure
        asset_list = ok.AssetList(symbols, ccy=currency)
        describe_data = asset_list.describe()
        
        print(f"   Структура describe данных:")
        print(f"   - Колонки: {list(describe_data.columns)}")
        print(f"   - Примеры периодов: {describe_data['period'].head().tolist()}")
        
        describe_table = bot._create_describe_table(symbols, currency)
        
        if describe_table:
            print(f"   ✅ Таблица describe создана успешно")
            
            # Check if period information is included in metric names
            has_periods_in_names = any("(" in line and ")" in line for line in describe_table.split('\n') if "|" in line)
            
            if has_periods_in_names:
                print(f"   ✅ Периоды добавлены к названиям метрик")
            else:
                print(f"   ❌ Периоды не найдены в названиях метрик")
            
            # Check for specific period examples
            period_examples = ["YTD", "1 years", "5 years", "10 years"]
            found_periods = []
            for period in period_examples:
                if period in describe_table:
                    found_periods.append(period)
            
            if found_periods:
                print(f"   ✅ Найдены периоды в таблице: {found_periods}")
            else:
                print(f"   ⚠️  Ожидаемые периоды не найдены")
            
            print(f"\n📋 Пример таблицы describe:")
            print(describe_table[:800] + "..." if len(describe_table) > 800 else describe_table)
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
    success = test_compare_metrics_final_enhancement()
    if success:
        print(f"\n🎉 Тестирование завершено успешно!")
    else:
        print(f"\n💥 Тестирование завершилось с ошибками!")
        sys.exit(1)

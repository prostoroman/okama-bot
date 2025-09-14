#!/usr/bin/env python3
"""
Тест для проверки структуры данных okama.AssetList.describe
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd

def test_describe_data_structure():
    """Тестирует структуру данных describe"""
    
    symbols = ['SBER.MOEX', 'LKOH.MOEX', 'LQDT.MOEX', 'OBLG.MOEX', 'GOLD.MOEX']
    currency = 'RUB'
    
    print("=== ТЕСТИРОВАНИЕ СТРУКТУРЫ ДАННЫХ DESCRIBE ===")
    
    try:
        # Создаем AssetList
        asset_list = ok.AssetList(symbols, ccy=currency)
        describe_data = asset_list.describe()
        
        print(f"Создан AssetList с символами: {symbols}")
        print(f"Валюта: {currency}")
        print(f"Размер describe_data: {describe_data.shape}")
        print(f"Колонки describe_data: {list(describe_data.columns)}")
        print(f"Индексы describe_data: {list(describe_data.index)}")
        
        print("\n=== СОДЕРЖИМОЕ DESCRIBE_DATA ===")
        print(describe_data)
        
        print("\n=== ПОИСК КЛЮЧЕВЫХ МЕТРИК ===")
        
        # Ищем ключевые метрики
        for idx in describe_data.index:
            property_name = describe_data.loc[idx, 'property']
            period = describe_data.loc[idx, 'period']
            
            print(f"Строка {idx}: property='{property_name}', period='{period}'")
            
            # Проверяем значения для каждого символа
            for symbol in symbols:
                if symbol in describe_data.columns:
                    value = describe_data.loc[idx, symbol]
                    print(f"  {symbol}: {value}")
            
            print()
        
        return describe_data
        
    except Exception as e:
        print(f"Ошибка при тестировании структуры данных: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Основная функция тестирования"""
    
    print("ТЕСТИРОВАНИЕ СТРУКТУРЫ ДАННЫХ OKAMA.ASSETLIST.DESCRIBE")
    print("=" * 60)
    
    describe_data = test_describe_data_structure()
    
    if describe_data is not None:
        print("\n=== ВЫВОДЫ ===")
        print("1. Проверена структура данных describe_data")
        print("2. Найдены ключевые метрики и их значения")
        print("3. Определен формат данных для извлечения метрик")

if __name__ == "__main__":
    main()

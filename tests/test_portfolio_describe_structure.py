#!/usr/bin/env python3
"""
Тест для проверки структуры данных okama.Portfolio.describe
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd

def test_portfolio_describe_structure():
    """Тестирует структуру данных portfolio.describe"""
    
    symbols = ['SBER.MOEX', 'LKOH.MOEX']
    weights = [0.6, 0.4]
    currency = 'RUB'
    
    print("=== ТЕСТИРОВАНИЕ СТРУКТУРЫ ДАННЫХ PORTFOLIO.DESCRIBE ===")
    
    try:
        # Создаем Portfolio
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
        describe_data = portfolio.describe()
        
        print(f"Создан Portfolio с символами: {symbols}")
        print(f"Веса: {weights}")
        print(f"Валюта: {currency}")
        print(f"Размер describe_data: {describe_data.shape}")
        print(f"Колонки describe_data: {list(describe_data.columns)}")
        print(f"Индексы describe_data: {list(describe_data.index)}")
        
        print("\n=== СОДЕРЖИМОЕ DESCRIBE_DATA ===")
        print(describe_data)
        
        print("\n=== ПОИСК КЛЮЧЕВЫХ МЕТРИК ===")
        
        # Ищем ключевые метрики
        for idx in describe_data.index:
            print(f"Строка {idx}:")
            for col in describe_data.columns:
                value = describe_data.loc[idx, col]
                print(f"  {col}: {value} (тип: {type(value)})")
            print()
        
        return describe_data
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    test_portfolio_describe_structure()

#!/usr/bin/env python3
"""
Тест консистентности Sharpe Ratio между кнопкой "Метрики" и AI-анализом
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
import asyncio
from bot import ShansAi

def test_sharpe_ratio_consistency():
    """Тестирует консистентность Sharpe Ratio между метриками и AI-анализом"""
    
    print("🔍 Тест консистентности Sharpe Ratio")
    print("=" * 50)
    
    # Создаем экземпляр бота
    bot = ShansAi()
    
    # Тестовые данные
    symbols = ['AAPL.US', 'TSLA.US']
    currency = 'USD'
    expanded_symbols = symbols
    portfolio_contexts = []
    user_id = 12345
    
    print(f"Тестируем символы: {symbols}")
    print(f"Валюта: {currency}")
    print()
    
    # 1. Создаем таблицу метрик (кнопка "Метрики")
    print("1. Создание таблицы метрик (кнопка 'Метрики')...")
    metrics_table = bot._create_summary_metrics_table(
        symbols=symbols,
        currency=currency,
        expanded_symbols=expanded_symbols,
        portfolio_contexts=portfolio_contexts,
        specified_period=None
    )
    
    # 2. Подготавливаем данные для AI-анализа
    print("2. Подготовка данных для AI-анализа...")
    
    async def prepare_ai_data():
        return await bot._prepare_data_for_analysis(
            symbols=symbols,
            currency=currency,
            expanded_symbols=expanded_symbols,
            portfolio_contexts=portfolio_contexts,
            user_id=user_id
        )
    
    data_info = asyncio.run(prepare_ai_data())
    ai_table = data_info['summary_metrics_table']
    
    # 3. Извлекаем строки Sharpe Ratio
    print("3. Извлечение строк Sharpe Ratio...")
    
    def extract_sharpe_ratio_line(table):
        lines = table.split('\n')
        for line in lines:
            if 'Sharpe Ratio' in line:
                return line
        return None
    
    metrics_sharpe_line = extract_sharpe_ratio_line(metrics_table)
    ai_sharpe_line = extract_sharpe_ratio_line(ai_table)
    
    print(f"Sharpe Ratio (Метрики): {metrics_sharpe_line}")
    print(f"Sharpe Ratio (AI):      {ai_sharpe_line}")
    print()
    
    # 4. Проверяем консистентность
    print("4. Проверка консистентности...")
    
    if metrics_sharpe_line == ai_sharpe_line:
        print("✅ СТРОКИ SHARPE RATIO ИДЕНТИЧНЫ!")
        print("Данные Sharpe Ratio корректно передаются в AI-анализ.")
    else:
        print("❌ СТРОКИ SHARPE RATIO РАЗЛИЧАЮТСЯ!")
        print("Проблема с передачей данных в AI-анализ.")
    
    # 5. Проверяем наличие числовых значений
    print("\n5. Проверка числовых значений...")
    
    def has_numeric_values(line):
        if line is None:
            return False
        return 'N/A' not in line and ('0.244' in line or '0.093' in line)
    
    metrics_has_numeric = has_numeric_values(metrics_sharpe_line)
    ai_has_numeric = has_numeric_values(ai_sharpe_line)
    
    if metrics_has_numeric and ai_has_numeric:
        print("✅ ОБЕ ТАБЛИЦЫ СОДЕРЖАТ ЧИСЛОВЫЕ ЗНАЧЕНИЯ SHARPE RATIO")
        print("Исправление работает корректно.")
    elif metrics_has_numeric and not ai_has_numeric:
        print("❌ ТОЛЬКО ТАБЛИЦА МЕТРИК СОДЕРЖИТ ЧИСЛОВЫЕ ЗНАЧЕНИЯ")
        print("Проблема с передачей данных в AI-анализ.")
    elif not metrics_has_numeric and ai_has_numeric:
        print("❌ ТОЛЬКО AI ТАБЛИЦА СОДЕРЖИТ ЧИСЛОВЫЕ ЗНАЧЕНИЯ")
        print("Проблема с таблицей метрик.")
    else:
        print("❌ НИ ОДНА ТАБЛИЦА НЕ СОДЕРЖИТ ЧИСЛОВЫЕ ЗНАЧЕНИЯ")
        print("Исправление не работает.")
    
    # 6. Детальный анализ значений
    print("\n6. Детальный анализ значений...")
    
    def extract_sharpe_values(line):
        if line is None:
            return None, None
        
        # Парсим строку таблицы: | Sharpe Ratio | 0.244 | 0.093 |
        parts = line.split('|')
        if len(parts) >= 4:
            try:
                aapl_value = float(parts[2].strip())
                tsla_value = float(parts[3].strip())
                return aapl_value, tsla_value
            except (ValueError, IndexError):
                pass
        return None, None
    
    metrics_values = extract_sharpe_values(metrics_sharpe_line)
    ai_values = extract_sharpe_values(ai_sharpe_line)
    
    if metrics_values[0] is not None and ai_values[0] is not None:
        print(f"AAPL.US Sharpe Ratio:")
        print(f"  Метрики: {metrics_values[0]:.3f}")
        print(f"  AI:      {ai_values[0]:.3f}")
        print(f"  Разница: {abs(metrics_values[0] - ai_values[0]):.6f}")
        
        print(f"TSLA.US Sharpe Ratio:")
        print(f"  Метрики: {metrics_values[1]:.3f}")
        print(f"  AI:      {ai_values[1]:.3f}")
        print(f"  Разница: {abs(metrics_values[1] - ai_values[1]):.6f}")
        
        # Проверяем точность (допустимая погрешность 0.001)
        tolerance = 0.001
        aapl_match = abs(metrics_values[0] - ai_values[0]) < tolerance
        tsla_match = abs(metrics_values[1] - ai_values[1]) < tolerance
        
        if aapl_match and tsla_match:
            print("✅ ЗНАЧЕНИЯ СООТВЕТСТВУЮТ С ТОЧНОСТЬЮ ДО 0.001")
        else:
            print("❌ ЗНАЧЕНИЯ НЕ СООТВЕТСТВУЮТ")
    else:
        print("❌ НЕ УДАЛОСЬ ИЗВЛЕЧЬ ЧИСЛОВЫЕ ЗНАЧЕНИЯ")
    
    print("\n" + "=" * 50)
    print("Тест завершен.")

if __name__ == "__main__":
    test_sharpe_ratio_consistency()

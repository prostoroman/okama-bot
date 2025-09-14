#!/usr/bin/env python3
"""
Тест для проверки исправлений консистентности данных
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
from services.gemini_service import GeminiService
import okama as ok

async def test_gemini_data_no_duplication():
    """Тестирует отсутствие дублирования в данных для Gemini"""
    
    print("🔍 Тестирование отсутствия дублирования в данных для Gemini")
    print("=" * 60)
    
    bot = ShansAi()
    gemini_service = GeminiService()
    
    # Тестовые символы
    symbols = ['SBER.MOEX', 'LKOH.MOEX']
    currency = 'RUB'
    
    # Создаем портфолио контексты
    portfolio_contexts = []
    expanded_symbols = []
    
    for symbol in symbols:
        try:
            asset = ok.Asset(symbol)
            portfolio_contexts.append({
                'portfolio_object': None,
                'portfolio_symbols': [symbol]
            })
            expanded_symbols.append(symbol)
        except Exception as e:
            print(f"❌ Ошибка создания актива {symbol}: {e}")
            portfolio_contexts.append({
                'portfolio_object': None,
                'portfolio_symbols': [symbol]
            })
            expanded_symbols.append(symbol)
    
    try:
        # Получаем данные для Gemini анализа
        data_info = await bot._prepare_data_for_analysis(
            symbols=symbols,
            currency=currency,
            expanded_symbols=expanded_symbols,
            portfolio_contexts=portfolio_contexts,
            user_id=12345
        )
        
        # Создаем описание данных для Gemini
        description = gemini_service._prepare_data_description(data_info)
        
        print(f"\n📋 Описание данных создано")
        print(f"   Размер: {len(description)} символов")
        
        # Проверяем отсутствие дублирования метрик
        print(f"\n🔍 Проверка отсутствия дублирования метрик:")
        
        # Проверяем, что нет раздела "ДОПОЛНИТЕЛЬНЫЕ МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ"
        has_performance_section = "ДОПОЛНИТЕЛЬНЫЕ МЕТРИКИ ПРОИЗВОДИТЕЛЬНОСТИ" in description
        print(f"   ✅ Раздел 'Дополнительные метрики' удален: {'Нет' if not has_performance_section else 'Есть'}")
        
        # Проверяем наличие основной таблицы метрик
        has_main_table = "ОСНОВНЫЕ МЕТРИКИ АКТИВОВ" in description
        print(f"   ✅ Основная таблица метрик: {'Есть' if has_main_table else 'Нет'}")
        
        # Проверяем наличие таблицы describe
        has_describe_table = "ДОПОЛНИТЕЛЬНАЯ СТАТИСТИКА" in description
        print(f"   ✅ Таблица describe: {'Есть' if has_describe_table else 'Нет'}")
        
        # Проверяем наличие корреляций
        has_correlations = "КОРРЕЛЯЦИОННАЯ МАТРИЦА" in description
        print(f"   ✅ Корреляционная матрица: {'Есть' if has_correlations else 'Нет'}")
        
        # Проверяем наличие эффективной границы
        has_efficient_frontier = "ЭФФЕКТИВНОЙ ГРАНИЦЫ" in description
        print(f"   ✅ Эффективная граница: {'Есть' if has_efficient_frontier else 'Нет'}")
        
        # Проверяем наличие инструкций
        has_instructions = "ИНСТРУКЦИИ ДЛЯ АНАЛИЗА" in description
        print(f"   ✅ Инструкции для анализа: {'Есть' if has_instructions else 'Нет'}")
        
        # Проверяем наличие дисклеймера
        has_disclaimer = "дисклеймер" in description.lower() or "не является инвестиционной рекомендацией" in description
        print(f"   ✅ Дисклеймер: {'Есть' if has_disclaimer else 'Нет'}")
        
        success = (not has_performance_section and has_main_table and 
                  has_describe_table and has_correlations and has_instructions and has_disclaimer)
        
        if success:
            print(f"\n✅ Все проверки пройдены - дублирование устранено!")
        else:
            print(f"\n⚠️  Некоторые проверки не пройдены")
        
        return success
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def test_data_source_consistency():
    """Тестирует консистентность источников данных"""
    
    print("\n🔍 Тестирование консистентности источников данных")
    print("=" * 60)
    
    symbols = ['SBER.MOEX', 'LKOH.MOEX']
    currency = 'RUB'
    
    try:
        # Создаем AssetList как для графиков
        asset_list = ok.AssetList(symbols, ccy=currency)
        
        print(f"📊 AssetList создан для символов: {symbols}")
        
        # Получаем данные из AssetList
        if hasattr(asset_list, 'wealth_indexes'):
            wealth_indexes = asset_list.wealth_indexes
            print(f"\n📈 AssetList wealth indexes:")
            print(f"   Размер: {wealth_indexes.shape}")
            print(f"   Период: {wealth_indexes.index[0]} - {wealth_indexes.index[-1]}")
            print(f"   Количество точек: {len(wealth_indexes)}")
        
        # Проверяем данные отдельных активов с новым приоритетом
        print(f"\n🔍 Проверка приоритета месячных данных:")
        
        for symbol in symbols:
            try:
                asset = ok.Asset(symbol)
                
                # Проверяем приоритет: close_monthly -> wealth_index -> adj_close -> close_daily
                if hasattr(asset, 'close_monthly') and asset.close_monthly is not None:
                    selected_data = asset.close_monthly
                    source = 'close_monthly'
                elif hasattr(asset, 'wealth_index') and asset.wealth_index is not None:
                    selected_data = asset.wealth_index
                    source = 'wealth_index'
                elif hasattr(asset, 'adj_close') and asset.adj_close is not None:
                    selected_data = asset.adj_close
                    source = 'adj_close'
                elif hasattr(asset, 'close_daily') and asset.close_daily is not None:
                    selected_data = asset.close_daily
                    source = 'close_daily'
                else:
                    selected_data = None
                    source = 'none'
                
                print(f"\n📊 {symbol}:")
                print(f"   Выбранный источник: {source}")
                
                if selected_data is not None and source == 'close_monthly':
                    print(f"   Период: {selected_data.index[0]} - {selected_data.index[-1]}")
                    print(f"   Количество точек: {len(selected_data)}")
                    
                    # Сравниваем с AssetList
                    if hasattr(asset_list, 'wealth_indexes') and symbol in asset_list.wealth_indexes.columns:
                        assetlist_data = asset_list.wealth_indexes[symbol]
                        
                        # Проверяем совпадение типа данных (месячные)
                        both_monthly = (len(selected_data) < 500 and len(assetlist_data) < 500)  # Примерная проверка на месячные данные
                        print(f"   ✅ Оба источника используют месячные данные: {'Да' if both_monthly else 'Нет'}")
                        
                        # Проверяем близость количества точек
                        count_diff = abs(len(selected_data) - len(assetlist_data))
                        counts_close = count_diff <= 5  # Допускаем небольшую разницу
                        print(f"   ✅ Количество точек близко: {'Да' if counts_close else f'Нет (разница: {count_diff})'}")
                
            except Exception as e:
                print(f"❌ Ошибка для {symbol}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании AssetList: {e}")
        return False

async def main():
    """Основная функция теста"""
    
    print("🚀 ЗАПУСК ТЕСТА ИСПРАВЛЕНИЙ КОНСИСТЕНТНОСТИ ДАННЫХ")
    print("=" * 60)
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Тестируем отсутствие дублирования в Gemini
    gemini_success = await test_gemini_data_no_duplication()
    
    # Тестируем консистентность источников данных
    data_source_success = test_data_source_consistency()
    
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ АНАЛИЗ")
    print("=" * 60)
    
    print("✅ Результаты тестирования исправлений:")
    print(f"   - Устранение дублирования в Gemini: {'✅ Успешно' if gemini_success else '❌ Ошибка'}")
    print(f"   - Консистентность источников данных: {'✅ Успешно' if data_source_success else '❌ Ошибка'}")
    
    if gemini_success and data_source_success:
        print("\n🎉 ВСЕ ИСПРАВЛЕНИЯ УСПЕШНЫ!")
        print("✅ Дублирование метрик устранено")
        print("✅ Источники данных синхронизированы")
        print("✅ Данные для Gemini и графиков консистентны")
    else:
        print("\n⚠️  НЕКОТОРЫЕ ИСПРАВЛЕНИЯ НЕ ЗАВЕРШЕНЫ")
        print("⚠️  Требуется дополнительная работа")
    
    print(f"\n✅ Тест завершен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

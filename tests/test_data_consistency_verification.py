#!/usr/bin/env python3
"""
Тест для проверки консистентности данных между Gemini анализом и таблицами метрик
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

def test_data_source_consistency():
    """Тестирует консистентность источников данных между функциями"""
    
    print("🔍 Тестирование консистентности источников данных")
    print("=" * 60)
    
    bot = ShansAi()
    
    # Тестовые символы
    symbols = ['SBER.MOEX', 'LKOH.MOEX', 'OBLG.MOEX']
    currency = 'RUB'
    
    print(f"\n📊 Тестируемые символы: {', '.join(symbols)}")
    print(f"💰 Валюта: {currency}")
    
    data_sources = {}
    
    for symbol in symbols:
        try:
            asset = ok.Asset(symbol)
            
            # Проверяем приоритет источников данных
            sources = []
            
            if hasattr(asset, 'adj_close') and asset.adj_close is not None:
                sources.append(('adj_close', len(asset.adj_close)))
            
            if hasattr(asset, 'close_monthly') and asset.close_monthly is not None:
                sources.append(('close_monthly', len(asset.close_monthly)))
            
            if hasattr(asset, 'close_daily') and asset.close_daily is not None:
                sources.append(('close_daily', len(asset.close_daily)))
            
            if hasattr(asset, 'wealth_index') and asset.wealth_index is not None:
                sources.append(('wealth_index', len(asset.wealth_index)))
            
            data_sources[symbol] = sources
            
            print(f"\n📊 {symbol}:")
            for source_name, length in sources:
                print(f"   {source_name}: {length} точек данных")
            
            # Определяем, какой источник будет использован
            if hasattr(asset, 'adj_close') and asset.adj_close is not None:
                selected_source = 'adj_close'
                selected_data = asset.adj_close
            elif hasattr(asset, 'close_monthly') and asset.close_monthly is not None:
                selected_source = 'close_monthly'
                selected_data = asset.close_monthly
            elif hasattr(asset, 'close_daily') and asset.close_daily is not None:
                selected_source = 'close_daily'
                selected_data = asset.close_daily
            else:
                selected_source = 'none'
                selected_data = None
            
            print(f"   ✅ Выбранный источник: {selected_source}")
            
            if selected_data is not None:
                print(f"   📅 Период: {selected_data.index[0]} - {selected_data.index[-1]}")
                print(f"   📊 Количество точек: {len(selected_data)}")
                
        except Exception as e:
            print(f"❌ Ошибка для {symbol}: {e}")
            data_sources[symbol] = []
    
    return data_sources

async def test_metrics_calculation_consistency():
    """Тестирует консистентность расчета метрик"""
    
    print("\n🔍 Тестирование консистентности расчета метрик")
    print("=" * 60)
    
    bot = ShansAi()
    
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
        # Получаем метрики из таблицы метрик
        summary_table = bot._create_summary_metrics_table(
            symbols=symbols,
            currency=currency,
            expanded_symbols=expanded_symbols,
            portfolio_contexts=portfolio_contexts,
            specified_period=None
        )
        
        print(f"\n📋 Таблица метрик создана успешно")
        print(f"   Размер: {len(summary_table)} символов")
        
        # Проверяем наличие ключевых метрик в таблице
        key_metrics = [
            'Период инвестиций',
            'Среднегодовая доходность (CAGR)',
            'Волатильность',
            'Безрисковая ставка',
            'Коэфф. Шарпа',
            'Макс. просадка',
            'Коэф. Сортино',
            'Коэф. Кальмара',
            'VaR 95%',
            'CVaR 95%'
        ]
        
        print(f"\n🔍 Проверка наличия метрик в таблице:")
        for metric in key_metrics:
            present = metric in summary_table
            status = "✅" if present else "❌"
            print(f"   {status} {metric}")
        
        # Получаем данные для Gemini анализа
        data_info = await bot._prepare_data_for_analysis(
            symbols=symbols,
            currency=currency,
            expanded_symbols=expanded_symbols,
            portfolio_contexts=portfolio_contexts,
            user_id=12345
        )
        
        print(f"\n📋 Данные для Gemini анализа подготовлены")
        print(f"   Символы: {data_info.get('symbols', [])}")
        print(f"   Валюта: {data_info.get('currency', 'N/A')}")
        
        # Проверяем наличие таблицы метрик в данных для Gemini
        gemini_summary_table = data_info.get('summary_metrics_table', '')
        gemini_performance = data_info.get('performance', {})
        
        print(f"\n🔍 Проверка данных для Gemini:")
        print(f"   ✅ Основная таблица метрик: {'Есть' if gemini_summary_table else 'Нет'}")
        print(f"   ✅ Дополнительные метрики: {'Есть' if gemini_performance else 'Нет'}")
        
        # Сравниваем таблицы
        tables_match = summary_table == gemini_summary_table
        print(f"   ✅ Таблицы идентичны: {'Да' if tables_match else 'Нет'}")
        
        if not tables_match:
            print(f"   ⚠️  Размер основной таблицы: {len(summary_table)}")
            print(f"   ⚠️  Размер таблицы для Gemini: {len(gemini_summary_table)}")
        
        # Проверяем дублирование метрик
        print(f"\n🔍 Проверка дублирования метрик:")
        
        duplicated_metrics = []
        for symbol in symbols:
            if symbol in gemini_performance:
                perf_metrics = gemini_performance[symbol]
                
                # Проверяем метрики, которые есть и в таблице, и в performance
                if 'annual_return' in perf_metrics and 'CAGR' in summary_table:
                    duplicated_metrics.append(f"{symbol}: annual_return/CAGR")
                
                if 'volatility' in perf_metrics and 'Волатильность' in summary_table:
                    duplicated_metrics.append(f"{symbol}: volatility/Волатильность")
                
                if 'sharpe_ratio' in perf_metrics and 'Шарпа' in summary_table:
                    duplicated_metrics.append(f"{symbol}: sharpe_ratio/Коэфф. Шарпа")
                
                if 'max_drawdown' in perf_metrics and 'просадка' in summary_table:
                    duplicated_metrics.append(f"{symbol}: max_drawdown/Макс. просадка")
        
        if duplicated_metrics:
            print(f"   ⚠️  Найдены дублированные метрики:")
            for dup in duplicated_metrics:
                print(f"     - {dup}")
        else:
            print(f"   ✅ Дублированных метрик не найдено")
        
        return {
            'tables_match': tables_match,
            'duplicated_metrics': duplicated_metrics,
            'summary_table_size': len(summary_table),
            'gemini_table_size': len(gemini_summary_table)
        }
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return None

def test_assetlist_data_consistency():
    """Тестирует консистентность данных AssetList с данными для анализа"""
    
    print("\n🔍 Тестирование консистентности данных AssetList")
    print("=" * 60)
    
    symbols = ['SBER.MOEX', 'LKOH.MOEX']
    currency = 'RUB'
    
    try:
        # Создаем AssetList как для графиков
        asset_list = ok.AssetList(symbols, ccy=currency)
        
        print(f"📊 AssetList создан для символов: {symbols}")
        print(f"💰 Валюта: {currency}")
        
        # Получаем данные из AssetList
        if hasattr(asset_list, 'wealth_indexes'):
            wealth_indexes = asset_list.wealth_indexes
            print(f"\n📈 Wealth indexes:")
            print(f"   Размер: {wealth_indexes.shape}")
            print(f"   Символы: {list(wealth_indexes.columns)}")
            print(f"   Период: {wealth_indexes.index[0]} - {wealth_indexes.index[-1]}")
        
        # Сравниваем с данными отдельных активов
        print(f"\n🔍 Сравнение с отдельными активами:")
        
        for symbol in symbols:
            try:
                asset = ok.Asset(symbol)
                
                # Получаем данные по тому же приоритету, что и в функциях
                if hasattr(asset, 'adj_close') and asset.adj_close is not None:
                    asset_data = asset.adj_close
                    source = 'adj_close'
                elif hasattr(asset, 'close_monthly') and asset.close_monthly is not None:
                    asset_data = asset.close_monthly
                    source = 'close_monthly'
                elif hasattr(asset, 'close_daily') and asset.close_daily is not None:
                    asset_data = asset.close_daily
                    source = 'close_daily'
                else:
                    asset_data = None
                    source = 'none'
                
                print(f"\n📊 {symbol}:")
                print(f"   Источник данных: {source}")
                
                if asset_data is not None:
                    print(f"   Период актива: {asset_data.index[0]} - {asset_data.index[-1]}")
                    print(f"   Количество точек актива: {len(asset_data)}")
                    
                    if hasattr(asset_list, 'wealth_indexes') and symbol in asset_list.wealth_indexes.columns:
                        assetlist_data = asset_list.wealth_indexes[symbol]
                        print(f"   Период AssetList: {assetlist_data.index[0]} - {assetlist_data.index[-1]}")
                        print(f"   Количество точек AssetList: {len(assetlist_data)}")
                        
                        # Проверяем совпадение периодов
                        periods_match = (asset_data.index[0] == assetlist_data.index[0] and 
                                       asset_data.index[-1] == assetlist_data.index[-1])
                        print(f"   ✅ Периоды совпадают: {'Да' if periods_match else 'Нет'}")
                        
                        # Проверяем совпадение количества точек
                        counts_match = len(asset_data) == len(assetlist_data)
                        print(f"   ✅ Количество точек совпадает: {'Да' if counts_match else 'Нет'}")
                
            except Exception as e:
                print(f"❌ Ошибка для {symbol}: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании AssetList: {e}")
        return False

async def main():
    """Основная функция теста"""
    
    print("🚀 ЗАПУСК ТЕСТА КОНСИСТЕНТНОСТИ ДАННЫХ")
    print("=" * 60)
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Тестируем источники данных
    data_sources = test_data_source_consistency()
    
    # Тестируем консистентность метрик
    metrics_result = await test_metrics_calculation_consistency()
    
    # Тестируем консистентность AssetList
    assetlist_result = test_assetlist_data_consistency()
    
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ АНАЛИЗ")
    print("=" * 60)
    
    print("✅ Результаты тестирования:")
    print(f"   - Источники данных: {'✅ Проверены' if data_sources else '❌ Ошибка'}")
    print(f"   - Консистентность метрик: {'✅ Успешно' if metrics_result else '❌ Ошибка'}")
    print(f"   - Консистентность AssetList: {'✅ Успешно' if assetlist_result else '❌ Ошибка'}")
    
    if metrics_result:
        print(f"\n📊 Детали консистентности метрик:")
        print(f"   - Таблицы идентичны: {'✅ Да' if metrics_result['tables_match'] else '❌ Нет'}")
        print(f"   - Дублированные метрики: {'❌ Есть' if metrics_result['duplicated_metrics'] else '✅ Нет'}")
        
        if metrics_result['duplicated_metrics']:
            print(f"   - Количество дубликатов: {len(metrics_result['duplicated_metrics'])}")
    
    if data_sources and metrics_result and assetlist_result and metrics_result['tables_match'] and not metrics_result['duplicated_metrics']:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Данные консистентны между всеми компонентами")
    else:
        print("\n⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("⚠️  Требуется дополнительная синхронизация данных")
    
    print(f"\n✅ Тест завершен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

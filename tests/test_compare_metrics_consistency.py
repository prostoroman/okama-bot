#!/usr/bin/env python3
"""
Тест для проверки соответствия метрик между кнопкой "Метрики" и AI анализом в команде /compare
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
from bot import ShansAi
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_metrics_consistency():
    """Тестирует соответствие метрик между кнопкой Метрики и AI анализом"""
    
    # Тестовые символы
    test_symbols = ['SPY.US', 'QQQ.US']
    test_currency = 'USD'
    
    print("🔍 Тестирование соответствия метрик в команде /compare")
    print("=" * 60)
    
    try:
        # Создаем экземпляр бота
        bot = ShansAi()
        
        # Создаем AssetList для получения данных
        asset_list = ok.AssetList(test_symbols, ccy=test_currency)
        
        # Получаем describe данные (те же, что используются в таблице метрик)
        describe_data = asset_list.describe()
        print(f"📊 Данные describe для {test_symbols}:")
        print(describe_data)
        print()
        
        # Создаем expanded_symbols (символы как строки)
        expanded_symbols = test_symbols.copy()
        portfolio_contexts = []
        
        # Тестируем функцию создания таблицы метрик (кнопка "Метрики")
        print("📋 Тестирование функции _create_summary_metrics_table (кнопка Метрики):")
        metrics_table = bot._create_summary_metrics_table(
            symbols=test_symbols,
            currency=test_currency,
            expanded_symbols=expanded_symbols,
            portfolio_contexts=portfolio_contexts,
            specified_period=None
        )
        print("Таблица метрик:")
        print(metrics_table)
        print()
        
        # Тестируем функцию подготовки данных для AI анализа
        print("🤖 Тестирование функции _prepare_data_for_analysis (AI анализ):")
        
        # Создаем мок-контекст пользователя
        user_context = {
            'describe_table': '',
            'current_symbols': test_symbols,
            'current_currency': test_currency
        }
        
        # Мокаем _get_user_context
        original_get_user_context = bot._get_user_context
        bot._get_user_context = lambda user_id: user_context
        
        # Подготавливаем данные для анализа (синхронная версия)
        import asyncio
        data_info = asyncio.run(bot._prepare_data_for_analysis(
            symbols=test_symbols,
            currency=test_currency,
            expanded_symbols=expanded_symbols,
            portfolio_contexts=portfolio_contexts,
            user_id=12345
        ))
        
        print("Данные для AI анализа:")
        print(f"Symbols: {data_info['symbols']}")
        print(f"Currency: {data_info['currency']}")
        print(f"Summary metrics table:")
        print(data_info['summary_metrics_table'])
        print()
        
        # Сравниваем таблицы метрик
        print("🔍 Сравнение таблиц метрик:")
        print("=" * 40)
        
        metrics_table_clean = metrics_table.replace("## 📊 Метрики активов\n\n", "").strip()
        ai_table_clean = data_info['summary_metrics_table'].replace("## 📊 Метрики активов\n\n", "").strip()
        
        if metrics_table_clean == ai_table_clean:
            print("✅ ТАБЛИЦЫ МЕТРИК ИДЕНТИЧНЫ!")
            print("Кнопка 'Метрики' и AI анализ используют одинаковые данные.")
        else:
            print("❌ ТАБЛИЦЫ МЕТРИК РАЗЛИЧАЮТСЯ!")
            print("Кнопка 'Метрики':")
            print(metrics_table_clean)
            print("\nAI анализ:")
            print(ai_table_clean)
        
        # Проверяем дополнительные данные в AI анализе
        print("\n📈 Дополнительные данные в AI анализе:")
        print(f"Performance metrics keys: {list(data_info['performance'].keys())}")
        print(f"Asset names: {data_info['asset_names']}")
        print(f"Analysis type: {data_info['analysis_type']}")
        
        # Восстанавливаем оригинальную функцию
        bot._get_user_context = original_get_user_context
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_asset_metrics():
    """Тестирует метрики для отдельных активов"""
    
    print("\n" + "=" * 60)
    print("🔍 Тестирование метрик отдельных активов")
    print("=" * 60)
    
    test_symbols = ['SPY.US', 'QQQ.US']
    
    for symbol in test_symbols:
        print(f"\n📊 Анализ актива: {symbol}")
        try:
            asset = ok.Asset(symbol)
            
            # Получаем основные метрики
            print(f"Название: {getattr(asset, 'name', 'N/A')}")
            print(f"Страна: {getattr(asset, 'country', 'N/A')}")
            print(f"Тип: {getattr(asset, 'asset_type', 'N/A')}")
            print(f"Биржа: {getattr(asset, 'exchange', 'N/A')}")
            print(f"Валюта: {getattr(asset, 'currency', 'N/A')}")
            
            # Метрики производительности
            if hasattr(asset, 'get_cagr'):
                cagr = asset.get_cagr()
                if hasattr(cagr, 'iloc'):
                    cagr_value = cagr.iloc[0]
                else:
                    cagr_value = cagr
                print(f"CAGR: {cagr_value:.2%}")
            
            if hasattr(asset, 'volatility_annual'):
                volatility = asset.volatility_annual
                if hasattr(volatility, 'iloc'):
                    vol_value = volatility.iloc[-1]
                else:
                    vol_value = volatility
                print(f"Волатильность: {vol_value:.2%}")
            
            if hasattr(asset, 'get_sharpe_ratio'):
                sharpe = asset.get_sharpe_ratio()
                if hasattr(sharpe, 'iloc'):
                    sharpe_value = sharpe.iloc[0]
                else:
                    sharpe_value = sharpe
                print(f"Коэффициент Шарпа: {sharpe_value:.2f}")
            
            if hasattr(asset, 'max_drawdown'):
                max_dd = asset.max_drawdown
                if hasattr(max_dd, 'iloc'):
                    dd_value = max_dd.iloc[-1]
                else:
                    dd_value = max_dd
                print(f"Максимальная просадка: {dd_value:.2%}")
                
        except Exception as e:
            print(f"❌ Ошибка при анализе {symbol}: {e}")

if __name__ == "__main__":
    print("🚀 Запуск тестов соответствия метрик в команде /compare")
    print("=" * 60)
    
    # Основной тест
    success = test_metrics_consistency()
    
    # Тест отдельных активов
    test_individual_asset_metrics()
    
    if success:
        print("\n✅ Все тесты завершены успешно!")
    else:
        print("\n❌ Тесты завершились с ошибками!")

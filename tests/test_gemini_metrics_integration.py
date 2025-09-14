#!/usr/bin/env python3
"""
Тест для проверки интеграции таблиц метрик с Gemini анализом
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

async def test_gemini_data_preparation():
    """Тестирует подготовку данных для Gemini анализа с таблицами метрик"""
    
    print("🔍 Тестирование подготовки данных для Gemini анализа")
    print("=" * 60)
    
    bot = ShansAi()
    
    # Тестовые символы
    symbols = ['SBER.MOEX', 'LKOH.MOEX', 'OBLG.MOEX']
    currency = 'RUB'
    
    print(f"\n📊 Тестируемые символы: {', '.join(symbols)}")
    print(f"💰 Валюта: {currency}")
    
    try:
        # Создаем портфолио контексты для тестирования
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
        
        # Подготавливаем данные для анализа
        print(f"\n🔍 Подготовка данных для анализа...")
        
        # Имитируем вызов функции _prepare_data_for_analysis
        data_info = await bot._prepare_data_for_analysis(
            symbols=symbols,
            currency=currency,
            expanded_symbols=expanded_symbols,
            portfolio_contexts=portfolio_contexts,
            user_id=12345
        )
        
        print(f"\n📋 Подготовленные данные:")
        print(f"   Символы: {data_info.get('symbols', [])}")
        print(f"   Валюта: {data_info.get('currency', 'N/A')}")
        print(f"   Тип анализа: {data_info.get('analysis_type', 'N/A')}")
        print(f"   Количество активов: {data_info.get('asset_count', 0)}")
        
        # Проверяем наличие таблиц метрик
        summary_table = data_info.get('summary_metrics_table', '')
        describe_table = data_info.get('describe_table', '')
        
        print(f"\n📊 Таблицы метрик:")
        print(f"   Основная таблица метрик: {'✅ Есть' if summary_table else '❌ Нет'}")
        print(f"   Таблица describe: {'✅ Есть' if describe_table else '❌ Нет'}")
        
        if summary_table:
            print(f"\n📋 Основная таблица метрик (первые 500 символов):")
            print(summary_table[:500] + "..." if len(summary_table) > 500 else summary_table)
        
        # Проверяем метрики производительности
        performance = data_info.get('performance', {})
        print(f"\n📈 Метрики производительности:")
        for symbol, metrics in performance.items():
            print(f"   {symbol}:")
            for metric, value in metrics.items():
                if value is not None:
                    if isinstance(value, float):
                        if 'return' in metric.lower() or 'drawdown' in metric.lower():
                            print(f"     {metric}: {value:.2%}")
                        else:
                            print(f"     {metric}: {value:.4f}")
                    else:
                        print(f"     {metric}: {value}")
        
        # Проверяем корреляции
        correlations = data_info.get('correlations', [])
        print(f"\n🔗 Корреляции: {'✅ Есть' if correlations else '❌ Нет'}")
        
        print(f"\n✅ Подготовка данных завершена успешно!")
        return data_info
        
    except Exception as e:
        print(f"❌ Ошибка при подготовке данных: {e}")
        return None

def test_gemini_service_data_description():
    """Тестирует создание описания данных для Gemini"""
    
    print("\n🔍 Тестирование создания описания данных для Gemini")
    print("=" * 60)
    
    gemini_service = GeminiService()
    
    # Создаем тестовые данные
    test_data_info = {
        'symbols': ['SBER.MOEX', 'LKOH.MOEX', 'OBLG.MOEX'],
        'currency': 'RUB',
        'period': 'полный доступный период данных',
        'analysis_type': 'asset_comparison',
        'asset_count': 3,
        'asset_names': {
            'SBER.MOEX': 'Сбербанк',
            'LKOH.MOEX': 'Лукойл',
            'OBLG.MOEX': 'ОФЗ'
        },
        'summary_metrics_table': """
| Метрика                         | SBER.MOEX   | LKOH.MOEX   | OBLG.MOEX   |
|:--------------------------------|:------------|:------------|:------------|
| Период инвестиций               | 19.1 лет    | 22.1 лет    | 6.6 лет     |
| Среднегодовая доходность (CAGR) | 14.51%      | 17.50%      | 9.60%       |
| Волатильность                   | 43.46%      | 35.90%      | 6.59%       |
| Безрисковая ставка              | 33.70%      | 33.70%      | 33.70%      |
| Коэфф. Шарпа                    | -0.44       | -0.45       | -3.66       |
| Макс. просадка                  | -87.29%     | -71.84%     | -15.87%     |
| Коэф. Сортино                   | -8.97       | -9.53       | -46.75      |
| Коэф. Кальмара                  | 0.17        | 0.24        | 0.60        |
| VaR 95%                         | -3.54%      | -2.98%      | -0.29%      |
| CVaR 95%                        | -6.00%      | -4.92%      | -0.69%      |
        """,
        'describe_table': """
|   Метрика | SBER.MOEX   | LKOH.MOEX   | OBLG.MOEX   |
|----------:|:------------|:------------|:------------|
|         0 | 0.2442      | -0.1123     | 0.2259      |
|         1 | 0.3529      | 0.0362      | 0.2746      |
|         2 | 0.1789      | 0.1377      | 0.0901      |
        """,
        'performance': {
            'SBER.MOEX': {
                'total_return': 0.1451,
                'annual_return': 0.1451,
                'volatility': 0.4346,
                'sharpe_ratio': -0.44,
                'sortino_ratio': -8.97,
                'max_drawdown': -0.8729
            },
            'LKOH.MOEX': {
                'total_return': 0.1750,
                'annual_return': 0.1750,
                'volatility': 0.3590,
                'sharpe_ratio': -0.45,
                'sortino_ratio': -9.53,
                'max_drawdown': -0.7184
            },
            'OBLG.MOEX': {
                'total_return': 0.0960,
                'annual_return': 0.0960,
                'volatility': 0.0659,
                'sharpe_ratio': -3.66,
                'sortino_ratio': -46.75,
                'max_drawdown': -0.1587
            }
        },
        'correlations': [
            [1.0, 0.3, 0.1],
            [0.3, 1.0, 0.2],
            [0.1, 0.2, 1.0]
        ]
    }
    
    try:
        # Создаем описание данных
        description = gemini_service._prepare_data_description(test_data_info)
        
        print(f"\n📋 Созданное описание данных:")
        print("=" * 60)
        print(description)
        
        # Проверяем наличие ключевых элементов
        checks = [
            ("Анализируемые активы", "Анализируемые активы:" in description),
            ("Основные метрики", "📊 ОСНОВНЫЕ МЕТРИКИ АКТИВОВ:" in description),
            ("Дополнительная статистика", "📊 ДОПОЛНИТЕЛЬНАЯ СТАТИСТИКА" in description),
            ("Период инвестиций", "Период инвестиций" in description),
            ("CAGR", "Среднегодовая доходность (CAGR)" in description),
            ("Волатильность", "Волатильность" in description),
            ("Коэффициент Шарпа", "Коэфф. Шарпа" in description),
            ("Инструкции для анализа", "ИНСТРУКЦИИ ДЛЯ АНАЛИЗА:" in description)
        ]
        
        print(f"\n🔍 Проверка элементов описания:")
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"   {status} {check_name}")
        
        all_checks_passed = all(check_result for _, check_result in checks)
        
        if all_checks_passed:
            print(f"\n✅ Все элементы описания присутствуют!")
        else:
            print(f"\n⚠️  Некоторые элементы описания отсутствуют")
        
        return description
        
    except Exception as e:
        print(f"❌ Ошибка при создании описания: {e}")
        return None

def test_gemini_analysis_flow():
    """Тестирует полный поток анализа Gemini"""
    
    print("\n🔍 Тестирование полного потока анализа Gemini")
    print("=" * 60)
    
    gemini_service = GeminiService()
    
    # Проверяем доступность сервиса
    if not gemini_service.is_available():
        print("❌ Gemini сервис недоступен - пропускаем тест")
        return False
    
    print("✅ Gemini сервис доступен")
    
    # Создаем тестовые данные
    test_data_info = {
        'symbols': ['SBER.MOEX', 'LKOH.MOEX'],
        'currency': 'RUB',
        'period': 'полный доступный период данных',
        'analysis_type': 'asset_comparison',
        'asset_count': 2,
        'asset_names': {
            'SBER.MOEX': 'Сбербанк',
            'LKOH.MOEX': 'Лукойл'
        },
        'summary_metrics_table': """
| Метрика                         | SBER.MOEX   | LKOH.MOEX   |
|:--------------------------------|:------------|:------------|
| Период инвестиций               | 19.1 лет    | 22.1 лет    |
| Среднегодовая доходность (CAGR) | 14.51%      | 17.50%      |
| Волатильность                   | 43.46%      | 35.90%      |
| Безрисковая ставка              | 33.70%      | 33.70%      |
| Коэфф. Шарпа                    | -0.44       | -0.45       |
| Макс. просадка                  | -87.29%     | -71.84%     |
        """,
        'performance': {
            'SBER.MOEX': {
                'annual_return': 0.1451,
                'volatility': 0.4346,
                'sharpe_ratio': -0.44,
                'max_drawdown': -0.8729
            },
            'LKOH.MOEX': {
                'annual_return': 0.1750,
                'volatility': 0.3590,
                'sharpe_ratio': -0.45,
                'max_drawdown': -0.7184
            }
        }
    }
    
    try:
        # Выполняем анализ
        print(f"\n🤖 Выполнение анализа...")
        analysis_result = gemini_service.analyze_data(test_data_info)
        
        if analysis_result and analysis_result.get('success'):
            analysis_text = analysis_result.get('analysis', '')
            print(f"\n📋 Результат анализа:")
            print("=" * 60)
            print(analysis_text)
            
            # Проверяем качество анализа
            quality_checks = [
                ("Упоминание активов", any(symbol in analysis_text for symbol in ['SBER', 'LKOH', 'Сбербанк', 'Лукойл'])),
                ("Анализ метрик", any(metric in analysis_text for metric in ['доходность', 'волатильность', 'риск', 'Sharpe'])),
                ("Рекомендации", any(word in analysis_text.lower() for word in ['рекоменд', 'совет', 'лучше', 'предпочт'])),
                ("Сравнение", any(word in analysis_text.lower() for word in ['сравн', 'лучше', 'хуже', 'выше', 'ниже']))
            ]
            
            print(f"\n🔍 Проверка качества анализа:")
            for check_name, check_result in quality_checks:
                status = "✅" if check_result else "❌"
                print(f"   {status} {check_name}")
            
            quality_score = sum(check_result for _, check_result in quality_checks) / len(quality_checks)
            
            if quality_score >= 0.75:
                print(f"\n✅ Анализ высокого качества (оценка: {quality_score:.1%})")
                return True
            else:
                print(f"\n⚠️  Анализ среднего качества (оценка: {quality_score:.1%})")
                return False
                
        else:
            print(f"❌ Анализ не выполнен: {analysis_result}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        return False

async def main():
    """Основная функция теста"""
    
    print("🚀 ЗАПУСК ТЕСТА ИНТЕГРАЦИИ GEMINI С ТАБЛИЦАМИ МЕТРИК")
    print("=" * 60)
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Тестируем подготовку данных
    data_info = await test_gemini_data_preparation()
    
    # Тестируем создание описания данных
    description = test_gemini_service_data_description()
    
    # Тестируем полный поток анализа
    analysis_success = test_gemini_analysis_flow()
    
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ АНАЛИЗ")
    print("=" * 60)
    
    print("✅ Результаты тестирования:")
    print(f"   - Подготовка данных: {'✅ Успешно' if data_info else '❌ Ошибка'}")
    print(f"   - Создание описания: {'✅ Успешно' if description else '❌ Ошибка'}")
    print(f"   - Полный анализ: {'✅ Успешно' if analysis_success else '❌ Ошибка'}")
    
    if data_info and description and analysis_success:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("✅ Интеграция таблиц метрик с Gemini анализом работает корректно")
    else:
        print("\n⚠️  НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        print("⚠️  Требуется дополнительная проверка интеграции")
    
    print(f"\n✅ Тест завершен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

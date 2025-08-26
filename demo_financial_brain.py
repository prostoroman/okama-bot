#!/usr/bin/env python3
"""
Демонстрация Okama Financial Brain

Показывает основные возможности интеллектуальной системы финансового анализа
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.financial_brain_enhanced import EnhancedOkamaFinancialBrain
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def demo_financial_brain():
    """Демонстрация основных возможностей Financial Brain"""
    print("🧠 Демонстрация Okama Financial Brain")
    print("=" * 60)
    
    try:
        # Инициализация
        brain = EnhancedOkamaFinancialBrain()
        print("✅ Financial Brain инициализирован успешно")
        
        # Демонстрация декомпозиции запросов
        print("\n📝 Демонстрация декомпозиции запросов:")
        print("-" * 40)
        
        demo_queries = [
            "Проанализируй Apple",
            "Сравни золото и серебро", 
            "Портфель из VOO.US и AGG.US с весами 60% и 40%",
            "Анализ инфляции в США",
            "Сравни S&P 500 и NASDAQ в рублях"
        ]
        
        for i, query in enumerate(demo_queries, 1):
            print(f"\n🔍 Запрос {i}: {query}")
            try:
                # Декомпозиция запроса
                decomposed = brain._decompose_query(query)
                print(f"   Намерение: {decomposed.intent}")
                print(f"   Активы: {decomposed.assets}")
                print(f"   Классы активов: {decomposed.asset_classes}")
                print(f"   Веса: {decomposed.weights}")
                print(f"   Валюта: {decomposed.currency}")
                print(f"   Период: {decomposed.period}")
                
            except Exception as e:
                print(f"   ❌ Ошибка: {e}")
        
        # Демонстрация извлечения параметров
        print("\n🔧 Демонстрация извлечения параметров:")
        print("-" * 40)
        
        # Тест извлечения весов
        print("\n⚖️ Извлечение весов:")
        weight_tests = [
            "Портфель 60% акции, 40% облигации",
            "Веса: 50% и 50%",
            "70% золото, 30% серебро",
            "Портфель с весами 80% и 20%"
        ]
        
        for test in weight_tests:
            weights = brain._extract_weights(test, 2)
            print(f"   '{test}' -> {weights}")
        
        # Тест извлечения валюты
        print("\n💰 Извлечение валюты:")
        currency_tests = [
            "Анализ в долларах",
            "Покажи в евро",
            "Данные в рублях",
            "Отчет в USD"
        ]
        
        for test in currency_tests:
            currency = brain._extract_currency(test, {})
            print(f"   '{test}' -> {currency}")
        
        # Тест извлечения периода
        print("\n📅 Извлечение периода:")
        period_tests = [
            "За последние 5 лет",
            "Анализ за 3 года",
            "Данные с 2020 по 2024",
            "За период 1Y"
        ]
        
        for test in period_tests:
            period = brain._extract_period(test, {})
            print(f"   '{test}' -> {period}")
        
        # Демонстрация форматирования ответа
        print("\n📊 Демонстрация форматирования ответа:")
        print("-" * 40)
        
        # Создаем тестовый результат
        from services.financial_brain_enhanced import EnhancedFinancialQuery, EnhancedAnalysisResult
        
        test_query = EnhancedFinancialQuery(
            intent='single_asset_info',
            assets=['AAPL.US'],
            asset_classes=['US'],
            weights=None,
            currency='USD',
            period='5Y',
            user_message='Проанализируй Apple'
        )
        
        test_result = EnhancedAnalysisResult(
            query=test_query,
            data_report={
                'ticker': 'AAPL.US',
                'name': 'Apple Inc.',
                'currency': 'USD',
                'metrics': {
                    'cagr': 0.1523,
                    'volatility': 0.1845,
                    'sharpe': 0.82,
                    'max_drawdown': -0.2345
                }
            },
            charts=[],
            ai_insights='Apple показывает стабильный рост с хорошим соотношением риск-доходность.',
            recommendations='Рекомендуется включить в диверсифицированный портфель.'
        )
        
        # Форматируем ответ
        formatted_response = brain.format_final_response(test_result)
        print("📝 Пример форматированного ответа:")
        print(formatted_response)
        
        # Получаем резюме
        summary = brain.get_analysis_summary(test_result)
        print(f"\n📋 Резюме анализа:")
        print(f"   Временная метка: {summary['timestamp']}")
        print(f"   Количество графиков: {summary['charts_count']}")
        print(f"   AI выводы: {'Да' if summary['has_ai_insights'] else 'Нет'}")
        print(f"   Рекомендации: {'Да' if summary['has_recommendations'] else 'Нет'}")
        
        print("\n🎉 Демонстрация завершена успешно!")
        print("Financial Brain готов к работе!")
        
    except Exception as e:
        print(f"❌ Ошибка в демонстрации: {e}")
        return False
    
    return True

def show_capabilities():
    """Показывает возможности системы"""
    print("\n🚀 Возможности Okama Financial Brain:")
    print("=" * 50)
    
    capabilities = [
        "🧠 Автоматическое распознавание намерений",
        "📝 Извлечение активов из естественного языка",
        "⚖️ Автоматическое извлечение весов портфеля",
        "💰 Определение валюты отчета",
        "📅 Анализ временных периодов",
        "📊 Построение аналитических отчетов",
        "🎨 Генерация графиков и визуализаций",
        "🤖 AI-анализ результатов",
        "💡 Практические рекомендации",
        "🔄 Fallback к традиционным командам"
    ]
    
    for capability in capabilities:
        print(f"   {capability}")
    
    print("\n💡 Примеры запросов:")
    examples = [
        '"Проанализируй Apple"',
        '"Сравни золото и серебро"',
        '"Портфель 60% акции, 40% облигации"',
        '"Анализ инфляции в США за 5 лет"',
        '"Сравни S&P 500 и NASDAQ в рублях"'
    ]
    
    for example in examples:
        print(f"   • {example}")

if __name__ == "__main__":
    print("🚀 Запуск демонстрации Okama Financial Brain")
    print("=" * 70)
    
    # Показываем возможности
    show_capabilities()
    
    # Запускаем демонстрацию
    success = demo_financial_brain()
    
    if success:
        print("\n🎯 Демонстрация прошла успешно!")
        print("Теперь вы можете использовать Financial Brain в боте!")
    else:
        print("\n❌ Демонстрация завершилась с ошибками")
        sys.exit(1)

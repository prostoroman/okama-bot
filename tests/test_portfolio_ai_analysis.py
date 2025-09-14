#!/usr/bin/env python3
"""
Test script for portfolio AI analysis functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import okama as ok

async def test_portfolio_ai_analysis():
    """Test the new portfolio AI analysis functionality"""
    print("🧪 Тестирование AI-анализа портфеля")
    print("=" * 50)
    
    # Initialize bot
    bot = ShansAi()
    
    # Test portfolio
    symbols = ['SPY.US', 'QQQ.US', 'BND.US']
    weights = [0.5, 0.3, 0.2]
    currency = 'USD'
    user_id = 12345
    
    print(f"📊 Тестовый портфель:")
    print(f"   Символы: {symbols}")
    print(f"   Веса: {weights}")
    print(f"   Валюта: {currency}")
    
    try:
        # Create portfolio object
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
        print(f"✅ Портфель создан успешно")
        
        # Test portfolio data preparation
        print(f"\n🔍 Подготовка данных для анализа...")
        portfolio_data = await bot._prepare_portfolio_data_for_analysis(
            portfolio=portfolio,
            symbols=symbols,
            weights=weights,
            currency=currency,
            user_id=user_id
        )
        
        print(f"✅ Данные портфеля подготовлены")
        print(f"   Тип анализа: {portfolio_data.get('analysis_type', 'N/A')}")
        print(f"   Количество активов: {len(portfolio_data.get('symbols', []))}")
        print(f"   Есть метрики портфеля: {'Да' if portfolio_data.get('portfolio_metrics_table') else 'Нет'}")
        print(f"   Есть метрики активов: {'Да' if portfolio_data.get('individual_assets_metrics') else 'Нет'}")
        print(f"   Есть корреляции: {'Да' if portfolio_data.get('correlations') else 'Нет'}")
        print(f"   Есть эффективная граница: {'Да' if portfolio_data.get('efficient_frontier') else 'Нет'}")
        
        # Test Gemini service availability
        if bot.gemini_service and bot.gemini_service.is_available():
            print(f"\n🤖 Тестирование Gemini анализа...")
            
            # Test portfolio analysis
            portfolio_analysis = bot.gemini_service.analyze_portfolio(portfolio_data)
            
            if portfolio_analysis and portfolio_analysis.get('success'):
                analysis_text = portfolio_analysis.get('analysis', '')
                print(f"✅ Анализ портфеля выполнен успешно")
                print(f"   Длина анализа: {len(analysis_text)} символов")
                print(f"   Тип анализа: {portfolio_analysis.get('analysis_type', 'N/A')}")
                
                # Show first 200 characters of analysis
                if analysis_text:
                    print(f"\n📝 Начало анализа:")
                    print(f"   {analysis_text[:200]}...")
            else:
                error_msg = portfolio_analysis.get('error', 'Неизвестная ошибка') if portfolio_analysis else 'Анализ не выполнен'
                print(f"❌ Ошибка анализа портфеля: {error_msg}")
        else:
            print(f"⚠️ Gemini сервис недоступен - пропускаем тест анализа")
        
        print(f"\n✅ Тест завершен успешно")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_portfolio_ai_analysis())

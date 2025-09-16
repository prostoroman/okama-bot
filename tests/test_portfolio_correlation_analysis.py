#!/usr/bin/env python3
"""
Test script to verify that correlation data is properly passed to Gemini portfolio analysis
"""

import sys
import os
import asyncio
import logging

# Add the parent directory to the path so we can import the bot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import okama as ok

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_portfolio_correlation_analysis():
    """Test that correlation data is properly included in portfolio AI analysis"""
    try:
        print("🧪 Тестирование передачи корреляции в AI анализ портфеля...")
        
        # Initialize bot
        bot = ShansAi()
        
        # Test symbols
        symbols = ['AAPL.US', 'MSFT.US', 'GOOGL.US']
        weights = [0.4, 0.3, 0.3]
        currency = 'USD'
        user_id = 12345
        
        print(f"📊 Тестовые активы: {symbols}")
        print(f"⚖️ Веса: {weights}")
        
        # Create portfolio
        try:
            portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
            print(f"✅ Портфель создан успешно")
        except Exception as e:
            print(f"❌ Ошибка создания портфеля: {e}")
            return
        
        # Test data preparation
        print(f"\n🔧 Тестирование подготовки данных...")
        portfolio_data = await bot._prepare_portfolio_data_for_analysis(
            portfolio=portfolio,
            symbols=symbols,
            weights=weights,
            currency=currency,
            user_id=user_id
        )
        
        if portfolio_data:
            print(f"✅ Данные портфеля подготовлены успешно")
            
            # Check if correlations are present
            correlations = portfolio_data.get('correlations', [])
            print(f"🔗 Корреляции: {'Есть' if correlations else 'Нет'}")
            
            if correlations:
                print(f"   Размер матрицы корреляции: {len(correlations)}x{len(correlations[0]) if correlations else 0}")
                
                # Show correlation values
                print(f"   Значения корреляции:")
                for i, symbol1 in enumerate(symbols):
                    for j, symbol2 in enumerate(symbols):
                        if i < j:  # Only upper triangle
                            corr = correlations[i][j]
                            print(f"     {symbol1} ↔ {symbol2}: {corr:.3f}")
            else:
                print(f"❌ Корреляции отсутствуют в данных портфеля")
            
            # Test Gemini service description preparation
            if bot.gemini_service and bot.gemini_service.is_available():
                print(f"\n🤖 Тестирование подготовки описания для Gemini...")
                
                # Test portfolio description preparation
                description = bot.gemini_service._prepare_portfolio_description(portfolio_data)
                
                if description:
                    print(f"✅ Описание для Gemini подготовлено успешно")
                    print(f"   Длина описания: {len(description)} символов")
                    
                    # Check if correlation section is in description
                    if "КОРРЕЛЯЦИОННАЯ МАТРИЦА" in description:
                        print(f"✅ Секция корреляции найдена в описании")
                        
                        # Extract correlation section
                        lines = description.split('\n')
                        correlation_section = []
                        in_correlation_section = False
                        
                        for line in lines:
                            if "КОРРЕЛЯЦИОННАЯ МАТРИЦА" in line:
                                in_correlation_section = True
                                correlation_section.append(line)
                            elif in_correlation_section:
                                if line.strip().startswith('•') and '↔' in line:
                                    correlation_section.append(line)
                                elif line.strip() and not line.strip().startswith('•'):
                                    break
                        
                        if correlation_section:
                            print(f"   Секция корреляции:")
                            for line in correlation_section:
                                print(f"     {line}")
                    else:
                        print(f"❌ Секция корреляции не найдена в описании")
                else:
                    print(f"❌ Описание для Gemini не подготовлено")
            else:
                print(f"⚠️ Gemini сервис недоступен - пропускаем тест описания")
            
            # Test full portfolio analysis
            if bot.gemini_service and bot.gemini_service.is_available():
                print(f"\n🤖 Тестирование полного анализа портфеля...")
                
                portfolio_analysis = bot.gemini_service.analyze_portfolio(portfolio_data)
                
                if portfolio_analysis and portfolio_analysis.get('success'):
                    analysis_text = portfolio_analysis.get('analysis', '')
                    print(f"✅ Анализ портфеля выполнен успешно")
                    print(f"   Длина анализа: {len(analysis_text)} символов")
                    
                    # Check if correlation is mentioned in analysis
                    if any(word in analysis_text.lower() for word in ['корреляц', 'correlation', 'связ']):
                        print(f"✅ Корреляция упоминается в анализе")
                    else:
                        print(f"⚠️ Корреляция не упоминается в анализе")
                else:
                    error_msg = portfolio_analysis.get('error', 'Неизвестная ошибка') if portfolio_analysis else 'Анализ не выполнен'
                    print(f"❌ Ошибка анализа портфеля: {error_msg}")
            else:
                print(f"⚠️ Gemini сервис недоступен - пропускаем тест анализа")
        else:
            print(f"❌ Данные портфеля не подготовлены")
        
        print(f"\n✅ Тест завершен")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_portfolio_correlation_analysis())

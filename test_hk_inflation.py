#!/usr/bin/env python3
"""
Тест для проверки доступности тикера инфляции HK.INFL в okama
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_hk_inflation_ticker():
    """Тест доступности тикера HK.INFL"""
    try:
        import okama as ok
        
        print("🧪 Тестирование доступности тикеров инфляции...")
        
        # Список тикеров инфляции для проверки
        inflation_tickers = [
            'US.INFL',
            'CNY.INFL', 
            'HK.INFL',
            'CN.INFL',
            'RUS.INFL',
            'EU.INFL',
            'GB.INFL'
        ]
        
        available_tickers = []
        unavailable_tickers = []
        
        for ticker in inflation_tickers:
            try:
                print(f"📊 Проверяем {ticker}...")
                asset = ok.Asset(ticker)
                print(f"✅ {ticker} - доступен")
                available_tickers.append(ticker)
            except Exception as e:
                print(f"❌ {ticker} - недоступен: {e}")
                unavailable_tickers.append(ticker)
        
        print(f"\n📈 Доступные тикеры инфляции: {available_tickers}")
        print(f"❌ Недоступные тикеры: {unavailable_tickers}")
        
        # Проверяем, есть ли HK.INFL
        if 'HK.INFL' in available_tickers:
            print("✅ HK.INFL доступен - можно использовать для HKD")
            return 'HK.INFL'
        elif 'CNY.INFL' in available_tickers:
            print("⚠️ HK.INFL недоступен, но CNY.INFL доступен")
            return 'CNY.INFL'
        else:
            print("⚠️ Ни HK.INFL, ни CNY.INFL недоступны, используем US.INFL")
            return 'US.INFL'
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return 'US.INFL'

if __name__ == "__main__":
    recommended_ticker = test_hk_inflation_ticker()
    print(f"\n🎯 Рекомендуемый тикер для HKD: {recommended_ticker}")

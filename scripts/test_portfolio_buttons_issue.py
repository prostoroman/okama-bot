#!/usr/bin/env python3
"""
Test script to reproduce the portfolio buttons issue
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tushare_service import TushareService
import okama as ok

def test_portfolio_creation():
    """Test portfolio creation with the same symbols as the user"""
    
    print("Testing portfolio creation with SBER.MOEX, GAZP.MOEX, LKOH.MOEX...")
    
    try:
        # Create portfolio with the same symbols
        symbols = ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']
        weights = [0.4, 0.3, 0.3]
        
        # Create portfolio
        portfolio = ok.Portfolio(symbols, weights=weights, ccy='RUB')
        
        print(f"Portfolio created successfully!")
        print(f"Portfolio symbol: {getattr(portfolio, 'symbol', 'No symbol attribute')}")
        
        # Test portfolio string representation
        portfolio_str = f"{portfolio}"
        print(f"\nPortfolio string representation:")
        print(portfolio_str)
        print(f"String length: {len(portfolio_str)}")
        
        # Check for potential Markdown issues
        problematic_chars = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        found_chars = []
        for char in problematic_chars:
            if char in portfolio_str:
                found_chars.append(char)
        
        if found_chars:
            print(f"\nPotentially problematic Markdown characters found: {found_chars}")
        else:
            print(f"\nNo problematic Markdown characters found")
        
        # Test button creation
        portfolio_symbol = getattr(portfolio, 'symbol', 'PF_1')
        print(f"\nTesting button creation with symbol: {portfolio_symbol}")
        
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        
        keyboard = [
            [InlineKeyboardButton("📈 График накопленной доходности", callback_data=f"portfolio_wealth_chart_{portfolio_symbol}")],
            [InlineKeyboardButton("💰 Доходность", callback_data=f"portfolio_returns_{portfolio_symbol}")],
            [InlineKeyboardButton("📉 Просадки", callback_data=f"portfolio_drawdowns_{portfolio_symbol}")],
            [InlineKeyboardButton("📊 Риск метрики", callback_data=f"portfolio_risk_metrics_{portfolio_symbol}")],
            [InlineKeyboardButton("🎲 Монте Карло", callback_data=f"portfolio_monte_carlo_{portfolio_symbol}")],
            [InlineKeyboardButton("📈 Процентили 10, 50, 90", callback_data=f"portfolio_forecast_{portfolio_symbol}")],
            [InlineKeyboardButton("📊 Портфель vs Активы", callback_data=f"portfolio_compare_assets_{portfolio_symbol}")],
            [InlineKeyboardButton("📈 Rolling CAGR", callback_data=f"portfolio_rolling_cagr_{portfolio_symbol}")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        print(f"Created keyboard with {len(keyboard)} buttons")
        for i, button_row in enumerate(keyboard):
            for j, button in enumerate(button_row):
                print(f"Button [{i}][{j}]: '{button.text}' -> '{button.callback_data}' (length: {len(button.callback_data)})")
        
        # Test final message
        final_message = portfolio_str + f"\n\n🏷️ Символ портфеля: `{portfolio_symbol}`\n💾 Портфель сохранен в контексте для использования в /compare"
        print(f"\nFinal message length: {len(final_message)}")
        
        if len(final_message) > 4000:
            print("⚠️  WARNING: Message is longer than 4000 characters!")
        
        print("\n✅ Portfolio creation and button generation test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during portfolio creation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_portfolio_creation()

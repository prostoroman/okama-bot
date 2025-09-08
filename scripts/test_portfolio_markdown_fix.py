#!/usr/bin/env python3
"""
Test script to verify the Markdown escaping fix for portfolio buttons
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok

def escape_markdown(text: str) -> str:
    """Escape special Markdown characters"""
    if not text:
        return text
    
    # Escape special Markdown characters
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text

def test_portfolio_markdown_fix():
    """Test the Markdown escaping fix"""
    
    print("Testing Markdown escaping fix for portfolio creation...")
    
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
        print(f"\nOriginal portfolio string:")
        print(portfolio_str)
        
        # Apply Markdown escaping
        escaped_portfolio_str = escape_markdown(portfolio_str)
        print(f"\nEscaped portfolio string:")
        print(escaped_portfolio_str)
        
        # Test final message
        portfolio_symbol = getattr(portfolio, 'symbol', 'PF_1')
        final_message = escaped_portfolio_str + f"\n\n🏷️ Символ портфеля: `{portfolio_symbol}`\n💾 Портфель сохранен в контексте для использования в /compare"
        
        print(f"\nFinal message length: {len(final_message)}")
        
        # Test button creation
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
        
        print(f"\nCreated keyboard with {len(keyboard)} buttons")
        for i, button_row in enumerate(keyboard):
            for j, button in enumerate(button_row):
                print(f"Button [{i}][{j}]: '{button.text}' -> '{button.callback_data}' (length: {len(button.callback_data)})")
        
        print("\n✅ Markdown escaping fix test completed successfully!")
        print("The portfolio text should now be safe for Markdown parsing.")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_portfolio_markdown_fix()

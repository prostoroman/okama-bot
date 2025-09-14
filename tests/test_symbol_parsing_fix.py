#!/usr/bin/env python3
"""
Test script to verify the symbol parsing fix for compare command.
Tests that trailing commas are properly stripped from asset symbols.
"""

import sys
import os

# Add the parent directory to the path so we can import the bot module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import logging

def test_symbol_parsing():
    """Test that symbol parsing correctly handles trailing commas"""
    
    # Create a mock bot instance (we only need the parsing method)
    bot = ShansAi()
    
    # Test case 1: Symbols with trailing commas (the original issue)
    test_args = ['SBER.MOEX,', 'LKOH.MOEX,', 'LQDT.MOEX,', 'OBLG.MOEX,', 'GOLD.MOEX']
    symbols, currency, period = bot._parse_currency_and_period(test_args)
    
    print("Test Case 1: Symbols with trailing commas")
    print(f"Input: {test_args}")
    print(f"Output symbols: {symbols}")
    print(f"Expected: ['SBER.MOEX', 'LKOH.MOEX', 'LQDT.MOEX', 'OBLG.MOEX', 'GOLD.MOEX']")
    
    expected_symbols = ['SBER.MOEX', 'LKOH.MOEX', 'LQDT.MOEX', 'OBLG.MOEX', 'GOLD.MOEX']
    assert symbols == expected_symbols, f"Expected {expected_symbols}, got {symbols}"
    print("✅ Test Case 1 PASSED\n")
    
    # Test case 2: Mixed symbols with and without commas
    test_args2 = ['AAPL.US', 'MSFT.US,', 'GOOGL.US']
    symbols2, currency2, period2 = bot._parse_currency_and_period(test_args2)
    
    print("Test Case 2: Mixed symbols with and without commas")
    print(f"Input: {test_args2}")
    print(f"Output symbols: {symbols2}")
    print(f"Expected: ['AAPL.US', 'MSFT.US', 'GOOGL.US']")
    
    expected_symbols2 = ['AAPL.US', 'MSFT.US', 'GOOGL.US']
    assert symbols2 == expected_symbols2, f"Expected {expected_symbols2}, got {symbols2}"
    print("✅ Test Case 2 PASSED\n")
    
    # Test case 3: Symbols with weights and commas
    test_args3 = ['AAPL.US:0.5,', 'MSFT.US:0.3', 'GOOGL.US:0.2,']
    symbols3, currency3, period3 = bot._parse_currency_and_period(test_args3, preserve_weights=False)
    
    print("Test Case 3: Symbols with weights and commas (compare command)")
    print(f"Input: {test_args3}")
    print(f"Output symbols: {symbols3}")
    print(f"Expected: ['AAPL.US', 'MSFT.US', 'GOOGL.US']")
    
    expected_symbols3 = ['AAPL.US', 'MSFT.US', 'GOOGL.US']
    assert symbols3 == expected_symbols3, f"Expected {expected_symbols3}, got {symbols3}"
    print("✅ Test Case 3 PASSED\n")
    
    # Test case 4: Currency and period with comma symbols
    test_args4 = ['SBER.MOEX,', 'LKOH.MOEX,', 'USD', '5Y']
    symbols4, currency4, period4 = bot._parse_currency_and_period(test_args4)
    
    print("Test Case 4: Currency and period with comma symbols")
    print(f"Input: {test_args4}")
    print(f"Output symbols: {symbols4}")
    print(f"Output currency: {currency4}")
    print(f"Output period: {period4}")
    print(f"Expected symbols: ['SBER.MOEX', 'LKOH.MOEX']")
    print(f"Expected currency: USD")
    print(f"Expected period: 5Y")
    
    expected_symbols4 = ['SBER.MOEX', 'LKOH.MOEX']
    assert symbols4 == expected_symbols4, f"Expected {expected_symbols4}, got {symbols4}"
    assert currency4 == 'USD', f"Expected USD, got {currency4}"
    assert period4 == '5Y', f"Expected 5Y, got {period4}"
    print("✅ Test Case 4 PASSED\n")
    
    print("🎉 All tests passed! The symbol parsing fix is working correctly.")

if __name__ == "__main__":
    test_symbol_parsing()

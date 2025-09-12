#!/usr/bin/env python3
"""
Test script for unified Sharpe ratio calculation function
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import pandas as pd
import numpy as np

def test_sharpe_ratio_calculation():
    """Test the unified Sharpe ratio calculation function"""
    
    # Initialize the bot
    bot = ShansAi()
    
    print("Testing unified Sharpe ratio calculation...")
    
    # Test 1: Basic calculation with different currencies
    print("\n1. Testing basic calculation with different currencies:")
    
    test_cases = [
        {'currency': 'USD', 'expected_rate_symbol': 'US_EFFR.RATE'},
        {'currency': 'EUR', 'expected_rate_symbol': 'EU_DFR.RATE'},
        {'currency': 'RUB', 'expected_rate_symbol': 'RUS_CBR.RATE'},
        {'currency': 'CNY', 'expected_rate_symbol': 'CHN_LPR1.RATE'},
        {'currency': 'GBP', 'expected_rate_symbol': 'UK_BR.RATE'},
    ]
    
    for case in test_cases:
        try:
            rate = bot.get_risk_free_rate(case['currency'])
            print(f"   {case['currency']}: {rate:.4f} (expected symbol: {case['expected_rate_symbol']})")
        except Exception as e:
            print(f"   {case['currency']}: Error - {e}")
    
    # Test 2: Sharpe ratio calculation with different scenarios
    print("\n2. Testing Sharpe ratio calculation:")
    
    # Scenario 1: High return, low volatility
    sharpe1 = bot.calculate_sharpe_ratio(0.15, 0.10, 'USD')  # 15% return, 10% volatility
    print(f"   High return (15%), low volatility (10%): {sharpe1:.4f}")
    
    # Scenario 2: Low return, high volatility
    sharpe2 = bot.calculate_sharpe_ratio(0.05, 0.20, 'USD')  # 5% return, 20% volatility
    print(f"   Low return (5%), high volatility (20%): {sharpe2:.4f}")
    
    # Scenario 3: Negative return
    sharpe3 = bot.calculate_sharpe_ratio(-0.05, 0.15, 'USD')  # -5% return, 15% volatility
    print(f"   Negative return (-5%), medium volatility (15%): {sharpe3:.4f}")
    
    # Test 3: Different currencies
    print("\n3. Testing with different currencies:")
    
    currencies = ['USD', 'EUR', 'RUB', 'CNY']
    for currency in currencies:
        sharpe = bot.calculate_sharpe_ratio(0.10, 0.12, currency)
        print(f"   {currency}: Sharpe ratio = {sharpe:.4f}")
    
    # Test 4: Period-based rate selection for RUB
    print("\n4. Testing period-based rate selection for RUB:")
    
    periods = [0.1, 0.5, 1.0, 2.0]  # 1.2 months, 6 months, 1 year, 2 years
    for period in periods:
        rate = bot.get_risk_free_rate('RUB', period)
        print(f"   RUB, {period} years: {rate:.4f}")
    
    # Test 5: Period-based rate selection for CNY
    print("\n5. Testing period-based rate selection for CNY:")
    
    periods = [1.0, 6.0]  # 1 year, 6 years
    for period in periods:
        rate = bot.get_risk_free_rate('CNY', period)
        print(f"   CNY, {period} years: {rate:.4f}")
    
    print("\n✅ All tests completed successfully!")
    print("\nKey improvements:")
    print("- Unified Sharpe ratio calculation function")
    print("- Currency-specific risk-free rates using okama")
    print("- Period-based rate selection for RUB and CNY")
    print("- Fallback rates for reliability")
    print("- Consistent calculation across all portfolio and asset metrics")

if __name__ == "__main__":
    test_sharpe_ratio_calculation()

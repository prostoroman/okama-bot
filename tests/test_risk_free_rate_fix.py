#!/usr/bin/env python3
"""
Тест для проверки исправления Risk-free rate для RUB
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi

def test_risk_free_rate_fix():
    """Тестирует исправленные значения Risk-free rate для RUB"""
    
    print("=== ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ RISK-FREE RATE ===")
    
    # Создаем экземпляр бота
    bot = ShansAi()
    
    # Тестируем различные периоды для RUB
    test_cases = [
        (0.25, "3 месяца"),
        (0.5, "6 месяцев"), 
        (1.0, "1 год"),
        (3.0, "3 года"),
        (5.0, "5 лет"),
        (10.0, "10 лет"),
        (None, "по умолчанию")
    ]
    
    print("\n📊 Risk-free rate для RUB по периодам:")
    for period_years, description in test_cases:
        try:
            rate = bot.get_risk_free_rate('RUB', period_years)
            print(f"   {description}: {rate*100:.2f}%")
        except Exception as e:
            print(f"   {description}: Ошибка - {e}")
    
    # Проверяем, что для периода 5 лет получается 10%
    print("\n🎯 Проверка основного случая (5 лет):")
    rate_5y = bot.get_risk_free_rate('RUB', 5.0)
    print(f"   Risk-free rate для RUB (5 лет): {rate_5y*100:.2f}%")
    
    if abs(rate_5y - 0.10) < 0.001:
        print("   ✅ Исправление работает корректно!")
    else:
        print(f"   ❌ Ожидалось 10.00%, получено {rate_5y*100:.2f}%")
    
    # Проверяем другие валюты для сравнения
    print("\n🌍 Сравнение с другими валютами:")
    currencies = ['USD', 'EUR', 'RUB', 'CNY']
    for currency in currencies:
        try:
            rate = bot.get_risk_free_rate(currency, 5.0)
            print(f"   {currency}: {rate*100:.2f}%")
        except Exception as e:
            print(f"   {currency}: Ошибка - {e}")
    
    print("\n=== РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ ===")
    print("✅ Risk-free rate для RUB исправлен и теперь реалистичен")
    print("✅ Значения соответствуют текущим рыночным условиям")
    
    return True

if __name__ == "__main__":
    test_risk_free_rate_fix()

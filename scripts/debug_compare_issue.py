#!/usr/bin/env python3
"""
Скрипт для диагностики проблемы с командой /compare sber.moex oblg.moex
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
from unittest.mock import Mock, patch

def debug_compare_issue():
    """Диагностика проблемы с командой compare"""
    
    # Мокаем конфигурацию
    with patch('bot.Config') as mock_config:
        mock_config.validate.return_value = None
        bot = ShansAi()
    
    # Симулируем команду /compare sber.moex oblg.moex
    symbols = ['sber.moex', 'oblg.moex']
    
    print("🔍 Диагностика команды /compare sber.moex oblg.moex")
    print("=" * 50)
    
    # Симулируем пустой контекст пользователя (нет сохраненных портфелей)
    user_context = {'saved_portfolios': {}}
    saved_portfolios = user_context.get('saved_portfolios', {})
    
    print(f"📊 Сохраненные портфели: {list(saved_portfolios.keys())}")
    print()
    
    expanded_symbols = []
    portfolio_descriptions = []
    portfolio_contexts = []
    
    for symbol in symbols:
        print(f"🔍 Обработка символа: '{symbol}'")
        
        # Проверяем, является ли символ портфелем
        is_portfolio = symbol in saved_portfolios
        print(f"   🔍 is_portfolio после проверки в saved_portfolios: {is_portfolio}")
        
        # Additional check: avoid treating asset symbols as portfolios
        if is_portfolio and ('.' in symbol and 
            not any(indicator in symbol.upper() for indicator in ['PORTFOLIO_', 'PF_', '.PF', '.pf'])):
            # This looks like an asset symbol, not a portfolio
            print(f"   🔍 Дополнительная проверка: символ '{symbol}' содержит '.' и не имеет индикаторов портфеля")
            print(f"   🔍 Индикаторы портфеля: {[indicator for indicator in ['PORTFOLIO_', 'PF_', '.PF', '.pf'] if indicator in symbol.upper()]}")
            is_portfolio = False
            print(f"   ✅ Символ '{symbol}' переопределен как актив")
        else:
            print(f"   🔍 Дополнительная проверка НЕ применена:")
            print(f"   🔍   is_portfolio: {is_portfolio}")
            print(f"   🔍   содержит '.': {'.' in symbol}")
            print(f"   🔍   индикаторы портфеля: {[indicator for indicator in ['PORTFOLIO_', 'PF_', '.PF', '.pf'] if indicator in symbol.upper()]}")
        
        if not is_portfolio:
            # Проверяем case-insensitive match
            for portfolio_key in saved_portfolios.keys():
                if (symbol.lower() == portfolio_key.lower() or
                    symbol.upper() == portfolio_key.upper()):
                    # Additional check: avoid treating asset symbols as portfolios
                    if ('.' in symbol and 
                        not any(indicator in symbol.upper() for indicator in ['PORTFOLIO_', 'PF_', '.PF', '.pf'])):
                        # This looks like an asset symbol, not a portfolio
                        is_portfolio = False
                        break
                    else:
                        # Use the exact key from saved_portfolios
                        symbol = portfolio_key
                        is_portfolio = True
                        break
        
        print(f"   is_portfolio: {is_portfolio}")
        print(f"   в saved_portfolios: {symbol in saved_portfolios}")
        
        if is_portfolio:
            print(f"   ❌ ОШИБКА: Символ '{symbol}' распознан как портфель!")
            # Это не должно происходить для обычных активов
        else:
            print(f"   ✅ Символ '{symbol}' распознан как актив")
            # Обычный актив
            expanded_symbols.append(symbol)
            portfolio_descriptions.append(symbol)
            portfolio_contexts.append({
                'symbol': symbol,
                'portfolio_symbols': [symbol],
                'portfolio_weights': [1.0],
                'portfolio_currency': None,
                'portfolio_object': None
            })
        
        print()
    
    print("📋 Результат обработки:")
    print(f"   expanded_symbols: {expanded_symbols}")
    print(f"   portfolio_descriptions: {portfolio_descriptions}")
    print(f"   portfolio_contexts: {[ctx['symbol'] for ctx in portfolio_contexts]}")
    print()
    
    # Проверяем типы для определения типа сравнения
    try:
        has_portfolios_only = all(isinstance(s, (Mock,)) for s in expanded_symbols)
        has_assets_only = all(not isinstance(s, (Mock,)) for s in expanded_symbols)
        is_mixed_comparison = not (has_portfolios_only or has_assets_only)
        
        print("🔍 Определение типа сравнения:")
        print(f"   has_portfolios_only: {has_portfolios_only}")
        print(f"   has_assets_only: {has_assets_only}")
        print(f"   is_mixed_comparison: {is_mixed_comparison}")
        
        if has_assets_only:
            print("   ✅ Правильно: сравнение только активов")
        elif has_portfolios_only:
            print("   ❌ ОШИБКА: сравнение только портфелей (не должно быть)")
        elif is_mixed_comparison:
            print("   ❌ ОШИБКА: смешанное сравнение (не должно быть)")
            
    except Exception as e:
        print(f"   ❌ ОШИБКА при определении типа: {e}")
    
    print()
    print("🎯 Ожидаемый результат:")
    print("   - expanded_symbols: ['sber.moex', 'oblg.moex']")
    print("   - has_assets_only: True")
    print("   - is_mixed_comparison: False")
    print("   - has_portfolios_only: False")

def test_with_existing_portfolios():
    """Тест с существующими портфелями"""
    print("\n" + "=" * 50)
    print("🧪 Тест с существующими портфелями")
    print("=" * 50)
    
    # Симулируем контекст с портфелями
    user_context = {
        'saved_portfolios': {
            'sber.moex': {
                'symbols': ['SBER.MOEX', 'GAZP.MOEX'],
                'weights': [0.7, 0.3],
                'currency': 'RUB'
            },
            'oblg.moex': {
                'symbols': ['OBLG.MOEX', 'SUGD.MOEX'],
                'weights': [0.6, 0.4],
                'currency': 'RUB'
            }
        }
    }
    
    saved_portfolios = user_context.get('saved_portfolios', {})
    symbols = ['sber.moex', 'oblg.moex']
    
    print(f"📊 Сохраненные портфели: {list(saved_portfolios.keys())}")
    print()
    
    for symbol in symbols:
        print(f"🔍 Обработка символа: '{symbol}'")
        
        is_portfolio = symbol in saved_portfolios
        print(f"   🔍 is_portfolio после проверки в saved_portfolios: {is_portfolio}")
        
        # Additional check: avoid treating asset symbols as portfolios
        if is_portfolio and ('.' in symbol and 
            not any(indicator in symbol.upper() for indicator in ['PORTFOLIO_', 'PF_', '.PF', '.pf'])):
            # This looks like an asset symbol, not a portfolio
            print(f"   🔍 Дополнительная проверка: символ '{symbol}' содержит '.' и не имеет индикаторов портфеля")
            print(f"   🔍 Индикаторы портфеля: {[indicator for indicator in ['PORTFOLIO_', 'PF_', '.PF', '.pf'] if indicator in symbol.upper()]}")
            is_portfolio = False
            print(f"   ✅ Символ '{symbol}' переопределен как актив")
        else:
            print(f"   🔍 Дополнительная проверка НЕ применена:")
            print(f"   🔍   is_portfolio: {is_portfolio}")
            print(f"   🔍   содержит '.': {'.' in symbol}")
            print(f"   🔍   индикаторы портфеля: {[indicator for indicator in ['PORTFOLIO_', 'PF_', '.PF', '.pf'] if indicator in symbol.upper()]}")
        
        if not is_portfolio:
            for portfolio_key in saved_portfolios.keys():
                if (symbol.lower() == portfolio_key.lower() or
                    symbol.upper() == portfolio_key.upper()):
                    # Additional check: avoid treating asset symbols as portfolios
                    if ('.' in symbol and 
                        not any(indicator in symbol.upper() for indicator in ['PORTFOLIO_', 'PF_', '.PF', '.pf'])):
                        # This looks like an asset symbol, not a portfolio
                        is_portfolio = False
                        break
                    else:
                        # Use the exact key from saved_portfolios
                        symbol = portfolio_key
                        is_portfolio = True
                        break
        
        print(f"   is_portfolio: {is_portfolio}")
        
        if is_portfolio:
            print(f"   ✅ Символ '{symbol}' распознан как портфель")
            portfolio_info = saved_portfolios[symbol]
            print(f"   Состав: {portfolio_info['symbols']}")
            print(f"   Веса: {portfolio_info['weights']}")
        else:
            print(f"   ❌ Символ '{symbol}' НЕ распознан как портфель")
        
        print()

if __name__ == '__main__':
    debug_compare_issue()
    test_with_existing_portfolios()

#!/usr/bin/env python3
"""
Тест для проверки исправления проблемы с Sharpe Ratio и Calmar Ratio
Проверяем что SPY.US и VTI.US теперь возвращают корректные значения
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
import numpy as np

def test_sharpe_calmar_fix():
    """Тестируем исправленный расчет Sharpe и Calmar Ratio для SPY.US и VTI.US"""
    
    symbols = ['SPY.US', 'VTI.US']
    currency = 'USD'
    
    print("=== ТЕСТ ИСПРАВЛЕНИЯ SHARPE И CALMAR RATIO ===")
    print(f"Символы: {symbols}")
    print(f"Валюта: {currency}")
    print()
    
    try:
        # Создаем AssetList
        asset_list = ok.AssetList(symbols, ccy=currency)
        describe_data = asset_list.describe()
        
        # Имитируем исправленную логику из bot.py
        risk_free_rate = 0.05  # 5% для USD
        
        print("=== РЕЗУЛЬТАТЫ ИСПРАВЛЕННОГО РАСЧЕТА ===")
        
        for symbol in symbols:
            print(f"=== {symbol} ===")
            
            # Исправленная логика поиска CAGR и Risk
            cagr_value = None
            risk_value = None
            max_drawdown_value = None
            
            # Try to find 5-year period first, then fallback to available periods
            for idx in describe_data.index:
                property_name = describe_data.loc[idx, 'property']
                period = describe_data.loc[idx, 'period']
                
                if symbol in describe_data.columns:
                    value = describe_data.loc[idx, symbol]
                    if not pd.isna(value):
                        # Look for 5-year CAGR first
                        if property_name == 'CAGR' and ('5 years' in str(period) or period == '5 years'):
                            cagr_value = value
                        # Look for Risk - try 5-year first, then any available
                        elif property_name == 'Risk' and ('5 years' in str(period) or period == '5 years'):
                            risk_value = value
                        # Look for Max drawdowns - try 5-year first, then any available
                        elif property_name == 'Max drawdowns' and ('5 years' in str(period) or period == '5 years'):
                            max_drawdown_value = value
            
            # If we didn't find 5-year Risk, try to find any Risk period
            if risk_value is None:
                for idx in describe_data.index:
                    property_name = describe_data.loc[idx, 'property']
                    period = describe_data.loc[idx, 'period']
                    
                    if symbol in describe_data.columns:
                        value = describe_data.loc[idx, symbol]
                        if not pd.isna(value) and property_name == 'Risk':
                            risk_value = value
                            break
            
            # If we didn't find 5-year CAGR, try to find any CAGR period
            if cagr_value is None:
                for idx in describe_data.index:
                    property_name = describe_data.loc[idx, 'property']
                    period = describe_data.loc[idx, 'period']
                    
                    if symbol in describe_data.columns:
                        value = describe_data.loc[idx, symbol]
                        if not pd.isna(value) and property_name == 'CAGR':
                            cagr_value = value
                            break
            
            # If we didn't find 5-year Max drawdowns, try to find any Max drawdowns period
            if max_drawdown_value is None:
                for idx in describe_data.index:
                    property_name = describe_data.loc[idx, 'property']
                    period = describe_data.loc[idx, 'period']
                    
                    if symbol in describe_data.columns:
                        value = describe_data.loc[idx, symbol]
                        if not pd.isna(value) and property_name == 'Max drawdowns':
                            max_drawdown_value = value
                            break
            
            print(f"  CAGR: {cagr_value}")
            print(f"  Risk: {risk_value}")
            print(f"  Max drawdown: {max_drawdown_value}")
            print(f"  Risk-free rate: {risk_free_rate}")
            
            # Расчет Sharpe Ratio
            if cagr_value is not None and risk_value is not None and risk_value > 0:
                sharpe = (cagr_value - risk_free_rate) / risk_value
                print(f"  Sharpe Ratio: {sharpe:.3f}")
            else:
                print(f"  Sharpe Ratio: N/A (cagr={cagr_value}, risk={risk_value})")
            
            # Расчет Calmar Ratio
            if cagr_value is not None and max_drawdown_value is not None and max_drawdown_value < 0:
                calmar = cagr_value / abs(max_drawdown_value)
                print(f"  Calmar Ratio: {calmar:.3f}")
            else:
                print(f"  Calmar Ratio: N/A (cagr={cagr_value}, max_dd={max_drawdown_value})")
            
            print()
        
        # Проверяем что теперь есть значения
        print("=== ПРОВЕРКА УСПЕШНОСТИ ИСПРАВЛЕНИЯ ===")
        success_count = 0
        total_tests = len(symbols) * 2  # 2 метрики на символ
        
        for symbol in symbols:
            # Повторяем расчет для проверки
            cagr_value = None
            risk_value = None
            max_drawdown_value = None
            
            # Поиск значений
            for idx in describe_data.index:
                property_name = describe_data.loc[idx, 'property']
                period = describe_data.loc[idx, 'period']
                
                if symbol in describe_data.columns:
                    value = describe_data.loc[idx, symbol]
                    if not pd.isna(value):
                        if property_name == 'CAGR' and ('5 years' in str(period) or period == '5 years'):
                            cagr_value = value
                        elif property_name == 'Risk' and ('5 years' in str(period) or period == '5 years'):
                            risk_value = value
                        elif property_name == 'Max drawdowns' and ('5 years' in str(period) or period == '5 years'):
                            max_drawdown_value = value
            
            # Fallback поиск
            if risk_value is None:
                for idx in describe_data.index:
                    property_name = describe_data.loc[idx, 'property']
                    if symbol in describe_data.columns:
                        value = describe_data.loc[idx, symbol]
                        if not pd.isna(value) and property_name == 'Risk':
                            risk_value = value
                            break
            
            if cagr_value is None:
                for idx in describe_data.index:
                    property_name = describe_data.loc[idx, 'property']
                    if symbol in describe_data.columns:
                        value = describe_data.loc[idx, symbol]
                        if not pd.isna(value) and property_name == 'CAGR':
                            cagr_value = value
                            break
            
            if max_drawdown_value is None:
                for idx in describe_data.index:
                    property_name = describe_data.loc[idx, 'property']
                    if symbol in describe_data.columns:
                        value = describe_data.loc[idx, symbol]
                        if not pd.isna(value) and property_name == 'Max drawdowns':
                            max_drawdown_value = value
                            break
            
            # Проверка Sharpe Ratio
            if cagr_value is not None and risk_value is not None and risk_value > 0:
                sharpe = (cagr_value - risk_free_rate) / risk_value
                print(f"✅ {symbol} Sharpe Ratio: {sharpe:.3f}")
                success_count += 1
            else:
                print(f"❌ {symbol} Sharpe Ratio: N/A")
            
            # Проверка Calmar Ratio
            if cagr_value is not None and max_drawdown_value is not None and max_drawdown_value < 0:
                calmar = cagr_value / abs(max_drawdown_value)
                print(f"✅ {symbol} Calmar Ratio: {calmar:.3f}")
                success_count += 1
            else:
                print(f"❌ {symbol} Calmar Ratio: N/A")
        
        print(f"\n=== ИТОГ ===")
        print(f"Успешных расчетов: {success_count}/{total_tests}")
        if success_count == total_tests:
            print("🎉 Все метрики рассчитаны успешно!")
        else:
            print("⚠️ Некоторые метрики все еще возвращают N/A")
        
    except Exception as e:
        print(f"Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sharpe_calmar_fix()

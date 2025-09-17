#!/usr/bin/env python3
"""
Тест для отладки проблемы с Sharpe Ratio и Calmar Ratio в сравнении метрик
Проверяем почему SPY.US и VTI.US возвращают N/A
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
import numpy as np

def test_sharpe_calmar_debug():
    """Тестируем расчет Sharpe и Calmar Ratio для SPY.US и VTI.US"""
    
    symbols = ['SPY.US', 'VTI.US']
    currency = 'USD'
    
    print("=== ОТЛАДКА SHARPE И CALMAR RATIO ===")
    print(f"Символы: {symbols}")
    print(f"Валюта: {currency}")
    print()
    
    try:
        # Создаем AssetList
        asset_list = ok.AssetList(symbols, ccy=currency)
        describe_data = asset_list.describe()
        
        print("=== ДАННЫЕ DESCRIBE ===")
        print(describe_data)
        print()
        
        # Проверяем каждый символ
        for symbol in symbols:
            print(f"=== АНАЛИЗ {symbol} ===")
            
            # Ищем CAGR и Risk для 5-летнего периода
            cagr_value = None
            risk_value = None
            max_drawdown_value = None
            
            for idx in describe_data.index:
                property_name = describe_data.loc[idx, 'property']
                period = describe_data.loc[idx, 'period']
                
                if symbol in describe_data.columns:
                    value = describe_data.loc[idx, symbol]
                    print(f"  {property_name} ({period}): {value}")
                    
                    if not pd.isna(value):
                        if property_name == 'CAGR' and period == '5 years, 1 months':
                            cagr_value = value
                        elif property_name == 'Risk' and period == '5 years, 1 months':
                            risk_value = value
                        elif property_name == 'Max drawdowns' and period == '5 years, 1 months':
                            max_drawdown_value = value
            
            print(f"  CAGR (5 лет): {cagr_value}")
            print(f"  Risk (5 лет): {risk_value}")
            print(f"  Max drawdown (5 лет): {max_drawdown_value}")
            
            # Проверяем безрисковую ставку
            try:
                # Имитируем логику из bot.py
                if currency == 'USD':
                    risk_free_rate = 0.05  # 5% для USD
                elif currency == 'RUB':
                    risk_free_rate = 0.14  # 14% для RUB
                else:
                    risk_free_rate = 0.05  # По умолчанию
                
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
                    
            except Exception as e:
                print(f"  Ошибка при расчете: {e}")
            
            print()
        
        # Проверяем альтернативные периоды
        print("=== ПРОВЕРКА АЛЬТЕРНАТИВНЫХ ПЕРИОДОВ ===")
        for symbol in symbols:
            print(f"=== {symbol} - ВСЕ ПЕРИОДЫ ===")
            for idx in describe_data.index:
                property_name = describe_data.loc[idx, 'property']
                period = describe_data.loc[idx, 'period']
                
                if symbol in describe_data.columns:
                    value = describe_data.loc[idx, symbol]
                    if not pd.isna(value) and property_name in ['CAGR', 'Risk', 'Max drawdowns']:
                        print(f"  {property_name} ({period}): {value}")
            print()
        
        # Проверяем данные активов напрямую
        print("=== ПРОВЕРКА ДАННЫХ АКТИВОВ НАПРЯМУЮ ===")
        for symbol in symbols:
            print(f"=== {symbol} - ПРЯМЫЕ ДАННЫЕ ===")
            try:
                asset = ok.Asset(symbol)
                
                # Проверяем доступные атрибуты
                print(f"  Доступные атрибуты: {[attr for attr in dir(asset) if not attr.startswith('_')]}")
                
                # Проверяем основные метрики
                if hasattr(asset, 'annual_return'):
                    print(f"  annual_return: {asset.annual_return}")
                
                if hasattr(asset, 'risk_annual'):
                    print(f"  risk_annual: {asset.risk_annual}")
                
                if hasattr(asset, 'get_sharpe_ratio'):
                    try:
                        sharpe = asset.get_sharpe_ratio()
                        print(f"  get_sharpe_ratio(): {sharpe}")
                    except Exception as e:
                        print(f"  get_sharpe_ratio() error: {e}")
                
                if hasattr(asset, 'wealth_index'):
                    try:
                        wealth_index = asset.wealth_index
                        print(f"  wealth_index length: {len(wealth_index)}")
                        
                        # Рассчитываем max drawdown вручную
                        if len(wealth_index) > 0:
                            running_max = wealth_index.expanding().max()
                            drawdown = (wealth_index - running_max) / running_max
                            max_dd = drawdown.min()
                            print(f"  Calculated max drawdown: {max_dd:.4f}")
                    except Exception as e:
                        print(f"  wealth_index error: {e}")
                
            except Exception as e:
                print(f"  Ошибка при работе с активом: {e}")
            print()
        
    except Exception as e:
        print(f"Ошибка при создании AssetList: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sharpe_calmar_debug()


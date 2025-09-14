#!/usr/bin/env python3
"""
Тест для проверки исправленных расчетов метрик в команде /compare
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
import numpy as np

def test_corrected_metrics():
    """Тестирует исправленные расчеты метрик"""
    
    symbols = ['SBER.MOEX', 'LKOH.MOEX', 'LQDT.MOEX', 'OBLG.MOEX', 'GOLD.MOEX']
    currency = 'RUB'
    
    print("=== ТЕСТИРОВАНИЕ ИСПРАВЛЕННЫХ РАСЧЕТОВ ===")
    
    try:
        # Создаем AssetList для получения данных как в okama
        asset_list = ok.AssetList(symbols, ccy=currency)
        describe_data = asset_list.describe()
        
        print(f"Создан AssetList с символами: {symbols}")
        print(f"Валюта: {currency}")
        
        # Извлекаем ключевые метрики из describe_data
        corrected_metrics = {}
        
        for symbol in symbols:
            symbol_metrics = {}
            
            # Извлекаем метрики из describe_data
            for idx in describe_data.index:
                property_name = describe_data.loc[idx, 'property']
                period = describe_data.loc[idx, 'period']
                
                if symbol in describe_data.columns:
                    value = describe_data.loc[idx, symbol]
                    if not pd.isna(value):
                        # Map okama properties to our metrics
                        if property_name == 'CAGR (5 years, 1 months)':
                            symbol_metrics['cagr'] = value
                        elif property_name == 'CAGR (1 years)':
                            symbol_metrics['cagr_1y'] = value
                        elif property_name == 'CAGR (5 years)':
                            symbol_metrics['cagr_5y'] = value
                        elif property_name == 'Risk (5 years, 1 months)':
                            symbol_metrics['volatility'] = value
                        elif property_name == 'Max drawdowns (5 years, 1 months)':
                            symbol_metrics['max_drawdown'] = value
                        elif property_name == 'Inception date':
                            symbol_metrics['inception_date'] = value
                        elif property_name == 'Common last data date':
                            symbol_metrics['last_data_date'] = value
            
            # Рассчитываем дополнительные метрики
            if symbol_metrics.get('cagr') is not None and symbol_metrics.get('volatility') is not None:
                # Безрисковая ставка для 5-летнего периода
                risk_free_rate = 0.14  # 14% для RUB на 5 лет
                
                # Коэффициент Шарпа
                if symbol_metrics['volatility'] > 0:
                    symbol_metrics['sharpe'] = (symbol_metrics['cagr'] - risk_free_rate) / symbol_metrics['volatility']
                
                # Коэффициент Кальмара
                if symbol_metrics.get('max_drawdown') is not None and symbol_metrics['max_drawdown'] < 0:
                    symbol_metrics['calmar'] = symbol_metrics['cagr'] / abs(symbol_metrics['max_drawdown'])
                
                # Рассчитываем период инвестиций
                if symbol_metrics.get('inception_date') and symbol_metrics.get('last_data_date'):
                    inception = pd.to_datetime(symbol_metrics['inception_date'])
                    last_date = pd.to_datetime(symbol_metrics['last_data_date'])
                    years = (last_date - inception).days / 365.25
                    symbol_metrics['period_years'] = years
            
            corrected_metrics[symbol] = symbol_metrics
        
        # Выводим исправленные метрики
        print("\n=== ИСПРАВЛЕННЫЕ МЕТРИКИ ===")
        
        for symbol, metrics in corrected_metrics.items():
            print(f"\n--- {symbol} ---")
            
            if 'period_years' in metrics:
                print(f"Период инвестиций: {metrics['period_years']:.1f} лет")
            
            if 'cagr_1y' in metrics:
                print(f"CAGR 1 год: {metrics['cagr_1y']*100:.2f}%")
            
            if 'cagr_5y' in metrics:
                print(f"CAGR 5 лет: {metrics['cagr_5y']*100:.2f}%")
            
            if 'cagr' in metrics:
                print(f"CAGR (общий): {metrics['cagr']*100:.2f}%")
            
            if 'volatility' in metrics:
                print(f"Волатильность: {metrics['volatility']*100:.2f}%")
            
            if 'max_drawdown' in metrics:
                print(f"Макс. просадка: {metrics['max_drawdown']*100:.2f}%")
            
            if 'sharpe' in metrics:
                print(f"Коэф. Шарпа: {metrics['sharpe']:.2f}")
            
            if 'calmar' in metrics:
                print(f"Коэф. Кальмара: {metrics['calmar']:.2f}")
        
        # Сравниваем с ожидаемыми значениями
        print("\n=== СРАВНЕНИЕ С ОЖИДАЕМЫМИ ЗНАЧЕНИЯМИ ===")
        
        expected_values = {
            'SBER.MOEX': {
                'cagr': 0.1797,  # 17.97%
                'volatility': 0.4789,  # 47.89%
                'max_drawdown': -0.6948,  # -69.48%
                'calmar': 0.26  # 17.97% / 69.48%
            },
            'LKOH.MOEX': {
                'cagr': 0.1303,  # 13.03%
                'volatility': 0.3830,  # 38.30%
                'max_drawdown': -0.4340,  # -43.40%
                'calmar': 0.30  # 13.03% / 43.40%
            },
            'LQDT.MOEX': {
                'cagr': 0.1152,  # 11.52%
                'volatility': 0.0192,  # 1.92%
                'max_drawdown': 0.0000,  # 0.00%
                'calmar': None  # n/a (DD=0)
            },
            'OBLG.MOEX': {
                'cagr': 0.0893,  # 8.93%
                'volatility': 0.0752,  # 7.52%
                'max_drawdown': -0.1046,  # -10.46%
                'calmar': 0.85  # 8.93% / 10.46%
            },
            'GOLD.MOEX': {
                'cagr': 0.1146,  # 11.46%
                'volatility': 0.2404,  # 24.04%
                'max_drawdown': -0.3641,  # -36.41%
                'calmar': 0.31  # 11.46% / 36.41%
            }
        }
        
        print("\nСравнение исправленных расчетов:")
        print("Символ | Метрика | Ожидаемое | Получено | Отклонение")
        print("-" * 60)
        
        for symbol, expected in expected_values.items():
            if symbol in corrected_metrics:
                metrics = corrected_metrics[symbol]
                
                # CAGR
                if 'cagr' in metrics and metrics['cagr'] is not None:
                    expected_cagr = expected['cagr']
                    actual_cagr = metrics['cagr']
                    diff_cagr = (actual_cagr - expected_cagr) * 100
                    print(f"{symbol} | CAGR | {expected_cagr*100:.2f}% | {actual_cagr*100:.2f}% | {diff_cagr:+.2f}п.п.")
                
                # Волатильность
                if 'volatility' in metrics and metrics['volatility'] is not None:
                    expected_vol = expected['volatility']
                    actual_vol = metrics['volatility']
                    diff_vol = (actual_vol - expected_vol) * 100
                    print(f"{symbol} | Волатильность | {expected_vol*100:.2f}% | {actual_vol*100:.2f}% | {diff_vol:+.2f}п.п.")
                
                # Макс. просадка
                if 'max_drawdown' in metrics and metrics['max_drawdown'] is not None:
                    expected_dd = expected['max_drawdown']
                    actual_dd = metrics['max_drawdown']
                    diff_dd = (actual_dd - expected_dd) * 100
                    print(f"{symbol} | Макс. просадка | {expected_dd*100:.2f}% | {actual_dd*100:.2f}% | {diff_dd:+.2f}п.п.")
                
                # Кальмар
                if 'calmar' in metrics and metrics['calmar'] is not None:
                    expected_calmar = expected['calmar']
                    actual_calmar = metrics['calmar']
                    if expected_calmar is not None:
                        diff_calmar = actual_calmar - expected_calmar
                        print(f"{symbol} | Кальмар | {expected_calmar:.2f} | {actual_calmar:.2f} | {diff_calmar:+.2f}")
        
        return corrected_metrics
        
    except Exception as e:
        print(f"Ошибка при тестировании исправленных расчетов: {e}")
        return None

def main():
    """Основная функция тестирования"""
    
    print("ТЕСТИРОВАНИЕ ИСПРАВЛЕННЫХ РАСЧЕТОВ МЕТРИК")
    print("=" * 50)
    
    corrected_metrics = test_corrected_metrics()
    
    if corrected_metrics:
        print("\n=== ВЫВОДЫ ===")
        print("1. Исправленные расчеты должны соответствовать значениям из okama.AssetList.describe")
        print("2. Используется период 5y1m как в okama")
        print("3. Безрисковая ставка для RUB: 14% (5-летний период)")
        print("4. Все метрики рассчитываются на едином периоде")

if __name__ == "__main__":
    main()

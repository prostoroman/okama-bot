#!/usr/bin/env python3
"""
Тест для проверки и исправления расчетов метрик в команде /compare
Проверяет расчеты на примере SBER.MOEX LKOH.MOEX LQDT.MOEX OBLG.MOEX GOLD.MOEX
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import okama as ok
import pandas as pd
import numpy as np
from datetime import datetime

def test_okama_describe_data():
    """Тестирует данные из okama.AssetList.describe для проверки корректных значений"""
    
    symbols = ['SBER.MOEX', 'LKOH.MOEX', 'LQDT.MOEX', 'OBLG.MOEX', 'GOLD.MOEX']
    currency = 'RUB'
    
    print("=== ТЕСТИРОВАНИЕ ДАННЫХ OKAMA.ASSETLIST.DESCRIBE ===")
    
    try:
        # Создаем AssetList
        asset_list = ok.AssetList(symbols, ccy=currency)
        describe_data = asset_list.describe()
        
        print(f"Создан AssetList с символами: {symbols}")
        print(f"Валюта: {currency}")
        print(f"Размер describe_data: {describe_data.shape}")
        
        # Извлекаем ключевые метрики
        key_metrics = {}
        
        for idx in describe_data.index:
            property_name = describe_data.loc[idx, 'property']
            period = describe_data.loc[idx, 'period']
            
            # Создаем ключ метрики
            if pd.isna(period) or period == 'None' or period == '':
                metric_key = str(property_name)
            else:
                metric_key = f"{property_name}_{period}"
            
            # Извлекаем значения для всех символов
            metric_values = {}
            for symbol in symbols:
                if symbol in describe_data.columns:
                    value = describe_data.loc[idx, symbol]
                    metric_values[symbol] = value
            
            key_metrics[metric_key] = metric_values
        
        # Выводим ключевые метрики
        print("\n=== КЛЮЧЕВЫЕ МЕТРИКИ ИЗ OKAMA ===")
        
        # CAGR (5 years, 1 months) - это основной CAGR
        cagr_key = 'CAGR (5 years, 1 months)'
        if cagr_key in key_metrics:
            print(f"\n{cagr_key}:")
            for symbol, value in key_metrics[cagr_key].items():
                if not pd.isna(value):
                    print(f"  {symbol}: {value*100:.2f}%")
        
        # Risk (5 years, 1 months) - это волатильность
        risk_key = 'Risk (5 years, 1 months)'
        if risk_key in key_metrics:
            print(f"\n{risk_key} (Волатильность):")
            for symbol, value in key_metrics[risk_key].items():
                if not pd.isna(value):
                    print(f"  {symbol}: {value*100:.2f}%")
        
        # Max drawdowns (5 years, 1 months)
        dd_key = 'Max drawdowns (5 years, 1 months)'
        if dd_key in key_metrics:
            print(f"\n{dd_key}:")
            for symbol, value in key_metrics[dd_key].items():
                if not pd.isna(value):
                    print(f"  {symbol}: {value*100:.2f}%")
        
        # CAGR (1 years)
        cagr_1y_key = 'CAGR (1 years)'
        if cagr_1y_key in key_metrics:
            print(f"\n{cagr_1y_key}:")
            for symbol, value in key_metrics[cagr_1y_key].items():
                if not pd.isna(value):
                    print(f"  {symbol}: {value*100:.2f}%")
        
        # CAGR (5 years)
        cagr_5y_key = 'CAGR (5 years)'
        if cagr_5y_key in key_metrics:
            print(f"\n{cagr_5y_key}:")
            for symbol, value in key_metrics[cagr_5y_key].items():
                if not pd.isna(value):
                    print(f"  {symbol}: {value*100:.2f}%")
        
        return key_metrics
        
    except Exception as e:
        print(f"Ошибка при тестировании okama данных: {e}")
        return None

def test_manual_calculations():
    """Тестирует ручные расчеты метрик для сравнения с okama"""
    
    symbols = ['SBER.MOEX', 'LKOH.MOEX', 'LQDT.MOEX', 'OBLG.MOEX', 'GOLD.MOEX']
    currency = 'RUB'
    
    print("\n=== ТЕСТИРОВАНИЕ РУЧНЫХ РАСЧЕТОВ ===")
    
    manual_metrics = {}
    
    for symbol in symbols:
        print(f"\n--- {symbol} ---")
        
        try:
            # Создаем Asset объект
            asset = ok.Asset(symbol)
            
            # Получаем месячные данные (как в okama)
            if hasattr(asset, 'close_monthly') and asset.close_monthly is not None:
                prices = asset.close_monthly
                print(f"Используем месячные данные: {len(prices)} точек")
            else:
                print(f"Месячные данные недоступны для {symbol}")
                continue
            
            if len(prices) < 2:
                print(f"Недостаточно данных для {symbol}")
                continue
            
            # Рассчитываем доходности
            returns = prices.pct_change().dropna()
            
            if len(returns) < 2:
                print(f"Недостаточно доходностей для {symbol}")
                continue
            
            # 1. CAGR (общий период)
            start_date = prices.index[0]
            end_date = prices.index[-1]
            
            # Вычисляем годы
            if hasattr(start_date, 'to_timestamp'):
                start_date = start_date.to_timestamp()
            if hasattr(end_date, 'to_timestamp'):
                end_date = end_date.to_timestamp()
            
            years = (end_date - start_date).days / 365.25
            total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
            cagr = (1 + total_return) ** (1 / years) - 1
            
            print(f"Период: {years:.1f} лет")
            print(f"Общая доходность: {total_return*100:.2f}%")
            print(f"CAGR: {cagr*100:.2f}%")
            
            # 2. CAGR 1 год (последние 12 месяцев)
            cagr_1y = None
            if len(prices) >= 12:
                prices_1y = prices.tail(12)
                if len(prices_1y) > 1:
                    total_return_1y = (prices_1y.iloc[-1] / prices_1y.iloc[0]) - 1
                    cagr_1y = (1 + total_return_1y) ** (12 / len(prices_1y)) - 1
                    print(f"CAGR 1 год: {cagr_1y*100:.2f}%")
            
            # 3. CAGR 5 лет (последние 60 месяцев)
            cagr_5y = None
            if len(prices) >= 60:
                prices_5y = prices.tail(60)
                if len(prices_5y) > 1:
                    total_return_5y = (prices_5y.iloc[-1] / prices_5y.iloc[0]) - 1
                    cagr_5y = (1 + total_return_5y) ** (12 / len(prices_5y)) - 1
                    print(f"CAGR 5 лет: {cagr_5y*100:.2f}%")
            
            # 4. Волатильность (аннуализированная для месячных данных)
            volatility = returns.std() * np.sqrt(12)
            print(f"Волатильность: {volatility*100:.2f}%")
            
            # 5. Максимальная просадка
            running_max = prices.expanding().max()
            drawdown = (prices - running_max) / running_max
            max_drawdown = drawdown.min()
            print(f"Макс. просадка: {max_drawdown*100:.2f}%")
            
            # 6. Коэффициент Кальмара
            calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else None
            if calmar is not None:
                print(f"Коэф. Кальмара: {calmar:.2f}")
            
            # Сохраняем метрики
            manual_metrics[symbol] = {
                'cagr': cagr,
                'cagr_1y': cagr_1y,
                'cagr_5y': cagr_5y,
                'volatility': volatility,
                'max_drawdown': max_drawdown,
                'calmar': calmar,
                'period_years': years
            }
            
        except Exception as e:
            print(f"Ошибка при расчете метрик для {symbol}: {e}")
            manual_metrics[symbol] = {}
    
    return manual_metrics

def compare_with_expected_values():
    """Сравнивает расчеты с ожидаемыми значениями из okama"""
    
    print("\n=== СРАВНЕНИЕ С ОЖИДАЕМЫМИ ЗНАЧЕНИЯМИ ===")
    
    # Ожидаемые значения из okama (5y1m период)
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
    
    # Получаем ручные расчеты
    manual_metrics = test_manual_calculations()
    
    print("\nСравнение расчетов:")
    print("Символ | Метрика | Ожидаемое | Получено | Отклонение")
    print("-" * 60)
    
    for symbol, expected in expected_values.items():
        if symbol in manual_metrics:
            manual = manual_metrics[symbol]
            
            # CAGR
            if 'cagr' in manual and manual['cagr'] is not None:
                expected_cagr = expected['cagr']
                actual_cagr = manual['cagr']
                diff_cagr = (actual_cagr - expected_cagr) * 100
                print(f"{symbol} | CAGR | {expected_cagr*100:.2f}% | {actual_cagr*100:.2f}% | {diff_cagr:+.2f}п.п.")
            
            # Волатильность
            if 'volatility' in manual and manual['volatility'] is not None:
                expected_vol = expected['volatility']
                actual_vol = manual['volatility']
                diff_vol = (actual_vol - expected_vol) * 100
                print(f"{symbol} | Волатильность | {expected_vol*100:.2f}% | {actual_vol*100:.2f}% | {diff_vol:+.2f}п.п.")
            
            # Макс. просадка
            if 'max_drawdown' in manual and manual['max_drawdown'] is not None:
                expected_dd = expected['max_drawdown']
                actual_dd = manual['max_drawdown']
                diff_dd = (actual_dd - expected_dd) * 100
                print(f"{symbol} | Макс. просадка | {expected_dd*100:.2f}% | {actual_dd*100:.2f}% | {diff_dd:+.2f}п.п.")
            
            # Кальмар
            if 'calmar' in manual and manual['calmar'] is not None:
                expected_calmar = expected['calmar']
                actual_calmar = manual['calmar']
                if expected_calmar is not None:
                    diff_calmar = actual_calmar - expected_calmar
                    print(f"{symbol} | Кальмар | {expected_calmar:.2f} | {actual_calmar:.2f} | {diff_calmar:+.2f}")

def main():
    """Основная функция тестирования"""
    
    print("ТЕСТИРОВАНИЕ РАСЧЕТОВ МЕТРИК ДЛЯ КОМАНДЫ /COMPARE")
    print("=" * 60)
    
    # Тестируем данные okama
    okama_metrics = test_okama_describe_data()
    
    # Тестируем ручные расчеты
    manual_metrics = test_manual_calculations()
    
    # Сравниваем с ожидаемыми значениями
    compare_with_expected_values()
    
    print("\n=== ВЫВОДЫ ===")
    print("1. Проверьте соответствие расчетов ожидаемым значениям из okama")
    print("2. Обратите внимание на отклонения в волатильности и просадках")
    print("3. Убедитесь, что используется правильная частота данных (месячная)")
    print("4. Проверьте расчет безрисковой ставки для разных периодов")

if __name__ == "__main__":
    main()

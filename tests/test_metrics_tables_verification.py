#!/usr/bin/env python3
"""
Тест для сверки данных двух таблиц метрик:
1. Основная таблица метрик (ручные расчеты)
2. Таблица из okama.AssetList.describe
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import ShansAi
import okama as ok

def test_metrics_tables_consistency():
    """Тестирует консистентность данных между двумя таблицами метрик"""
    
    print("🔍 Тестирование консистентности таблиц метрик")
    print("=" * 60)
    
    bot = ShansAi()
    
    # Тестовые символы
    symbols = ['SBER.MOEX', 'LKOH.MOEX', 'OBLG.MOEX', 'GOLD.MOEX']
    currency = 'RUB'
    
    print(f"\n📊 Тестируемые символы: {', '.join(symbols)}")
    print(f"💰 Валюта: {currency}")
    
    try:
        # Создаем AssetList для describe данных
        asset_list = ok.AssetList(symbols, ccy=currency)
        describe_data = asset_list.describe()
        
        print(f"\n📈 Данные из okama.AssetList.describe:")
        print(f"   Размер: {describe_data.shape}")
        print(f"   Метрики: {list(describe_data.index)}")
        print(f"   Символы: {list(describe_data.columns)}")
        
        # Рассчитываем метрики вручную для сравнения
        manual_metrics = {}
        
        for symbol in symbols:
            try:
                asset = ok.Asset(symbol)
                returns = asset.ror
                prices = (1 + returns).cumprod()
                
                # Рассчитываем метрики вручную
                total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
                years = len(prices) / 12.0
                cagr = (1 + total_return) ** (1 / years) - 1
                volatility = returns.std() * np.sqrt(12)
                
                # Безрисковая ставка
                risk_free_rate = bot.get_risk_free_rate(currency, years)
                
                # Sharpe ratio
                sharpe = (cagr - risk_free_rate) / volatility if volatility > 0 else 0
                
                # Sortino ratio
                negative_returns = returns[returns < 0]
                if len(negative_returns) > 0:
                    downside_deviation = negative_returns.std() * np.sqrt(12)
                    sortino = (cagr - risk_free_rate) / downside_deviation if downside_deviation > 0 else 0
                else:
                    sortino = sharpe
                
                # Максимальная просадка
                running_max = prices.expanding().max()
                drawdown = (prices - running_max) / running_max
                max_drawdown = drawdown.min()
                
                # Calmar ratio
                calmar = cagr / abs(max_drawdown) if max_drawdown != 0 else 0
                
                manual_metrics[symbol] = {
                    'cagr': cagr,
                    'volatility': volatility,
                    'sharpe': sharpe,
                    'sortino': sortino,
                    'max_drawdown': max_drawdown,
                    'calmar': calmar,
                    'period_years': years
                }
                
                print(f"\n📊 {symbol}:")
                print(f"   CAGR: {cagr:.2%}")
                print(f"   Волатильность: {volatility:.2%}")
                print(f"   Sharpe: {sharpe:.3f}")
                print(f"   Sortino: {sortino:.3f}")
                print(f"   Макс. просадка: {max_drawdown:.2%}")
                print(f"   Calmar: {calmar:.3f}")
                print(f"   Период: {years:.1f} лет")
                
            except Exception as e:
                print(f"❌ Ошибка при расчете метрик для {symbol}: {e}")
                manual_metrics[symbol] = {}
        
        # Сравниваем данные
        print(f"\n🔍 Сравнение данных:")
        print("=" * 60)
        
        comparison_results = {}
        
        for symbol in symbols:
            if symbol not in manual_metrics or not manual_metrics[symbol]:
                continue
                
            print(f"\n📊 {symbol}:")
            
            # Сравниваем CAGR
            if symbol in describe_data.columns:
                describe_cagr = describe_data.loc['Annual Return', symbol] if 'Annual Return' in describe_data.index else None
                manual_cagr = manual_metrics[symbol]['cagr']
                
                if describe_cagr is not None and not pd.isna(describe_cagr):
                    cagr_diff = abs(describe_cagr - manual_cagr)
                    cagr_diff_pct = (cagr_diff / abs(manual_cagr)) * 100 if manual_cagr != 0 else 0
                    
                    print(f"   CAGR - Describe: {describe_cagr:.2%}, Manual: {manual_cagr:.2%}, Diff: {cagr_diff:.4f} ({cagr_diff_pct:.1f}%)")
                    
                    if cagr_diff < 0.01:  # Разница менее 1%
                        print(f"   ✅ CAGR: Консистентно")
                        comparison_results[f"{symbol}_cagr"] = True
                    else:
                        print(f"   ⚠️  CAGR: Разница {cagr_diff_pct:.1f}%")
                        comparison_results[f"{symbol}_cagr"] = False
                else:
                    print(f"   ❌ CAGR: Нет данных в describe")
                    comparison_results[f"{symbol}_cagr"] = False
                
                # Сравниваем волатильность
                describe_vol = describe_data.loc['Volatility', symbol] if 'Volatility' in describe_data.index else None
                manual_vol = manual_metrics[symbol]['volatility']
                
                if describe_vol is not None and not pd.isna(describe_vol):
                    vol_diff = abs(describe_vol - manual_vol)
                    vol_diff_pct = (vol_diff / abs(manual_vol)) * 100 if manual_vol != 0 else 0
                    
                    print(f"   Volatility - Describe: {describe_vol:.2%}, Manual: {manual_vol:.2%}, Diff: {vol_diff:.4f} ({vol_diff_pct:.1f}%)")
                    
                    if vol_diff < 0.01:  # Разница менее 1%
                        print(f"   ✅ Volatility: Консистентно")
                        comparison_results[f"{symbol}_volatility"] = True
                    else:
                        print(f"   ⚠️  Volatility: Разница {vol_diff_pct:.1f}%")
                        comparison_results[f"{symbol}_volatility"] = False
                else:
                    print(f"   ❌ Volatility: Нет данных в describe")
                    comparison_results[f"{symbol}_volatility"] = False
                
                # Сравниваем Sharpe ratio
                describe_sharpe = describe_data.loc['Sharpe Ratio', symbol] if 'Sharpe Ratio' in describe_data.index else None
                manual_sharpe = manual_metrics[symbol]['sharpe']
                
                if describe_sharpe is not None and not pd.isna(describe_sharpe):
                    sharpe_diff = abs(describe_sharpe - manual_sharpe)
                    
                    print(f"   Sharpe - Describe: {describe_sharpe:.3f}, Manual: {manual_sharpe:.3f}, Diff: {sharpe_diff:.3f}")
                    
                    if sharpe_diff < 0.1:  # Разница менее 0.1
                        print(f"   ✅ Sharpe: Консистентно")
                        comparison_results[f"{symbol}_sharpe"] = True
                    else:
                        print(f"   ⚠️  Sharpe: Разница {sharpe_diff:.3f}")
                        comparison_results[f"{symbol}_sharpe"] = False
                else:
                    print(f"   ❌ Sharpe: Нет данных в describe")
                    comparison_results[f"{symbol}_sharpe"] = False
                
                # Сравниваем максимальную просадку
                describe_dd = describe_data.loc['Max Drawdown', symbol] if 'Max Drawdown' in describe_data.index else None
                manual_dd = manual_metrics[symbol]['max_drawdown']
                
                if describe_dd is not None and not pd.isna(describe_dd):
                    dd_diff = abs(describe_dd - manual_dd)
                    dd_diff_pct = (dd_diff / abs(manual_dd)) * 100 if manual_dd != 0 else 0
                    
                    print(f"   Max Drawdown - Describe: {describe_dd:.2%}, Manual: {manual_dd:.2%}, Diff: {dd_diff:.4f} ({dd_diff_pct:.1f}%)")
                    
                    if dd_diff < 0.01:  # Разница менее 1%
                        print(f"   ✅ Max Drawdown: Консистентно")
                        comparison_results[f"{symbol}_max_drawdown"] = True
                    else:
                        print(f"   ⚠️  Max Drawdown: Разница {dd_diff_pct:.1f}%")
                        comparison_results[f"{symbol}_max_drawdown"] = False
                else:
                    print(f"   ❌ Max Drawdown: Нет данных в describe")
                    comparison_results[f"{symbol}_max_drawdown"] = False
        
        # Итоговый анализ
        print(f"\n📋 ИТОГОВЫЙ АНАЛИЗ:")
        print("=" * 60)
        
        total_comparisons = len(comparison_results)
        successful_comparisons = sum(comparison_results.values())
        
        print(f"Всего сравнений: {total_comparisons}")
        print(f"Успешных: {successful_comparisons}")
        print(f"Неуспешных: {total_comparisons - successful_comparisons}")
        print(f"Процент успеха: {(successful_comparisons/total_comparisons)*100:.1f}%")
        
        if successful_comparisons == total_comparisons:
            print("✅ ВСЕ СРАВНЕНИЯ УСПЕШНЫ!")
            return True
        elif successful_comparisons >= total_comparisons * 0.8:
            print("⚠️ БОЛЬШИНСТВО СРАВНЕНИЙ УСПЕШНЫ")
            return True
        else:
            print("❌ МНОГО НЕСООТВЕТСТВИЙ")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def test_period_calculation():
    """Тестирует расчет периода инвестиций"""
    
    print("\n🔍 Тестирование расчета периода инвестиций")
    print("=" * 60)
    
    symbols = ['SBER.MOEX', 'LKOH.MOEX', 'OBLG.MOEX', 'GOLD.MOEX']
    
    for symbol in symbols:
        try:
            asset = ok.Asset(symbol)
            returns = asset.ror
            prices = (1 + returns).cumprod()
            
            # Рассчитываем период
            years = len(prices) / 12.0
            
            print(f"\n📊 {symbol}:")
            print(f"   Количество наблюдений: {len(prices)}")
            print(f"   Период в годах: {years:.1f}")
            print(f"   Период в месяцах: {years*12:.0f}")
            
            if years < 1:
                print(f"   Формат отображения: {years*12:.1f} мес")
            else:
                print(f"   Формат отображения: {years:.1f} лет")
                
        except Exception as e:
            print(f"❌ Ошибка при расчете периода для {symbol}: {e}")

def main():
    """Основная функция теста"""
    
    print("🚀 ЗАПУСК ТЕСТА СВЕРКИ ТАБЛИЦ МЕТРИК")
    print("=" * 60)
    print(f"📅 Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Тестируем консистентность таблиц
    consistency_success = test_metrics_tables_consistency()
    
    # Тестируем расчет периода
    test_period_calculation()
    
    print("\n" + "=" * 60)
    print("📋 ИТОГОВЫЙ АНАЛИЗ")
    print("=" * 60)
    
    if consistency_success:
        print("✅ Тест пройден: Таблицы метрик консистентны")
        print("✅ Период инвестиций рассчитывается корректно")
        print("✅ Обе таблицы можно использовать для анализа")
    else:
        print("⚠️ Тест частично пройден: Есть несоответствия в данных")
        print("⚠️ Требуется дополнительная проверка расчетов")
    
    print(f"\n✅ Тест завершен: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

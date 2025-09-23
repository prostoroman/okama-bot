#!/usr/bin/env python3
"""
Тест для проверки исправления названий символов в легенде графика сравнения
"""

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.chart_styles import ChartStyles
import okama as ok
import pandas as pd
import matplotlib.pyplot as plt


class TestLegendLabelsFix(unittest.TestCase):
    """Тест для проверки исправления названий символов в легенде"""
    
    def setUp(self):
        """Инициализация тестового сервиса"""
        self.chart_styles = ChartStyles()
    
    def test_legend_labels_match_symbols(self):
        """Тест соответствия названий в легенде оригинальным символам"""
        # Создаем тестовые символы
        symbols = ['AAPL.US', 'MSFT.US', 'GOOGL.US']
        
        try:
            # Создаем AssetList
            asset_list = ok.AssetList(symbols, ccy='USD')
            wealth_indexes = asset_list.wealth_indexes
            
            print(f"Оригинальные символы: {symbols}")
            print(f"Колонки в wealth_indexes: {list(wealth_indexes.columns)}")
            
            # Создаем график с помощью исправленного метода
            fig, ax = self.chart_styles.create_unified_wealth_chart(
                wealth_indexes, symbols, 'USD', title='Тест сравнения накопленной доходности'
            )
            
            # Получаем легенду
            legend = ax.get_legend()
            self.assertIsNotNone(legend, "Легенда должна быть создана")
            
            legend_labels = [text.get_text() for text in legend.get_texts()]
            print(f"Названия в легенде: {legend_labels}")
            
            # Проверяем соответствие
            for i, (original_symbol, legend_label) in enumerate(zip(symbols, legend_labels)):
                self.assertEqual(original_symbol, legend_label, 
                               f"Символ {i+1}: {original_symbol} должен соответствовать легенде {legend_label}")
            
            plt.close(fig)
            
        except Exception as e:
            self.fail(f"Ошибка при тестировании: {e}")
    
    def test_legend_labels_with_different_symbol_formats(self):
        """Тест с различными форматами символов"""
        test_cases = [
            ['AAPL.US', 'MSFT.US'],
            ['SBER.MOEX', 'GAZP.MOEX'],
            ['VOO.US', 'BND.US', 'GLD.US']
        ]
        
        for symbols in test_cases:
            with self.subTest(symbols=symbols):
                try:
                    # Создаем AssetList
                    asset_list = ok.AssetList(symbols, ccy='USD')
                    wealth_indexes = asset_list.wealth_indexes
                    
                    # Создаем график
                    fig, ax = self.chart_styles.create_unified_wealth_chart(
                        wealth_indexes, symbols, 'USD', title=f'Тест {symbols}'
                    )
                    
                    # Получаем легенду
                    legend = ax.get_legend()
                    self.assertIsNotNone(legend, f"Легенда должна быть создана для {symbols}")
                    
                    legend_labels = [text.get_text() for text in legend.get_texts()]
                    
                    # Проверяем соответствие
                    for i, (original_symbol, legend_label) in enumerate(zip(symbols, legend_labels)):
                        self.assertEqual(original_symbol, legend_label, 
                                       f"Для {symbols}: символ {i+1}: {original_symbol} должен соответствовать легенде {legend_label}")
                    
                    plt.close(fig)
                    
                except Exception as e:
                    self.fail(f"Ошибка при тестировании {symbols}: {e}")


if __name__ == '__main__':
    unittest.main()

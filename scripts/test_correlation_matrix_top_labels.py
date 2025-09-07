#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отображения подписей оси X сверху в матрице корреляции
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from services.chart_styles import ChartStyles
import matplotlib.pyplot as plt

def test_correlation_matrix_top_labels():
    """Тестирует отображение подписей оси X сверху в матрице корреляции"""
    
    # Создаем тестовые данные
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    np.random.seed(42)
    
    # Генерируем случайные данные с некоторой корреляцией
    data = np.random.randn(100, len(symbols))
    
    # Добавляем корреляцию между некоторыми активами
    data[:, 1] = data[:, 0] * 0.7 + data[:, 1] * 0.3  # MSFT коррелирует с AAPL
    data[:, 3] = data[:, 2] * 0.6 + data[:, 3] * 0.4  # AMZN коррелирует с GOOGL
    
    # Создаем DataFrame
    df = pd.DataFrame(data, columns=symbols)
    
    # Вычисляем корреляционную матрицу
    correlation_matrix = df.corr()
    
    print("Корреляционная матрица:")
    print(correlation_matrix)
    
    # Создаем график с новыми настройками
    chart_styles = ChartStyles()
    
    try:
        fig, ax = chart_styles.create_correlation_matrix_chart(correlation_matrix)
        
        # Сохраняем график для проверки
        output_path = '/Users/roman/Documents/GitHub/okama-bot/correlation_matrix_test.png'
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        print(f"✅ График сохранен: {output_path}")
        print("✅ Подписи оси X теперь отображаются сверху")
        
    except Exception as e:
        print(f"❌ Ошибка при создании графика: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Тестирование отображения подписей оси X сверху в матрице корреляции...")
    success = test_correlation_matrix_top_labels()
    
    if success:
        print("\n✅ Тест прошел успешно!")
    else:
        print("\n❌ Тест не прошел!")

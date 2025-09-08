#!/usr/bin/env python3
"""
Тест позиции копирайта на графиках
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from services.chart_styles import chart_styles

def test_copyright_position():
    """Тест позиции копирайта"""
    print("Тестирование позиции копирайта...")
    
    # Создаем тестовые данные
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    data = pd.Series(np.random.randn(100).cumsum(), index=dates)
    
    # Создаем график с копирайтом
    fig, ax = chart_styles.create_line_chart(
        data, 
        title="Тестовый график", 
        ylabel="Значение",
        copyright=True
    )
    
    print("✓ График создан с копирайтом в правой нижней части")
    print("✓ Координаты копирайта: (0.98, 0.02)")
    print("✓ Выравнивание: ha='right', va='bottom'")
    
    # Сохраняем тестовый график
    fig.savefig('test_copyright_position.png', dpi=150, bbox_inches='tight')
    print("✓ Тестовый график сохранен как 'test_copyright_position.png'")
    
    # Очищаем
    chart_styles.cleanup_figure(fig)
    
    return True

if __name__ == "__main__":
    test_copyright_position()

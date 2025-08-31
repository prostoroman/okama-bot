"""
Chart Styles Module - Refactored Version

Централизованный модуль для управления стилями графиков с:
- Едиными настройками стилей
- Универсальными базовыми методами
- Централизованным копирайтом
- Настройками цветов и шрифтов
- Устранением дублирования кода
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from scipy.interpolate import make_interp_spline
import logging
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class ChartStyles:
    """Класс для управления стилями графиков (Nordic Pro)"""
    
    def __init__(self):
        # Настройки шрифта с fallback на доступные шрифты
        mpl.rcParams.update({
            'font.family': ['PT Sans', 'Arial', 'Helvetica', 'sans-serif'],
            'font.weight': 'medium',
            'axes.titleweight': 'semibold',
            'axes.labelweight': 'medium',
            'figure.titlesize': 16,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.title_fontsize': 11,
            'legend.fontsize': 10,
            'axes.edgecolor': '#2E3440',
            'axes.linewidth': 1.1,
            'grid.color': '#CBD5E1',
            'grid.linewidth': 0.7,
            'grid.alpha': 0.25,
        })
        # Цветовая палитра (Nordic Pro)
        self.colors = {
            'primary': '#005F73',   # глубокий морской синий
            'secondary': '#0A9396',   # бирюзовый акцент
            'success': '#94D2BD',   # мягкий мятный
            'danger': '#AE2012',   # глубокий красный
            'warning': '#EE9B00',   # янтарный
            'neutral': '#E9ECEF',   # светло-серый фон
            'text': '#2E3440',   # строгий графитовый
            'grid': '#CBD5E1',   # светло-серые линии сетки
        }
        
        # Базовый стиль
        self.style_config = {
            'style': 'seaborn-v0_8-whitegrid',
            'figsize': (12, 7),
            'dpi': 160,
            'facecolor': 'white',
            'edgecolor': 'none',
            'bbox_inches': 'tight'
        }

        # Линии
        self.line_config = {
            'linewidth': 2.2,
            'alpha': 0.95,
            'smooth_points': 2000
        }

        # Monte Carlo
        self.monte_carlo_config = {
            'main_linewidth': 3.0,        # основная линия графика - плотная
            'main_alpha': 0.95,           # основная линия - непрозрачная
            'test_linewidth': 0.8,        # линии тестирования - тонкие
            'test_alpha': 0.6,            # линии тестирования - полупрозрачные
            'test_colors': [
                '#FF6B6B',    # яркий красный
                '#4ECDC4',    # яркий бирюзовый
                '#45B7D1',    # яркий синий
                '#96CEB4',    # яркий зеленый
                '#FFEAA7',    # яркий желтый
                '#DDA0DD',    # яркий пурпурный
                '#98D8C8',    # яркий мятный
                '#F7DC6F'     # яркий золотой
            ]
        }

        # Копирайт
        self.copyright_config = {
            'text': '© shans.ai | data source: okama',
            'fontsize': 10,
            'color': self.colors['text'],
            'alpha': 0.55,
            'position': (0.01, -0.18)
        }

        # Заголовки
        self.title_config = {
            'fontsize': 16,
            'fontweight': 'semibold',
            'pad': 18,
            'color': self.colors['text']
        }

        # Оси
        self.axis_config = {
            'fontsize': 12,
            'fontweight': 'medium',
            'color': self.colors['text'],
            'label_fontsize': 12,
            'label_fontweight': 'medium',
            'label_color': self.colors['text'],
            'tick_fontsize': 10,
            'tick_color': self.colors['text']
        }

        # Сетка
        self.grid_config = {
            'alpha': 0.25,  # соответствует grid.alpha
            'linestyle': '-',
            'linewidth': 0.7,  # соответствует grid.linewidth
            'color': '#CBD5E1',  # соответствует grid.color
            'zorder': 0
        }

        # Рамки
        self.spine_config = {
            'color': '#2E3440',  # соответствует axes.edgecolor
            'linewidth': 1.1
        }

        # Легенда
        self.legend_config = {
            'fontsize': 10,
            'frameon': True,
            'fancybox': True,
            'shadow': True,
            'loc': 'upper left'
        }

# Глобальный экземпляр для использования в других модулях
chart_styles = ChartStyles()

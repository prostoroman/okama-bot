"""
Chart Styles Module

Централизованный модуль для управления стилями графиков с:
- Едиными настройками стилей
- Интерполяцией сплайнами для плавных линий
- Централизованным копирайтом
- Настройками цветов и шрифтов
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline
import logging

logger = logging.getLogger(__name__)

class ChartStyles:
    """Класс для управления стилями графиков"""
    
    def __init__(self):
        """Инициализация стилей"""
        # Цветовая палитра
        self.colors = {
            'primary': '#1f77b4',      # Синий
            'secondary': '#ff7f0e',    # Оранжевый
            'success': '#2ca02c',      # Зеленый
            'danger': '#d62728',       # Красный
            'purple': '#9467bd',       # Фиолетовый
            'brown': '#8c564b',        # Коричневый
            'pink': '#e377c2',         # Розовый
            'gray': '#7f7f7f',         # Серый
            'olive': '#bcbd22',        # Оливковый
            'cyan': '#17becf'          # Голубой
        }
        
        # Настройки стиля
        self.style_config = {
            'style': 'fivethirtyeight',
            'figsize': (14, 9),
            'dpi': 150,
            'facecolor': 'white',
            'edgecolor': 'none',
            'bbox_inches': 'tight'
        }
        
        # Настройки линий
        self.line_config = {
            'linewidth': 2.5,
            'alpha': 0.9,
            'smooth_points': 3000  # Увеличено количество точек для более плавного скругления
        }
        
        # Настройки копирайта
        self.copyright_config = {
            'text': '© Цбот, data source: okama',
            'fontsize': 12,
            'color': 'grey',
            'alpha': 0.7,
            'position': (0.02, -0.25)
        }
        
        # Настройки заголовков
        self.title_config = {
            'fontsize': 16,
            'fontweight': 'bold',
            'pad': 20,
            'color': '#2E3440'
        }
        
        # Настройки осей
        self.axis_config = {
            'label_fontsize': 13,
            'label_fontweight': 'semibold',
            'label_color': '#4C566A',
            'tick_fontsize': 10,
            'tick_color': '#4C566A'
        }
        
        # Настройки сетки
        self.grid_config = {
            'alpha': 0.2,
            'linestyle': '-',
            'linewidth': 0.8
        }
        
        # Настройки рамок
        self.spine_config = {
            'color': '#D1D5DB',
            'linewidth': 0.8
        }
        
        # Настройки легенды
        self.legend_config = {
            'fontsize': 11,
            'frameon': True,
            'fancybox': True,
            'shadow': True,
            'loc': 'upper left',
            'bbox_to_anchor': (0.02, 0.98)
        }
    
    def apply_base_style(self, fig, ax):
        """Применить базовый стиль к графику"""
        try:
            # Применяем стиль matplotlib
            plt.style.use(self.style_config['style'])
            
            # Настройка фона
            ax.set_facecolor('#F8F9FA')
            ax.set_alpha(0.95)
            
            # Настройка сетки
            ax.grid(True, **self.grid_config)
            
            # Настройка рамок
            for spine in ax.spines.values():
                spine.set_color(self.spine_config['color'])
                spine.set_linewidth(self.spine_config['linewidth'])
            
            # Настройка меток осей
            ax.tick_params(axis='both', which='major', 
                          labelsize=self.axis_config['tick_fontsize'], 
                          colors=self.axis_config['tick_color'])
            
        except Exception as e:
            logger.error(f"Error applying base style: {e}")
    
    def add_copyright(self, ax):
        """Добавить копирайт к графику"""
        try:
            ax.text(self.copyright_config['position'][0], 
                   self.copyright_config['position'][1], 
                   self.copyright_config['text'],
                   transform=ax.transAxes, 
                   fontsize=self.copyright_config['fontsize'], 
                   color=self.copyright_config['color'], 
                   alpha=self.copyright_config['alpha'])
        except Exception as e:
            logger.error(f"Error adding copyright: {e}")
    
    def smooth_line_data(self, x_data, y_data, n_points=None):
        """
        Сгладить данные линии с помощью интерполяции сплайнами
        
        Args:
            x_data: массив x-координат
            y_data: массив y-координат
            n_points: количество точек для интерполяции (по умолчанию из конфига)
            
        Returns:
            tuple: (x_smooth, y_smooth) - сглаженные данные
        """
        try:
            if n_points is None:
                n_points = self.line_config['smooth_points']
            
            # Проверяем, что у нас достаточно данных для интерполяции
            if len(x_data) < 3 or len(y_data) < 3:
                logger.warning("Insufficient data for spline interpolation, returning original data")
                return x_data, y_data
            
            # Убираем NaN значения
            valid_mask = ~(np.isnan(x_data) | np.isnan(y_data))
            if np.sum(valid_mask) < 3:
                logger.warning("Too many NaN values for interpolation, returning original data")
                return x_data, y_data
            
            x_valid = x_data[valid_mask]
            y_valid = y_data[valid_mask]
            
            # Проверяем типы данных
            if hasattr(x_valid, 'dtype') and x_valid.dtype.kind in ['M', 'O']:
                # Для datetime или object типов используем числовые индексы
                x_numeric = np.arange(len(x_valid))
                use_numeric_x = True
            else:
                x_numeric = x_valid
                use_numeric_x = False
            
            # Сортируем данные по x для корректной интерполяции
            if use_numeric_x:
                sort_idx = np.argsort(x_numeric)
                x_sorted = x_numeric[sort_idx]
                y_sorted = y_valid[sort_idx]
            else:
                sort_idx = np.argsort(x_valid)
                x_sorted = x_valid[sort_idx]
                y_sorted = y_valid[sort_idx]
            
            # Убираем дублирующиеся x-координаты
            unique_mask = np.concatenate(([True], np.diff(x_sorted) > 0))
            x_unique = x_sorted[unique_mask]
            y_unique = y_sorted[unique_mask]
            
            if len(x_unique) < 3:
                logger.warning("Too few unique x-coordinates for interpolation, returning original data")
                return x_data, y_data
            
            # Создаем сплайн
            spline = make_interp_spline(x_unique, y_unique, k=min(3, len(x_unique) - 1))
            
            # Генерируем новые точки
            x_smooth = np.linspace(x_unique.min(), x_unique.max(), n_points)
            y_smooth = spline(x_smooth)
            
            # Если использовали числовые индексы, конвертируем обратно к оригинальным датам
            if use_numeric_x:
                # Интерполируем оригинальные даты
                from scipy.interpolate import interp1d
                date_interp = interp1d(x_numeric, x_valid, kind='linear', 
                                      bounds_error=False, fill_value='extrapolate')
                x_smooth_dates = date_interp(x_smooth)
                return x_smooth_dates, y_smooth
            
            return x_smooth, y_smooth
            
        except Exception as e:
            logger.error(f"Error in spline interpolation: {e}")
            return x_data, y_data
    
    def plot_smooth_line(self, ax, x_data, y_data, **kwargs):
        """
        Нарисовать сглаженную линию с интерполяцией сплайнами
        
        Args:
            ax: matplotlib axes
            x_data: массив x-координат
            y_data: массив y-координат
            **kwargs: дополнительные параметры для plot
            
        Returns:
            matplotlib.lines.Line2D: объект линии
        """
        try:
            logger.debug(f"plot_smooth_line called with x_data type={type(x_data)}, y_data type={type(y_data)}")
            logger.debug(f"x_data length={len(x_data)}, y_data length={len(y_data)}")
            
            # Сглаживаем данные
            x_smooth, y_smooth = self.smooth_line_data(x_data, y_data)
            
            logger.debug(f"Smoothing completed, x_smooth type={type(x_smooth)}, y_smooth type={type(y_smooth)}")
            
            # Применяем настройки по умолчанию
            plot_kwargs = {
                'linewidth': self.line_config['linewidth'],
                'alpha': self.line_config['alpha']
            }
            plot_kwargs.update(kwargs)
            
            # Рисуем сглаженную линию
            line = ax.plot(x_smooth, y_smooth, **plot_kwargs)
            
            return line[0] if isinstance(line, list) else line
            
        except Exception as e:
            logger.error(f"Error plotting smooth line: {e}")
            # Fallback к обычной линии
            plot_kwargs = {
                'linewidth': self.line_config['linewidth'],
                'alpha': self.line_config['alpha']
            }
            plot_kwargs.update(kwargs)
            return ax.plot(x_data, y_data, **plot_kwargs)
    
    def create_figure(self, figsize=None, **kwargs):
        """Создать фигуру с настройками по умолчанию"""
        if figsize is None:
            figsize = self.style_config['figsize']
        
        fig_kwargs = {
            'figsize': figsize,
            'facecolor': self.style_config['facecolor']
        }
        fig_kwargs.update(kwargs)
        
        return plt.subplots(**fig_kwargs)
    
    def save_figure(self, fig, output_buffer, **kwargs):
        """Сохранить фигуру с настройками по умолчанию"""
        save_kwargs = {
            'format': 'png',
            'dpi': self.style_config['dpi'],
            'bbox_inches': self.style_config['bbox_inches'],
            'facecolor': self.style_config['facecolor'],
            'edgecolor': self.style_config['edgecolor']
        }
        save_kwargs.update(kwargs)
        
        fig.savefig(output_buffer, **save_kwargs)
    
    def cleanup_figure(self, fig):
        """Очистить фигуру и освободить память"""
        try:
            plt.close(fig)
            plt.clf()
            plt.cla()
        except Exception as e:
            logger.error(f"Error cleaning up figure: {e}")
    
    def get_color(self, index):
        """Получить цвет по индексу"""
        colors_list = list(self.colors.values())
        return colors_list[index % len(colors_list)]

# Глобальный экземпляр для использования в других модулях
chart_styles = ChartStyles()

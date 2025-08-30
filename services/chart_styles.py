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
from datetime import datetime

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
        
        # Настройки для линий Монте-Карло
        self.monte_carlo_config = {
            'linewidth': 0.8,  # Тонкие линии для Монте-Карло
            'alpha': 0.6,      # Прозрачность для лучшей видимости множественных линий
            'color': '#1f77b4' # Цвет линий Монте-Карло
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
    
    def apply_monte_carlo_style(self, ax):
        """Применить специальные стили для линий Монте-Карло"""
        try:
            # Находим все линии на графике и применяем стили Монте-Карло
            for line in ax.lines:
                line.set_linewidth(self.monte_carlo_config['linewidth'])
                line.set_alpha(self.monte_carlo_config['alpha'])
                line.set_color(self.monte_carlo_config['color'])
            
            logger.info(f"Applied Monte Carlo styles to {len(ax.lines)} lines")
            
        except Exception as e:
            logger.error(f"Error applying Monte Carlo styles: {e}")
    
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
            
            # Убираем NaN значения (безопасно для нечисловых x)
            try:
                y_arr = np.asarray(y_data, dtype=float)
            except Exception:
                y_arr = np.array(y_data, dtype=float)
            x_arr = np.asarray(x_data)
            y_isnan = np.isnan(y_arr)
            if getattr(x_arr, 'dtype', None) is not None and getattr(x_arr.dtype, 'kind', '') == 'f':
                x_isnan = np.isnan(x_arr)
            else:
                x_isnan = np.zeros_like(y_isnan, dtype=bool)
            valid_mask = ~(x_isnan | y_isnan)
            if np.sum(valid_mask) < 3:
                logger.warning("Too many NaN values for interpolation, returning original data")
                return x_data, y_data
            
            x_valid = x_arr[valid_mask]
            y_valid = y_arr[valid_mask]
            
            # Определяем, датоподобные ли x (datetime/period/obj)
            is_period = hasattr(x_arr, 'dtype') and str(x_arr.dtype).startswith('period')
            is_datetime_kind = hasattr(x_arr, 'dtype') and getattr(x_arr.dtype, 'kind', '') == 'M'
            is_object = hasattr(x_arr, 'dtype') and getattr(x_arr.dtype, 'kind', '') == 'O'
            is_date_like = is_period or is_datetime_kind or is_object
            
            if is_date_like:
                # Преобразуем x в числовые таймстемпы (секунды с эпохи)
                x_numeric = []
                for x_val in x_valid:
                    try:
                        if hasattr(x_val, 'to_timestamp'):
                            x_val = x_val.to_timestamp()
                        if hasattr(x_val, 'timestamp'):
                            x_numeric.append(float(x_val.timestamp()))
                        elif isinstance(x_val, np.datetime64):
                            x_numeric.append(float(np.datetime64(x_val).astype('datetime64[s]').astype(int)))
                        else:
                            # Попытка привести через pandas
                            try:
                                import pandas as pd
                                ts = pd.to_datetime(x_val)
                                x_numeric.append(float(ts.timestamp()))
                            except Exception:
                                # Последний шанс: индекс позиции
                                x_numeric.append(float(len(x_numeric)))
                    except Exception:
                        x_numeric.append(float(len(x_numeric)))
                x_numeric = np.asarray(x_numeric, dtype=float)
                
                # Сортируем
                sort_idx = np.argsort(x_numeric)
                x_sorted = x_numeric[sort_idx]
                y_sorted = y_valid[sort_idx]
                
                # Убираем дубли
                unique_mask = np.concatenate(([True], np.diff(x_sorted) > 0))
                x_unique = x_sorted[unique_mask]
                y_unique = y_sorted[unique_mask]
                if len(x_unique) < 3:
                    logger.warning("Too few unique x-coordinates for interpolation, returning original data")
                    return x_data, y_data
                
                # Сплайн и новые точки
                spline = make_interp_spline(x_unique, y_unique, k=min(3, len(x_unique) - 1))
                x_smooth_num = np.linspace(x_unique.min(), x_unique.max(), n_points)
                y_smooth = spline(x_smooth_num)
                
                # Конвертация обратно в datetime
                try:
                    x_smooth_dates = np.array([datetime.fromtimestamp(ts) for ts in x_smooth_num])
                    return x_smooth_dates, y_smooth
                except Exception:
                    return x_smooth_num, y_smooth
            else:
                # Чисто числовые x
                sort_idx = np.argsort(x_valid)
                x_sorted = x_valid[sort_idx]
                y_sorted = y_valid[sort_idx]
                unique_mask = np.concatenate(([True], np.diff(x_sorted) > 0))
                x_unique = x_sorted[unique_mask]
                y_unique = y_sorted[unique_mask]
                if len(x_unique) < 3:
                    logger.warning("Too few unique x-coordinates for interpolation, returning original data")
                    return x_data, y_data
                spline = make_interp_spline(x_unique, y_unique, k=min(3, len(x_unique) - 1))
                x_smooth = np.linspace(float(x_unique.min()), float(x_unique.max()), n_points)
                y_smooth = spline(x_smooth)
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

            # Гарантируем совместимость x с matplotlib (конвертация Period -> datetime)
            try:
                import numpy as np  # noqa: F401
                # Преобразуем потенциальные Period/PeriodIndex к datetime перед отрисовкой
                def _coerce_dates(seq):
                    try:
                        # Если это pandas Index/Series с методом to_timestamp
                        if hasattr(seq, 'to_timestamp'):
                            return seq.to_timestamp()
                    except Exception:
                        pass
                    try:
                        # Итерируем и конвертируем элементы с to_timestamp()/timestamp()
                        converted = []
                        for xv in list(seq):
                            try:
                                if hasattr(xv, 'to_timestamp'):
                                    xv = xv.to_timestamp()
                                # datetime-like с методом timestamp
                                if hasattr(xv, 'timestamp'):
                                    converted.append(xv)
                                else:
                                    # Попробуем привести через pandas
                                    try:
                                        import pandas as pd  # noqa: F401
                                        xv_dt = pd.to_datetime(xv)
                                        converted.append(xv_dt.to_pydatetime())
                                    except Exception:
                                        converted.append(xv)
                            except Exception:
                                converted.append(xv)
                        return converted
                    except Exception:
                        return seq

                x_smooth = _coerce_dates(x_smooth)
            except Exception:
                # В случае любой ошибки оставляем исходные значения
                pass
            
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
            # Fallback к обычной линии с безопасной конвертацией дат
            plot_kwargs = {
                'linewidth': self.line_config['linewidth'],
                'alpha': self.line_config['alpha']
            }
            plot_kwargs.update(kwargs)
            try:
                # Конвертируем возможный Period/PeriodIndex в datetime
                def _coerce_dates_simple(seq):
                    try:
                        if hasattr(seq, 'to_timestamp'):
                            return seq.to_timestamp()
                    except Exception:
                        pass
                    try:
                        out = []
                        for xv in list(seq):
                            try:
                                if hasattr(xv, 'to_timestamp'):
                                    xv = xv.to_timestamp()
                                out.append(xv)
                            except Exception:
                                out.append(xv)
                        return out
                    except Exception:
                        return seq
                x_safe = _coerce_dates_simple(x_data)
            except Exception:
                x_safe = x_data
            return ax.plot(x_safe, y_data, **plot_kwargs)
    
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

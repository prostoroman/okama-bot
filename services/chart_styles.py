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

class ChartStylesConstructivist:
    """Стиль графиков в духе советского конструктивизма — ярко, строго, стильно"""
    
    def __init__(self):
        # Цветовая палитра в духе плакатов 30-х
        self.colors = {
            'red': '#D62828',  # ярко-красный (основной акцент)
            'black': '#1A1A1A',  # глубокий черный
            'yellow': '#FFB703',  # индустриальный желтый
            'blue': '#023E8A',  # насыщенный синий
            'white': '#F8F9FA',  # чисто-белый
            'gray': '#6C757D'   # нейтральный серый
        }

        # Базовый стиль
        self.style_config = {
            'style': 'seaborn-v0_8-white',
            'figsize': (12, 7),
            'dpi': 150,
            'facecolor': self.colors['white'],
            'edgecolor': 'none',
            'bbox_inches': 'tight'
        }

        # Линии
        self.line_config = {
            'linewidth': 2.8,
            'alpha': 0.95,
            'smooth_points': 1500
        }

        # Monte Carlo (приглушенные цвета)
        self.monte_carlo_config = {
            'linewidth': 0.7,
            'alpha': 0.35,
            'color': self.colors['gray']
        }

        # Копирайт внизу, в стиле типографии
        self.copyright_config = {
            'text': '© Цбот | Данные: okama',
            'fontsize': 11,
            'color': self.colors['black'],
            'alpha': 0.7,
            'position': (0.01, -0.20)
        }

        # Заголовки
        self.title_config = {
            'fontsize': 20,
            'fontweight': 'bold',
            'pad': 20,
            'color': self.colors['red']   # заголовки всегда красные
        }

        # Оси
        self.axis_config = {
            'label_fontsize': 13,
            'label_fontweight': 'bold',
            'label_color': self.colors['black'],
            'tick_fontsize': 11,
            'tick_color': self.colors['black']
        }

        # Сетка — минимальная, строгая
        self.grid_config = {
            'alpha': 0.2,
            'linestyle': '-',
            'linewidth': 0.9,
            'color': self.colors['gray']
        }

        # Рамки — строгие черные
        self.spine_config = {
            'color': self.colors['black'],
            'linewidth': 1.2
        }

        # Легенда
        self.legend_config = {
            'fontsize': 11,
            'frameon': True,
            'facecolor': self.colors['white'],
            'edgecolor': self.colors['black'],
            'loc': 'upper left',
            'framealpha': 0.95
        }

    def apply_base_style(self, fig, ax):
        """Применить стиль конструктивизма"""
        try:
            plt.style.use(self.style_config['style'])
            ax.set_facecolor(self.colors['white'])
            
            # Сетка
            ax.grid(True, **self.grid_config)
            
            # Рамки — жирные и чёткие
            for spine in ax.spines.values():
                spine.set_color(self.spine_config['color'])
                spine.set_linewidth(self.spine_config['linewidth'])
            
            # Тики
            ax.tick_params(axis='both', which='major',
                           labelsize=self.axis_config['tick_fontsize'],
                           colors=self.axis_config['tick_color'])
        except Exception as e:
            logger.error(f"Error applying constructivist base style: {e}")
    
    def apply_monte_carlo_style(self, ax):
        """Применить специальные стили для линий Монте-Карло"""
        try:
            # Находим все линии на графике и применяем стили Монте-Карло
            for line in ax.lines:
                line.set_linewidth(self.monte_carlo_config['linewidth'])
                line.set_alpha(self.monte_carlo_config['alpha'])
                line.set_color(self.monte_carlo_config['color'])
            
            logger.info(f"Applied constructivist Monte Carlo styles to {len(ax.lines)} lines")
            
        except Exception as e:
            logger.error(f"Error applying constructivist Monte Carlo styles: {e}")
    
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
            logger.error(f"Error adding constructivist copyright: {e}")
    
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

class ChartStyles:
    """Класс для управления стилями графиков"""
    
    def __init__(self):
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
            'linewidth': 0.6,
            'alpha': 0.45,
            'colors': [
                self.colors['primary'],    # глубокий морской синий
                self.colors['secondary'],  # бирюзовый акцент
                self.colors['success'],    # мягкий мятный
                self.colors['warning'],    # янтарный
                self.colors['danger']      # глубокий красный
            ]
        }

        # Копирайт
        self.copyright_config = {
            'text': '© Цбот Pro | Data source: okama',
            'fontsize': 10,
            'color': self.colors['text'],
            'alpha': 0.55,
            'position': (0.01, -0.18)
        }

        # Заголовки
        self.title_config = {
            'fontsize': 18,
            'fontweight': 'semibold',
            'pad': 18,
            'color': self.colors['text']
        }

        # Оси
        self.axis_config = {
            'label_fontsize': 12,
            'label_fontweight': 'medium',
            'label_color': self.colors['text'],
            'tick_fontsize': 10,
            'tick_color': '#475569'
        }

        # Сетка
        self.grid_config = {
            'alpha': 0.15,
            'linestyle': '--',
            'linewidth': 0.8,
            'color': self.colors['grid']
        }

        # Рамки
        self.spine_config = {
            'color': '#E2E8F0',
            'linewidth': 1.0
        }

        # Легенда
        self.legend_config = {
            'fontsize': 10,
            'frameon': False,
            'loc': 'upper right'
        }

    def apply_base_style(self, fig, ax):
        """Применить базовый стиль"""
        try:
            plt.style.use(self.style_config['style'])
            ax.set_facecolor(self.colors['neutral'])
            
            # Сетка
            ax.grid(True, **self.grid_config)
            
            # Рамки — только снизу и слева (минимализм)
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)
            for spine in ['left', 'bottom']:
                ax.spines[spine].set_color(self.spine_config['color'])
                ax.spines[spine].set_linewidth(self.spine_config['linewidth'])
            
            # Тики
            ax.tick_params(axis='both', which='major', 
                           labelsize=self.axis_config['tick_fontsize'], 
                           colors=self.axis_config['tick_color'])
                
        except Exception as e:
            logger.error(f"Error applying base style: {e}")
    
    def apply_monte_carlo_style(self, ax):
        """Применить специальные стили для линий Монте-Карло"""
        try:
            # Находим все линии на графике и применяем стили Монте-Карло
            colors = self.monte_carlo_config['colors']
            for i, line in enumerate(ax.lines):
                line.set_linewidth(self.monte_carlo_config['linewidth'])
                line.set_alpha(self.monte_carlo_config['alpha'])
                # Применяем разные цвета по кругу для контраста
                line.set_color(colors[i % len(colors)])
            
            logger.info(f"Applied Monte Carlo styles to {len(ax.lines)} lines with {len(colors)} colors")
            
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

class ChartStylesNordicMinimal:
    """Уникальный стиль Nordic Minimal Pro+ — строгий, минималистичный, современный"""
    
    def __init__(self):
        # Цветовая палитра (сдержанные тона + акцент)
        self.colors = {
            'primary':   '#2E3440',  # графитовый
            'accent':    '#0096C7',  # ледяной сине-бирюзовый (акцент)
            'success':   '#52B788',  # мягкий мятный
            'danger':    '#D90429',  # глубокий красный для важных данных
            'warning':   '#FFB703',  # янтарный акцент
            'neutral':   '#F9FAFB',  # фоновый светлый серо-белый
            'grid':      '#CBD5E1',  # светлая сетка
            'text_main': '#1E293B',  # основной текст (почти черный)
            'text_sub':  '#64748B'   # второстепенный текст (стальной серый)
        }

        # Общие настройки
        self.style_config = {
            'style': 'seaborn-v0_8-white',
            'figsize': (13, 7.5),
            'dpi': 170,
            'facecolor': self.colors['neutral'],
            'edgecolor': 'none',
            'bbox_inches': 'tight'
        }

        # Линии
        self.line_config = {
            'linewidth': 2.4,
            'alpha': 0.92,
            'smooth_points': 2500
        }

        # Monte Carlo — «дымчатый» эффект
        self.monte_carlo_config = {
            'linewidth': 0.7,
            'alpha': 0.25,
            'color': self.colors['accent']
        }

        # Копирайт — мелкий и сбоку
        self.copyright_config = {
            'text': '© Цбот | Nordic Minimal Pro',
            'fontsize': 9,
            'color': self.colors['text_sub'],
            'alpha': 0.55,
            'position': (1.02, -0.15)   # сбоку под легендой
        }

        # Заголовки
        self.title_config = {
            'fontsize': 21,
            'fontweight': 'semibold',
            'pad': 18,
            'color': self.colors['text_main']
        }

        # Подзаголовки (новое)
        self.subtitle_config = {
            'fontsize': 13,
            'fontweight': 'medium',
            'color': self.colors['text_sub'],
            'pad': 10
        }

        # Оси
        self.axis_config = {
            'label_fontsize': 12,
            'label_fontweight': 'medium',
            'label_color': self.colors['text_main'],
            'tick_fontsize': 10,
            'tick_color': self.colors['text_sub']
        }

        # Сетка (только по Y, пунктир)
        self.grid_config = {
            'alpha': 0.18,
            'linestyle': (0, (3, 3)),  # пунктир
            'linewidth': 0.8,
            'color': self.colors['grid'],
            'axis': 'y'
        }

        # Рамки (только слева и снизу, светлые)
        self.spine_config = {
            'color': self.colors['grid'],
            'linewidth': 1.0
        }

        # Легенда
        self.legend_config = {
            'fontsize': 10,
            'frameon': False,
            'loc': 'upper center',
            'bbox_to_anchor': (0.5, 1.12),
            'ncol': 3
        }

    def apply_base_style(self, fig, ax):
        """Применить Nordic Minimal Pro+ стиль"""
        try:
            plt.style.use(self.style_config['style'])
            ax.set_facecolor(self.colors['neutral'])

            # Сетка только по Y
            ax.grid(True, **{k: v for k, v in self.grid_config.items() if k != 'axis'}, axis='y')

            # Рамки минимальные
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)
            for spine in ['left', 'bottom']:
                ax.spines[spine].set_color(self.spine_config['color'])
                ax.spines[spine].set_linewidth(self.spine_config['linewidth'])

            # Тики
            ax.tick_params(axis='both', which='major',
                           labelsize=self.axis_config['tick_fontsize'],
                           colors=self.axis_config['tick_color'])
        except Exception as e:
            logger.error(f"Error applying Nordic Minimal base style: {e}")
    
    def apply_monte_carlo_style(self, ax):
        """Применить специальные стили для линий Монте-Карло"""
        try:
            # Находим все линии на графике и применяем стили Монте-Карло
            for line in ax.lines:
                line.set_linewidth(self.monte_carlo_config['linewidth'])
                line.set_alpha(self.monte_carlo_config['alpha'])
                line.set_color(self.monte_carlo_config['color'])
            
            logger.info(f"Applied Nordic Minimal Monte Carlo styles to {len(ax.lines)} lines")
            
        except Exception as e:
            logger.error(f"Error applying Nordic Minimal Monte Carlo styles: {e}")
    
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
            logger.error(f"Error adding Nordic Minimal copyright: {e}")
    
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

class ChartStylesNordicMinimal:
    """Уникальный стиль Nordic Minimal Pro+ — строгий, минималистичный, современный"""
    
    def __init__(self):
        # Цветовая палитра (сдержанные тона + акцент)
        self.colors = {
            'primary':   '#2E3440',  # графитовый
            'accent':    '#0096C7',  # ледяной сине-бирюзовый (акцент)
            'success':   '#52B788',  # мягкий мятный
            'danger':    '#D90429',  # глубокий красный для важных данных
            'warning':   '#FFB703',  # янтарный акцент
            'neutral':   '#F9FAFB',  # фоновый светлый серо-белый
            'grid':      '#CBD5E1',  # светлая сетка
            'text_main': '#1E293B',  # основной текст (почти черный)
            'text_sub':  '#64748B'   # второстепенный текст (стальной серый)
        }

        # Общие настройки
        self.style_config = {
            'style': 'seaborn-v0_8-white',
            'figsize': (13, 7.5),
            'dpi': 170,
            'facecolor': self.colors['neutral'],
            'edgecolor': 'none',
            'bbox_inches': 'tight'
        }

        # Линии
        self.line_config = {
            'linewidth': 2.4,
            'alpha': 0.92,
            'smooth_points': 2500
        }

        # Monte Carlo — «дымчатый» эффект
        self.monte_carlo_config = {
            'linewidth': 0.7,
            'alpha': 0.25,
            'color': self.colors['accent']
        }

        # Копирайт — мелкий и сбоку
        self.copyright_config = {
            'text': '© Цбот | Nordic Minimal Pro',
            'fontsize': 9,
            'color': self.colors['text_sub'],
            'alpha': 0.55,
            'position': (1.02, -0.15)   # сбоку под легендой
        }

        # Заголовки
        self.title_config = {
            'fontsize': 21,
            'fontweight': 'semibold',
            'pad': 18,
            'color': self.colors['text_main']
        }

        # Подзаголовки (новое)
        self.subtitle_config = {
            'fontsize': 13,
            'fontweight': 'medium',
            'color': self.colors['text_sub'],
            'pad': 10
        }

        # Оси
        self.axis_config = {
            'label_fontsize': 12,
            'label_fontweight': 'medium',
            'label_color': self.colors['text_main'],
            'tick_fontsize': 10,
            'tick_color': self.colors['text_sub']
        }

        # Сетка (только по Y, пунктир)
        self.grid_config = {
            'alpha': 0.18,
            'linestyle': (0, (3, 3)),  # пунктир
            'linewidth': 0.8,
            'color': self.colors['grid'],
            'axis': 'y'
        }

        # Рамки (только слева и снизу, светлые)
        self.spine_config = {
            'color': self.colors['grid'],
            'linewidth': 1.0
        }

        # Легенда
        self.legend_config = {
            'fontsize': 10,
            'frameon': False,
            'loc': 'upper center',
            'bbox_to_anchor': (0.5, 1.12),
            'ncol': 3
        }

    def apply_base_style(self, fig, ax):
        """Применить Nordic Minimal Pro+ стиль"""
        try:
            plt.style.use(self.style_config['style'])
            ax.set_facecolor(self.colors['neutral'])

            # Сетка только по Y
            ax.grid(True, **{k: v for k, v in self.grid_config.items() if k != 'axis'}, axis='y')

            # Рамки минимальные
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)
            for spine in ['left', 'bottom']:
                ax.spines[spine].set_color(self.spine_config['color'])
                ax.spines[spine].set_linewidth(self.spine_config['linewidth'])

            # Тики
            ax.tick_params(axis='both', which='major',
                           labelsize=self.axis_config['tick_fontsize'],
                           colors=self.axis_config['tick_color'])
        except Exception as e:
            logger.error(f"Error applying Nordic Minimal base style: {e}")
    
    def apply_monte_carlo_style(self, ax):
        """Применить специальные стили для линий Монте-Карло"""
        try:
            # Находим все линии на графике и применяем стили Монте-Карло
            for line in ax.lines:
                line.set_linewidth(self.monte_carlo_config['linewidth'])
                line.set_alpha(self.monte_carlo_config['alpha'])
                line.set_color(self.monte_carlo_config['color'])
            
            logger.info(f"Applied Nordic Minimal Monte Carlo styles to {len(ax.lines)} lines")
            
        except Exception as e:
            logger.error(f"Error applying Nordic Minimal Monte Carlo styles: {e}")
    
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
            logger.error(f"Error adding Nordic Minimal copyright: {e}")
    
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
def get_chart_styles():
    """Получить экземпляр стилей графиков на основе конфигурации"""
    try:
        from config import Config
        style_type = Config.CHART_STYLE.lower()
        if style_type == 'constructivist':
            return ChartStylesConstructivist()
        elif style_type == 'nordic_minimal':
            return ChartStylesNordicMinimal()
        else:
            return ChartStylesNordicMinimal()  # default to Nordic Minimal Pro+
    except Exception as e:
        logger.warning(f"Error loading chart style config, using default: {e}")
        return ChartStylesNordicMinimal()  # default to Nordic Minimal Pro+

chart_styles = get_chart_styles()

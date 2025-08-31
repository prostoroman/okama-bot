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
    """Класс для управления стилями графиков (Nordic Pro)"""
    
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
            'fontsize': 18,
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
            'frameon': True,
            'fancybox': True,
            'shadow': True,
            'loc': 'upper left'
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
            test_colors = self.monte_carlo_config['test_colors']
            
            if len(ax.lines) > 0:
                # Первая линия - основная (плотная)
                main_line = ax.lines[0]
                main_line.set_linewidth(self.monte_carlo_config['main_linewidth'])
                main_line.set_alpha(self.monte_carlo_config['main_alpha'])
                main_line.set_color(self.colors['primary'])  # основной цвет стиля
                
                # Остальные линии - тестирование (тонкие, яркие)
                for i, line in enumerate(ax.lines[1:], 1):
                    line.set_linewidth(self.monte_carlo_config['test_linewidth'])
                    line.set_alpha(self.monte_carlo_config['test_alpha'])
                    # Применяем яркие контрастные цвета по кругу
                    line.set_color(test_colors[i % len(test_colors)])
            
            logger.info(f"Applied Monte Carlo styles: main line (thick), {len(ax.lines)-1} test lines (thin, bright)")
            
        except Exception as e:
            logger.error(f"Error applying Monte Carlo styles: {e}")
    
    def apply_percentile_style(self, ax):
        """Применить специальные стили для графика с процентилями"""
        try:
            if len(ax.lines) >= 3:
                # Цвета для процентилей: 10% (красный), 50% (синий), 90% (зеленый)
                percentile_colors = [
                    self.colors['danger'],    # 10% - красный (пессимистичный)
                    self.colors['primary'],   # 50% - синий (средний)
                    self.colors['success']    # 90% - зеленый (оптимистичный)
                ]
                
                # Метки для процентилей
                percentile_labels = [
                    '10% процентиль (пессимистичный)',
                    '50% процентиль (средний)',
                    '90% процентиль (оптимистичный)'
                ]
                
                # Применяем цвета и метки к линиям процентилей
                for i, line in enumerate(ax.lines[:3]):
                    if i < len(percentile_colors):
                        line.set_color(percentile_colors[i])
                        line.set_linewidth(2.5)
                        line.set_alpha(0.9)
                        # Устанавливаем метку для легенды
                        if i < len(percentile_labels):
                            line.set_label(percentile_labels[i])
                
                # Если есть дополнительные линии (например, текущее значение), делаем их менее заметными
                for line in ax.lines[3:]:
                    line.set_color(self.colors['neutral'])
                    line.set_linewidth(1.5)
                    line.set_alpha(0.6)
                    # Убираем метку для дополнительных линий
                    line.set_label('')
                
                logger.info(f"Applied percentile styles: 10% (red), 50% (blue), 90% (green)")
            
        except Exception as e:
            logger.error(f"Error applying percentile styles: {e}")
    
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
    
    def create_standard_chart(self, figsize=None, style='default', **kwargs):
        """
        Создать стандартную фигуру с унифицированными настройками
        
        Args:
            figsize: размер фигуры
            style: стиль matplotlib ('default', 'fivethirtyeight', 'seaborn-v0_8-whitegrid')
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        try:
            # Применяем стиль
            if style == 'default':
                plt.style.use(self.style_config['style'])
            else:
                plt.style.use(style)
            
            # Создаем фигуру
            fig, ax = self.create_figure(figsize, **kwargs)
            
            # Применяем базовый стиль
            self.apply_base_style(fig, ax)
            
            return fig, ax
            
        except Exception as e:
            logger.error(f"Error creating standard chart: {e}")
            # Fallback к простому созданию
            return plt.subplots(figsize=figsize or self.style_config['figsize'])
    
    def apply_standard_chart_styling(self, ax, title=None, xlabel=None, ylabel=None, 
                                   grid=True, legend=True, copyright=True, show_xlabel=False, **kwargs):
        """
        Применить стандартные стили к графику
        
        Args:
            ax: matplotlib axes
            title: заголовок графика
            xlabel: подпись оси X
            ylabel: подпись оси Y
            grid: показывать сетку
            legend: показывать легенду
            copyright: добавлять копирайт
            show_xlabel: показывать подпись оси X (по умолчанию False)
            **kwargs: дополнительные параметры стилизации
        """
        try:
            # Заголовок
            if title:
                ax.set_title(title, **self.title_config)
            
            # Подписи осей
            if xlabel and show_xlabel:
                ax.set_xlabel(xlabel, **self.axis_config)
            if ylabel:
                ax.set_ylabel(ylabel, **self.axis_config)
            
            # Сетка
            if grid:
                ax.grid(True, **self.grid_config)
            
            # Легенда
            if legend and ax.get_legend() is not None:
                ax.legend(**self.legend_config)
            
            # Копирайт
            if copyright:
                self.add_copyright(ax)
            
            # Дополнительные стили
            if kwargs.get('spines', True):
                for spine in ['top', 'right']:
                    ax.spines[spine].set_visible(False)
                for spine in ['left', 'bottom']:
                    ax.spines[spine].set_color(self.spine_config['color'])
                    ax.spines[spine].set_linewidth(self.spine_config['linewidth'])
            
            # Тики
            if kwargs.get('ticks', True):
                ax.tick_params(axis='both', which='major', 
                               labelsize=self.axis_config['tick_fontsize'], 
                               colors=self.axis_config['tick_color'])
                
        except Exception as e:
            logger.error(f"Error applying standard chart styling: {e}")
    
    def create_drawdowns_chart(self, data, symbols, currency, figsize=(14, 9), **kwargs):
        """
        Создать стандартный график drawdowns
        
        Args:
            data: данные drawdowns
            symbols: список символов
            currency: валюта
            figsize: размер фигуры
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(figsize=figsize, style='fivethirtyeight')
        
        # Рисуем данные
        if hasattr(data, 'plot'):
            data.plot(ax=ax, linewidth=2.5, alpha=0.9)
        
        # Применяем стили
        title = f'История Drawdowns\n{", ".join(symbols)}'
        ylabel = f'Drawdown ({currency})'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel,
            grid=True, legend=True, copyright=True
        )
        
        return fig, ax
    
    def create_dividend_yield_chart(self, data, symbols, figsize=(14, 9), **kwargs):
        """
        Создать стандартный график дивидендной доходности
        
        Args:
            data: данные дивидендной доходности
            symbols: список символов
            figsize: размер фигуры
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(figsize=figsize, style='fivethirtyeight')
        
        # Рисуем данные
        if hasattr(data, 'plot'):
            data.plot(ax=ax, linewidth=2.5, alpha=0.9)
        
        # Применяем стили
        title = f'Дивидендная доходность\n{", ".join(symbols)}'
        ylabel = 'Дивидендная доходность (%)'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel,
            grid=True, legend=True, copyright=True
        )
        
        return fig, ax
    
    def create_correlation_matrix_chart(self, correlation_matrix, figsize=(10, 8), **kwargs):
        """
        Создать стандартную корреляционную матрицу
        
        Args:
            correlation_matrix: матрица корреляций
            figsize: размер фигуры
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(figsize=figsize, style='fivethirtyeight')
        
        # Создаем heatmap
        im = ax.imshow(correlation_matrix.values, cmap='RdYlBu_r', aspect='auto', vmin=-1, vmax=1)
        
        # Настраиваем тики и метки
        ax.set_xticks(range(len(correlation_matrix.columns)))
        ax.set_yticks(range(len(correlation_matrix.index)))
        ax.set_xticklabels(correlation_matrix.columns, rotation=45, ha='right')
        ax.set_yticklabels(correlation_matrix.index)
        
        # Добавляем colorbar
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Корреляция', rotation=270, labelpad=15)
        
        # Добавляем значения корреляции для небольших матриц
        if len(correlation_matrix) <= 8:
            for i in range(len(correlation_matrix.index)):
                for j in range(len(correlation_matrix.columns)):
                    value = correlation_matrix.iloc[i, j]
                    text_color = 'white' if abs(value) > 0.7 else 'black'
                    ax.text(j, i, f'{value:.2f}', 
                           ha='center', va='center', 
                           color=text_color, fontsize=9, fontweight='bold')
        
        # Применяем стили
        title = 'Корреляционная матрица активов'
        xlabel = 'Активы'
        ylabel = 'Активы'
        
        self.apply_standard_chart_styling(
            ax, title=title, xlabel=xlabel, ylabel=ylabel,
            grid=False, legend=False, copyright=True
        )
        
        return fig, ax
    
    def create_wealth_index_chart(self, data, symbols, currency, figsize=(14, 9), **kwargs):
        """
        Создать стандартный график накопленной доходности
        
        Args:
            data: данные накопленной доходности
            symbols: список символов
            currency: валюта
            figsize: размер фигуры
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(figsize=figsize, style='fivethirtyeight')
        
        # Рисуем данные
        if hasattr(data, 'plot'):
            data.plot(ax=ax, linewidth=2.5, alpha=0.9)
        
        # Применяем стили
        title = f'Накопленная доходность портфеля\n{", ".join(symbols)}'
        ylabel = f'Накопленная доходность ({currency})'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel,
            grid=True, legend=True, copyright=True
        )
        
        return fig, ax
    
    def create_price_chart(self, data, symbol, currency, period='', figsize=(10, 4), **kwargs):
        """
        Создать стандартный график цен
        
        Args:
            data: данные цен
            symbol: символ актива
            currency: валюта
            period: период (daily, monthly)
            figsize: размер фигуры
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(figsize=figsize, style='fivethirtyeight')
        
        # Рисуем данные
        if hasattr(data, 'plot'):
            data.plot(ax=ax, color=self.colors['primary'], linewidth=2, alpha=0.8)
        else:
            ax.plot(data.index, data.values, color=self.colors['primary'], linewidth=2, alpha=0.8)
        
        # Применяем стили
        title = f'Динамика цены: {symbol} ({period})' if period else f'Динамика цены: {symbol}'
        ylabel = f'{currency}'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel,
            grid=True, legend=False, copyright=True
        )
        
        return fig, ax
    
    def create_dividends_chart(self, data, symbol, currency, figsize=(14, 10), **kwargs):
        """
        Создать стандартный график дивидендов
        
        Args:
            data: данные дивидендов
            symbol: символ актива
            currency: валюта
            figsize: размер фигуры
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(figsize=figsize, style='fivethirtyeight')
        
        # Рисуем данные
        if hasattr(data, 'plot'):
            data.plot(ax=ax, kind='bar', color=self.colors['success'], alpha=0.8)
        else:
            ax.bar(data.index, data.values, color=self.colors['success'], alpha=0.8)
        
        # Применяем стили
        title = f'Дивиденды {symbol}'
        ylabel = f'Сумма ({currency})'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel,
            grid=True, legend=False, copyright=True
        )
        
        # Настройка для столбчатого графика
        ax.tick_params(axis='x', rotation=45)
        
        return fig, ax
    
    def create_monte_carlo_chart(self, data, symbols, figsize=(14, 9), **kwargs):
        """
        Создать стандартный график Монте-Карло
        
        Args:
            data: данные Монте-Карло
            symbols: список символов
            figsize: размер фигуры
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(figsize=figsize, style='fivethirtyeight')
        
        # Рисуем данные
        if hasattr(data, 'plot'):
            data.plot(ax=ax, alpha=0.6)
        
        # Применяем специальные стили Монте-Карло
        self.apply_monte_carlo_style(ax)
        
        # Применяем стандартные стили
        title = f'Прогноз Монте-Карло\n{", ".join(symbols)}'
        ylabel = 'Накопленная доходность'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel,
            grid=True, legend=True, copyright=True
        )
        
        return fig, ax
    
    def create_percentile_chart(self, data, symbols, figsize=(14, 9), **kwargs):
        """
        Создать стандартный график с процентилями
        
        Args:
            data: данные с процентилями
            symbols: список символов
            figsize: размер фигуры
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(figsize=figsize, style='fivethirtyeight')
        
        # Рисуем данные
        if hasattr(data, 'plot'):
            data.plot(ax=ax)
        
        # Применяем специальные стили процентилей
        self.apply_percentile_style(ax)
        
        # Применяем стандартные стили
        title = f'Прогноз с процентилями\n{", ".join(symbols)}'
        ylabel = 'Накопленная доходность'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel,
            grid=True, legend=True, copyright=True
        )
        
        return fig, ax
    
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
    
    def _add_price_statistics(self, ax, values):
        """Добавить статистику цен на график"""
        try:
            if len(values) > 0:
                current_price = float(values[-1])
                start_price = float(values[0])
                min_price = float(min(values))
                max_price = float(max(values))
                
                if start_price != 0:
                    price_change = ((current_price - start_price) / start_price) * 100
                    stats_text = f'Изменение: {price_change:+.2f}%\n'
                    stats_text += f'Мин: {min_price:.2f}\n'
                    stats_text += f'Макс: {max_price:.2f}'
                    
                    # Добавляем статистику в правый верхний угол
                    ax.text(0.98, 0.98, stats_text, transform=ax.transAxes,
                           fontsize=10, verticalalignment='top', horizontalalignment='right',
                           bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, 
                                   edgecolor=self.colors['grid'], linewidth=0.8))
        except Exception:
            pass

# Глобальный экземпляр для использования в других модулях
chart_styles = ChartStyles()

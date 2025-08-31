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
            'color': self.colors['text']
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
    
    def add_copyright_to_image(self, chart_data: bytes) -> bytes:
        """Добавить копирайт к готовому изображению (bytes)"""
        try:
            import matplotlib.pyplot as plt
            import io
            from PIL import Image, ImageDraw, ImageFont
            
            # Конвертируем bytes в PIL Image
            img = Image.open(io.BytesIO(chart_data))
            
            # Создаем объект для рисования
            draw = ImageDraw.Draw(img)
            
            # Получаем размеры изображения
            width, height = img.size
            
            # Добавляем копирайт в правом нижнем углу
            copyright_text = self.copyright_config['text']
            
            # Пытаемся использовать системный шрифт
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", self.copyright_config['fontsize'])
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", self.copyright_config['fontsize'])
                except:
                    font = ImageFont.load_default()
            
            # Получаем размер текста
            bbox = draw.textbbox((0, 0), copyright_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Позиция текста (правый нижний угол с отступом)
            x = width - text_width - 10
            y = height - text_height - 10
            
            # Рисуем фон для текста
            draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], 
                         fill='white', outline='black', width=1)
            
            # Рисуем текст
            draw.text((x, y), copyright_text, fill='black', font=font)
            
            # Конвертируем обратно в bytes
            output = io.BytesIO()
            img.save(output, format='PNG')
            output.seek(0)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Error adding copyright to image: {e}")
            # Возвращаем оригинальный график если не удалось добавить копирайт
            return chart_data

    
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
    
    def create_price_chart(self, symbol: str, dates, values, currency: str, 
                          chart_type: str = 'daily', title_suffix: str = '') -> bytes:
        """
        Создать график цен с унифицированными стилями
        
        Args:
            symbol: символ актива
            dates: даты
            values: значения цен
            currency: валюта
            chart_type: тип графика ('daily' или 'monthly')
            title_suffix: дополнительный текст в заголовке
            
        Returns:
            bytes: изображение графика
        """
        try:
            import matplotlib.pyplot as plt
            import io
            import matplotlib.dates as mdates
            
            # Создаем фигуру
            fig, ax = self.create_figure(figsize=(12, 7))
            
            # Применяем базовый стиль
            self.apply_base_style(fig, ax)
            
            # Выбираем цвет в зависимости от типа графика
            line_color = self.colors['primary'] if chart_type == 'daily' else self.colors['secondary']
            
            # Рисуем линию
            self.plot_smooth_line(ax, dates, values, 
                                color=line_color,
                                label=f'{symbol} ({currency})')
            
            # Настраиваем заголовок
            title = f'{"Ежедневный" if chart_type == "daily" else "Месячный"} график: {symbol}'
            if title_suffix:
                title += f' {title_suffix}'
            ax.set_title(title, **self.title_config)
            
            # Настраиваем оси
            ax.set_xlabel('Дата', **self.axis_config)
            ax.set_ylabel(f'Цена ({currency})', **self.axis_config)
            
            # Форматируем ось X для дат
            if hasattr(dates, 'dtype') and dates.dtype.kind in ['M', 'O']:
                if chart_type == 'daily':
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
                else:  # monthly
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
                    ax.xaxis.set_major_locator(mdates.YearLocator(2))
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Добавляем статистику
            self._add_price_statistics(ax, values)
            
            # Добавляем копирайт
            self.add_copyright(ax)
            
            # Сохраняем график
            img_buffer = io.BytesIO()
            self.save_figure(fig, img_buffer)
            img_buffer.seek(0)
            
            # Очищаем память
            self.cleanup_figure(fig)
            
            return img_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Error creating price chart: {e}")
            return None
    
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

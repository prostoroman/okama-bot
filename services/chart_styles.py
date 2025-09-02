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
import tempfile
import os

# Set matplotlib cache directory to avoid permission issues
matplotlib_cache_dir = os.path.join(tempfile.gettempdir(), 'matplotlib_cache')
os.makedirs(matplotlib_cache_dir, exist_ok=True)
mpl.rcParams['cache_dir'] = matplotlib_cache_dir

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

    # ============================================================================
    # БАЗОВЫЕ МЕТОДЫ СОЗДАНИЯ И СТИЛИЗАЦИИ
    # ============================================================================
    
    def create_standard_chart(self, rows=1, cols=1, figsize=None, **kwargs):
        """
        Универсальный метод создания стандартной фигуры
        
        Args:
            rows: количество строк
            cols: количество столбцов
            figsize: размер фигуры
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) или (fig, (ax1, ax2, ...)) - фигура и оси
        """
        try:
            # Применяем стиль
            plt.style.use(self.style_config['style'])
            
            # Создаем фигуру
            if figsize is None:
                if rows == 1 and cols == 1:
                    figsize = self.style_config['figsize']
                elif rows > 1 or cols > 1:
                    # Адаптируем размер для множественных панелей
                    base_width, base_height = self.style_config['figsize']
                    figsize = (base_width, base_height * rows / cols)
                else:
                    figsize = self.style_config['figsize']
            
            if rows == 1 and cols == 1:
                fig, ax = plt.subplots(figsize=figsize, **kwargs)
                self._apply_base_style(fig, ax)
                return fig, ax
            else:
                fig, axes = plt.subplots(rows, cols, figsize=figsize, **kwargs)
                if rows == 1 or cols == 1:
                    axes = [axes] if rows == 1 else [axes]
                else:
                    axes = axes.flatten()
                
                # Применяем базовый стиль ко всем осям
                for ax in axes:
                    self._apply_base_style(fig, ax)
                
                return fig, axes if len(axes) > 1 else axes[0]
                
        except Exception as e:
            logger.error(f"Error creating standard chart: {e}")
            # Fallback к простому созданию
            return plt.subplots(figsize=figsize or self.style_config['figsize'])
    
    def _apply_base_style(self, fig, ax):
        """Применить базовый стиль к оси"""
        try:
            ax.set_facecolor(self.colors['neutral'])
            
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
    
    def apply_standard_chart_styling(self, ax, title=None, xlabel=None, ylabel=None, 
                                   grid=True, legend=True, copyright=True, show_xlabel=False, **kwargs):
        """
        Универсальный метод применения стандартных стилей
        
        Args:
            ax: matplotlib axes
            title: заголовок графика
            xlabel: подпись оси X
            ylabel: подпись оси Y
            grid: показывать сетку
            legend: показывать легенду
            copyright: добавлять копирайт
            show_xlabel: показывать подпись оси X
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
            
            # Легенда - исправлено: создаем легенду если есть данные
            if legend:
                handles, labels = ax.get_legend_handles_labels()
                if handles and labels:
                    # Если есть данные для легенды, создаем её
                    ax.legend(**self.legend_config)
                elif ax.get_legend() is not None:
                    # Если легенда уже существует, применяем стили
                    legend_obj = ax.get_legend()
                    legend_obj.set_fontsize(self.legend_config['fontsize'])
                    legend_obj.set_frame_on(self.legend_config['frameon'])
                    legend_obj.set_fancybox(self.legend_config['fancybox'])
                    legend_obj.set_shadow(self.legend_config['shadow'])
                    legend_obj.set_loc(self.legend_config['loc'])
            
            # Копирайт - исправлено: улучшено позиционирование
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
                               labelsize=10, 
                               colors=self.colors['text'])
                
        except Exception as e:
            logger.error(f"Error applying standard chart styling: {e}")
    
    def add_copyright(self, ax):
        """Добавить копирайт к графику - исправлено позиционирование"""
        try:
            # Улучшенное позиционирование копирайта
            # Позиция: (x, y) где x=0.01 (1% от ширины), y=-0.02 (2% ниже графика)
            ax.text(0.01, -0.02, 
                   self.copyright_config['text'],
                   transform=ax.transAxes, 
                   fontsize=self.copyright_config['fontsize'], 
                   color=self.copyright_config['color'], 
                   alpha=self.copyright_config['alpha'],
                   ha='left',  # выравнивание по левому краю
                   va='top')   # выравнивание по верхнему краю
        except Exception as e:
            logger.error(f"Error adding copyright: {e}")
    
    def get_color(self, index):
        """Получить цвет по индексу"""
        colors_list = list(self.colors.values())
        return colors_list[index % len(colors_list)]
    
    # ============================================================================
    # УНИВЕРСАЛЬНЫЕ МЕТОДЫ СОЗДАНИЯ ГРАФИКОВ
    # ============================================================================
    
    def create_line_chart(self, data, title, ylabel, xlabel='', 
                         legend=True, grid=True, copyright=True, 
                         line_config=None, **kwargs):
        """
        Универсальный метод создания линейного графика
        
        Args:
            data: данные для графика
            title: заголовок
            ylabel: подпись оси Y
            xlabel: подпись оси X
            legend: показывать легенду
            grid: показывать сетку
            copyright: добавлять копирайт
            line_config: настройки линий
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Настройки линий по умолчанию
        if line_config is None:
            line_config = self.line_config
        
        # Рисуем данные
        if hasattr(data, 'plot'):
            data.plot(ax=ax, linewidth=line_config['linewidth'], alpha=line_config['alpha'])
        else:
            ax.plot(data.index, data.values, linewidth=line_config['linewidth'], alpha=line_config['alpha'])
        
        # Применяем стандартные стили
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel, xlabel=xlabel, show_xlabel=False,
            grid=grid, legend=False, copyright=copyright  # Отключаем легенду для одиночных линий
        )
        
        return fig, ax
    
    def create_bar_chart(self, data, title, ylabel, xlabel='', 
                        legend=False, grid=True, copyright=True, 
                        bar_color=None, **kwargs):
        """
        Универсальный метод создания столбчатого графика
        
        Args:
            data: данные для графика
            title: заголовок
            ylabel: подпись оси Y
            xlabel: подпись оси X
            legend: показывать легенду
            grid: показывать сетку
            copyright: добавлять копирайт
            bar_color: цвет столбцов
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Цвет столбцов по умолчанию
        if bar_color is None:
            bar_color = self.colors['success']
        
        # Рисуем столбчатую диаграмму
        if hasattr(data, 'plot'):
            data.plot(ax=ax, kind='bar', color=bar_color, alpha=0.8)
        else:
            ax.bar(data.index, data.values, color=bar_color, alpha=0.8)
        
        # Применяем стандартные стили
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel, xlabel=xlabel, show_xlabel=False,
            grid=grid, legend=legend, copyright=copyright
        )
        
        # Настройка для столбчатого графика
        ax.tick_params(axis='x', rotation=45)
        
        return fig, ax
    
    def create_multi_line_chart(self, data, title, ylabel, xlabel='', 
                               legend=True, grid=True, copyright=True, 
                               line_config=None, **kwargs):
        """
        Универсальный метод создания графика с множественными линиями
        
        Args:
            data: DataFrame с данными
            title: заголовок
            ylabel: подпись оси Y
            xlabel: подпись оси X
            legend: показывать легенду
            grid: показывать сетку
            copyright: добавлять копирайт
            line_config: настройки линий
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Настройки линий по умолчанию
        if line_config is None:
            line_config = self.line_config
        
        # Подготовка безопасной оси X: конвертация Period/дато-подобных значений в datetime
        x_index = data.index
        x_values = []
        try:
            # Явная обработка PeriodIndex
            if isinstance(x_index, pd.PeriodIndex):
                x_values = x_index.to_timestamp().to_pydatetime()
            else:
                # Поштучная конвертация значений индекса
                for idx, x_val in enumerate(list(x_index)):
                    try:
                        # Если это Period-подобный объект
                        if hasattr(x_val, 'to_timestamp'):
                            try:
                                x_val = x_val.to_timestamp()
                            except Exception:
                                x_val = pd.to_datetime(str(x_val))
                        # Универсальная конвертация к datetime
                        dt = pd.to_datetime(x_val)
                        # Преобразуем к native datetime для Matplotlib
                        if hasattr(dt, 'to_pydatetime'):
                            dt = dt.to_pydatetime()
                        x_values.append(dt)
                    except Exception:
                        # Фоллбэк: помечаем как None, позже заменим
                        x_values.append(None)
                # Если все элементы не удалось сконвертировать — используем числовой индекс
                if all(v is None for v in x_values):
                    x_values = np.arange(len(x_index))
                else:
                    # Заменяем None на монотонно возрастающие даты-фоллбэки
                    base = pd.to_datetime('1970-01-01')
                    x_values = [
                        (base + pd.to_timedelta(i, unit='D')).to_pydatetime() if v is None else v
                        for i, v in enumerate(x_values)
                    ]
        except Exception:
            # Любые неожиданные ошибки — фоллбэк к числовой оси
            x_values = np.arange(len(x_index))

        # Рисуем данные для каждого столбца
        for i, column in enumerate(data.columns):
            color = self.get_color(i)
            ax.plot(x_values, data[column].values,
                    color=color, linewidth=line_config['linewidth'],
                    alpha=line_config['alpha'], label=column)
        
        # Применяем стандартные стили
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel, xlabel=xlabel, show_xlabel=False,
            grid=grid, legend=legend, copyright=copyright
        )
        
        # Настройка для временных рядов
        ax.tick_params(axis='x', rotation=45)
        
        return fig, ax
    
    # ============================================================================
    # СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ДЛЯ ПОРТФЕЛЯ
    # ============================================================================
    
    def create_portfolio_wealth_chart(self, data, symbols, currency, **kwargs):
        """Создать график накопленной доходности портфеля"""
        return self.create_line_chart(
            data=data, 
            title=f'Накопленная доходность портфеля\n{", ".join(symbols)}',
            ylabel=f'Накопленная доходность ({currency})' if currency else 'Накопленная доходность',
            **kwargs
        )
    
    def create_portfolio_returns_chart(self, data, symbols, currency, **kwargs):
        """Создать график годовой доходности портфеля"""
        return self.create_bar_chart(
            data=data,
            title=f'Годовая доходность портфеля\n{", ".join(symbols)}',
            ylabel=f'Доходность ({currency}) (%)',
            **kwargs
        )
    
    def create_portfolio_drawdowns_chart(self, data, symbols, currency, **kwargs):
        """Создать график просадок портфеля"""
        return self.create_line_chart(
            data=data,
            title=f'Просадки портфеля\n{", ".join(symbols)}',
            ylabel=f'Просадка ({currency}) (%)',
            **kwargs
        )
    
    def create_portfolio_rolling_cagr_chart(self, data, symbols, currency, **kwargs):
        """Создать график скользящего CAGR портфеля"""
        return self.create_line_chart(
            data=data,
            title=f'Скользящий CAGR портфеля\n{", ".join(symbols)}',
            ylabel=f'CAGR ({currency}) (%)',
            **kwargs
        )
    
    def create_portfolio_compare_assets_chart(self, data, symbols, currency, **kwargs):
        """Создать график сравнения портфеля с активами"""
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Рисуем данные с кастомными стилями линий
        if hasattr(data, 'plot'):
            data.plot(ax=ax, alpha=0.8)
        
        # Кастомизируем стили линий: портфель толще, активы тоньше
        lines = ax.get_lines()
        if len(lines) > 0:
            # Первая линия - обычно портфель (комбинированный)
            if len(lines) >= 1:
                lines[0].set_linewidth(3.0)  # Линия портфеля толще
                lines[0].set_alpha(1.0)      # Полная непрозрачность
                lines[0].set_color(self.colors['primary'])  # Основной цвет для портфеля
            
            # Линии активов тоньше
            for i in range(1, len(lines)):
                lines[i].set_linewidth(1.5)  # Линии активов тоньше
                lines[i].set_alpha(0.8)      # Слегка прозрачные
                # Используем разные цвета для активов
                lines[i].set_color(self.get_color(i-1))
        
        # Применяем стандартные стили
        title = f'Портфель vs Активы\n{", ".join(symbols)}'
        ylabel = f'Накопленная доходность ({currency})' if currency else 'Накопленная доходность'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel, xlabel='', show_xlabel=True,
            grid=True, legend=True, copyright=True
        )
        
        return fig, ax
    
    # ============================================================================
    # СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ДЛЯ АКТИВОВ
    # ============================================================================
    
    def create_price_chart(self, data, symbol, currency, period='', **kwargs):
        """Создать график цен актива"""
        return self.create_line_chart(
            data=data,
            title=f'Динамика цены: {symbol} ({period})' if period else f'Динамика цены: {symbol}',
            ylabel=f'Цена ({currency})' if currency else 'Цена',
            copyright=False,
            **kwargs
        )
    
    def create_dividends_chart(self, data, symbol, currency, **kwargs):
        """Создать график дивидендов"""
        return self.create_bar_chart(
            data=data,
            title=f'Дивиденды {symbol}',
            ylabel=f'Сумма ({currency})',
            bar_color=self.colors['success'],
            **kwargs
        )
    
    def create_dividend_yield_chart(self, data, symbols, **kwargs):
        """Создать график дивидендной доходности"""
        return self.create_multi_line_chart(
            data=data,
            title=f'Дивидендная доходность: {", ".join(symbols)}',
            ylabel='Дивидендная доходность (%)',
            **kwargs
        )
    
    def create_dividend_table_chart(self, table_data, headers, title='История дивидендов', **kwargs):
        """Создать график с таблицей дивидендов"""
        fig, ax = self.create_standard_chart(**kwargs)
        
        ax.axis('tight')
        ax.axis('off')
        
        # Создаем таблицу
        table = ax.table(cellText=table_data,
                       colLabels=headers,
                       cellLoc='center',
                       loc='center')
        
        # Базовые стили таблицы
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        # Применяем стили
        self.apply_standard_chart_styling(
            ax, title=title,
            grid=False, legend=False, copyright=True
        )
        
        return fig, ax, table
    
    # ============================================================================
    # СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ДЛЯ АНАЛИЗА
    # ============================================================================
    
    def create_price_volatility_chart(self, data, symbol, currency, **kwargs):
        """Создать график скользящей волатильности"""
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Вычисляем скользящую волатильность
        window_size = min(30, len(data) // 4)
        rolling_vol = data.pct_change().rolling(window=window_size).std() * np.sqrt(252)
        
        # Рисуем график волатильности
        ax.plot(rolling_vol.index, rolling_vol.values, color=self.colors['warning'], linewidth=1.5)
        
        # Применяем стандартные стили
        title = f'Скользящая волатильность ({window_size} дней): {symbol}'
        ylabel = 'Волатильность (годовая)'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel, xlabel='', show_xlabel=True,
            grid=True, legend=False, copyright=True
        )
        
        # Настройка для временных рядов
        ax.tick_params(axis='x', rotation=45)
        
        return fig, ax
    
    def create_drawdowns_chart(self, data, symbols, currency, **kwargs):
        """
        Создать график просадок для нескольких активов
        
        Args:
            data: данные просадок (pandas DataFrame или Series)
            symbols: список символов активов
            currency: валюта
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Handle different data types
        if isinstance(data, pd.Series):
            # Single series - convert to DataFrame
            data = pd.DataFrame({symbols[0] if symbols else 'Asset': data})
        
        # Ensure data is DataFrame
        if not isinstance(data, pd.DataFrame):
            self.logger.warning(f"Unexpected data type for drawdowns: {type(data)}")
            return fig, ax
        
        # Plot each column
        for i, column in enumerate(data.columns):
            if column in data.columns and not data[column].empty:
                color = self.get_color(i)
                ax.plot(data.index, data[column].values * 100,  # Convert to percentage
                       color=color, linewidth=self.line_config['linewidth'], 
                       alpha=self.line_config['alpha'], label=column)
        
        # Apply standard styling
        title = f'Просадки активов: {", ".join(symbols)}'
        ylabel = f'Просадка (%)'
        
        self.apply_standard_chart_styling(
            ax,
            title=title,
            ylabel=ylabel,
            grid=True,
            legend=True,
            copyright=True
        )
        
        return fig, ax
    
    def create_drawdowns_history_chart(self, data, symbol, **kwargs):
        """Создать график истории просадок"""
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Вычисляем просадки
        cummax = data.cummax()
        drawdowns = (data - cummax) / cummax * 100
        
        # Рисуем график просадок
        ax.fill_between(drawdowns.index, drawdowns.values, 0, color=self.colors['danger'], alpha=0.3)
        ax.plot(drawdowns.index, drawdowns.values, color=self.colors['danger'], linewidth=1)
        
        # Применяем стандартные стили
        title = f'История просадок: {symbol}'
        ylabel = 'Просадка (%)'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel, xlabel='', show_xlabel=True,
            grid=True, legend=False, copyright=True
        )
        
        # Настройка для временных рядов
        ax.tick_params(axis='x', rotation=45)
        
        return fig, ax
    
    def create_price_returns_comparison_chart(self, prices, returns, symbol, currency, **kwargs):
        """Создать график сравнения цен и доходности"""
        fig, (ax1, ax2) = self.create_standard_chart(2, 1, **kwargs)
        
        # График цены
        ax1.plot(prices.index, prices.values, color=self.colors['primary'], linewidth=2)
        ax1.set_title(f'Динамика цены: {symbol}', **self.title_config)
        ax1.set_ylabel(f'Цена ({currency})', **self.axis_config)
        ax1.grid(True, **self.grid_config)
        ax1.tick_params(axis='x', rotation=45)
        
        # График доходности
        ax2.plot(returns.index, returns.values, color=self.colors['success'], linewidth=2)
        ax2.set_title('Накопленная доходность', **self.title_config)
        ax2.set_ylabel('Доходность (разы)', **self.axis_config)
        ax2.grid(True, **self.grid_config)
        ax2.tick_params(axis='x', rotation=45)
        
        # Применяем базовые стили
        self._apply_base_style(fig, ax1)
        self._apply_base_style(fig, ax2)
        
        # Добавляем копирайт
        self.add_copyright(ax1)
        self.add_copyright(ax2)
        
        # Настройка макета
        fig.tight_layout()
        
        return fig, ax1, ax2
    
    def create_asset_comparison_chart(self, data, symbols, currency, **kwargs):
        """Создать график сравнения активов"""
        return self.create_multi_line_chart(
            data=data,
            title=f'Сравнение активов: {", ".join(symbols)}',
            ylabel=f'Цена ({currency})' if currency else 'Цена',
            **kwargs
        )
    
    def create_correlation_chart(self, correlation_matrix, **kwargs):
        """Создать график корреляции"""
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Создаем тепловую карту корреляции
        im = ax.imshow(correlation_matrix.values, cmap='RdYlBu_r', aspect='auto')
        
        # Применяем стандартные стили
        title = 'Корреляция между активами'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel='', xlabel='', show_xlabel=False,
            grid=False, legend=False, copyright=True
        )
        
        # Настройка цветовой шкалы
        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label('Корреляция')
        
        # Настройка меток осей
        ax.set_xticks(range(len(correlation_matrix.columns)))
        ax.set_yticks(range(len(correlation_matrix.index)))
        ax.set_xticklabels(correlation_matrix.columns, rotation=45)
        ax.set_yticklabels(correlation_matrix.index)
        
        return fig, ax
    
    def create_dividend_yield_history_chart(self, data, symbols, **kwargs):
        """Создать график истории дивидендной доходности"""
        return self.create_multi_line_chart(
            data=data,
            title=f'История дивидендной доходности: {", ".join(symbols)}',
            ylabel='Дивидендная доходность (%)',
            **kwargs
        )
    
    # ============================================================================
    # СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ ДЛЯ МОНТЕ-КАРЛО И ПРОЦЕНТИЛЕЙ
    # ============================================================================
    
    def create_monte_carlo_chart(self, data, symbols, **kwargs):
        """Создать график Монте-Карло"""
        return self._create_special_chart(
            data=data, symbols=symbols, 
            chart_type='Прогноз Монте-Карло', 
            ylabel='Накопленная доходность',
            style_method=self._apply_monte_carlo_style, **kwargs
        )
    
    def create_percentile_chart(self, data, symbols, **kwargs):
        """Создать график с процентилями"""
        return self._create_special_chart(
            data=data, symbols=symbols, 
            chart_type='Прогноз с процентилями', 
            ylabel='Накопленная доходность',
            style_method=self._apply_percentile_style, **kwargs
        )
    
    def _create_special_chart(self, data, symbols, chart_type, ylabel, 
                             style_method=None, **kwargs):
        """Базовый метод для создания специальных графиков"""
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Рисуем данные
        if hasattr(data, 'plot'):
            data.plot(ax=ax, alpha=0.6)
        
        # Применяем специальные стили, если указан метод
        if style_method:
            style_method(ax)
        
        # Применяем стандартные стили
        title = f'{chart_type}\n{", ".join(symbols)}'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel, xlabel='', show_xlabel=True,
            grid=True, legend=True, copyright=True
        )
        
        return fig, ax
    
    def _apply_monte_carlo_style(self, ax):
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
            
            # Применяем стандартную сетку для консистентности
            ax.grid(True, **self.grid_config)
            
            logger.info(f"Applied Monte Carlo styles: main line (thick), {len(ax.lines)-1} test lines (thin, bright)")
            
        except Exception as e:
            logger.error(f"Error applying Monte Carlo styles: {e}")
    
    def _apply_percentile_style(self, ax):
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
                
                # Применяем стандартную сетку для консистентности
                ax.grid(True, **self.grid_config)
                
                # Применяем стандартную легенду для консистентности
                if ax.get_legend() is not None:
                    ax.legend(**self.legend_config)
                
                logger.info(f"Applied percentile styles: 10% (red), 50% (blue), 90% (green)")
            
        except Exception as e:
            logger.error(f"Error applying percentile styles: {e}")
    
    # ============================================================================
    # УТИЛИТЫ И ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ============================================================================
    
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
    
    def smooth_line_data(self, x_data, y_data, n_points=None):
        """Сгладить данные линии с помощью интерполяции сплайнами"""
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
                        # Handle Period objects specifically
                        if hasattr(x_val, 'to_timestamp'):
                            try:
                                x_val = x_val.to_timestamp()
                            except Exception:
                                # If to_timestamp fails, try to convert Period to string first
                                if hasattr(x_val, 'strftime'):
                                    x_val = pd.to_datetime(str(x_val))
                                else:
                                    x_val = pd.to_datetime(x_val)
                        
                        if hasattr(x_val, 'timestamp'):
                            x_numeric.append(float(x_val.timestamp()))
                        elif isinstance(x_val, np.datetime64):
                            x_numeric.append(float(np.datetime64(x_val).astype('datetime64[s]').astype(int)))
                        else:
                            # Попытка привести через pandas
                            try:
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
                
                # Интерполяция сплайнами
                try:
                    spline = make_interp_spline(x_unique, y_unique, k=min(3, len(x_unique)-1))
                    x_smooth = np.linspace(x_unique.min(), x_unique.max(), n_points)
                    y_smooth = spline(x_smooth)
                    
                    # Преобразуем обратно в даты
                    x_smooth_dates = []
                    for x_val in x_smooth:
                        try:
                            dt = datetime.fromtimestamp(x_val)
                            x_smooth_dates.append(dt)
                        except Exception:
                            x_smooth_dates.append(dt)
                    
                    return x_smooth_dates, y_smooth
                    
                except Exception as e:
                    logger.warning(f"Spline interpolation failed: {e}, returning original data")
                    return x_data, y_data
            else:
                # Для числовых x используем простую интерполяцию
                try:
                    # Сортируем
                    sort_idx = np.argsort(x_valid)
                    x_sorted = x_valid[sort_idx]
                    y_sorted = y_valid[sort_idx]
                    
                    # Убираем дубли
                    unique_mask = np.concatenate(([True], np.diff(x_sorted) > 0))
                    x_unique = x_sorted[unique_mask]
                    y_unique = y_sorted[unique_mask]
                    if len(x_unique) < 3:
                        logger.warning("Too few unique x-coordinates for interpolation, returning original data")
                        return x_data, y_data
                    
                    # Интерполяция сплайнами
                    spline = make_interp_spline(x_unique, y_unique, k=min(3, len(x_unique)-1))
                    x_smooth = np.linspace(x_unique.min(), x_unique.max(), n_points)
                    y_smooth = spline(x_smooth)
                    
                    return x_smooth, y_smooth
                    
                except Exception as e:
                    logger.warning(f"Spline interpolation failed: {e}, returning original data")
                    return x_data, y_data
                    
        except Exception as e:
            logger.error(f"Error in smooth_line_data: {e}")
            return x_data, y_data
    
    def create_comparison_chart(self, data, symbols, currency, **kwargs):
        """
        Создать график сравнения активов
        
        Args:
            data: DataFrame с данными накопленной доходности
            symbols: список символов активов
            currency: валюта
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(**kwargs)
        # Безопасно обработаем PeriodIndex у данных
        try:
            if hasattr(data, 'index') and hasattr(data.index, 'dtype') and str(data.index.dtype).startswith('period'):
                data = data.copy()
                try:
                    data.index = data.index.to_timestamp()
                except Exception:
                    # Fallback: привести к datetime через to_datetime строкового представления
                    try:
                        data.index = pd.to_datetime(data.index.astype(str))
                    except Exception:
                        pass
        except Exception:
            pass
        
        # Рисуем данные для каждого столбца
        for i, column in enumerate(data.columns):
            color = self.get_color(i)
            ax.plot(data.index, data[column].values, 
                   color=color, linewidth=self.line_config['linewidth'], 
                   alpha=self.line_config['alpha'], label=column)
        
        # Применяем стандартные стили
        title = f'Сравнение активов: {", ".join(symbols)}'
        ylabel = f'Накопленная доходность ({currency})' if currency else 'Накопленная доходность'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel, xlabel='', show_xlabel=False,
            grid=True, legend=True, copyright=True
        )
        
        # Настройка для временных рядов
        ax.tick_params(axis='x', rotation=45)
        
        return fig, ax
    
    def create_correlation_matrix_chart(self, correlation_matrix, **kwargs):
        """
        Создать график корреляционной матрицы
        
        Args:
            correlation_matrix: DataFrame с корреляционной матрицей
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Создаем тепловую карту корреляционной матрицы
        im = ax.imshow(correlation_matrix.values, cmap='RdYlBu_r', vmin=-1, vmax=1, aspect='auto')
        
        # Настройка осей
        ax.set_xticks(range(len(correlation_matrix.columns)))
        ax.set_yticks(range(len(correlation_matrix.index)))
        ax.set_xticklabels(correlation_matrix.columns, rotation=45, ha='right')
        ax.set_yticklabels(correlation_matrix.index)
        
        # Добавляем цветовую шкалу
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Корреляция', rotation=270, labelpad=15)
        
        # Добавляем значения в ячейки
        for i in range(len(correlation_matrix.index)):
            for j in range(len(correlation_matrix.columns)):
                value = correlation_matrix.iloc[i, j]
                text_color = 'white' if abs(value) > 0.5 else 'black'
                ax.text(j, i, f'{value:.2f}', ha='center', va='center', 
                       color=text_color, fontweight='bold', fontsize=10)
        
        # Применяем стандартные стили
        title = f'Корреляционная матрица ({len(correlation_matrix.columns)} активов)'
        
        self.apply_standard_chart_styling(
            ax, title=title, xlabel='', ylabel='', show_xlabel=False, show_ylabel=False,
            grid=False, legend=False, copyright=True
        )
        
        return fig, ax
    
    def create_dividends_chart_enhanced(self, data, symbol, currency, **kwargs):
        """
        Создать улучшенный график дивидендов
        
        Args:
            data: Series с данными дивидендов
            symbol: символ актива
            currency: валюта
            **kwargs: дополнительные параметры
            
        Returns:
            tuple: (fig, ax) - фигура и оси
        """
        fig, ax = self.create_standard_chart(**kwargs)
        
        # Рисуем столбчатую диаграмму
        dates = [pd.to_datetime(date) for date in data.index]
        amounts = data.values
        
        bars = ax.bar(dates, amounts, color=self.colors['success'], alpha=0.7, width=20)
        
        # Применяем стандартные стили
        title = f'Дивиденды {symbol}'
        ylabel = f'Сумма ({currency})'
        
        self.apply_standard_chart_styling(
            ax, title=title, ylabel=ylabel, xlabel='', show_xlabel=False,
            grid=True, legend=False, copyright=True
        )
        
        # Форматирование оси X
        fig.autofmt_xdate()
        
        # Добавляем статистику в левом верхнем углу
        total_dividends = data.sum()
        avg_dividend = data.mean()
        max_dividend = data.max()
        
        stats_text = f'Общая сумма: {total_dividends:.2f} {currency}\n'
        stats_text += f'Средняя выплата: {avg_dividend:.2f} {currency}\n'
        stats_text += f'Максимальная выплата: {max_dividend:.2f} {currency}'
        
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
               verticalalignment='top', fontsize=10,
               bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
        
        return fig, ax
    
    def apply_monte_carlo_style(self, ax):
        """
        Применить стили для графиков Monte Carlo
        
        Args:
            ax: matplotlib axes
        """
        self._apply_monte_carlo_style(ax)
    
    def apply_percentile_style(self, ax):
        """
        Применить стили для графиков процентилей
        
        Args:
            ax: matplotlib axes
        """
        self._apply_percentile_style(ax)

# Глобальный экземпляр для использования в других модулях
chart_styles = ChartStyles()

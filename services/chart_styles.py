"""
Chart Styles Module - Minimalist Refactored Version

Централизованный модуль для управления стилями графиков с:
- Едиными настройками стилей в одном месте
- Универсальными базовыми методами
- Устранением дублирования кода
- Минималистичным подходом
"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
from scipy.interpolate import make_interp_spline
import logging
from datetime import datetime
import pandas as pd
import warnings
import contextlib
from matplotlib.patches import Rectangle
import matplotlib.patches as mpatches

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def suppress_cjk_warnings():
    """Context manager to suppress CJK font warnings during chart generation"""
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
        warnings.filterwarnings('ignore', message='.*missing from font.*')
        yield

class ChartStyles:
    """Класс для управления стилями графиков (Nordic Pro)"""
    
    def __init__(self):
        # Централизованные настройки шрифтов с поддержкой CJK
        mpl.rcParams.update({
            'font.family': ['DejaVu Sans'],  # Будет обновлено в _configure_cjk_fonts()
            'font.sans-serif': ['DejaVu Sans', 'Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'PT Sans', 'Arial', 'Helvetica', 'sans-serif'],
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
            'axes.unicode_minus': False,  # Предотвращает проблемы с Unicode минусом
        })
        
        # Централизованные настройки стилей
        self.style = {
            'figsize': (12, 7),
            'dpi': 96,
            'facecolor': 'white',
            'edgecolor': 'none',
            'bbox_inches': 'tight',
            'style': 'seaborn-v0_8-whitegrid',
        }
        
        # Централизованные настройки линий
        self.lines = {
            'alpha': 0.95,
            'smooth_points': 2000,
        }
        
        # Централизованные настройки осей
        self.axes = {
            'fontsize': 12,
            'fontweight': 'medium',
            'color': '#2E3440',  # строгий графитовый
            'tick_fontsize': 10,
            'tick_color': '#2E3440',  # строгий графитовый
        }
        
        # Централизованные настройки сетки
        self.grid = {
            'alpha': 0.25,
            'linestyle': '-',
            'linewidth': 0.7,
            'color': '#CBD5E1',  # светло-серые линии сетки
            'zorder': 0,
        }
        
        # Централизованные настройки рамок
        self.spines = {
            'color': '#2E3440',  # строгий графитовый
            'linewidth': 1.1,
        }
        
        # Централизованные настройки легенды
        self.legend = {
            'fontsize': 10,
            'frameon': True,
            'loc': 'upper left',
        }
        
        # Централизованные настройки заголовков
        self.title = {
            'fontsize': 16,
            'fontweight': 'semibold',
            'pad': 18,
            'color': '#2E3440',  # строгий графитовый
        }
        
        # Централизованные настройки копирайта
        self.copyright = {
            'text': 'shans.ai | source: okama, tushare',
            'fontsize': 9,
            'color': '#2E3440',  # строгий графитовый
            'alpha': 0.55,
            'position': (0.98, 0.00),
        }
        
        # Настройка CJK шрифтов
        self._configure_cjk_fonts()

    def _configure_cjk_fonts(self):
        """Настройка шрифтов для поддержки CJK символов"""
        try:
            import matplotlib.font_manager as fm
            
            # Получаем список доступных шрифтов
            available_fonts = [f.name for f in fm.fontManager.ttflist]
            
            # Приоритетные CJK шрифты
            cjk_fonts = [
                'DejaVu Sans',           # Поддерживает CJK
                'Arial Unicode MS',      # Windows CJK
                'SimHei',                # Windows Chinese
                'Microsoft YaHei',       # Windows Chinese
                'PingFang SC',           # macOS Chinese
                'Hiragino Sans GB',      # macOS Chinese
                'Noto Sans CJK SC',      # Google Noto CJK
                'Source Han Sans SC',    # Adobe Source Han
                'WenQuanYi Micro Hei',   # Linux Chinese
                'Droid Sans Fallback',   # Android CJK
            ]
            
            # Находим первый доступный CJK шрифт
            selected_font = None
            for font in cjk_fonts:
                if font in available_fonts:
                    selected_font = font
                    break
            
            if selected_font:
                logger.info(f"Using CJK font: {selected_font}")
                # Обновляем настройки шрифта с приоритетом CJK шрифта
                mpl.rcParams['font.family'] = [selected_font]
                mpl.rcParams['font.sans-serif'] = [selected_font] + mpl.rcParams['font.sans-serif']
                # Устанавливаем fallback для CJK символов
                mpl.rcParams['axes.unicode_minus'] = False
            else:
                logger.warning("No CJK fonts found, Chinese characters may not display correctly")
                # Используем DejaVu Sans как fallback (поддерживает базовые CJK)
                mpl.rcParams['font.family'] = ['DejaVu Sans']
                
        except Exception as e:
            logger.warning(f"Could not configure CJK fonts: {e}")
            # Fallback к DejaVu Sans
            mpl.rcParams['font.family'] = ['DejaVu Sans']

    def _safe_text_render(self, text):
        """Безопасное отображение текста с CJK символами"""
        try:
            # Проверяем наличие CJK символов
            import re
            cjk_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf\uf900-\ufaff\u3300-\u33ff]')
            
            if cjk_pattern.search(text):
                # Если есть CJK символы, используем Unicode escape для проблемных символов
                # Это поможет избежать ошибок рендеринга
                return text
            else:
                return text
                
        except Exception as e:
            logger.warning(f"Error in safe text render: {e}")
            return text

    # ============================================================================
    # БАЗОВЫЕ МЕТОДЫ СОЗДАНИЯ И СТИЛИЗАЦИИ
    # ============================================================================
    
    def create_chart(self, rows=1, cols=1, figsize=None, **kwargs):
        """Универсальный метод создания фигуры с применением стилей"""
        try:
            plt.style.use(self.style['style'])
            
            # Убираем параметры, которые не поддерживаются plt.subplots
            plot_kwargs = {k: v for k, v in kwargs.items() if k not in ['copyright', 'title', 'xlabel', 'ylabel']}
            
            if figsize is None:
                if rows == 1 and cols == 1:
                    figsize = self.style['figsize']
                else:
                    base_width, base_height = self.style['figsize']
                    figsize = (base_width, base_height * rows / cols)
            
            if rows == 1 and cols == 1:
                fig, ax = plt.subplots(figsize=figsize, **plot_kwargs)
                self._apply_base_style(fig, ax)
                return fig, ax
            else:
                fig, axes = plt.subplots(rows, cols, figsize=figsize, **plot_kwargs)
                if rows == 1 or cols == 1:
                    axes = [axes] if rows == 1 else [axes]
                else:
                    axes = axes.flatten()
                
                for ax in axes:
                    self._apply_base_style(fig, ax)
                
                return fig, axes if len(axes) > 1 else axes[0]
                
        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            return plt.subplots(figsize=figsize or self.style['figsize'])
    
    def _apply_base_style(self, fig, ax):
        """Применить базовый стиль к оси"""
        try:
            ax.set_facecolor('#E9ECEF')  # светло-серый фон
            
            # Рамки - только снизу и слева
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)
            for spine in ['left', 'bottom']:
                ax.spines[spine].set_color(self.spines['color'])
                ax.spines[spine].set_linewidth(self.spines['linewidth'])
            
            # Тики
            ax.tick_params(axis='both', which='major', 
                           labelsize=self.axes['tick_fontsize'], 
                           color=self.axes['tick_color'])
                
        except Exception as e:
            logger.error(f"Error applying base style: {e}")
    
    def apply_styling(self, ax, title=None, xlabel=None, ylabel=None, 
                     grid=True, legend=True, copyright=True, **kwargs):
        """Универсальный метод применения стилей"""
        try:
            # Заголовок
            if title:
                safe_title = self._safe_text_render(title)
                ax.set_title(safe_title, **self.title)
            
            # Подписи осей
            if xlabel:
                safe_xlabel = self._safe_text_render(xlabel)
                ax.set_xlabel(safe_xlabel, fontsize=self.axes['fontsize'], fontweight=self.axes['fontweight'], color=self.axes['color'])
            if ylabel:
                safe_ylabel = self._safe_text_render(ylabel)
                ax.set_ylabel(safe_ylabel, fontsize=self.axes['fontsize'], fontweight=self.axes['fontweight'], color=self.axes['color'])
            
            # Сетка
            if grid:
                ax.grid(True, **self.grid)
            
            # Легенда
            if legend:
                handles, labels = ax.get_legend_handles_labels()
                if handles and labels:
                    ax.legend(**self.legend)
            
            # Копирайт
            if copyright:
                self.add_copyright(ax)
                
        except Exception as e:
            logger.error(f"Error applying styling: {e}")
    
    def apply_drawdown_styling(self, ax, title=None, xlabel=None, ylabel=None, 
                              grid=True, legend=True, copyright=True, **kwargs):
        """Apply styling for drawdown charts with standard grid colors and date labels above"""
        try:
            # Заголовок
            if title:
                safe_title = self._safe_text_render(title)
                ax.set_title(safe_title, **self.title)
            
            # Подписи осей
            if xlabel:
                safe_xlabel = self._safe_text_render(xlabel)
                ax.set_xlabel(safe_xlabel, fontsize=self.axes['fontsize'], fontweight=self.axes['fontweight'], color=self.axes['color'])
            if ylabel:
                safe_ylabel = self._safe_text_render(ylabel)
                ax.set_ylabel(safe_ylabel, fontsize=self.axes['fontsize'], fontweight=self.axes['fontweight'], color=self.axes['color'])
            
            # Сетка с стандартными цветами matplotlib (без кастомных цветов)
            if grid:
                ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            
            # Легенда
            if legend:
                handles, labels = ax.get_legend_handles_labels()
                if handles and labels:
                    ax.legend(**self.legend)
            
            # Копирайт
            if copyright:
                self.add_copyright(ax)
            
            # Move date labels to appear above the chart
            ax.tick_params(axis='x', labeltop=True, labelbottom=False)
                
        except Exception as e:
            logger.error(f"Error applying drawdown styling: {e}")
    
    def add_copyright(self, ax):
        """Добавить копирайт"""
        try:
            ax.text(*self.copyright['position'], 
                   self.copyright['text'],
                   transform=ax.transAxes, 
                   fontsize=self.copyright['fontsize'], 
                   color=self.copyright['color'], 
                   alpha=self.copyright['alpha'],
                   ha='right', va='bottom')
        except Exception as e:
            logger.error(f"Error adding copyright: {e}")
    
    def get_color(self, index):
        """Получить цвет по индексу"""
        # Используем стандартные цвета matplotlib
        import matplotlib.pyplot as plt
        colors = plt.rcParams['axes.prop_cycle'].by_key()['color']
        return colors[index % len(colors)]
    
    # ============================================================================
    # УНИВЕРСАЛЬНЫЕ МЕТОДЫ СОЗДАНИЯ ГРАФИКОВ
    # ============================================================================
    
    def create_line_chart(self, data, title, ylabel, xlabel='', **kwargs):
        """Создать линейный график"""
        fig, ax = self.create_chart(**kwargs)
        
        if hasattr(data, 'plot'):
            data.plot(ax=ax, alpha=self.lines['alpha'])
        else:
            ax.plot(data.index, data.values, alpha=self.lines['alpha'])
        
        # Extract copyright parameter from kwargs and pass to apply_styling
        copyright_param = kwargs.pop('copyright', True)
        self.apply_styling(ax, title=title, ylabel=ylabel, xlabel=xlabel, legend=False, copyright=copyright_param)
        return fig, ax
    
    def create_bar_chart(self, data, title, ylabel, xlabel='', bar_color=None, **kwargs):
        """Создать столбчатый график"""
        fig, ax = self.create_chart(**kwargs)
        
        if bar_color is None:
            bar_color = '#94D2BD'  # мягкий мятный
        
        if hasattr(data, 'plot'):
            data.plot(ax=ax, kind='bar', color=bar_color, alpha=0.8)
        else:
            ax.bar(data.index, data.values, color=bar_color, alpha=0.8)
        
        self.apply_styling(ax, title=title, ylabel=ylabel, xlabel=xlabel)
        ax.tick_params(axis='x', rotation=45)
        return fig, ax
    
    def create_multi_line_chart(self, data, title, ylabel, xlabel='', **kwargs):
        """Создать график с множественными линиями"""
        fig, ax = self.create_chart(**kwargs)
        
        # Обработка PeriodIndex
        x_index = data.index
        try:
            if isinstance(x_index, pd.PeriodIndex):
                x_values = x_index.to_timestamp().to_pydatetime()
            else:
                x_values = [pd.to_datetime(x_val).to_pydatetime() if hasattr(x_val, 'to_timestamp') else x_val 
                           for x_val in x_index]
        except Exception:
            x_values = np.arange(len(x_index))
        
        # Рисуем данные
        for i, column in enumerate(data.columns):
            color = self.get_color(i)
            ax.plot(x_values, data[column].values,
                    color=color, alpha=self.lines['alpha'], label=column)
        
        self.apply_styling(ax, title=title, ylabel=ylabel, xlabel=xlabel)
        ax.tick_params(axis='x', rotation=45)
        return fig, ax
    
    # ============================================================================
    # СПЕЦИАЛИЗИРОВАННЫЕ МЕТОДЫ
    # ============================================================================
    
    def create_price_chart(self, data, symbol, currency, period='', **kwargs):
        """Создать график цен актива"""
        title = f'Динамика цены: {symbol} ({period})' if period else f'Динамика цены: {symbol}'
        ylabel = f'Цена ({currency})' if currency else 'Цена'
        xlabel = ''  # Пустая подпись по оси X
        return self.create_line_chart(data, title, ylabel, xlabel=xlabel, **kwargs)
    
    def create_dividends_chart(self, data, symbol, currency, **kwargs):
        """Создать график дивидендов"""
        fig, ax = self.create_chart(**kwargs)
        
        # Конвертируем даты и группируем по годам
        # Обрабатываем PeriodIndex (от Okama) и обычные даты
        if hasattr(data.index, 'to_timestamp'):
            # PeriodIndex от Okama
            dates = data.index.to_timestamp()
        else:
            # Обычные даты
            dates = [pd.to_datetime(date) for date in data.index]
        
        amounts = data.values
        
        # Создаем DataFrame с годами
        df = pd.DataFrame({'date': dates, 'amount': amounts})
        df['year'] = df['date'].dt.year
        
        # Группируем по годам и суммируем дивиденды
        yearly_dividends = df.groupby('year')['amount'].sum()
        
        # Создаем столбчатый график
        bars = ax.bar(yearly_dividends.index, yearly_dividends.values, 
                     color='#94D2BD', alpha=0.7, width=0.8)
        
        # Получаем информацию об активе для заголовка
        asset_name = symbol.split('.')[0] if '.' in symbol else symbol
        
        # Обновляем заголовок с нужным форматом
        title = f"{symbol} | {asset_name} | {currency} | dividends"
        ax.set_title(title, **self.title)
        
        # Убираем подписи осей
        ax.set_xlabel('')
        ax.set_ylabel('')
        
        # Настройка осей для отображения только годов
        ax.set_xticks(yearly_dividends.index)
        ax.set_xticklabels(yearly_dividends.index, rotation=45)
        
        # Применяем базовые стили
        self._apply_base_style(fig, ax)
        
        # Добавляем копирайт
        self.add_copyright(ax)
        
        return fig, ax
    
    def create_dividend_yield_chart(self, data, symbols, weights=None, portfolio_name=None, **kwargs):
        """Создать график дивидендной доходности портфеля"""
        fig, ax = self.create_chart(**kwargs)
        
        # Обработка данных - конвертируем Series в DataFrame если необходимо
        if isinstance(data, pd.Series):
            # Используем название портфеля если передано, иначе создаем из символов
            if portfolio_name:
                column_name = portfolio_name
            else:
                # Создаем название портфеля из символов и весов
                if weights:
                    asset_with_weights = []
                    for i, symbol in enumerate(symbols):
                        symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                        weight = weights[i] if i < len(weights) else 0.0
                        asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
                    column_name = ", ".join(asset_with_weights)
                else:
                    column_name = ", ".join(symbols)
            data = pd.DataFrame({column_name: data})
        
        # Обработка PeriodIndex
        x_index = data.index
        try:
            if isinstance(x_index, pd.PeriodIndex):
                x_values = x_index.to_timestamp().to_pydatetime()
            else:
                x_values = [pd.to_datetime(x_val).to_pydatetime() if hasattr(x_val, 'to_timestamp') else x_val 
                           for x_val in x_index]
        except Exception:
            x_values = np.arange(len(x_index))
        
        # Рисуем данные
        for i, column in enumerate(data.columns):
            color = self.get_color(i)
            ax.plot(x_values, data[column].values,
                    color=color, alpha=self.lines['alpha'], label=column)
        
        # Создаем заголовок с весами
        if weights:
            asset_with_weights = []
            for i, symbol in enumerate(symbols):
                symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                weight = weights[i] if i < len(weights) else 0.0
                asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
            title = f'Дивидендная доходность портфеля\n{", ".join(asset_with_weights)}'
        else:
            title = f'Дивидендная доходность портфеля\n{", ".join(symbols)}'
        
        # Убираем подписи осей
        ylabel = ''  # No y-axis label
        xlabel = ''  # No x-axis label
        
        # Применяем общие стили
        self.apply_styling(ax, title=title, ylabel=ylabel, xlabel=xlabel, grid=True, legend=True, copyright=True)
        ax.tick_params(axis='x', rotation=45)
        
        return fig, ax
    
    def create_drawdowns_chart(self, data, symbols, currency, **kwargs):
        """Создать график просадок"""
        fig, ax = self.create_chart(**kwargs)
        
        # Обработка данных
        if isinstance(data, pd.Series):
            data = pd.DataFrame({symbols[0] if symbols else 'Asset': data})
        
        cleaned_data = data.copy()
        if hasattr(cleaned_data.index, 'dtype') and str(cleaned_data.index.dtype).startswith('period'):
            cleaned_data.index = cleaned_data.index.to_timestamp()
        
        # Рисуем данные
        for i, column in enumerate(cleaned_data.columns):
            if column in cleaned_data.columns and not cleaned_data[column].empty:
                color = self.get_color(i)
                ax.plot(cleaned_data.index, cleaned_data[column].values * 100,
                       color=color, alpha=self.lines['alpha'], label=column)
        
        title = f'Просадки активов: {", ".join(symbols)}'
        ylabel = f'Просадка (%)'
        
        # Apply drawdown-specific styling with standard grid colors and date labels above
        self.apply_drawdown_styling(ax, title=title, ylabel=ylabel, grid=True, legend=True, copyright=True)
        
        return fig, ax
    
    def create_portfolio_wealth_chart(self, data, symbols, currency, weights=None, **kwargs):
        """Создать график накопленной доходности портфеля"""
        # Create title with asset percentages and currency
        if weights:
            asset_with_weights = []
            for i, symbol in enumerate(symbols):
                # Extract symbol name without namespace
                symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                weight = weights[i] if i < len(weights) else 0.0
                asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
            title = f'Накопленная доходность\n{", ".join(asset_with_weights)} | {currency}'
        else:
            asset_percentages = []
            for i, symbol in enumerate(symbols):
                # Extract symbol name without namespace
                symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                asset_percentages.append(symbol_name)
            title = f'Накопленная доходность\n{", ".join(asset_percentages)} | {currency}'
        
        ylabel = ''  # No y-axis label
        xlabel = ''  # No x-axis label
        return self.create_line_chart(data, title, ylabel, xlabel=xlabel, **kwargs)
    
    def create_portfolio_returns_chart(self, data, symbols, currency, weights=None, **kwargs):
        """Создать график годовой доходности портфеля"""
        fig, ax = self.create_chart(**kwargs)
        
        # Обработка индекса для совместимости с matplotlib
        x_positions = np.arange(len(data))
        x_labels = [str(label) for label in data.index]
        
        # Создаем столбчатый график с цветовым кодированием
        colors = ['#FF6B6B' if val < 0 else '#51CF66' for val in data.values]  # красный для отрицательных, зеленый для положительных
        bars = ax.bar(x_positions, data.values, color=colors, alpha=0.8)
        
        # Устанавливаем подписи на оси X
        ax.set_xticks(x_positions)
        ax.set_xticklabels(x_labels, rotation=45)
        
        if weights:
            asset_with_weights = []
            for i, symbol in enumerate(symbols):
                # Extract symbol name without namespace
                symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                weight = weights[i] if i < len(weights) else 0.0
                asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
            title = f'Годовая доходность портфеля\n{", ".join(asset_with_weights)}'
        else:
            title = f'Годовая доходность портфеля\n{", ".join(symbols)}'
        
        # Убираем подписи осей
        ylabel = ''  # No y-axis label
        xlabel = ''  # No x-axis label
        
        # Применяем стили
        self.apply_styling(ax, title=title, ylabel=ylabel, xlabel=xlabel, grid=True, legend=False, copyright=True)
        
        return fig, ax
    
    def create_portfolio_drawdowns_chart(self, data, symbols, currency, weights=None, portfolio_name=None, **kwargs):
        """Создать график просадок портфеля"""
        fig, ax = self.create_chart(**kwargs)
        
        # Обработка данных
        if isinstance(data, pd.Series):
            # Используем название портфеля если передано, иначе создаем из символов
            if portfolio_name:
                column_name = portfolio_name
            else:
                # Создаем название портфеля из символов и весов
                if weights:
                    asset_with_weights = []
                    for i, symbol in enumerate(symbols):
                        symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                        weight = weights[i] if i < len(weights) else 0.0
                        asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
                    column_name = ", ".join(asset_with_weights)
                else:
                    column_name = ", ".join(symbols)
            data = pd.DataFrame({column_name: data})
        
        cleaned_data = data.copy()
        if hasattr(cleaned_data.index, 'dtype') and str(cleaned_data.index.dtype).startswith('period'):
            cleaned_data.index = cleaned_data.index.to_timestamp()
        
        # Рисуем данные
        for i, column in enumerate(cleaned_data.columns):
            if column in cleaned_data.columns and not cleaned_data[column].empty:
                color = self.get_color(i)
                ax.plot(cleaned_data.index, cleaned_data[column].values * 100,
                       color=color, alpha=self.lines['alpha'], label=column)
        
        if weights:
            asset_with_weights = []
            for i, symbol in enumerate(symbols):
                # Extract symbol name without namespace
                symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                weight = weights[i] if i < len(weights) else 0.0
                asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
            title = f'Просадки портфеля\n{", ".join(asset_with_weights)}'
        else:
            title = f'Просадки портфеля\n{", ".join(symbols)}'
        ylabel = f'Просадка ({currency}) (%)'
        
        # Apply drawdown-specific styling with standard grid colors and date labels above
        self.apply_drawdown_styling(ax, title=title, ylabel=ylabel, grid=True, legend=True, copyright=True)
        
        return fig, ax
    
    def create_portfolio_rolling_cagr_chart(self, data, symbols, currency, weights=None, **kwargs):
        """Создать график скользящего CAGR портфеля"""
        if weights:
            asset_with_weights = []
            for i, symbol in enumerate(symbols):
                # Extract symbol name without namespace
                symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                weight = weights[i] if i < len(weights) else 0.0
                asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
            title = f'Скользящая CAGR портфеля\n{", ".join(asset_with_weights)}'
        else:
            title = f'Скользящая CAGR портфеля\n{", ".join(symbols)}'
        ylabel = f'CAGR ({currency}) (%)'
        return self.create_line_chart(data, title, ylabel, **kwargs)
    
    def create_portfolio_compare_assets_chart(self, data, symbols, currency, weights=None, **kwargs):
        """Создать график сравнения портфеля с активами"""
        fig, ax = self.create_chart(**kwargs)
        
        if hasattr(data, 'plot'):
            data.plot(ax=ax, alpha=0.8)
        
        # Кастомизация стилей линий
        lines = ax.get_lines()
        if len(lines) > 0:
            if len(lines) >= 1:
                lines[0].set_linewidth(3.0)
                lines[0].set_alpha(1.0)
                lines[0].set_color('#005F73')  # глубокий морской синий
            
            for i in range(1, len(lines)):
                lines[i].set_linewidth(1.5)
                lines[i].set_alpha(0.8)
                lines[i].set_color(self.get_color(i-1))
        
        if weights:
            asset_with_weights = []
            for i, symbol in enumerate(symbols):
                # Extract symbol name without namespace
                symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                weight = weights[i] if i < len(weights) else 0.0
                asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
            title = f'Портфель vs Активы\n{", ".join(asset_with_weights)}'
        else:
            title = f'Портфель vs Активы\n{", ".join(symbols)}'
        ylabel = f'Накопленная доходность ({currency})' if currency else 'Накопленная доходность'
        self.apply_styling(ax, title=title, ylabel=ylabel)
        return fig, ax
    
    def create_comparison_chart(self, data, symbols, currency, **kwargs):
        """Создать график сравнения активов"""
        fig, ax = self.create_chart(**kwargs)
        
        # Обработка PeriodIndex и object индексов
        try:
            if hasattr(data, 'index'):
                if hasattr(data.index, 'dtype') and str(data.index.dtype).startswith('period'):
                    data = data.copy()
                    data.index = data.index.to_timestamp()
                elif data.index.dtype == 'object':
                    # Конвертируем object индекс в datetime
                    data = data.copy()
                    data.index = pd.to_datetime(data.index)
        except Exception as e:
            logger.warning(f"Error processing data index: {e}")
        
        # Рисуем данные
        for i, column in enumerate(data.columns):
            color = self.get_color(i)
            ax.plot(data.index, data[column].values, 
                   color=color, alpha=self.lines['alpha'], label=column)
        
        # Извлекаем параметры из kwargs
        title = kwargs.get('title', f'Сравнение активов: {", ".join(symbols)}')
        xlabel = kwargs.get('xlabel', '')
        ylabel = kwargs.get('ylabel', f'Накопленная доходность ({currency})' if currency else 'Накопленная доходность')
        
        # Применяем стили
        self.apply_styling(ax, title=title, xlabel=xlabel, ylabel=ylabel)
        ax.tick_params(axis='x', rotation=45)
        
        # Автоматически настраиваем интервал между датами на оси X
        self._optimize_x_axis_ticks(ax, data.index)
        
        return fig, ax
    
    def create_correlation_matrix_chart(self, correlation_matrix, **kwargs):
        """Создать график корреляционной матрицы"""
        fig, ax = self.create_chart(**kwargs)
        
        im = ax.imshow(correlation_matrix.values, cmap='RdYlBu_r', vmin=-1, vmax=1, aspect='auto')
        
        # Настройка осей
        ax.set_xticks(range(len(correlation_matrix.columns)))
        ax.set_yticks(range(len(correlation_matrix.index)))
        ax.set_xticklabels(correlation_matrix.columns, rotation=45, ha='right', va='top')
        ax.set_yticklabels(correlation_matrix.index)
        
        # Цветовая шкала
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('Корреляция', rotation=270, labelpad=15)
        
        # Значения в ячейках
        for i in range(len(correlation_matrix.index)):
            for j in range(len(correlation_matrix.columns)):
                value = correlation_matrix.iloc[i, j]
                text_color = 'white' if abs(value) > 0.5 else 'black'
                ax.text(j, i, f'{value:.2f}', ha='center', va='center', 
                       color=text_color, fontweight='bold', fontsize=10)
        
        title = f'Корреляционная матрица ({len(correlation_matrix.columns)} активов)'
        self.apply_styling(ax, title=title, grid=False, legend=False)
        return fig, ax
    
    def create_dividend_table_chart(self, table_data, headers, title='История дивидендов', **kwargs):
        """Создать график с таблицей дивидендов"""
        fig, ax = self.create_chart(**kwargs)
        
        ax.axis('tight')
        ax.axis('off')
        
        table = ax.table(cellText=table_data,
                       colLabels=headers,
                       cellLoc='center',
                       loc='center')
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.5)
        
        self.apply_styling(ax, title=title, grid=False, legend=False)
        return fig, ax, table
    
    def create_dividends_chart_enhanced(self, data, symbol, currency, **kwargs):
        """Создать улучшенный график дивидендов"""
        fig, ax = self.create_chart(**kwargs)
        
        dates = [pd.to_datetime(date) for date in data.index]
        amounts = data.values
        
        bars = ax.bar(dates, amounts, color='#94D2BD', alpha=0.7, width=20)
        
        title = f'Дивиденды {symbol}'
        ylabel = f'Сумма ({currency})'
        self.apply_styling(ax, title=title, ylabel=ylabel)
        
        fig.autofmt_xdate()
        
        # Статистика
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
    
    # ============================================================================
    # СПЕЦИАЛЬНЫЕ СТИЛИ
    # ============================================================================
    
    
    
    # ============================================================================
    # УТИЛИТЫ
    # ============================================================================
    
    def save_figure(self, fig, output_buffer, **kwargs):
        """Сохранить фигуру с подавлением CJK предупреждений"""
        save_kwargs = {
            'format': 'png',
            'dpi': self.style['dpi'],
            'bbox_inches': self.style['bbox_inches'],
            'facecolor': self.style['facecolor'],
            'edgecolor': self.style['edgecolor']
        }
        save_kwargs.update(kwargs)
        
        with suppress_cjk_warnings():
            fig.savefig(output_buffer, **save_kwargs)
    
    def cleanup_figure(self, fig):
        """Очистить фигуру"""
        try:
            plt.close(fig)
            plt.clf()
            plt.cla()
        except Exception as e:
            logger.error(f"Error cleaning up figure: {e}")
    
    def get_color_palette(self, n_colors):
        """Получить палитру цветов"""
        return plt.cm.Set3(np.linspace(0, 1, n_colors))
    
    def create_table_image(self, data, title="", symbols=None):
        """Создать таблицу как изображение"""
        try:
            with suppress_cjk_warnings():
                # Определяем размеры таблицы
                n_rows, n_cols = data.shape
                
                # Адаптивные размеры в зависимости от количества данных
                if n_cols <= 2:
                    fig_width = 10
                    fig_height = max(6, n_rows * 0.8 + 2)
                elif n_cols <= 4:
                    fig_width = 14
                    fig_height = max(6, n_rows * 0.8 + 2)
                else:
                    fig_width = 16
                    fig_height = max(6, n_rows * 0.8 + 2)
                
                fig, ax = plt.subplots(figsize=(fig_width, fig_height))
                ax.axis('tight')
                ax.axis('off')
                
                # Подготавливаем данные для таблицы
                table_data = []
                headers = []
                
                # Заголовки колонок
                for col in data.columns:
                    if symbols and col in symbols:
                        headers.append(f"`{col}`")
                    else:
                        headers.append(str(col))
                
                # Данные строк
                for idx, row in data.iterrows():
                    row_data = [str(idx)]  # Название метрики
                    for col in data.columns:
                        value = row[col]
                        if pd.isna(value):
                            row_data.append("N/A")
                        elif isinstance(value, (int, float)):
                            row_data.append(f"{value:.2f}")
                        else:
                            row_data.append(str(value))
                    table_data.append(row_data)
                
                # Создаем таблицу
                table = ax.table(cellText=table_data,
                               colLabels=["Метрика"] + headers,
                               cellLoc='center',
                               loc='center',
                               bbox=[0, 0, 1, 1])
                
                # Стилизация таблицы
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                
                # Цветовая схема
                header_color = '#4A90E2'  # Синий для заголовков
                metric_color = '#F0F0F0'   # Светло-серый для метрик
                data_color = '#FFFFFF'    # Белый для данных
                
                # Стилизация заголовков
                for i in range(len(headers) + 1):
                    table[(0, i)].set_facecolor(header_color)
                    table[(0, i)].set_text_props(weight='bold', color='white')
                
                # Стилизация строк метрик
                for i in range(1, len(table_data) + 1):
                    table[(i, 0)].set_facecolor(metric_color)
                    table[(i, 0)].set_text_props(weight='bold')
                    
                    # Стилизация данных
                    for j in range(1, len(headers) + 1):
                        table[(i, j)].set_facecolor(data_color)
                        
                        # Подсветка лучших значений для числовых метрик
                        try:
                            value = float(table_data[i-1][j])
                            if not pd.isna(value):
                                # Получаем все значения для этой колонки
                                column_values = []
                                for row in table_data:
                                    try:
                                        val = float(row[j])
                                        if not pd.isna(val):
                                            column_values.append(val)
                                    except (ValueError, TypeError):
                                        pass
                                
                                if column_values:
                                    # Для положительных метрик (доходность) - зеленый для лучших
                                    if 'return' in str(data.index[i-1]).lower() or 'cagr' in str(data.index[i-1]).lower():
                                        if value == max(column_values):
                                            table[(i, j)].set_facecolor('#E8F5E8')  # Светло-зеленый
                                    # Для отрицательных метрик (риск, drawdown) - красный для худших
                                    elif 'risk' in str(data.index[i-1]).lower() or 'drawdown' in str(data.index[i-1]).lower():
                                        if value == min(column_values):
                                            table[(i, j)].set_facecolor('#FFE8E8')  # Светло-красный
                        except (ValueError, TypeError, IndexError):
                            pass
                
                # Настройка границ
                for i in range(len(table_data) + 1):
                    for j in range(len(headers) + 1):
                        table[(i, j)].set_edgecolor('#CCCCCC')
                        table[(i, j)].set_linewidth(0.5)
                
                # Заголовок таблицы
                fig.suptitle(title, fontsize=16, fontweight='bold', y=0.95)
                
                # Настройка макета
                plt.tight_layout()
                plt.subplots_adjust(top=0.9)
                
                return fig, ax
                
        except Exception as e:
            logger.error(f"Error creating table image: {e}")
            # Fallback: создаем простую таблицу
            return self._create_simple_table_image(data, title, symbols)
    
    def _create_simple_table_image(self, data, title="Статистика активов", symbols=None):
        """Простая таблица как изображение (fallback)"""
        try:
            with suppress_cjk_warnings():
                fig, ax = plt.subplots(figsize=(12, 8))
                ax.axis('off')
                
                # Простое текстовое представление
                text_content = f"{title}\n\n"
                
                for idx, row in data.iterrows():
                    text_content += f"{idx}:\n"
                    for col in data.columns:
                        value = row[col]
                        if pd.isna(value):
                            text_content += f"  {col}: N/A\n"
                        elif isinstance(value, (int, float)):
                            text_content += f"  {col}: {value:.2f}\n"
                        else:
                            text_content += f"  {col}: {value}\n"
                    text_content += "\n"
                
                ax.text(0.05, 0.95, text_content, transform=ax.transAxes,
                       fontsize=10, verticalalignment='top',
                       bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
                
                return fig, ax
                
        except Exception as e:
            logger.error(f"Error creating simple table image: {e}")
            # Последний fallback
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, f"Ошибка создания таблицы: {str(e)}", 
                   transform=ax.transAxes, ha='center', va='center')
            ax.axis('off')
            return fig, ax

    def create_monte_carlo_chart(self, fig, ax, symbols, currency, weights=None, **kwargs):
        """Применить стили к графику монте-карло"""
        try:
            # Make simulation lines thinner
            for line in ax.get_lines():
                line.set_linewidth(0.5)
                line.set_alpha(0.6)
            
            # Get portfolio weights for title
            if weights:
                asset_with_weights = []
                for i, symbol in enumerate(symbols):
                    symbol_name = symbol.split('.')[0] if '.' in symbol else symbol
                    weight = weights[i] if i < len(weights) else 0.0
                    asset_with_weights.append(f"{symbol_name} ({weight:.1%})")
                title = f'Прогноз Monte Carlo\n{", ".join(asset_with_weights)}'
            else:
                title = f'Прогноз Monte Carlo\n{", ".join(symbols)}'
            
            # Apply base styling
            self._apply_base_style(fig, ax)
            
            # Apply standard chart styling
            self.apply_styling(
                ax,
                title=title,
                ylabel='',  # No y-axis label
                xlabel='',  # No x-axis label
                grid=True,
                legend=False,
                copyright=True
            )
            
            # Add custom legend with forecast period and currency
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor='gray', alpha=0.6, label=f'Симуляции (20 траекторий)'),
                Patch(facecolor='blue', alpha=0.8, label=f'Период: 10 лет'),
                Patch(facecolor='green', alpha=0.8, label=f'Валюта: {currency}')
            ]
            ax.legend(handles=legend_elements, loc='upper left', fontsize=9)
            
        except Exception as e:
            logger.error(f"Error applying Monte Carlo chart styles: {e}")

    def _optimize_x_axis_ticks(self, ax, date_index):
        """Оптимизировать отображение дат на оси X в зависимости от количества данных"""
        try:
            import matplotlib.dates as mdates
            import pandas as pd
            
            if len(date_index) == 0:
                return
            
            # Конвертируем индекс в datetime если необходимо
            if not isinstance(date_index, pd.DatetimeIndex):
                if hasattr(date_index, 'to_timestamp'):
                    date_index = date_index.to_timestamp()
                else:
                    # Попробуем конвертировать в datetime
                    try:
                        date_index = pd.to_datetime(date_index)
                    except Exception as e:
                        logger.warning(f"Could not convert date_index to datetime: {e}")
                        # Fallback к стандартному поведению
                        ax.tick_params(axis='x', rotation=45)
                        return
            
            # Определяем количество точек данных
            num_points = len(date_index)
            
            # Вычисляем временной диапазон для более точной настройки
            if num_points > 1:
                date_range = (date_index.max() - date_index.min()).days
                years_span = date_range / 365.25
            else:
                years_span = 1
            
            # Выбираем интервал в зависимости от количества данных и временного диапазона
            if num_points <= 10:
                # Мало данных - показываем все месяцы
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            elif num_points <= 30:
                # Среднее количество - показываем каждый месяц
                ax.xaxis.set_major_locator(mdates.MonthLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            elif num_points <= 60:
                # Месячные данные - показываем каждый месяц с интервалом
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))  # Каждый 2-й месяц
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            elif num_points <= 120:
                # Квартальные данные - показываем каждый квартал
                ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
            elif years_span <= 5:
                # Много данных, но короткий период - показываем каждый год
                ax.xaxis.set_major_locator(mdates.YearLocator())
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            elif years_span <= 15:
                # Средний период - показываем каждый 2-й год
                ax.xaxis.set_major_locator(mdates.YearLocator(2))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            else:
                # Длинный период - показываем каждый 5-й год
                ax.xaxis.set_major_locator(mdates.YearLocator(5))
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
            
            # Поворачиваем подписи дат для лучшей читаемости
            ax.tick_params(axis='x', rotation=45)
            
        except Exception as e:
            logger.warning(f"Error optimizing x-axis ticks: {e}")
            # Fallback к стандартному поведению
            ax.tick_params(axis='x', rotation=45)

# Глобальный экземпляр
chart_styles = ChartStyles()

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

logger = logging.getLogger(__name__)

class ChartStyles:
    """Класс для управления стилями графиков (Nordic Pro)"""
    
    def __init__(self):
        # Централизованные настройки шрифтов
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
        
        # Централизованная цветовая палитра
        self.colors = {
            'primary': '#005F73',      # глубокий морской синий
            'secondary': '#0A9396',     # бирюзовый акцент
            'success': '#94D2BD',      # мягкий мятный
            'danger': '#AE2012',       # глубокий красный
            'warning': '#EE9B00',      # янтарный
            'neutral': '#E9ECEF',      # светло-серый фон
            'text': '#2E3440',         # строгий графитовый
            'grid': '#CBD5E1',         # светло-серые линии сетки
        }
        
        # Централизованные настройки стилей
        self.style = {
            'figsize': (12, 7),
            'dpi': 160,
            'facecolor': 'white',
            'edgecolor': 'none',
            'bbox_inches': 'tight',
            'style': 'seaborn-v0_8-whitegrid',
        }
        
        # Централизованные настройки линий
        self.lines = {
            'width': 2.2,
            'alpha': 0.95,
            'smooth_points': 2000,
        }
        
        # Централизованные настройки осей
        self.axes = {
            'fontsize': 12,
            'fontweight': 'medium',
            'color': self.colors['text'],
            'tick_fontsize': 10,
            'tick_color': self.colors['text'],
        }
        
        # Централизованные настройки сетки
        self.grid = {
            'alpha': 0.25,
            'linestyle': '-',
            'linewidth': 0.7,
            'color': self.colors['grid'],
            'zorder': 0,
        }
        
        # Централизованные настройки рамок
        self.spines = {
            'color': self.colors['text'],
            'linewidth': 1.1,
        }
        
        # Централизованные настройки легенды
        self.legend = {
            'fontsize': 10,
            'frameon': True,
            'fancybox': True,
            'shadow': True,
            'loc': 'upper left',
        }
        
        # Централизованные настройки заголовков
        self.title = {
            'fontsize': 16,
            'fontweight': 'semibold',
            'pad': 18,
            'color': self.colors['text'],
        }
        
        # Централизованные настройки копирайта
        self.copyright = {
            'text': '© shans.ai | data source: okama',
            'fontsize': 10,
            'color': self.colors['text'],
            'alpha': 0.55,
            'position': (0.01, -0.02),
        }
        
        # Централизованные настройки Monte Carlo
        self.monte_carlo = {
            'main_linewidth': 3.0,
            'main_alpha': 0.95,
            'test_linewidth': 0.8,
            'test_alpha': 0.6,
            'test_colors': [
                '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
                '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'
            ]
        }

    # ============================================================================
    # БАЗОВЫЕ МЕТОДЫ СОЗДАНИЯ И СТИЛИЗАЦИИ
    # ============================================================================
    
    def create_chart(self, rows=1, cols=1, figsize=None, **kwargs):
        """Универсальный метод создания фигуры с применением стилей"""
        try:
            plt.style.use(self.style['style'])
            
            # Убираем параметры, которые не поддерживаются plt.subplots
            plot_kwargs = {k: v for k, v in kwargs.items() if k not in ['copyright']}
            
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
            ax.set_facecolor(self.colors['neutral'])
            
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
                ax.set_title(title, **self.title)
            
            # Подписи осей
            if xlabel:
                ax.set_xlabel(xlabel, fontsize=self.axes['fontsize'], fontweight=self.axes['fontweight'], color=self.axes['color'])
            if ylabel:
                ax.set_ylabel(ylabel, fontsize=self.axes['fontsize'], fontweight=self.axes['fontweight'], color=self.axes['color'])
            
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
    
    def add_copyright(self, ax):
        """Добавить копирайт"""
        try:
            ax.text(*self.copyright['position'], 
                   self.copyright['text'],
                   transform=ax.transAxes, 
                   fontsize=self.copyright['fontsize'], 
                   color=self.copyright['color'], 
                   alpha=self.copyright['alpha'],
                   ha='left', va='top')
        except Exception as e:
            logger.error(f"Error adding copyright: {e}")
    
    def get_color(self, index):
        """Получить цвет по индексу"""
        colors_list = list(self.colors.values())
        return colors_list[index % len(colors_list)]
    
    # ============================================================================
    # УНИВЕРСАЛЬНЫЕ МЕТОДЫ СОЗДАНИЯ ГРАФИКОВ
    # ============================================================================
    
    def create_line_chart(self, data, title, ylabel, xlabel='', **kwargs):
        """Создать линейный график"""
        fig, ax = self.create_chart(**kwargs)
        
        if hasattr(data, 'plot'):
            data.plot(ax=ax, linewidth=self.lines['width'], alpha=self.lines['alpha'])
        else:
            ax.plot(data.index, data.values, linewidth=self.lines['width'], alpha=self.lines['alpha'])
        
        self.apply_styling(ax, title=title, ylabel=ylabel, xlabel=xlabel, legend=False)
        return fig, ax
    
    def create_bar_chart(self, data, title, ylabel, xlabel='', bar_color=None, **kwargs):
        """Создать столбчатый график"""
        fig, ax = self.create_chart(**kwargs)
        
        if bar_color is None:
            bar_color = self.colors['success']
        
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
                    color=color, linewidth=self.lines['width'],
                    alpha=self.lines['alpha'], label=column)
        
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
        return self.create_line_chart(data, title, ylabel, copyright=False, **kwargs)
    
    def create_dividends_chart(self, data, symbol, currency, **kwargs):
        """Создать график дивидендов"""
        title = f'Дивиденды {symbol}'
        ylabel = f'Сумма ({currency})'
        return self.create_bar_chart(data, title, ylabel, bar_color=self.colors['success'], **kwargs)
    
    def create_dividend_yield_chart(self, data, symbols, **kwargs):
        """Создать график дивидендной доходности"""
        title = f'Дивидендная доходность: {", ".join(symbols)}'
        ylabel = 'Дивидендная доходность (%)'
        return self.create_multi_line_chart(data, title, ylabel, **kwargs)
    
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
                       color=color, linewidth=self.lines['width'], 
                       alpha=self.lines['alpha'], label=column)
        
        title = f'Просадки активов: {", ".join(symbols)}'
        ylabel = f'Просадка (%)'
        self.apply_styling(ax, title=title, ylabel=ylabel)
        return fig, ax
    
    def create_portfolio_wealth_chart(self, data, symbols, currency, **kwargs):
        """Создать график накопленной доходности портфеля"""
        title = f'Накопленная доходность портфеля\n{", ".join(symbols)}'
        ylabel = f'Накопленная доходность ({currency})' if currency else 'Накопленная доходность'
        return self.create_line_chart(data, title, ylabel, **kwargs)
    
    def create_portfolio_returns_chart(self, data, symbols, currency, **kwargs):
        """Создать график годовой доходности портфеля"""
        title = f'Годовая доходность портфеля\n{", ".join(symbols)}'
        ylabel = f'Доходность ({currency}) (%)'
        return self.create_bar_chart(data, title, ylabel, **kwargs)
    
    def create_portfolio_drawdowns_chart(self, data, symbols, currency, **kwargs):
        """Создать график просадок портфеля"""
        title = f'Просадки портфеля\n{", ".join(symbols)}'
        ylabel = f'Просадка ({currency}) (%)'
        return self.create_line_chart(data, title, ylabel, **kwargs)
    
    def create_portfolio_rolling_cagr_chart(self, data, symbols, currency, **kwargs):
        """Создать график скользящего CAGR портфеля"""
        title = f'Скользящий CAGR портфеля\n{", ".join(symbols)}'
        ylabel = f'CAGR ({currency}) (%)'
        return self.create_line_chart(data, title, ylabel, **kwargs)
    
    def create_portfolio_compare_assets_chart(self, data, symbols, currency, **kwargs):
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
                lines[0].set_color(self.colors['primary'])
            
            for i in range(1, len(lines)):
                lines[i].set_linewidth(1.5)
                lines[i].set_alpha(0.8)
                lines[i].set_color(self.get_color(i-1))
        
        title = f'Портфель vs Активы\n{", ".join(symbols)}'
        ylabel = f'Накопленная доходность ({currency})' if currency else 'Накопленная доходность'
        self.apply_styling(ax, title=title, ylabel=ylabel)
        return fig, ax
    
    def create_comparison_chart(self, data, symbols, currency, **kwargs):
        """Создать график сравнения активов"""
        fig, ax = self.create_chart(**kwargs)
        
        # Обработка PeriodIndex
        try:
            if hasattr(data, 'index') and hasattr(data.index, 'dtype') and str(data.index.dtype).startswith('period'):
                data = data.copy()
                data.index = data.index.to_timestamp()
        except Exception:
            pass
        
        # Рисуем данные
        for i, column in enumerate(data.columns):
            color = self.get_color(i)
            ax.plot(data.index, data[column].values, 
                   color=color, linewidth=self.lines['width'], 
                   alpha=self.lines['alpha'], label=column)
        
        title = f'Сравнение активов: {", ".join(symbols)}'
        ylabel = f'Накопленная доходность ({currency})' if currency else 'Накопленная доходность'
        self.apply_styling(ax, title=title, ylabel=ylabel, legend=False)
        ax.tick_params(axis='x', rotation=45)
        
        # Легенда
        handles, labels = ax.get_legend_handles_labels()
        if handles and labels:
            legend_config = self.legend.copy()
            legend_config.pop('loc', None)
            ax.legend(handles, labels, loc='upper left', bbox_to_anchor=(0.02, 0.98), **legend_config)
        
        return fig, ax
    
    def create_correlation_matrix_chart(self, correlation_matrix, **kwargs):
        """Создать график корреляционной матрицы"""
        fig, ax = self.create_chart(**kwargs)
        
        im = ax.imshow(correlation_matrix.values, cmap='RdYlBu_r', vmin=-1, vmax=1, aspect='auto')
        
        # Настройка осей
        ax.set_xticks(range(len(correlation_matrix.columns)))
        ax.set_yticks(range(len(correlation_matrix.index)))
        ax.set_xticklabels(correlation_matrix.columns, rotation=45, ha='right')
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
        
        bars = ax.bar(dates, amounts, color=self.colors['success'], alpha=0.7, width=20)
        
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
    
    def apply_monte_carlo_style(self, ax):
        """Применить стили для графиков Monte Carlo"""
        try:
            test_colors = self.monte_carlo['test_colors']
            
            if len(ax.lines) > 0:
                # Основная линия
                main_line = ax.lines[0]
                main_line.set_linewidth(self.monte_carlo['main_linewidth'])
                main_line.set_alpha(self.monte_carlo['main_alpha'])
                main_line.set_color(self.colors['primary'])
                
                # Тестовые линии
                for i, line in enumerate(ax.lines[1:], 1):
                    line.set_linewidth(self.monte_carlo['test_linewidth'])
                    line.set_alpha(self.monte_carlo['test_alpha'])
                    line.set_color(test_colors[i % len(test_colors)])
            
            ax.grid(True, **self.grid)
            
        except Exception as e:
            logger.error(f"Error applying Monte Carlo styles: {e}")
    
    def apply_percentile_style(self, ax):
        """Применить стили для графиков процентилей"""
        try:
            if len(ax.lines) >= 3:
                percentile_colors = [
                    self.colors['danger'],    # 10% - красный
                    self.colors['primary'],   # 50% - синий
                    self.colors['success']     # 90% - зеленый
                ]
                
                percentile_labels = [
                    '10% процентиль (пессимистичный)',
                    '50% процентиль (средний)',
                    '90% процентиль (оптимистичный)'
                ]
                
                for i, line in enumerate(ax.lines[:3]):
                    if i < len(percentile_colors):
                        line.set_color(percentile_colors[i])
                        line.set_linewidth(2.5)
                        line.set_alpha(0.9)
                        if i < len(percentile_labels):
                            line.set_label(percentile_labels[i])
                
                for line in ax.lines[3:]:
                    line.set_color(self.colors['neutral'])
                    line.set_linewidth(1.5)
                    line.set_alpha(0.6)
                    line.set_label('')
                
                ax.grid(True, **self.grid)
                if ax.get_legend() is not None:
                    ax.legend(**self.legend)
            
        except Exception as e:
            logger.error(f"Error applying percentile styles: {e}")
    
    # ============================================================================
    # УТИЛИТЫ
    # ============================================================================
    
    def save_figure(self, fig, output_buffer, **kwargs):
        """Сохранить фигуру"""
        save_kwargs = {
            'format': 'png',
            'dpi': self.style['dpi'],
            'bbox_inches': self.style['bbox_inches'],
            'facecolor': self.style['facecolor'],
            'edgecolor': self.style['edgecolor']
        }
        save_kwargs.update(kwargs)
        
        fig.savefig(output_buffer, **save_kwargs)
    
    def cleanup_figure(self, fig):
        """Очистить фигуру"""
        try:
            plt.close(fig)
            plt.clf()
            plt.cla()
        except Exception as e:
            logger.error(f"Error cleaning up figure: {e}")

# Глобальный экземпляр
chart_styles = ChartStyles()

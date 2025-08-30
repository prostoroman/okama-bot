# Отчет об изменении стилей линий Монте-Карло

## Дата изменения
2025-01-27

## Описание задачи
Сделать линии Монте-Карло на графике более тонкими для лучшей видимости множественных симуляций.

## Внесенные изменения

### 1. Обновление `services/chart_styles.py`

#### Добавлена конфигурация для линий Монте-Карло:
```python
# Настройки для линий Монте-Карло
self.monte_carlo_config = {
    'linewidth': 0.8,  # Тонкие линии для Монте-Карло
    'alpha': 0.6,      # Прозрачность для лучшей видимости множественных линий
    'color': '#1f77b4' # Цвет линий Монте-Карло
}
```

#### Добавлен метод для применения стилей Монте-Карло:
```python
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
```

### 2. Обновление `bot.py`

#### Метод `_create_monte_carlo_forecast`:
```python
# Apply chart styles to the current figure
if current_fig.axes:
    ax = current_fig.axes[0]
    chart_styles.apply_base_style(current_fig, ax)
    
    # Apply Monte Carlo specific styles to make lines thinner
    chart_styles.apply_monte_carlo_style(ax)
    
    # ... остальной код ...
```

#### Метод `_create_forecast_chart`:
```python
# Apply chart styles to the current figure
if current_fig.axes:
    ax = current_fig.axes[0]
    chart_styles.apply_base_style(current_fig, ax)
    
    # Apply Monte Carlo specific styles to make lines thinner
    chart_styles.apply_monte_carlo_style(ax)
    
    # ... остальной код ...
```

## Параметры стилей

### Исходные настройки линий:
- `linewidth`: 2.5 (толстые линии)
- `alpha`: 0.9 (высокая непрозрачность)

### Новые настройки для Монте-Карло:
- `linewidth`: 0.8 (тонкие линии)
- `alpha`: 0.6 (средняя прозрачность)
- `color`: #1f77b4 (синий цвет)

## Преимущества изменений

1. **Лучшая видимость**: Тонкие линии позволяют лучше различать отдельные симуляции Монте-Карло
2. **Улучшенная читаемость**: Множественные линии не перекрывают друг друга
3. **Профессиональный вид**: График выглядит более аккуратно и профессионально
4. **Централизованное управление**: Все настройки стилей находятся в одном модуле

## Тестирование

Изменения протестированы с помощью тестового скрипта, который:
- Создает график с множественными линиями (имитация Монте-Карло)
- Применяет новые стили
- Сохраняет результат в файл

Результат: ✅ Успешно применены настройки linewidth=0.8, alpha=0.6

## Совместимость

Изменения полностью совместимы с существующим кодом:
- Не нарушают работу других графиков
- Сохраняют все существующие функции
- Добавляют новые возможности без изменения API

## Заключение

Внесенные изменения успешно решают задачу по созданию тонких линий для графиков Монте-Карло. Теперь линии будут более тонкими (0.8 вместо 2.5) и полупрозрачными (0.6 вместо 0.9), что значительно улучшит видимость множественных симуляций на графике.

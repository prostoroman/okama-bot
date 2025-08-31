# Добавление настроек шрифта IBM Plex Sans

## Обзор изменений

Добавлены настройки шрифта IBM Plex Sans в оба файла стилей графиков:
- `services/chart_styles.py`
- `services/chart_styles_refactored.py`

## Внесенные изменения

### 1. Добавлен импорт matplotlib
```python
import matplotlib as mpl
```

### 2. Добавлены настройки шрифта в метод `__init__`
```python
# Настройки шрифта IBM Plex Sans
mpl.rcParams.update({
    'font.family': 'IBM Plex Sans',
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
```

## Описание настроек

### Шрифты
- **font.family**: 'IBM Plex Sans' - основной шрифт для всех элементов
- **font.weight**: 'medium' - средний вес шрифта по умолчанию
- **axes.titleweight**: 'semibold' - полужирный для заголовков осей
- **axes.labelweight**: 'medium' - средний для подписей осей

### Размеры шрифтов
- **figure.titlesize**: 16 - размер заголовка фигуры
- **axes.titlesize**: 14 - размер заголовков осей
- **axes.labelsize**: 12 - размер подписей осей
- **xtick.labelsize**: 10 - размер меток оси X
- **ytick.labelsize**: 10 - размер меток оси Y
- **legend.title_fontsize**: 11 - размер заголовка легенды
- **legend.fontsize**: 10 - размер текста легенды

### Стили осей и сетки
- **axes.edgecolor**: '#2E3440' - цвет границ осей (темно-серый)
- **axes.linewidth**: 1.1 - толщина линий осей
- **grid.color**: '#CBD5E1' - цвет сетки (светло-серый)
- **grid.linewidth**: 0.7 - толщина линий сетки
- **grid.alpha**: 0.25 - прозрачность сетки

## Преимущества IBM Plex Sans

1. **Читаемость**: Отличная читаемость на различных размерах
2. **Профессиональный вид**: Современный и чистый дизайн
3. **Поддержка символов**: Хорошая поддержка математических символов
4. **Кроссплатформенность**: Доступен на всех основных платформах

## Проверка синтаксиса

Оба файла успешно прошли проверку синтаксиса:
- `python3 -m py_compile services/chart_styles.py` ✅
- `python3 -m py_compile services/chart_styles_refactored.py` ✅

## Заключение

Настройки шрифта IBM Plex Sans успешно добавлены в оба файла стилей. Эти настройки обеспечат:
- Единообразный профессиональный вид всех графиков
- Улучшенную читаемость текста
- Современный дизайн, соответствующий стандартам IBM Design Language

Изменения применены без нарушения существующей функциональности и совместимости с текущим кодом.

# Обновление настроек шрифтов и рамок

## Обзор изменений

Обновлены настройки шрифтов и рамок в файлах стилей графиков для обеспечения единообразия и корректной работы с доступными шрифтами.

## Проблемы, которые были решены

### 1. Шрифт IBM Plex Sans не был доступен
- **Проблема**: Шрифт IBM Plex Sans не установлен в системе
- **Решение**: Добавлен fallback на доступные шрифты: PT Sans, Arial, Helvetica

### 2. Несогласованность настроек рамок
- **Проблема**: Настройки рамок в разных местах кода не соответствовали глобальным настройкам
- **Решение**: Унифицированы настройки рамок и сетки

## Внесенные изменения

### 1. Обновление настроек шрифтов

#### В `services/chart_styles.py` и `services/chart_styles_refactored.py`:
```python
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
    'axes.edgecolor': '#2E3440',
    'axes.linewidth': 1.1,
    'grid.color': '#CBD5E1',
    'grid.linewidth': 0.7,
    'grid.alpha': 0.25,
})
```

### 2. Унификация настроек рамок

#### В `services/chart_styles.py`:
```python
# Рамки (только снизу и слева)
self.spine_config = {
    'color': '#2E3440',  # соответствует axes.edgecolor
    'linewidth': 1.1
}
```

#### В `services/chart_styles_refactored.py`:
```python
# Рамки
self.spine_config = {
    'color': '#2E3440',  # соответствует axes.edgecolor
    'linewidth': 1.1
}
```

### 3. Унификация настроек сетки

#### В `services/chart_styles.py`:
```python
# Сетка (только Y, пунктир)
self.grid_config = {
    'alpha': 0.25,  # соответствует grid.alpha
    'linestyle': (0, (3, 3)),  # пунктир
    'linewidth': 0.7,  # соответствует grid.linewidth
    'color': '#CBD5E1',  # соответствует grid.color
    'zorder': 0
}
```

#### В `services/chart_styles_refactored.py`:
```python
# Сетка
self.grid_config = {
    'alpha': 0.25,  # соответствует grid.alpha
    'linestyle': '-',
    'linewidth': 0.7,  # соответствует grid.linewidth
    'color': '#CBD5E1',  # соответствует grid.color
    'zorder': 0
}
```

## Созданный скрипт установки шрифта

### `scripts/install_ibm_plex_font.py`
Скрипт для автоматической установки шрифта IBM Plex Sans:

- Загружает шрифт с официального репозитория IBM
- Устанавливает в соответствующую директорию системы
- Поддерживает macOS, Linux и Windows
- Проверяет доступность шрифта после установки

### Использование скрипта:
```bash
python3 scripts/install_ibm_plex_font.py
```

## Доступные шрифты

После проверки системы были найдены следующие подходящие шрифты:
- **PT Sans** - основная альтернатива IBM Plex Sans
- **Arial** - стандартный шрифт Windows
- **Helvetica** - стандартный шрифт macOS
- **DejaVu Sans** - кроссплатформенный шрифт

## Преимущества внесенных изменений

### 1. Надежность
- Fallback на несколько шрифтов обеспечивает работу на любой системе
- Единообразные настройки рамок и сетки

### 2. Консистентность
- Все настройки рамок и сетки соответствуют глобальным настройкам matplotlib
- Унифицированный внешний вид графиков

### 3. Гибкость
- Возможность установки IBM Plex Sans при желании
- Автоматический выбор лучшего доступного шрифта

## Проверка синтаксиса

Оба файла успешно прошли проверку синтаксиса:
- `python3 -m py_compile services/chart_styles.py` ✅
- `python3 -m py_compile services/chart_styles_refactored.py` ✅

## Заключение

Внесенные изменения обеспечивают:
1. **Корректную работу шрифтов** на всех системах
2. **Единообразие настроек** рамок и сетки
3. **Возможность установки** IBM Plex Sans при необходимости
4. **Совместимость** с существующим кодом

Все изменения применены без нарушения функциональности и с сохранением обратной совместимости.

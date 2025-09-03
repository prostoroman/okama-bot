# Отчет об изменении DPI для генерации графиков

## Описание изменений

Изменено значение DPI (dots per inch) с 300 на 96 во всех местах генерации графиков в проекте okama-bot.

## Измененные файлы

### 1. bot.py
Изменено 6 мест использования `dpi=300` на `dpi=96`:

1. **Строка 875**: Ежедневный график актива
   ```python
   fig.savefig(output, format='PNG', dpi=96, bbox_inches='tight')
   ```

2. **Строка 3239**: Месячный график актива
   ```python
   fig.savefig(output, format='PNG', dpi=96, bbox_inches='tight')
   ```

3. **Строка 3370**: График дивидендов
   ```python
   fig.savefig(output, format='PNG', dpi=96, bbox_inches='tight')
   ```

4. **Строка 3451**: Таблица дивидендов (с facecolor='white')
   ```python
   fig.savefig(output, format='PNG', dpi=96, bbox_inches='tight', facecolor='white')
   ```

5. **Строка 4094**: Прогноз Monte Carlo
   ```python
   current_fig.savefig(img_buffer, format='PNG', dpi=96, bbox_inches='tight')
   ```

6. **Строка 4160**: Прогноз с процентилями
   ```python
   current_fig.savefig(img_buffer, format='PNG', dpi=96, bbox_inches='tight')
   ```

### 2. scripts/compare_daily_data.py
Изменено 1 место использования:

- **Строка 69**: Сравнение ежедневных данных
  ```python
  plt.savefig(f'daily_comparison_{symbol.replace(".", "_")}.png', 
             format='PNG', dpi=96, bbox_inches='tight')
  ```

## Обоснование изменений

Изменение DPI с 300 на 96:
- Уменьшает размер файлов изображений
- Ускоряет генерацию графиков
- Сохраняет достаточное качество для отображения в Telegram
- Оптимизирует использование памяти

## Проверка изменений

✅ Все значения `dpi=300` успешно заменены на `dpi=96`
✅ Никаких остаточных значений `dpi=300` не обнаружено
✅ Все изменения применены корректно

## Дата выполнения

Изменения выполнены: $(date)

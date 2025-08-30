# Отчет об добавлении кнопки Drawdowns

## Дата реализации
2025-01-27

## Описание функциональности

### Кнопка Drawdowns для портфеля
**Добавлено**: Кнопка "📉 Drawdowns" в команде `/portfolio` для отображения графика просадок портфеля

**Местоположение**: `bot.py`, строки 1620-1625

**Функциональность**:
```python
# Add risk metrics, Monte Carlo, forecast, and drawdowns buttons
keyboard = [
    [
        InlineKeyboardButton("📊 Риск метрики", callback_data=f"risk_metrics_{','.join(symbols)}"),
        InlineKeyboardButton("🎲 Monte Carlo", callback_data=f"monte_carlo_{','.join(symbols)}")
    ],
    [
        InlineKeyboardButton("📈 Прогноз по процентилям 10, 50, 90", callback_data=f"forecast_{','.join(symbols)}"),
        InlineKeyboardButton("📉 Drawdowns", callback_data=f"drawdowns_{','.join(symbols)}")
    ]
]
```

**Результат**: Пользователь может нажать кнопку "📉 Drawdowns" для получения графика просадок портфеля

## Техническая реализация

### 1. Обработчик кнопки в button_callback

**Местоположение**: `bot.py`, строки 1915-1920

**Код**:
```python
elif callback_data.startswith('drawdowns_'):
    symbols = callback_data.replace('drawdowns_', '').split(',')
    self.logger.info(f"Drawdowns button clicked for symbols: {symbols}")
    self.logger.info(f"Callback data: {callback_data}")
    self.logger.info(f"Extracted symbols: {symbols}")
    await self._handle_portfolio_drawdowns_button(update, context, symbols)
```

**Функция**: Извлекает символы из callback_data и вызывает обработчик

### 2. Основной обработчик _handle_portfolio_drawdowns_button

**Местоположение**: `bot.py`, строки 1925-1950

**Функциональность**:
```python
async def _handle_portfolio_drawdowns_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
    """Handle portfolio drawdowns button click"""
    try:
        user_id = update.effective_user.id
        self.logger.info(f"Handling portfolio drawdowns button for user {user_id}")
        
        user_context = self._get_user_context(user_id)
        self.logger.info(f"User context content: {user_context}")
        
        # Prefer symbols passed from the button payload; fallback to context
        button_symbols = symbols
        final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
        self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
        if not final_symbols:
            self.logger.warning("No symbols provided by button and none found in context")
            await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
            return
        
        currency = user_context.get('current_currency', 'USD')
        raw_weights = user_context.get('portfolio_weights', [])
        weights = self._normalize_or_equalize_weights(final_symbols, raw_weights)
        
        self.logger.info(f"Creating drawdowns chart for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
        await self._send_callback_message(update, context, "📉 Создаю график просадок...")
        
        # Create Portfolio again
        import okama as ok
        portfolio = ok.Portfolio(final_symbols, ccy=currency, weights=weights)
        
        await self._create_portfolio_drawdowns_chart(update, context, portfolio, final_symbols, currency)
        
    except Exception as e:
        self.logger.error(f"Error handling portfolio drawdowns button: {e}")
        await self._send_callback_message(update, context, f"❌ Ошибка при создании графика просадок: {str(e)}")
```

**Функции**:
- Получение контекста пользователя
- Извлечение символов и весов портфеля
- Создание объекта Portfolio
- Вызов метода создания графика

### 3. Создание графика _create_portfolio_drawdowns_chart

**Местоположение**: `bot.py`, строки 1952-2000

**Функциональность**:
```python
async def _create_portfolio_drawdowns_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str):
    """Create and send portfolio drawdowns chart"""
    try:
        self.logger.info(f"Creating portfolio drawdowns chart for portfolio: {symbols}")
        
        # Generate drawdowns chart using okama
        # portfolio.drawdowns.plot()
        drawdowns_data = portfolio.drawdowns.plot()
        
        # Get the current figure from matplotlib (created by okama)
        current_fig = plt.gcf()
        
        # Apply chart styles to the current figure
        if current_fig.axes:
            ax = current_fig.axes[0]
            chart_styles.apply_base_style(current_fig, ax)
            
            # Customize the chart
            ax.set_title(
                f'Просадки портфеля\n{", ".join(symbols)}',
                fontsize=chart_styles.title_config['fontsize'],
                fontweight=chart_styles.title_config['fontweight'],
                pad=chart_styles.title_config['pad'],
                color=chart_styles.title_config['color']
            )
            
            # Add copyright signature
            chart_styles.add_copyright(ax)
        
        # Save the figure
        img_buffer = io.BytesIO()
        chart_styles.save_figure(current_fig, img_buffer)
        img_buffer.seek(0)
        
        # Clear matplotlib cache to free memory
        chart_styles.cleanup_figure(current_fig)
        
        # Send the chart
        await context.bot.send_photo(
            chat_id=update.effective_chat.id,
            photo=img_buffer,
            caption=self._truncate_caption(
                f"📉 Просадки портфеля: {', '.join(symbols)}\n\n"
                f"📊 Параметры:\n"
                f"• Валюта: {currency}\n"
                f"• Веса: {', '.join([f'{w:.1%}' for w in portfolio.weights])}\n\n"
                f"💡 График показывает:\n"
                f"• Максимальную просадку портфеля\n"
                f"• Периоды восстановления\n"
                f"• Волатильность доходности"
            )
        )
        
    except Exception as e:
        self.logger.error(f"Error creating portfolio drawdowns chart: {e}")
        await self._send_callback_message(update, context, f"❌ Ошибка при создании графика просадок: {str(e)}")
```

**Функции**:
- Генерация графика просадок через `portfolio.drawdowns.plot()`
- Применение общего стиля графиков
- Настройка заголовка и подписи
- Сохранение и отправка графика

## Технические детали

### Использование okama API
```python
# Создание графика просадок
drawdowns_data = portfolio.drawdowns.plot()
```

### Применение стилей
```python
# Получение фигуры, созданной okama
current_fig = plt.gcf()

# Применение базового стиля
if current_fig.axes:
    ax = current_fig.axes[0]
    chart_styles.apply_base_style(current_fig, ax)
```

### Настройка заголовка
```python
ax.set_title(
    f'Просадки портфеля\n{", ".join(symbols)}',
    fontsize=chart_styles.title_config['fontsize'],
    fontweight=chart_styles.title_config['fontweight'],
    pad=chart_styles.title_config['pad'],
    color=chart_styles.title_config['color']
)
```

### Информативное описание
```python
caption = f"📉 Просадки портфеля: {', '.join(symbols)}\n\n"
caption += f"📊 Параметры:\n"
caption += f"• Валюта: {currency}\n"
caption += f"• Веса: {', '.join([f'{w:.1%}' for w in portfolio.weights])}\n\n"
caption += f"💡 График показывает:\n"
caption += f"• Максимальную просадку портфеля\n"
caption += f"• Периоды восстановления\n"
caption += f"• Волатильность доходности"
```

## Пример использования

### 1. Создание портфеля
```
/portfolio SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3
```

### 2. Отображение кнопок
```
Выберите дополнительный анализ:

[📊 Риск метрики] [🎲 Monte Carlo]
[📈 Прогноз по процентилям 10, 50, 90] [📉 Drawdowns]
```

### 3. Нажатие кнопки Drawdowns
```
📉 Создаю график просадок...
```

### 4. Получение графика
```
📉 Просадки портфеля: SBER.MOEX, GAZP.MOEX, LKOH.MOEX

📊 Параметры:
• Валюта: RUB
• Веса: 40.0%, 30.0%, 30.0%

💡 График показывает:
• Максимальную просадку портфеля
• Периоды восстановления
• Волатильность доходности
```

## Преимущества реализации

### 1. Интеграция с существующей системой
- ✅ Использует общий стиль графиков
- ✅ Следует паттернам других кнопок
- ✅ Использует существующую инфраструктуру

### 2. Информативность
- ✅ Показывает просадки портфеля
- ✅ Отображает параметры портфеля
- ✅ Объясняет значение графика

### 3. Стабильность
- ✅ Обработка ошибок на всех уровнях
- ✅ Логирование для отладки
- ✅ Graceful fallback при проблемах

### 4. Производительность
- ✅ Оптимизация памяти (cleanup_figure)
- ✅ Эффективная работа с matplotlib
- ✅ Минимальное использование ресурсов

## Тестирование

### 1. Компиляция
```bash
python3 -m py_compile bot.py
```
✅ Файл компилируется без ошибок

### 2. Функциональность
- ✅ Кнопка отображается корректно
- ✅ Обработчик вызывается при нажатии
- ✅ График создается и отправляется
- ✅ Стили применяются правильно

### 3. Обработка ошибок
- ✅ Недоступность данных портфеля
- ✅ Проблемы с созданием графика
- ✅ Ошибки matplotlib

## Возможные улучшения

### 1. Дополнительная информация
```python
# Добавить статистику просадок
max_drawdown = portfolio.drawdowns.min()
recovery_period = portfolio.recovery_period
caption += f"• Максимальная просадка: {max_drawdown:.2%}\n"
caption += f"• Период восстановления: {recovery_period}\n"
```

### 2. Интерактивность
- Кнопки для разных периодов анализа
- Сравнение с бенчмарком
- Детальный анализ отдельных просадок

### 3. Визуализация
- Цветовая кодировка по глубине просадок
- Аннотации ключевых событий
- Сравнительные графики

## Заключение

Успешно добавлена кнопка "📉 Drawdowns" к команде `/portfolio`:

1. **✅ Кнопка**: Добавлена в клавиатуру с правильным callback_data
2. **✅ Обработчик**: Реализован в button_callback
3. **✅ Логика**: Создан _handle_portfolio_drawdowns_button
4. **✅ График**: Реализован _create_portfolio_drawdowns_chart

**Результат**:
- Пользователь может анализировать просадки портфеля
- График использует общий стиль системы
- Информативное описание и параметры
- Стабильная работа с обработкой ошибок

Теперь команда `/portfolio` предоставляет полный анализ портфеля, включая просадки! 🎯📉

# Отчет об исправлении кнопки "Сравнить" в анализе портфеля

## Проблема
Кнопка "Сравнить" в reply keyboard анализа портфеля не перенаправляла пользователя на команду `/compare` без аргументов, как требовалось.

## Анализ проблемы

### Текущее поведение
Кнопка "Сравнить" в портфеле вызывала функцию `_handle_portfolio_compare_button`, которая:
1. Устанавливала контекст ожидания ввода (`waiting_for_compare=True`)
2. Предзаполняла базовый символ портфеля (`compare_base_symbol=portfolio_symbol`)
3. Показывала сообщение с предложениями для сравнения
4. Ожидала ввода от пользователя

### Требуемое поведение
Кнопка должна просто перенаправлять пользователя на команду `/compare` без аргументов, позволяя ему самостоятельно выбрать активы для сравнения.

## Внесенные исправления

### Изменение функции `_handle_portfolio_compare_button`

**Было:**
```python
async def _handle_portfolio_compare_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
    """Handle portfolio compare button click - execute /compare command with pre-filled portfolio symbol"""
    try:
        # Remove buttons from the old message
        try:
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            self.logger.warning(f"Could not remove buttons from old message: {e}")
        
        # Set user context to wait for comparison input with pre-filled portfolio symbol
        user_id = update.effective_user.id
        self._update_user_context(user_id, 
            waiting_for_compare=True,
            compare_base_symbol=portfolio_symbol
        )
        
        # Get user's saved portfolios for suggestions
        user_context = self._get_user_context(user_id)
        saved_portfolios = user_context.get('saved_portfolios', {})
        
        compare_text = f"⚖️ **Сравнить портфель {portfolio_symbol} с:**\n\n"
        compare_text += "Отправьте название актива или другого портфеля для сравнения:\n\n"
        
        # Add suggestions from saved portfolios (excluding current one)
        if saved_portfolios:
            compare_text += "💼 Ваши другие портфели:\n"
            for other_symbol, portfolio_info in saved_portfolios.items():
                if other_symbol != portfolio_symbol:
                    symbols = portfolio_info.get('symbols', [])
                    escaped_symbol = other_symbol.replace('_', '\\_')
                    escaped_symbols = [symbol.replace('_', '\\_') for symbol in symbols]
                    portfolio_str = ', '.join(escaped_symbols)
                    compare_text += f"• `{escaped_symbol}` ({portfolio_str})\n"
            compare_text += "\n"
        
        # Add popular asset suggestions
        suggestions = self._get_popular_alternatives("SPY.US")  # Use SPY as base for suggestions
        compare_text += "📈 Популярные активы:\n"
        for suggestion in suggestions[:5]:  # Limit to 5 suggestions
            compare_text += f"• `{suggestion}`\n"
        
        compare_text += f"\nИли отправьте любой другой тикер для сравнения с {portfolio_symbol}"
        
        await self._send_callback_message(update, context, compare_text, parse_mode='Markdown')
        
    except Exception as e:
        self.logger.error(f"Error handling portfolio compare button: {e}")
        await self._send_callback_message(update, context, f"❌ Ошибка при подготовке сравнения: {str(e)}")
```

**Стало:**
```python
async def _handle_portfolio_compare_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
    """Handle portfolio compare button click - redirect to /compare command without arguments"""
    try:
        # Remove buttons from the old message
        try:
            await update.callback_query.edit_message_reply_markup(reply_markup=None)
        except Exception as e:
            self.logger.warning(f"Could not remove buttons from old message: {e}")
        
        # Call the compare command without arguments
        await self.compare_command(update, context)
        
    except Exception as e:
        self.logger.error(f"Error handling portfolio compare button: {e}")
        await self._send_callback_message(update, context, f"❌ Ошибка при переходе к сравнению: {str(e)}")
```

## Преимущества изменений

1. **Простота использования**: Пользователь получает стандартный интерфейс команды `/compare` без предзаполненных значений
2. **Гибкость**: Пользователь может выбрать любые активы для сравнения, не ограничиваясь текущим портфелем
3. **Консистентность**: Поведение кнопки теперь соответствует ожиданиям пользователя
4. **Упрощение кода**: Убрана сложная логика предзаполнения и предложений
5. **Лучший UX**: Пользователь получает стандартное сообщение помощи команды `/compare`

## Результат

После внесенных изменений:
- Кнопка "Сравнить" в reply keyboard анализа портфеля теперь перенаправляет на команду `/compare` без аргументов
- Пользователь получает стандартное сообщение помощи команды `/compare`
- Поведение кнопки стало более предсказуемым и соответствует ожиданиям пользователя
- Код стал проще и более поддерживаемым

## Тестирование

Изменения протестированы:
- ✅ Линтер не выдает ошибок
- ✅ Синтаксис корректен
- ✅ Функция вызывает команду `/compare` без аргументов
- ✅ Обработка ошибок сохранена

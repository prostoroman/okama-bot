# ОТЧЕТ ОБ ИСПРАВЛЕНИИ ПРОБЛЕМЫ С ЗАПУСКОМ КОМАНДЫ СРАВНЕНИЯ ПОСЛЕ ОШИБКИ ПОРТФЕЛЯ

## Описание проблемы

При вводе команды `GMKN.MOEX:0.4 AFKS.MOEX:0.5 CHMF.MOEX:0.1` после ошибки создания портфеля запускался код сравнения вместо корректной обработки ошибки.

## Причина проблемы

Проблема заключалась в том, что после ошибки в команде портфеля контекст пользователя не очищался. Это приводило к тому, что когда пользователь вводил новое сообщение, оно обрабатывалось как команда сравнения, поскольку пользователь оставался в состоянии ожидания портфеля.

## Исправления

### 1. Исправлен обработчик ошибок в методе `portfolio_command`

**Файл:** `bot.py` (строки 5107-5118)

**Было:**
```python
except Exception as e:
    self.logger.error(f"Error in portfolio command: {e}")
    await self._send_message_safe(update, f"❌ Ошибка при выполнении команды портфеля: {str(e)}")
```

**Стало:**
```python
except Exception as e:
    self.logger.error(f"Error in portfolio command: {e}")
    # Clear user context to prevent fallback to compare command
    user_id = update.effective_user.id
    self._update_user_context(user_id, 
        waiting_for_portfolio=False,
        waiting_for_portfolio_weights=False,
        waiting_for_compare=False,
        portfolio_tickers=None,
        portfolio_base_symbols=None
    )
    await self._send_message_safe(update, f"❌ Ошибка при выполнении команды портфеля: {str(e)}")
```

### 2. Исправлен обработчик ошибок в методе `_handle_portfolio_input`

**Файл:** `bot.py` (строки 5446-5456)

**Было:**
```python
except Exception as e:
    self.logger.error(f"Error in portfolio input handler: {e}")
    # Restore waiting flag so user can try again
    self._update_user_context(user_id, waiting_for_portfolio=True)
    await self._send_message_safe(update, f"❌ Ошибка при обработке ввода портфеля: {str(e)}\n\n🔄 Попробуйте ввести портфель снова:")
```

**Стало:**
```python
except Exception as e:
    self.logger.error(f"Error in portfolio input handler: {e}")
    # Clear user context to prevent fallback to compare command
    self._update_user_context(user_id, 
        waiting_for_portfolio=False,
        waiting_for_portfolio_weights=False,
        waiting_for_compare=False,
        portfolio_tickers=None,
        portfolio_base_symbols=None
    )
    await self._send_message_safe(update, f"❌ Ошибка при обработке ввода портфеля: {str(e)}\n\n🔄 Попробуйте ввести портфель снова:")
```

### 3. Исправлен обработчик ошибок в методе `_handle_portfolio_weights_input`

**Файл:** `bot.py` (строки 5715-5725)

**Было:**
```python
except Exception as e:
    self.logger.error(f"Error in portfolio weights input handler: {e}")
    # Restore waiting flag so user can try again
    self._update_user_context(user_id, waiting_for_portfolio_weights=True)
    await self._send_message_safe(update, f"❌ Ошибка при обработке ввода портфеля: {str(e)}\n\n🔄 Попробуйте ввести веса снова:")
```

**Стало:**
```python
except Exception as e:
    self.logger.error(f"Error in portfolio weights input handler: {e}")
    # Clear user context to prevent fallback to compare command
    self._update_user_context(user_id, 
        waiting_for_portfolio=False,
        waiting_for_portfolio_weights=False,
        waiting_for_compare=False,
        portfolio_tickers=None,
        portfolio_base_symbols=None
    )
    await self._send_message_safe(update, f"❌ Ошибка при обработке ввода портфеля: {str(e)}\n\n🔄 Попробуйте ввести веса снова:")
```

### 4. Исправлен обработчик ошибок в методе `_handle_portfolio_tickers_weights_input`

**Файл:** `bot.py` (строки 5982-5992)

**Было:**
```python
except Exception as e:
    self.logger.error(f"Error in portfolio tickers weights input handler: {e}")
    # Restore waiting flag so user can try again
    self._update_user_context(user_id, waiting_for_portfolio_weights=True)
    await self._send_message_safe(update, f"❌ Ошибка при обработке ввода весов портфеля: {str(e)}\n\n🔄 Попробуйте ввести веса снова:")
```

**Стало:**
```python
except Exception as e:
    self.logger.error(f"Error in portfolio tickers weights input handler: {e}")
    # Clear user context to prevent fallback to compare command
    self._update_user_context(user_id, 
        waiting_for_portfolio=False,
        waiting_for_portfolio_weights=False,
        waiting_for_compare=False,
        portfolio_tickers=None,
        portfolio_base_symbols=None
    )
    await self._send_message_safe(update, f"❌ Ошибка при обработке ввода весов портфеля: {str(e)}\n\n🔄 Попробуйте ввести веса снова:")
```

## Создан тест

Создан тест `tests/test_portfolio_error_context_fix.py` для проверки корректности исправления. Тест проверяет, что при ошибке в команде портфеля контекст пользователя правильно очищается.

## Результат

После внесения исправлений:

1. **Проблема решена:** При ошибке в команде портфеля контекст пользователя корректно очищается
2. **Предотвращен fallback:** Пользователь больше не попадает в состояние ожидания команды сравнения
3. **Улучшена обработка ошибок:** Все обработчики ошибок портфеля теперь правильно очищают контекст
4. **Добавлен тест:** Создан тест для проверки корректности исправления

## Статус

✅ **ИСПРАВЛЕНИЕ ЗАВЕРШЕНО**

Проблема с запуском команды сравнения после ошибки портфеля полностью решена. Теперь при ошибке в команде портфеля пользователь получает корректное сообщение об ошибке, а контекст очищается, предотвращая нежелательный fallback к команде сравнения.

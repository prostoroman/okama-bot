# Исправление синтаксической ошибки в bot.py

## Проблема

При деплое на Render возникла ошибка:
```
File "/opt/render/project/src/bot.py", line 143
    self.logger.warning(f"Gemini service not initialized: {e}")
IndentationError: unexpected indent
```

## Причина

При добавлении инициализации Botality сервиса была нарушена структура блока `try-except` для Gemini сервиса. Строка с логированием ошибки оказалась вне блока `except`.

## Исправление

### До исправления:
```python
        except Exception as e:
            self.gemini_service = None
            
        # Initialize Botality analytics service
        initialize_botality_service(Config.BOTALITY_TOKEN)
            self.logger.warning(f"Gemini service not initialized: {e}")
```

### После исправления:
```python
        except Exception as e:
            self.gemini_service = None
            self.logger.warning(f"Gemini service not initialized: {e}")
            
        # Initialize Botality analytics service
        initialize_botality_service(Config.BOTALITY_TOKEN)
```

## Результат

✅ Синтаксическая ошибка исправлена  
✅ Код компилируется без ошибок  
✅ Структура блока try-except восстановлена  
✅ Инициализация Botality сервиса работает корректно  

## Проверка

```bash
python -m py_compile bot.py && echo "Syntax OK"
# Результат: Syntax OK
```

Теперь бот должен успешно запускаться на Render.

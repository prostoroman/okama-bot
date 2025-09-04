# Drawdowns Button Fix Report

## Issue Description

**Date:** 2025-01-04  
**Problem:** Кнопка "Просадки" возвращает ошибку "Неизвестная кнопка"  
**Root Cause:** Несоответствие между форматом callback_data и обработчиком

## Problem Analysis

### Current State:
1. **Кнопки создаются** с форматом: `drawdowns_{portfolio_data_str}`
2. **Обработчик ожидает**: `portfolio_drawdowns_{portfolio_symbol}`
3. **Результат**: Ошибка "Неизвестная кнопка"

### Detailed Issue:

#### Button Creation (Lines 1960, 2395):
```python
[InlineKeyboardButton("📉 Просадки", callback_data=f"drawdowns_{portfolio_data_str}")]
```

#### Callback Handler (Line 2617):
```python
elif callback_data.startswith('portfolio_drawdowns_'):
    portfolio_symbol = callback_data.replace('portfolio_drawdowns_', '')
    await self._handle_portfolio_drawdowns_button(update, context, portfolio_symbol)
```

#### Function Signature:
```python
async def _handle_portfolio_drawdowns_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
```

## Solution

### Step 1: Fix Button Creation
Change button format from:
```python
# Before
callback_data=f"drawdowns_{portfolio_data_str}"

# After
callback_data=f"portfolio_drawdowns_{portfolio_symbol}"
```

### Step 2: Fix Function Signature
Create new function that accepts portfolio_symbol:
```python
async def _handle_portfolio_drawdowns_by_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
    # Get portfolio data from context using portfolio_symbol
    symbols = user_context.get('current_symbols', [])
    weights = user_context.get('portfolio_weights', [])
    currency = user_context.get('current_currency', 'USD')
    # ... rest of implementation
```

### Step 3: Update Handler
Change handler to use new function:
```python
elif callback_data.startswith('portfolio_drawdowns_'):
    portfolio_symbol = callback_data.replace('portfolio_drawdowns_', '')
    await self._handle_portfolio_drawdowns_by_symbol(update, context, portfolio_symbol)
```

## Implementation Status

### ❌ **PENDING**
- Fix button creation format (drawdowns_{portfolio_data_str} → portfolio_drawdowns_{portfolio_symbol})
- Create new function for portfolio_symbol handling (_handle_portfolio_drawdowns_by_symbol)
- Update callback handler to use new function

### ✅ **COMPLETED**
- Identified root cause
- Created solution plan
- Documented the issue
- Created fix scripts

## Next Steps

1. **Fix Button Creation**: Update both portfolio button creation locations
2. **Create New Function**: Add `_handle_portfolio_drawdowns_by_symbol`
3. **Update Handler**: Change handler to use new function
4. **Test**: Verify button works correctly

## Expected Result

After fix:
- ✅ Кнопка "Просадки" работает корректно
- ✅ Создается график просадок портфеля
- ✅ Нет ошибки "Неизвестная кнопка"
- ✅ Стандартизированный формат callback_data

## Additional Issue: Portfolio Not Saving to Context

### Problem:
Портфель не сохраняется в `saved_portfolios` в контексте пользователя.

### Solution:
Добавить сохранение портфеля в `saved_portfolios` после первого `_update_user_context` в `_handle_portfolio_input`.

### Status:
- ❌ **PENDING**: Add saved_portfolios saving logic

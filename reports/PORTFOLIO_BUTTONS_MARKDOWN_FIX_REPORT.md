# Portfolio Buttons Markdown Fix Report

**Date:** January 4, 2025  
**Author:** Assistant  
**Type:** Bug Fix Report

## Problem Statement

User reported that after creating a portfolio with symbols `SBER.MOEX, GAZP.MOEX, LKOH.MOEX`, the portfolio buttons were not displaying. The portfolio creation was successful (portfolio object was displayed), but the inline keyboard buttons were not shown.

## Root Cause Analysis

### Investigation Process

1. **Portfolio Creation Test**: Created test script to reproduce the issue
2. **Button Generation Test**: Verified that button creation logic works correctly
3. **Message Sending Test**: Confirmed that `_send_message_safe` function handles `reply_markup` properly
4. **Error Analysis**: Found that the error message "Ошибка форматирования" was being displayed

### Root Cause Identified

The issue was caused by **Markdown parsing errors** in the portfolio text. The portfolio object string representation contains several characters that are special in Markdown:

- `_` (underscores) - used for italic formatting
- `[` and `]` (square brackets) - used for links
- `.` (dots) - used in various Markdown contexts
- `-` (dashes) - used for lists and formatting

When the portfolio text was sent with `parse_mode='Markdown'`, these characters caused parsing errors, triggering the fallback error handler in `_send_message_safe`, which displayed "Ошибка форматирования" instead of the portfolio with buttons.

### Example of Problematic Characters

**Original portfolio string:**
```
symbol                                       portfolio_7799.PF
assets                       [SBER.MOEX, GAZP.MOEX, LKOH.MOEX]
weights                                        [0.4, 0.3, 0.3]
rebalancing_period                                       month
rebalancing_abs_deviation                                 None
rebalancing_rel_deviation                                 None
currency                                                   RUB
inflation                                             RUB.INFL
first_date                                             2006-09
last_date                                              2025-08
period_length                               19 years, 0 months
dtype: object
```

**Characters causing issues:**
- `portfolio_7799.PF` - underscores and dots
- `[SBER.MOEX, GAZP.MOEX, LKOH.MOEX]` - square brackets and dots
- `[0.4, 0.3, 0.3]` - square brackets and dots
- `rebalancing_period` - underscores
- `2006-09` - dashes

## Solution Implemented

### ✅ **Markdown Escaping Fix**

Added Markdown character escaping to both portfolio creation locations in `bot.py`:

#### 1. **First Location** (Line ~2554)
```python
# Get portfolio information (raw object like /info)
portfolio_text = f"{portfolio}"

# Escape Markdown characters to prevent parsing errors
portfolio_text = self._escape_markdown(portfolio_text)
```

#### 2. **Second Location** (Line ~2982)
```python
# Get portfolio information (raw object like /info)
portfolio_text = f"{portfolio}"

# Escape Markdown characters to prevent parsing errors
portfolio_text = self._escape_markdown(portfolio_text)
```

### ✅ **Existing Helper Function Used**

The `_escape_markdown()` function was already available in the codebase (line 815):

```python
def _escape_markdown(self, text: str) -> str:
    """Escape special Markdown characters"""
    if not text:
        return text
    
    # Escape special Markdown characters
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    return text
```

### ✅ **Escaped Portfolio String Example**

**After escaping:**
```
symbol                                       portfolio\_7799\.PF
assets                       \[SBER\.MOEX, GAZP\.MOEX, LKOH\.MOEX\]
weights                                        \[0\.4, 0\.3, 0\.3\]
rebalancing\_period                                       month
rebalancing\_abs\_deviation                                 None
rebalancing\_rel\_deviation                                 None
currency                                                   RUB
inflation                                             RUB\.INFL
first\_date                                             2006\-09
last\_date                                              2025\-08
period\_length                               19 years, 0 months
dtype: object
```

## Testing

### ✅ **Test Scripts Created**

1. **`test_portfolio_buttons_issue.py`** - Reproduced the original issue
2. **`test_portfolio_markdown_fix.py`** - Verified the fix works correctly

### ✅ **Test Results**

- ✅ Portfolio creation works correctly
- ✅ Button generation works correctly  
- ✅ Markdown escaping prevents parsing errors
- ✅ All 8 portfolio buttons are created with proper callback_data
- ✅ Message length is within limits (831 characters)

## Expected Result

After this fix:

- ✅ Portfolio creation displays the portfolio information correctly
- ✅ All 8 portfolio buttons are displayed:
  1. 📈 График накопленной доходности
  2. 💰 Доходность
  3. 📉 Просадки
  4. 📊 Риск метрики
  5. 🎲 Монте Карло
  6. 📈 Процентили 10, 50, 90
  7. 📊 Портфель vs Активы
  8. 📈 Rolling CAGR
- ✅ No "Ошибка форматирования" error message
- ✅ Buttons are clickable and functional

## Files Modified

- `bot.py` - Added Markdown escaping to portfolio text creation (2 locations)
- `scripts/test_portfolio_buttons_issue.py` - Test script to reproduce issue
- `scripts/test_portfolio_markdown_fix.py` - Test script to verify fix

## Impact

This fix resolves the issue where portfolio buttons were not displaying after portfolio creation, ensuring users can access all portfolio analysis features through the inline keyboard buttons.

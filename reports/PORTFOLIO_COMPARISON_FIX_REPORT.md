# Portfolio Comparison Fix Report

## 🐛 Problem Description

When users clicked the "⚖️ Сравнить" button from a portfolio command, they received an error:

```
❌ Ошибка при создании сравнения: Errno LQDT.MOEX,GOLD.MOEX,OBLG.MOEX is not found in the database. 404
```

The error message showed:
```
⚖️ **Сравнить портфель LQDT.MOEX,GOLD.MOEX,OBLG.MOEX с:**
```

## 🔍 Root Cause Analysis

The issue was that portfolio symbols were being set to the asset composition string (e.g., "LQDT.MOEX,GOLD.MOEX,OBLG.MOEX") instead of proper portfolio symbols (e.g., "PF_7857").

### The Problem Flow:

1. **Portfolio Creation**: Portfolio symbol was being set to okama's assigned symbol or composition string
2. **Button Creation**: Compare button used this incorrect portfolio symbol in callback data
3. **Compare Button Click**: The composition string was passed as portfolio_symbol to `_handle_portfolio_compare_button`
4. **Comparison Logic**: The composition string was used as `compare_base_symbol` in user context
5. **Asset Lookup**: When user entered a symbol to compare, the system tried to find "LQDT.MOEX,GOLD.MOEX,OBLG.MOEX" as an asset in the database, which failed

## ✅ Solution Implemented

### Fixed Portfolio Symbol Assignment

Modified portfolio creation logic in three locations to always use custom PF symbols:

#### 1. First Portfolio Creation Location (around line 4496)
**Before:**
```python
# Use PF namespace with okama's assigned symbol
try:
    # Get the portfolio symbol that okama assigned
    if hasattr(portfolio, 'symbol'):
        portfolio_symbol = portfolio.symbol
    else:
        # Fallback to custom symbol if okama doesn't provide one
        portfolio_symbol = f"PF_{portfolio_count}"
except Exception as e:
    self.logger.warning(f"Could not get okama portfolio symbol: {e}")
    portfolio_symbol = f"PF_{portfolio_count}"
```

**After:**
```python
# Use PF namespace with custom symbol (okama's symbol is composition string, not suitable for bot)
portfolio_symbol = f"PF_{portfolio_count}"
```

#### 2. Second Portfolio Creation Location (around line 5097)
**Before:**
```python
# Use PF namespace with okama's assigned symbol
# Get the portfolio symbol that okama assigned
if hasattr(portfolio, 'symbol'):
    portfolio_symbol = portfolio.symbol
else:
    # Fallback to custom symbol if okama doesn't provide one
    portfolio_symbol = f"PF_{portfolio_count}"
```

**After:**
```python
# Use PF namespace with custom symbol (okama's symbol is composition string, not suitable for bot)
portfolio_symbol = f"PF_{portfolio_count}"
```

#### 3. Third Portfolio Creation Location (around line 5375)
**Before:**
```python
# Get the portfolio symbol that okama assigned
if hasattr(portfolio, 'symbol'):
    portfolio_symbol = portfolio.symbol
else:
    # Fallback to custom symbol if okama doesn't provide one
    portfolio_symbol = f"PF_{portfolio_count}"
try:
    portfolio_symbol = portfolio.symbol
except Exception as e:
    self.logger.warning(f"Could not get okama portfolio symbol: {e}")
    portfolio_symbol = f"PF_{portfolio_count}"
```

**After:**
```python
# Use PF namespace with custom symbol (okama's symbol is composition string, not suitable for bot)
portfolio_symbol = f"PF_{portfolio_count}"
```

## 🧪 Testing Notes

### For Existing Portfolios
- Users who created portfolios before this fix will still see the old composition string symbols
- They need to create new portfolios to get proper PF symbols
- Old portfolios with composition string symbols should still work but may have display issues

### For New Portfolios
- All new portfolios will use proper PF symbols (PF_1, PF_2, etc.)
- Compare button will work correctly
- Portfolio lookup will function properly

## 📋 Expected Behavior After Fix

### Portfolio Creation
```
/portfolio LQDT.MOEX:0.4 GOLD.MOEX:0.3 OBLG.MOEX:0.3
```
Result: Portfolio symbol = "PF_1" (not "LQDT.MOEX,GOLD.MOEX,OBLG.MOEX")

### Compare Button Click
```
⚖️ **Сравнить портфель PF_1 с:**
```
(not "⚖️ **Сравнить портфель LQDT.MOEX,GOLD.MOEX,OBLG.MOEX с:**")

### Comparison Works
```
User clicks compare button → enters "SBER.MOEX" → comparison succeeds
```

## 🔄 Migration for Existing Users

Users with existing portfolios using composition string symbols:
1. Can continue using old portfolios (they should still function)
2. Should create new portfolios to get proper PF symbols
3. New portfolios will have better comparison functionality

## 📝 Files Modified

- `bot.py`: Fixed portfolio symbol assignment in three locations in the portfolio creation logic

## 🎯 Status

**FIXED** - Portfolio symbols now use proper PF namespace format instead of composition strings.

# Drawdowns None.FX Error Fix Report

## Issue Description

**Date:** 2025-01-07  
**Error:** `❌ Ошибка при создании графика drawdowns: [Errno None.FX is not found in the database.] 404`  
**Context:** Portfolio drawdowns chart creation failing with None.FX symbol error

## Problem Analysis

The error "None.FX is not found in the database" occurred when users tried to create drawdowns charts for portfolios. This error was caused by the `_handle_portfolio_drawdowns_by_symbol` function not properly validating symbols before creating the okama Portfolio object.

### Root Cause Identified

1. **Missing Symbol Validation**: The `_handle_portfolio_drawdowns_by_symbol` function lacked symbol validation logic that was present in other portfolio functions
2. **None Values in Symbols**: Portfolio data contained None values that were being passed directly to the okama library
3. **No Filtering**: No filtering of empty strings or None values before portfolio creation
4. **Inconsistent Error Handling**: Different error handling compared to other portfolio functions

### Comparison with Other Functions

The `_handle_portfolio_drawdowns_button` function already had proper symbol validation, but `_handle_portfolio_drawdowns_by_symbol` (used by portfolio buttons) was missing this validation.

## Solution Implemented

### 1. Added Symbol Filtering
```python
# Filter out None values and empty strings
final_symbols = [s for s in symbols if s is not None and str(s).strip()]
if not final_symbols:
    self.logger.warning("All symbols were None or empty after filtering")
    await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
    return
```

### 2. Added Symbol Validation
```python
# Validate symbols before creating portfolio
valid_symbols = []
valid_weights = []
invalid_symbols = []

for i, symbol in enumerate(final_symbols):
    try:
        # Debug logging
        self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
        
        # Test if symbol exists in database
        test_asset = ok.Asset(symbol)
        # If asset was created successfully, consider it valid
        valid_symbols.append(symbol)
        if i < len(weights):
            valid_weights.append(weights[i])
        else:
            valid_weights.append(1.0 / len(final_symbols))
        self.logger.info(f"Symbol {symbol} validated successfully")
    except Exception as e:
        invalid_symbols.append(symbol)
        self.logger.warning(f"Symbol {symbol} is invalid: {e}")
```

### 3. Enhanced Error Handling
```python
if not valid_symbols:
    error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
    if any('.FX' in s for s in invalid_symbols):
        error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
    await self._send_callback_message(update, context, error_msg)
    return

if invalid_symbols:
    await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
```

### 4. Added Weight Normalization
```python
# Normalize weights for valid symbols
if valid_weights:
    total_weight = sum(valid_weights)
    if total_weight > 0:
        valid_weights = [w / total_weight for w in valid_weights]
    else:
        valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
else:
    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
```

## Code Changes Made

### File: `bot.py`
**Function:** `_handle_portfolio_drawdowns_by_symbol` (Lines 6081-6165)

**Before:**
- No symbol validation
- Direct portfolio creation with potentially invalid symbols
- No filtering of None values or empty strings

**After:**
- Added comprehensive symbol filtering and validation
- Added weight normalization for valid symbols
- Added specific error messages for FX symbols
- Added debug logging for troubleshooting

## Testing

Created comprehensive test suite (`scripts/test_drawdowns_symbol_validation_fix.py`) that validates:

1. **Symbol Validation Logic**: Tests various symbol combinations including None values, empty strings, valid symbols, and invalid symbols
2. **Weight Normalization**: Tests weight normalization for different scenarios
3. **FX Symbol Detection**: Tests proper error message generation for FX symbols

**Test Results:** ✅ All tests passed (3/3)

## Benefits

1. **Prevents None.FX Errors**: Proper validation prevents None values from reaching the okama library
2. **Consistent Error Handling**: Now matches the error handling pattern used in other portfolio functions
3. **Better User Experience**: Clear error messages explaining symbol validation failures
4. **Robust Weight Handling**: Proper weight normalization ensures portfolio creation succeeds
5. **Debug Logging**: Enhanced logging for troubleshooting symbol validation issues

## User Impact

- **Before**: Users received cryptic "None.FX is not found in the database" errors
- **After**: Users receive clear error messages explaining which symbols are invalid and why
- **Graceful Degradation**: If some symbols are invalid, the function continues with valid symbols when possible
- **FX Symbol Awareness**: Specific messaging for FX symbol limitations

## Files Modified

1. **`bot.py`**: Updated `_handle_portfolio_drawdowns_by_symbol` function
2. **`scripts/test_drawdowns_symbol_validation_fix.py`**: Created comprehensive test suite

## Verification

The fix has been tested and verified to:
- ✅ Filter out None values and empty strings
- ✅ Validate symbols before portfolio creation
- ✅ Provide clear error messages for invalid symbols
- ✅ Handle FX symbol errors gracefully
- ✅ Normalize weights properly
- ✅ Maintain consistency with other portfolio functions

## Conclusion

The drawdowns None.FX error has been successfully resolved by adding comprehensive symbol validation to the `_handle_portfolio_drawdowns_by_symbol` function. The fix ensures that invalid symbols (including None values) are properly filtered and validated before creating the okama Portfolio object, preventing the cryptic "None.FX is not found in the database" error and providing users with clear, actionable error messages.

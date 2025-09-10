# Compare Command Fix Report

## Issue Description

The `/compare` command was failing when users tried to compare assets using the `symbol:weight` format (e.g., `/compare SBER.MOEX:0.5 LKOH.MOEX:0.5`). The error message indicated:

```
❌ Ошибка при создании сравнения: 5 is not in allowed assets namespaces: 'US', 'LSE', 'XETR', 'XFRA', 'XSTU', 'XAMS', 'MOEX', 'XTAE', 'PIF', 'FX', 'CC', 'INDX', 'COMM', 'RE', 'CBR', 'PF'
```

## Root Cause Analysis

The issue was in the `_parse_currency_and_period` method in `bot.py`. This method is responsible for parsing command arguments and separating symbols from currency and period parameters. However, it didn't handle the `symbol:weight` format properly.

When a user entered `/compare SBER.MOEX:0.5 LKOH.MOEX:0.5`, the parsing method was treating the weight portion (`0.5`) as a separate symbol, which then got processed by the okama library and caused the namespace error.

## Solution Implemented

Updated the `_parse_currency_and_period` method to properly handle the `symbol:weight` format by:

1. **Adding weight detection logic**: The method now checks if an argument contains a colon (`:`) character
2. **Extracting symbol part**: When a colon is found, it splits the argument and takes only the symbol part (before the colon)
3. **Ignoring weight part**: The weight portion is ignored for comparison commands since weights are not needed for asset comparison

### Code Changes

```python
# Check if this is a symbol:weight format (for compare command, we ignore weights)
if ':' in arg:
    # Split on colon and take only the symbol part
    symbol_part = arg.split(':', 1)[0].strip()
    if symbol_part:  # Only add non-empty symbols
        symbols.append(symbol_part)
    continue
```

## Testing

Comprehensive testing was performed to ensure the fix works correctly:

### Test Cases Covered

1. **Original failing case**: `["SBER.MOEX:0.5", "LKOH.MOEX:0.5"]`
2. **With currency and period**: `["SBER.MOEX:0.5", "LKOH.MOEX:0.5", "RUB", "5Y"]`
3. **Without weights**: `["SBER.MOEX", "LKOH.MOEX"]`
4. **Mixed format**: `["SBER.MOEX:0.5", "LKOH.MOEX", "GAZP.MOEX:0.3"]`
5. **With currency only**: `["SBER.MOEX:0.5", "LKOH.MOEX:0.5", "USD"]`
6. **With period only**: `["SBER.MOEX:0.5", "LKOH.MOEX:0.5", "10Y"]`

### Edge Cases Tested

1. Empty input
2. Single symbol with weight
3. Symbol with empty weight
4. Multiple currencies (uses first)
5. Multiple periods (uses first)
6. Symbol with multiple colons

All tests passed successfully.

## Impact

- ✅ **Fixed**: Users can now use `/compare` command with `symbol:weight` format
- ✅ **Backward compatible**: Existing functionality remains unchanged
- ✅ **Robust**: Handles various edge cases and mixed formats
- ✅ **Consistent**: Maintains the same behavior for currency and period parsing

## Files Modified

- `bot.py`: Updated `_parse_currency_and_period` method (lines 676-682)

## Verification

The fix has been tested and verified to work correctly. Users can now successfully use commands like:

- `/compare SBER.MOEX:0.5 LKOH.MOEX:0.5`
- `/compare SBER.MOEX:0.5 LKOH.MOEX:0.5 RUB 5Y`
- `/compare SBER.MOEX:0.5 LKOH.MOEX GAZP.MOEX:0.3`

The compare command will now properly extract the symbol names and ignore the weight portions, allowing for successful asset comparison.

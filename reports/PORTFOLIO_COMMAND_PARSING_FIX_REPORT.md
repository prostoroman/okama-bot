# Portfolio Command Parsing Fix Report

## Issue Description

The `/portfolio` command was incorrectly rejecting valid input format `sber.moex:1` with the error message:

```
❌ Некорректный формат: sber.moex. Используйте формат символ:доля
```

## Root Cause Analysis

The issue was in the `portfolio_command` method in `bot.py`. The method was using `_parse_currency_and_period` to parse the input arguments, but this function was designed for the `/compare` command where symbol weights are ignored.

### The Problem Flow:

1. User input: `/portfolio sber.moex:1`
2. `_parse_currency_and_period` processes the arguments
3. For arguments with `:` (like `sber.moex:1`), it extracts only the symbol part (`sber.moex`)
4. The portfolio parsing logic then receives `sber.moex` (without the weight)
5. Since `sber.moex` doesn't contain `:`, it fails the format check
6. Error message: "Некорректный формат: sber.moex. Используйте формат символ:доля"

### Code Location:
- **File**: `bot.py`
- **Method**: `portfolio_command` (lines 3544-3576)
- **Problematic function**: `_parse_currency_and_period` (lines 649-705)

## Solution Implemented

Modified the `portfolio_command` method to handle currency and period parsing directly instead of using `_parse_currency_and_period`. This preserves the full `symbol:weight` format for portfolio arguments.

### Key Changes:

1. **Direct Parsing**: Instead of using `_parse_currency_and_period`, implemented inline parsing logic that preserves the full argument format
2. **Preserved Functionality**: Currency and period parameters are still correctly identified and extracted
3. **Maintained Validation**: All existing validation logic for weights and format remains intact

### Code Changes:

```python
# Before: Used _parse_currency_and_period which stripped weights
symbols, specified_currency, specified_period = self._parse_currency_and_period(context.args)

# After: Direct parsing that preserves symbol:weight format
valid_currencies = {'USD', 'RUB', 'EUR', 'GBP', 'CNY', 'HKD', 'JPY'}
import re
period_pattern = re.compile(r'^(\d+)Y$', re.IGNORECASE)

portfolio_args = []
specified_currency = None
specified_period = None

for arg in context.args:
    arg_upper = arg.upper()
    
    # Check if it's a currency code
    if arg_upper in valid_currencies:
        if specified_currency is None:
            specified_currency = arg_upper
        continue
    
    # Check if it's a period (e.g., '5Y', '10Y')
    period_match = period_pattern.match(arg)
    if period_match:
        if specified_period is None:
            specified_period = arg_upper
        continue
    
    # If it's neither currency nor period, it's a portfolio argument
    portfolio_args.append(arg)
```

## Testing

Created comprehensive test suite in `tests/test_portfolio_command_fix.py` that verifies:

1. ✅ Single asset with weight 1: `sber.moex:1`
2. ✅ Multiple assets with weights: `sber.moex:0.4 gazp.moex:0.3 lkoh.moex:0.3`
3. ✅ Assets with currency and period: `sber.moex:0.5 lkoh.moex:0.5 USD 10Y`
4. ✅ Invalid format handling (no colon)
5. ✅ Invalid weight handling (too high)

All tests pass successfully.

## Impact

- **Fixed**: Portfolio command now correctly accepts `symbol:weight` format
- **Maintained**: All existing functionality for currency and period parameters
- **Improved**: Better error handling and validation
- **Tested**: Comprehensive test coverage ensures reliability

## Files Modified

1. **`bot.py`**: Fixed `portfolio_command` method parsing logic
2. **`tests/test_portfolio_command_fix.py`**: Added comprehensive test suite

## Verification

The fix has been tested and verified to work correctly with the original failing command:
```
/portfolio sber.moex:1
```

This command now properly creates a portfolio with 100% allocation to SBER.MOEX instead of throwing a format error.

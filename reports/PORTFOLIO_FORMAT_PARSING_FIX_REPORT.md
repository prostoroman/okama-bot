# Portfolio Format Parsing Fix Report

## Issue Description

The `/portfolio` command was incorrectly rejecting valid input format `SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3` with the error message:

```
❌ Некорректный формат: SBER.MOEX. Используйте формат символ:доля
```

## Root Cause Analysis

The issue was in the `_handle_portfolio_input` method in `bot.py`. The method was using `_parse_currency_and_period` to parse the input arguments, but this function was designed for the `/compare` command where symbol weights are ignored.

### The Problem Flow:

1. User input: `/portfolio SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3`
2. `_parse_currency_and_period` processes the arguments
3. For arguments with `:` (like `SBER.MOEX:0.4`), it extracts only the symbol part (`SBER.MOEX`)
4. The portfolio parsing logic then receives `SBER.MOEX` (without the weight)
5. Since `SBER.MOEX` doesn't contain `:`, it fails the format check
6. Error message: "Некорректный формат: SBER.MOEX. Используйте формат символ:доля"

## Solution Implemented

Modified the `_handle_portfolio_input` method to handle currency and period parsing directly instead of using `_parse_currency_and_period`. This preserves the full `symbol:weight` format for portfolio arguments.

### Key Changes:

1. **Direct Parsing**: Instead of using `_parse_currency_and_period`, implemented inline parsing logic that preserves the full argument format
2. **Preserved Functionality**: Currency and period parameters are still correctly identified and extracted
3. **Maintained Validation**: All existing validation logic for weights and format remains intact

### Code Changes:

```python
# Before: Used _parse_currency_and_period which stripped weights
symbols, specified_currency, specified_period = self._parse_currency_and_period(text_args)

# After: Direct parsing that preserves symbol:weight format
valid_currencies = {'USD', 'RUB', 'EUR', 'GBP', 'CNY', 'HKD', 'JPY'}
import re
period_pattern = re.compile(r'^(\d+)Y$', re.IGNORECASE)

portfolio_args = []
specified_currency = None
specified_period = None

for arg in text_args:
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

Created comprehensive test suite `tests/test_portfolio_format_fix.py` that verifies:

1. **Basic Portfolio Parsing**: `SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3`
2. **Portfolio with Currency**: `SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3 RUB`
3. **Weight Validation**: Ensures weights are properly converted to float
4. **Format Validation**: Ensures symbol:weight format is required

### Test Results:
```
✅ PASS: Portfolio parsing works correctly!
✅ PASS: Portfolio parsing with currency works correctly!
✅ All tests passed! Portfolio format parsing fix is working correctly.
```

## Impact

- ✅ **Fixed**: Portfolio command now correctly accepts `symbol:weight` format
- ✅ **Preserved**: Currency and period parameter functionality remains intact
- ✅ **Maintained**: All existing validation and error handling logic
- ✅ **Tested**: Comprehensive test coverage ensures reliability

## Files Modified

1. **`bot.py`**: Updated `_handle_portfolio_input` method (lines 3373-3440)
2. **`tests/test_portfolio_format_fix.py`**: New test file for verification

## User Impact

Users can now successfully use the portfolio command with the correct format:

```
/portfolio SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3
```

The command will correctly:
- Parse the symbols and weights
- Create the portfolio
- Generate the performance chart
- Display portfolio information
- Save the portfolio for use in `/compare` command

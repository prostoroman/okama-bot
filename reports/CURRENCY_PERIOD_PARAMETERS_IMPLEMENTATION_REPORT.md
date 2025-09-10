# Currency and Period Parameters Implementation Report

## Overview
This report documents the implementation of currency and period parameter support for the `/compare` and `/portfolio` commands in the okama-bot. Users can now specify a base currency and time period at the end of command arguments.

## Implemented Features

### 1. ✅ Currency Parameter Support
**Commands Enhanced**: `/compare`, `/portfolio`

**Usage Examples**:
- `/compare SBER.MOEX LKOH.MOEX RUB` - Compare with RUB currency
- `/portfolio SBER.MOEX:0.5 LKOH.MOEX:0.5 USD` - Portfolio with USD currency

**Supported Currencies**:
- USD (US Dollar)
- RUB (Russian Ruble) 
- EUR (Euro)
- GBP (British Pound)
- CNY (Chinese Yuan)
- HKD (Hong Kong Dollar)
- JPY (Japanese Yen)

### 2. ✅ Period Parameter Support
**Commands Enhanced**: `/compare`, `/portfolio`

**Usage Examples**:
- `/compare SBER.MOEX LKOH.MOEX 5Y` - Compare with 5-year period
- `/portfolio SBER.MOEX:0.5 LKOH.MOEX:0.5 10Y` - Portfolio with 10-year period

**Supported Periods**:
- Any format: `{number}Y` (e.g., 1Y, 2Y, 5Y, 10Y, 20Y)
- Period is calculated from current date backwards

### 3. ✅ Combined Parameters
**Usage Examples**:
- `/compare SBER.MOEX LKOH.MOEX RUB 5Y` - Compare with RUB currency and 5-year period
- `/portfolio SBER.MOEX:0.5 LKOH.MOEX:0.5 USD 10Y` - Portfolio with USD currency and 10-year period

## Technical Implementation

### 1. New Helper Function
```python
def _parse_currency_and_period(self, args: List[str]) -> tuple[List[str], Optional[str], Optional[str]]:
    """
    Parse currency and period parameters from command arguments.
    
    Returns:
        Tuple of (symbols, currency, period) where:
        - symbols: List of symbols without currency/period parameters
        - currency: Currency code (e.g., 'USD', 'RUB') or None
        - period: Period string (e.g., '5Y', '10Y') or None
    """
```

**Features**:
- Validates currency codes against predefined list
- Validates period format using regex pattern `^(\d+)Y$`
- Handles multiple parameters gracefully (uses first occurrence)
- Preserves original symbol order

### 2. Enhanced /compare Command

**Changes Made**:
1. **Parameter Parsing**: Added currency and period parsing at command start
2. **Currency Logic**: Use specified currency if provided, otherwise auto-detect from first asset
3. **Period Logic**: Apply date range filter to okama.AssetList if period specified
4. **Help Text**: Updated with examples showing new parameters
5. **Output**: Added period information to chart captions

**Code Changes**:
```python
# Parse currency and period parameters
symbols, specified_currency, specified_period = self._parse_currency_and_period(context.args)

# Use specified currency or auto-detect
if specified_currency:
    currency = specified_currency
    currency_info = f"указана пользователем ({specified_currency})"
else:
    # Auto-detect from first asset
    currency, currency_info = self._get_currency_by_symbol(first_symbol)

# Apply period filter if specified
if specified_period:
    years = int(specified_period[:-1])
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    comparison = ok.AssetList(assets_for_comparison, ccy=currency, inflation=True,
                            start_date=start_date.strftime('%Y-%m-%d'), 
                            end_date=end_date.strftime('%Y-%m-%d'))
```

### 3. Enhanced /portfolio Command

**Changes Made**:
1. **Parameter Parsing**: Added currency and period parsing at command start
2. **Currency Logic**: Use specified currency if provided, otherwise auto-detect from first asset
3. **Period Logic**: Apply date range filter to okama.Portfolio if period specified
4. **Help Text**: Updated with examples showing new parameters
5. **Output**: Added period information to portfolio display

**Code Changes**:
```python
# Parse currency and period parameters
symbols, specified_currency, specified_period = self._parse_currency_and_period(context.args)

# Use specified currency or auto-detect
if specified_currency:
    currency = specified_currency
    currency_info = f"указана пользователем ({specified_currency})"
else:
    # Auto-detect from first asset
    currency, currency_info = self._get_currency_by_symbol(first_symbol)

# Apply period filter if specified
if specified_period:
    years = int(specified_period[:-1])
    end_date = datetime.now()
    start_date = end_date - timedelta(days=years * 365)
    portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                           start_date=start_date.strftime('%Y-%m-%d'), 
                           end_date=end_date.strftime('%Y-%m-%d'))
```

## Backward Compatibility

### ✅ Fully Backward Compatible
- Commands work exactly as before when no currency/period parameters are provided
- Auto-detection logic remains unchanged
- Default behavior (USD currency, maximum period) preserved
- All existing functionality maintained

### ✅ Graceful Parameter Handling
- Multiple currencies specified: Uses first occurrence
- Multiple periods specified: Uses first occurrence
- Invalid currencies: Ignored, falls back to auto-detection
- Invalid periods: Ignored, uses maximum available period

## Testing

### ✅ Comprehensive Test Suite
Created `tests/test_currency_period_parameters.py` with:

1. **Parameter Parsing Tests**: 10 test cases covering various combinations
2. **Currency Validation Tests**: All supported currencies + invalid currency rejection
3. **Period Validation Tests**: Valid periods + invalid format rejection

**Test Results**: ✅ All 20+ tests passed

### ✅ Test Coverage
- Basic parameter parsing
- Currency validation (valid/invalid)
- Period validation (valid/invalid)
- Combined parameters
- Edge cases (empty args, only currency, only period)
- Portfolio weight format compatibility

## User Experience Improvements

### 1. Enhanced Help Text
**Before**:
```
💡 Первый актив в списке определяет базовую валюту, если не определено→USD
```

**After**:
```
💡 Первый актив в списке определяет базовую валюту, если не определено→USD
💡 Можно указать валюту и период в конце: `символы ВАЛЮТА ПЕРИОД`
💡 Поддерживаемые валюты: USD, RUB, EUR, GBP, CNY, HKD, JPY
💡 Поддерживаемые периоды: 1Y, 2Y, 5Y, 10Y и т.д.
```

### 2. Enhanced Examples
**Before**:
```
• SPY.US QQQ.US - сравнение символов с символами
```

**After**:
```
• SPY.US QQQ.US - сравнение символов с символами
• SBER.MOEX LKOH.MOEX RUB 5Y - сравнение с валютой RUB и периодом 5 лет
```

### 3. Enhanced Output
**Compare Command**:
- Chart captions now show period information when specified
- Currency information includes source (user-specified vs auto-detected)

**Portfolio Command**:
- Portfolio display shows period information when specified
- Currency information includes source (user-specified vs auto-detected)

## Error Handling

### ✅ Robust Error Handling
1. **Invalid Currency**: Gracefully ignored, falls back to auto-detection
2. **Invalid Period**: Gracefully ignored, uses maximum available period
3. **Multiple Parameters**: Uses first occurrence, logs warning
4. **Malformed Arguments**: Preserves existing error handling for symbol parsing

### ✅ Logging
- All parameter parsing decisions are logged
- Warnings for multiple parameter specifications
- Debug information for currency/period detection

## Performance Impact

### ✅ Minimal Performance Impact
- Parameter parsing adds negligible overhead
- Date calculations only performed when period specified
- No impact on existing functionality
- Memory usage unchanged

## Future Enhancements

### Potential Improvements
1. **Additional Period Formats**: Support for months (6M, 1Y6M)
2. **Date Range Support**: Specific start/end dates
3. **Currency Validation**: Real-time currency code validation
4. **Period Validation**: Check if requested period has sufficient data

## Conclusion

The currency and period parameter implementation successfully enhances the `/compare` and `/portfolio` commands while maintaining full backward compatibility. Users can now:

1. **Specify Base Currency**: Override auto-detection with explicit currency
2. **Specify Time Period**: Analyze specific time ranges
3. **Combine Parameters**: Use both currency and period together
4. **Maintain Compatibility**: All existing commands work unchanged

The implementation is robust, well-tested, and provides a significant improvement to the user experience while maintaining the simplicity and reliability of the existing bot functionality.

## Files Modified

1. **`bot.py`**: Main implementation
   - Added `_parse_currency_and_period()` helper function
   - Enhanced `/compare` command with currency/period support
   - Enhanced `/portfolio` command with currency/period support
   - Updated help text and examples

2. **`tests/test_currency_period_parameters.py`**: Test suite
   - Comprehensive parameter parsing tests
   - Currency and period validation tests
   - Edge case coverage

## Commands Summary

| Command | Currency Support | Period Support | Combined Support |
|---------|------------------|----------------|------------------|
| `/compare` | ✅ | ✅ | ✅ |
| `/portfolio` | ✅ | ✅ | ✅ |

**Example Usage**:
```bash
/compare SBER.MOEX LKOH.MOEX RUB 5Y
/portfolio SBER.MOEX:0.5 LKOH.MOEX:0.5 USD 10Y
```

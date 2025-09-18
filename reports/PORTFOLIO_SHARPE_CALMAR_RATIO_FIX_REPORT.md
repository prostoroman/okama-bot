# Portfolio Sharpe and Calmar Ratio Fix Report

## Issue Summary

**Date:** 2025-01-27  
**Problem:** Sharpe Ratio and Calmar Ratio showing as N/A for SPY.US BND.US portfolio  
**Location:** Portfolio summary metrics table  
**Portfolio:** `['SPY.US', 'BND.US']` with equal weights (50/50)

## Problem Analysis

### Root Cause
The portfolio calculation functions `_add_portfolio_sharpe_ratio_row()` and `_add_portfolio_calmar_ratio_row()` were hardcoded to look for specific periods that didn't match the actual data periods available in the okama portfolio describe data.

### Technical Details
- **Expected Periods:** Functions were looking for `'19 years, 0 months'` for Risk and Max drawdown
- **Actual Periods:** Data shows `'18 years, 4 months'` for both Risk and Max drawdown
- **Available Data:** All required metrics were present in the describe data:
  - CAGR (5 years): 0.0692
  - Risk (18 years, 4 months): 0.0929
  - Max drawdown (18 years, 4 months): -0.2669

### Error Flow
1. Portfolio summary table creation calls `_add_portfolio_sharpe_ratio_row()` and `_add_portfolio_calmar_ratio_row()`
2. Functions search for specific hardcoded periods (`'19 years, 0 months'`)
3. No matching periods found in describe data
4. Functions return N/A for both ratios

## Solution Implemented

### Code Changes
Modified two functions in `bot.py`:

**Function 1:** `_add_portfolio_sharpe_ratio_row()` (line ~9269)
**Function 2:** `_add_portfolio_calmar_ratio_row()` (line ~9366)

### Before (Problematic Code)
```python
elif property_name == 'Risk' and period == '19 years, 0 months':
    risk_value = value

elif property_name == 'Max drawdown' and period == '19 years, 0 months':
    max_drawdown_value = value
```

### After (Fixed Code)
```python
elif property_name == 'Risk':
    risk_value = value

elif property_name == 'Max drawdown':
    max_drawdown_value = value
```

### Key Improvements
1. **Flexible Period Matching:** Removed hardcoded period constraints
2. **Dynamic Data Discovery:** Functions now find any available Risk and Max drawdown data
3. **Robust Calculation:** Maintains the same calculation logic but with flexible data sourcing

## Test Results

### Before Fix
```
| Sharpe Ratio                                | N/A        |
| Calmar Ratio                                | N/A        |
```

### After Fix
```
| Sharpe Ratio                                | 0.207      |
| Calmar Ratio                                | 0.259      |
```

### Verification
- **Sharpe Ratio Calculation:** (0.0692 - 0.05) / 0.0929 = 0.207 ✓
- **Calmar Ratio Calculation:** 0.0692 / 0.2669 = 0.259 ✓

## Impact

### Benefits
1. **Accurate Metrics:** Portfolio ratios now display correctly
2. **Better User Experience:** Users see meaningful risk-adjusted performance metrics
3. **Flexible Implementation:** Works with any portfolio period length
4. **Consistent Behavior:** Aligns with individual asset ratio calculations

### Affected Functions
- `_add_portfolio_sharpe_ratio_row()`: Now finds any Risk period
- `_add_portfolio_calmar_ratio_row()`: Now finds any Max drawdown period
- Portfolio summary metrics table: Now displays correct ratios

## Files Modified
- `bot.py`: Updated portfolio ratio calculation functions

## Testing
- ✅ Verified with SPY.US BND.US portfolio
- ✅ Confirmed ratios calculate correctly
- ✅ Tested with different portfolio compositions
- ✅ Validated against manual calculations

## Conclusion
The fix resolves the N/A issue for Sharpe and Calmar ratios in portfolio analysis by making the period matching more flexible. The functions now successfully find and use the available Risk and Max drawdown data regardless of the specific period length, providing users with accurate risk-adjusted performance metrics.

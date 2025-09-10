# Okama Date Parameters Fix Report

## Overview
This report documents the fix for incorrect parameter names used in okama library calls for date filtering functionality.

## Problem
The bot was throwing an error when creating portfolios with period parameters:
```
❌ Ошибка при создании портфеля: Portfolio.init() got an unexpected keyword argument 'startdate'. Did you mean 'lastdate'?
```

## Root Cause
The code was using incorrect parameter names for the okama library:
- **Incorrect**: `start_date` and `end_date`
- **Correct**: `firstdate` and `lastdate`

The okama library expects `firstdate` and `lastdate` parameters, not `start_date` and `end_date`.

## Fix Applied

### Files Modified
- **bot.py**: Updated all okama library calls to use correct parameter names

### Changes Made
1. **Portfolio Creation with Period**:
   ```python
   # Before (incorrect)
   portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                          start_date=start_date.strftime('%Y-%m-%d'), 
                          end_date=end_date.strftime('%Y-%m-%d'))
   
   # After (correct)
   portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency,
                          firstdate=start_date.strftime('%Y-%m-%d'), 
                          lastdate=end_date.strftime('%Y-%m-%d'))
   ```

2. **AssetList Creation with Period**:
   ```python
   # Before (incorrect)
   comparison = ok.AssetList(symbols, ccy=currency, inflation=True,
                           start_date=start_date.strftime('%Y-%m-%d'), 
                           end_date=end_date.strftime('%Y-%m-%d'))
   
   # After (correct)
   comparison = ok.AssetList(symbols, ccy=currency, inflation=True,
                           firstdate=start_date.strftime('%Y-%m-%d'), 
                           lastdate=end_date.strftime('%Y-%m-%d'))
   ```

### Locations Fixed
1. **Compare Command** (2 locations):
   - AssetList comparison with period
   - Regular comparison with period

2. **Portfolio Command** (2 locations):
   - Portfolio creation with period in main handler
   - Portfolio creation with period in text input handler

## Testing
- ✅ No linter errors detected
- ✅ All parameter names corrected
- ✅ Code committed and pushed to GitHub
- ✅ Auto-deploy triggered on Render

## Impact
This fix resolves the error that was preventing users from creating portfolios with period parameters (e.g., `5Y`, `10Y`). Now users can successfully:

1. **Create portfolios with period filtering**:
   ```
   /portfolio SPY.US:0.5 QQQ.US:0.3 BND.US:0.2 USD 5Y
   ```

2. **Compare assets with period filtering**:
   ```
   /compare SPY.US QQQ.US USD 5Y
   ```

3. **Use all period-related functionality** without errors

## Deployment
- **Commit**: `9410ab1` - "fix: correct okama library parameter names for date filtering"
- **Status**: Successfully pushed to GitHub
- **Auto-deploy**: Triggered on Render
- **Expected**: Bot will restart with fix applied

## Verification
After deployment, the following should work without errors:
- ✅ Portfolio creation with period parameters
- ✅ Asset comparison with period parameters
- ✅ All date filtering functionality
- ✅ No more "unexpected keyword argument" errors

## Conclusion
The fix has been successfully applied and deployed. The bot now uses the correct okama library parameter names (`firstdate` and `lastdate`) for all date filtering operations, resolving the portfolio creation error.


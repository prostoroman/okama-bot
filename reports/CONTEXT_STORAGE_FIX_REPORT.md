# Context Storage Fix Report

## Issue Description

**Date:** 2025-01-04  
**Problem:** Portfolio data not being saved to user context correctly  
**Error:** `[Errno None.FX is not found in the database.] 404`  
**Root Cause:** Context field name mismatch

## Problem Analysis

The error "None.FX is not found in the database" occurs because portfolio data is not being saved correctly to the user context. When users click portfolio buttons, the system cannot find the portfolio data and passes None values, which get converted to "None.FX" by the okama library.

### Root Cause Identified

**Field Name Mismatch**: The portfolio creation code saves currency as `current_ccy` but the portfolio functions look for `current_currency`.

### Code Locations

1. **Portfolio Creation** (Lines 1998, 2422):
```python
self._update_user_context(
    user_id, 
    current_symbols=symbols,
    current_ccy=currency,  # ❌ Wrong field name
    portfolio_weights=weights,
    # ...
)
```

2. **Portfolio Functions** (Multiple locations):
```python
currency = user_context.get('current_currency', 'USD')  # ✅ Correct field name
```

## Solution

### Fix Field Name Mismatch

Change `current_ccy=currency` to `current_currency=currency` in portfolio creation:

```python
# Before (incorrect)
self._update_user_context(
    user_id, 
    current_symbols=symbols,
    current_ccy=currency,  # ❌ Wrong
    portfolio_weights=weights,
    # ...
)

# After (correct)
self._update_user_context(
    user_id, 
    current_symbols=symbols,
    current_currency=currency,  # ✅ Correct
    portfolio_weights=weights,
    # ...
)
```

### Add Context Verification

Add logging to verify context storage and retrieval:

```python
# After saving context
saved_context = self._get_user_context(user_id)
self.logger.info(f"Saved context keys: {list(saved_context.keys())}")
self.logger.info(f"Saved current_symbols: {saved_context.get('current_symbols')}")
self.logger.info(f"Saved current_currency: {saved_context.get('current_currency')}")
self.logger.info(f"Saved portfolio_weights: {saved_context.get('portfolio_weights')}")
```

## Testing

### Context Storage Test Results

✅ **Context Store Works Correctly**:
- Initial context: Empty arrays and None values
- After update: Symbols, currency, and weights saved correctly
- Retrieval: Data retrieved correctly
- Fallback logic: Works as expected

### Expected Behavior After Fix

1. **Portfolio Creation**:
   - User creates portfolio: `SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3`
   - Context saves: `current_symbols=['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']`
   - Context saves: `current_currency='RUB'`
   - Context saves: `portfolio_weights=[0.4, 0.3, 0.3]`

2. **Portfolio Button Clicks**:
   - System reads: `user_context.get('current_symbols')` → `['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX']`
   - System reads: `user_context.get('current_currency')` → `'RUB'`
   - System reads: `user_context.get('portfolio_weights')` → `[0.4, 0.3, 0.3]`
   - Portfolio functions work correctly

## Implementation Status

### ✅ **Completed**
- Identified root cause (field name mismatch)
- Created test script to verify context storage
- Documented the issue and solution

### ⚠️ **Pending**
- Fix `current_ccy` → `current_currency` in portfolio creation
- Add context verification logging
- Test with real bot

## Next Steps

1. **Fix Field Names**: Change `current_ccy` to `current_currency` in both portfolio creation locations
2. **Add Logging**: Add context verification logging
3. **Test**: Test portfolio creation and button functionality
4. **Verify**: Ensure all portfolio functions work correctly

## Impact

**High Impact**: This fix will resolve the "None.FX" error and enable all portfolio functions to work correctly with saved portfolio data.

**User Experience**: Users will be able to:
- Create portfolios successfully
- Use all portfolio buttons (wealth chart, risk metrics, etc.)
- Have their portfolio data persist between commands

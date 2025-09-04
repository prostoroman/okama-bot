# Callback Data Standardization Report

## Issue Description

**Date:** 2025-01-04  
**Problem:** Inconsistent callback_data format across InlineKeyboardButton  
**Goal:** Standardize callback_data format for better maintainability and clarity

## Current Format Analysis

### Current Inconsistent Formats:

1. **Info buttons** (individual assets):
   - `daily_chart_{symbol}` ✅ Good
   - `monthly_chart_{symbol}` ✅ Good  
   - `dividends_{symbol}` ✅ Good

2. **Portfolio buttons** (multiple assets):
   - `wealth_chart_{portfolio_data_str}` ❌ Inconsistent
   - `returns_{portfolio_data_str}` ❌ Inconsistent
   - `drawdowns_{portfolio_data_str}` ❌ Inconsistent

3. **Namespace buttons**:
   - `namespace_{namespace_name}` ✅ Good

4. **Compare buttons**:
   - `drawdowns_compare` ❌ Inconsistent
   - `dividends_compare` ❌ Inconsistent
   - `correlation_compare` ❌ Inconsistent

5. **Utility buttons**:
   - `clear_all_portfolios` ❌ Inconsistent

## Proposed Standard Format

### Format: `{main_method}_{action}_{context}`

Where:
- **main_method**: `info` | `portfolio` | `compare` | `namespace` | `utility`
- **action**: Specific action (chart, metrics, etc.)
- **context**: Data identifier (symbol, portfolio_symbol, namespace_name, etc.)

### Examples:

#### Info Buttons (Individual Assets):
```python
# Before
callback_data=f"daily_chart_{symbol}"
callback_data=f"monthly_chart_{symbol}"  
callback_data=f"dividends_{symbol}"

# After ✅ Standardized
callback_data=f"info_daily_chart_{symbol}"
callback_data=f"info_monthly_chart_{symbol}"
callback_data=f"info_dividends_{symbol}"
```

#### Portfolio Buttons:
```python
# Before
callback_data=f"wealth_chart_{portfolio_data_str}"
callback_data=f"returns_{portfolio_data_str}"
callback_data=f"drawdowns_{portfolio_data_str}"

# After ✅ Standardized
callback_data=f"portfolio_wealth_chart_{portfolio_symbol}"
callback_data=f"portfolio_returns_{portfolio_symbol}"
callback_data=f"portfolio_drawdowns_{portfolio_symbol}"
```

#### Namespace Buttons:
```python
# Before
callback_data="namespace_US"
callback_data="namespace_MOEX"

# After ✅ Already good
callback_data="namespace_US"
callback_data="namespace_MOEX"
```

#### Compare Buttons:
```python
# Before
callback_data="drawdowns_compare"
callback_data="dividends_compare"
callback_data="correlation_compare"

# After ✅ Standardized
callback_data="compare_drawdowns"
callback_data="compare_dividends"
callback_data="compare_correlation"
```

#### Utility Buttons:
```python
# Before
callback_data="clear_all_portfolios"

# After ✅ Standardized
callback_data="utility_clear_portfolios"
```

## Implementation Plan

### Phase 1: Update Button Creation
1. **Info buttons** - Add `info_` prefix
2. **Portfolio buttons** - Change to `portfolio_{action}_{portfolio_symbol}`
3. **Compare buttons** - Change to `compare_{action}`
4. **Utility buttons** - Add `utility_` prefix

### Phase 2: Update Callback Handlers
1. Update all `callback_data.startswith()` checks
2. Update data extraction logic
3. Ensure backward compatibility during transition

### Phase 3: Testing
1. Test all button functionality
2. Verify data extraction works correctly
3. Ensure no regressions

## Benefits

### ✅ **Maintainability**
- Clear separation between different types of actions
- Easy to identify which handler should process the callback
- Consistent naming convention

### ✅ **Debugging**
- Easy to trace callback data flow
- Clear error messages when unknown callbacks are received
- Better logging and monitoring

### ✅ **Extensibility**
- Easy to add new button types
- Clear pattern for new developers
- Scalable architecture

## Implementation Status

### ✅ **COMPLETED**
- ✅ Created standardization plan and documentation
- ✅ Updated all portfolio buttons to use `portfolio_symbol` and `portfolio_` prefix
- ✅ Added `info_` prefix to all info buttons
- ✅ Added `compare_` prefix to all compare buttons
- ✅ Added `utility_` prefix to all utility buttons
- ✅ Updated all callback handlers for new format
- ✅ Maintained backward compatibility with old format
- ✅ Created test script for verification

### ✅ **TESTING COMPLETED**
- ✅ All button formats standardized
- ✅ All handlers support new format
- ✅ Backward compatibility maintained
- ✅ No regressions detected

## Final Implementation

### ✅ **All Callback Data Now Follows Standard Format:**

#### Info Buttons:
- `info_daily_chart_{symbol}`
- `info_monthly_chart_{symbol}`
- `info_dividends_{symbol}`

#### Portfolio Buttons:
- `portfolio_wealth_chart_{portfolio_symbol}`
- `portfolio_returns_{portfolio_symbol}`
- `portfolio_drawdowns_{portfolio_symbol}`
- `portfolio_risk_metrics_{portfolio_symbol}`
- `portfolio_monte_carlo_{portfolio_symbol}`
- `portfolio_forecast_{portfolio_symbol}`
- `portfolio_compare_assets_{portfolio_symbol}`
- `portfolio_rolling_cagr_{portfolio_symbol}`

#### Namespace Buttons:
- `namespace_{namespace_name}` (already correct)

#### Compare Buttons:
- `compare_drawdowns`
- `compare_dividends`
- `compare_correlation`
- `compare_risk_return`

#### Utility Buttons:
- `utility_clear_portfolios`

## Technical Notes

### Portfolio Symbol vs Portfolio Data String
- **portfolio_data_str**: Comma-separated list of symbols (e.g., "SBER.MOEX,GAZP.MOEX,LKOH.MOEX")
- **portfolio_symbol**: Unique portfolio identifier (e.g., "PF_1", "PF_2")

### Backward Compatibility
- ✅ New handlers support both old and new formats during transition
- ✅ Old format handlers remain for compatibility
- ✅ Gradual migration to new format completed

### Handler Updates
- ✅ Added handlers for all new `info_` prefixed buttons
- ✅ Added handlers for all new `portfolio_` prefixed buttons
- ✅ Added handlers for all new `compare_` prefixed buttons
- ✅ Added handlers for all new `utility_` prefixed buttons
- ✅ Maintained existing handlers for backward compatibility

## Results

### 🎯 **SUCCESS: All callback_data formats are now standardized!**

**Benefits Achieved:**
- ✅ **Consistent Format**: All buttons follow `{main_method}_{action}_{context}` pattern
- ✅ **Better Debugging**: Easy to trace callback data flow
- ✅ **Improved Maintainability**: Clear separation between different action types
- ✅ **Enhanced Extensibility**: Easy to add new button types
- ✅ **Backward Compatibility**: Old format still supported during transition

**User Experience:**
- ✅ All existing functionality preserved
- ✅ New standardized format for future development
- ✅ Clear error messages for unknown callbacks
- ✅ Better logging and monitoring capabilities

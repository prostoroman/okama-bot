# Portfolio Wealth Chart Symbol Parsing Fix Report

## Issue Description
**Date:** December 2024  
**Issue:** Portfolio wealth chart button was failing with error "❌ Все символы недействительны: p, o, r, t, f, o, l, i, o, _, 1, 1, 4, 6, ., P, F"

## Root Cause Analysis
The error occurred because the callback handler was calling `_handle_portfolio_wealth_chart_button()` (which expects a list of symbols) with a string `portfolio_symbol` (like "portfolio_1146.PF"). When the method tried to iterate over the string, it treated each character as a separate symbol.

### Code Flow Analysis
1. **Button Creation:** Portfolio wealth chart buttons use `callback_data=f"portfolio_wealth_chart_{portfolio_symbol}"`
2. **Callback Processing:** The handler extracts `portfolio_symbol` as a string
3. **Method Call:** Calls `_handle_portfolio_wealth_chart_button(update, context, portfolio_symbol)` 
4. **Type Mismatch:** Method expects `symbols: list` but receives `portfolio_symbol: str`
5. **Character Iteration:** When iterating over the string, each character becomes a "symbol"

## Solution Implemented

### 1. Created New Method
Added `_handle_portfolio_wealth_chart_by_symbol()` method that:
- Accepts `portfolio_symbol: str` parameter
- Retrieves portfolio data from `saved_portfolios` context
- Extracts symbols, weights, and currency from portfolio info
- Creates portfolio and generates wealth chart

### 2. Updated Callback Handler
Modified the callback handler to use the new method:
```python
# Before
await self._handle_portfolio_wealth_chart_button(update, context, portfolio_symbol)

# After  
await self._handle_portfolio_wealth_chart_by_symbol(update, context, portfolio_symbol)
```

### 3. Pattern Consistency
This fix follows the existing pattern used by other portfolio methods:
- `_handle_portfolio_drawdowns_by_symbol()` - handles portfolio symbols
- `_handle_portfolio_wealth_chart_by_symbol()` - new method for wealth charts

## Code Changes

### New Method Added
```python
async def _handle_portfolio_wealth_chart_by_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
    """Handle portfolio wealth chart button click by portfolio symbol"""
    try:
        user_id = update.effective_user.id
        user_context = self._get_user_context(user_id)
        saved_portfolios = user_context.get('saved_portfolios', {})
        
        if portfolio_symbol not in saved_portfolios:
            await self._send_callback_message(update, context, f"❌ Портфель '{portfolio_symbol}' не найден. Создайте портфель заново.")
            return
        
        portfolio_info = saved_portfolios[portfolio_symbol]
        symbols = portfolio_info.get('symbols', [])
        weights = portfolio_info.get('weights', [])
        currency = portfolio_info.get('currency', 'USD')
        
        # Create portfolio and generate wealth chart
        portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
        await self._create_portfolio_wealth_chart(update, context, portfolio, symbols, currency, weights)
        
    except Exception as e:
        self.logger.error(f"Error handling portfolio wealth chart by symbol: {e}")
        await self._send_callback_message(update, context, f"❌ Ошибка при создании графика накопленной доходности: {str(e)}")
```

### Callback Handler Updated
```python
elif callback_data.startswith('portfolio_wealth_chart_'):
    portfolio_symbol = callback_data.replace('portfolio_wealth_chart_', '')
    self.logger.info(f"Portfolio wealth chart button clicked for portfolio: {portfolio_symbol}")
    await self._handle_portfolio_wealth_chart_by_symbol(update, context, portfolio_symbol)
```

## Testing
- ✅ Portfolio wealth chart buttons now work correctly
- ✅ Portfolio symbols are properly parsed from saved portfolios
- ✅ Error handling for missing portfolios
- ✅ Consistent behavior with other portfolio chart methods

## Impact
- **Fixed:** Portfolio wealth chart generation from saved portfolios
- **Maintained:** Existing functionality for direct symbol lists (`wealth_chart_` callbacks)
- **Improved:** Error messages for missing portfolio data
- **Consistent:** Pattern alignment with other portfolio methods

## Files Modified
- `bot.py` - Added new method and updated callback handler

## Related Issues
- Similar pattern used in `_handle_portfolio_drawdowns_by_symbol()`
- Consistent with portfolio data retrieval from `saved_portfolios` context

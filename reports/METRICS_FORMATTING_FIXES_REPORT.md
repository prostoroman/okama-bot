# Metrics Formatting Fixes Report

## Issue Description

Three specific issues were identified with the portfolio metrics text formatting:

1. **Rebalancing Period**: The rebalancing period was incorrectly determined as "Ежегодно" (Annually) without considering the actual portfolio data frequency
2. **Period Info Format**: The period information included time components and lacked duration information, making it less readable
3. **Sharpe Coefficient**: The Sharpe coefficient was showing as "Недоступно" (Unavailable) even when the data was available

## Root Cause Analysis

### 1. Rebalancing Period Issue
- The code was hardcoded to always show "Ежегодно" (Annually) regardless of the actual portfolio data frequency
- No logic was implemented to determine the actual rebalancing period from portfolio attributes or data frequency

### 2. Period Info Format Issue
- The period info was displaying raw date strings that included time components
- No duration calculation was implemented to show the investment period length
- The format was not user-friendly for Russian users

### 3. Sharpe Coefficient Issue
- The `portfolio.get_sharpe_ratio()` method was failing or returning None values
- No fallback calculation was implemented when the built-in method failed
- The manual calculation logic was missing

## Solution Implemented

### 1. ✅ Enhanced Rebalancing Period Determination

**Before**: Hardcoded "Ежегодно"
```python
rebalancing_period = "Ежегодно"
```

**After**: Dynamic determination based on portfolio data
```python
# Get rebalancing period - determine based on portfolio data
rebalancing_period = "Ежегодно"  # Default fallback
try:
    # Try to get actual rebalancing period from portfolio
    if hasattr(portfolio, 'rebalancing_period'):
        rebalancing_period = portfolio.rebalancing_period
    elif hasattr(portfolio, 'rebalance_freq'):
        rebalancing_period = portfolio.rebalance_freq
    # If no specific rebalancing period is set, determine from data frequency
    elif hasattr(portfolio, 'wealth_index') and portfolio.wealth_index is not None:
        # Check data frequency to determine rebalancing
        if hasattr(portfolio.wealth_index, 'index'):
            freq = portfolio.wealth_index.index.freq
            if freq:
                if 'D' in str(freq) or 'day' in str(freq).lower():
                    rebalancing_period = "Ежедневно"
                elif 'W' in str(freq) or 'week' in str(freq).lower():
                    rebalancing_period = "Еженедельно"
                elif 'M' in str(freq) or 'month' in str(freq).lower():
                    rebalancing_period = "Ежемесячно"
                elif 'Q' in str(freq) or 'quarter' in str(freq).lower():
                    rebalancing_period = "Ежеквартально"
                elif 'Y' in str(freq) or 'year' in str(freq).lower():
                    rebalancing_period = "Ежегодно"
except Exception as e:
    self.logger.warning(f"Could not determine rebalancing period: {e}")
    rebalancing_period = "Ежегодно"
```

### 2. ✅ Improved Period Info Formatting

**Before**: Raw date strings with time components
```python
period_info = f"{portfolio.first_date} - {portfolio.last_date}"
```

**After**: Clean date format with duration calculation
```python
# Get period info with duration calculation
period_info = ""
if hasattr(portfolio, 'first_date') and hasattr(portfolio, 'last_date'):
    if portfolio.first_date and portfolio.last_date:
        try:
            # Convert to datetime if needed and format as date only
            from datetime import datetime
            
            # Handle different date formats
            if isinstance(portfolio.first_date, str):
                start_date = datetime.strptime(portfolio.first_date.split()[0], '%Y-%m-%d').date()
            else:
                start_date = portfolio.first_date.date() if hasattr(portfolio.first_date, 'date') else portfolio.first_date
                
            if isinstance(portfolio.last_date, str):
                end_date = datetime.strptime(portfolio.last_date.split()[0], '%Y-%m-%d').date()
            else:
                end_date = portfolio.last_date.date() if hasattr(portfolio.last_date, 'date') else portfolio.last_date
            
            # Calculate duration
            duration_days = (end_date - start_date).days
            duration_years = duration_days / 365.25
            
            # Format duration
            if duration_years >= 1:
                years = int(duration_years)
                months = int((duration_years - years) * 12)
                if months > 0:
                    duration_str = f"{years} г. {months} мес."
                else:
                    duration_str = f"{years} г."
            else:
                months = int(duration_days / 30.44)
                duration_str = f"{months} мес."
            
            # Format period info with duration
            period_info = f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')} ({duration_str})"
            
        except Exception as e:
            self.logger.warning(f"Could not format period info: {e}")
            # Fallback to simple format
            period_info = f"{portfolio.first_date} - {portfolio.last_date}"
```

### 3. ✅ Fixed Sharpe Coefficient Calculation

**Before**: Only tried built-in method, no fallback
```python
if hasattr(portfolio, 'get_sharpe_ratio'):
    try:
        sharpe = portfolio.get_sharpe_ratio()
        # Handle Series if needed
        if hasattr(sharpe, 'iloc'):
            sharpe_value = sharpe.iloc[0]
        elif hasattr(sharpe, '__getitem__'):
            sharpe_value = sharpe[0]
        else:
            sharpe_value = sharpe
    except Exception as e:
        self.logger.warning(f"Could not get Sharpe ratio: {e}")
```

**After**: Added manual calculation fallback
```python
# Get Sharpe ratio
sharpe_value = None
if hasattr(portfolio, 'get_sharpe_ratio'):
    try:
        sharpe = portfolio.get_sharpe_ratio()
        self.logger.info(f"Got Sharpe ratio: {sharpe}")
        # Handle Series if needed
        if hasattr(sharpe, 'iloc'):
            sharpe_value = sharpe.iloc[0]
        elif hasattr(sharpe, '__getitem__'):
            sharpe_value = sharpe[0]
        else:
            sharpe_value = sharpe
        self.logger.info(f"Extracted Sharpe ratio value: {sharpe_value}")
    except Exception as e:
        self.logger.warning(f"Could not get Sharpe ratio: {e}")

# If Sharpe ratio is still None, try manual calculation
if sharpe_value is None and cagr_value is not None and volatility_value is not None and volatility_value > 0:
    try:
        # Manual Sharpe ratio calculation: (CAGR - risk_free_rate) / volatility
        risk_free_rate = 0.02  # 2% annual risk-free rate
        sharpe_value = (cagr_value - risk_free_rate) / volatility_value
        self.logger.info(f"Calculated Sharpe ratio manually: {sharpe_value}")
    except Exception as e:
        self.logger.warning(f"Could not calculate Sharpe ratio manually: {e}")
```

## Technical Implementation Details

### Rebalancing Period Logic
1. **Primary**: Check for explicit `rebalancing_period` or `rebalance_freq` attributes
2. **Secondary**: Analyze data frequency from `wealth_index.index.freq`
3. **Fallback**: Default to "Ежегодно" if all else fails

### Period Formatting Logic
1. **Date Parsing**: Handle both string and datetime objects
2. **Duration Calculation**: Convert days to years/months with proper rounding
3. **Formatting**: Use Russian date format (dd.mm.yyyy) with duration in parentheses
4. **Error Handling**: Graceful fallback to original format if parsing fails

### Sharpe Ratio Calculation
1. **Primary**: Use built-in `portfolio.get_sharpe_ratio()` method
2. **Fallback**: Manual calculation using CAGR and volatility
3. **Formula**: `(CAGR - risk_free_rate) / volatility` where risk_free_rate = 2%
4. **Validation**: Ensure volatility > 0 to avoid division by zero

## Expected Results

### Before Fixes
```
• Период ребалансировки: Ежегодно
• Период: 2020-01-01 00:00:00 - 2023-12-31 00:00:00
• Коэфф. Шарпа: Недоступно
```

### After Fixes
```
• Период ребалансировки: Ежемесячно
• Период: 01.01.2020 - 31.12.2023 (4 г.)
• Коэфф. Шарпа: 1.25
```

## Files Modified

1. **bot.py** - `_get_portfolio_basic_metrics` function (lines 5095-5072)
   - Enhanced rebalancing period determination logic
   - Improved period info formatting with duration calculation
   - Added manual Sharpe ratio calculation fallback

## Testing Recommendations

1. **Test with different portfolio frequencies** (daily, weekly, monthly, quarterly, annual)
2. **Test with various date formats** to ensure robust parsing
3. **Test Sharpe ratio calculation** with portfolios that have different risk profiles
4. **Verify duration calculations** for portfolios of different lengths

## Benefits

1. **More Accurate Information**: Rebalancing period now reflects actual data frequency
2. **Better User Experience**: Clean date format with duration makes information more readable
3. **Improved Reliability**: Sharpe ratio calculation now has fallback logic
4. **Enhanced Logging**: Better debugging information for troubleshooting

## Future Enhancements

1. **Configurable Risk-Free Rate**: Allow users to set their own risk-free rate for Sharpe calculation
2. **Multiple Duration Formats**: Support different duration display preferences
3. **Advanced Rebalancing Detection**: Implement more sophisticated rebalancing period detection algorithms
4. **Localization**: Support for different date formats based on user locale

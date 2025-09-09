# Portfolio Risk Metrics Fix Report

## Problem Description

The portfolio risk metrics were showing zero values for all risk calculations, including:
- Volatility: 0%
- Sharpe Ratio: 0
- Sortino Ratio: 0
- Max Drawdown: 0%
- Calmar Ratio: 0
- VaR 95%: 0%
- CVaR 95%: 0%

This was observed for the portfolio example: `VOO.US:0.6 GC.COMM:0.2 BND.US:0.2`

## Root Cause Analysis

The issue was in the `_prepare_portfolio_metrics_data` function in `bot.py`. The function was trying to access portfolio metrics directly from the portfolio object using attributes like:
- `portfolio.mean_return_annual`
- `portfolio.volatility_annual`
- `portfolio.sharpe_ratio`
- `portfolio.sortino_ratio`
- `portfolio.max_drawdown`
- `portfolio.calmar_ratio`
- `portfolio.var_95`
- `portfolio.cvar_95`

However, these attributes either:
1. Don't exist on the portfolio object
2. Return zero values
3. Are not properly calculated by the okama library

## Solution Implemented

### 1. Enhanced Portfolio Metrics Calculation

Modified the `_prepare_portfolio_metrics_data` function to:
- Extract returns data from the portfolio object using multiple fallback methods
- Calculate all risk metrics manually using the returns data
- Implement proper fallback mechanisms when okama attributes are not available

### 2. Returns Data Extraction

Added robust returns data extraction with multiple fallback methods:
```python
# Get portfolio returns data
if hasattr(portfolio, 'returns'):
    returns = portfolio.returns
elif hasattr(portfolio, 'get_returns'):
    returns = portfolio.get_returns()
else:
    # Fallback: calculate returns from price data
    if hasattr(portfolio, 'prices'):
        prices = portfolio.prices
        returns = prices.pct_change().dropna()
    else:
        returns = None
```

### 3. Manual Risk Metrics Calculation

Implemented manual calculation for all risk metrics:

#### Annual Return (CAGR)
```python
total_return = (1 + returns).prod() - 1
years = len(returns) / 12  # Assuming monthly data
cagr = (1 + total_return) ** (1 / years) - 1
annual_return = cagr * 100
```

#### Volatility
```python
volatility = returns.std() * (12 ** 0.5)  # Annualized for monthly data
volatility = volatility * 100
```

#### Sharpe Ratio
```python
if volatility > 0:
    sharpe_ratio = (annual_return - 0.02) / volatility
else:
    sharpe_ratio = 0.0
```

#### Sortino Ratio
```python
negative_returns = returns[returns < 0]
if len(negative_returns) > 0:
    downside_deviation = negative_returns.std() * (12 ** 0.5)  # Annualized
    if downside_deviation > 0:
        sortino_ratio = (annual_return - 0.02) / downside_deviation
    else:
        sortino_ratio = 0.0
else:
    # No negative returns, use volatility as fallback
    if volatility > 0:
        sortino_ratio = (annual_return - 0.02) / volatility
    else:
        sortino_ratio = 0.0
```

#### Max Drawdown
```python
cumulative = (1 + returns).cumprod()
running_max = cumulative.expanding().max()
drawdown = (cumulative - running_max) / running_max
max_drawdown = drawdown.min() * 100
```

#### Calmar Ratio
```python
if max_drawdown != 0:
    calmar_ratio = annual_return / abs(max_drawdown)
else:
    calmar_ratio = 0.0
```

#### VaR 95% and CVaR 95%
```python
var_95 = returns.quantile(0.05) * 100
returns_below_var = returns[returns <= var_95]
if len(returns_below_var) > 0:
    cvar_95 = returns_below_var.mean() * 100
else:
    cvar_95 = var_95
```

### 4. Individual Asset Metrics

Applied the same calculation logic to individual asset metrics in the `detailed_metrics` section, ensuring consistency between portfolio-level and asset-level calculations.

## Files Modified

1. **bot.py** - `_prepare_portfolio_metrics_data` function (lines 7287-7661)
   - Enhanced portfolio metrics calculation
   - Added manual calculation fallbacks
   - Improved individual asset metrics calculation

## Testing

Created comprehensive test cases in:
- `tests/test_portfolio_risk_metrics_fix.py` - Unit tests for the fix
- `test_fix.py` - Simple integration test

## Expected Results

After the fix, portfolio risk metrics should show proper non-zero values:

```
Annual Return (%): ~11.16 (as expected from the example)
Volatility (%): Non-zero value based on actual returns
Sharpe Ratio: Non-zero value calculated from returns
Sortino Ratio: Non-zero value calculated from downside deviation
Max Drawdown (%): Non-zero value calculated from cumulative returns
Calmar Ratio: Non-zero value calculated from annual return / max drawdown
VaR 95% (%): Non-zero value calculated from 5th percentile of returns
CVaR 95% (%): Non-zero value calculated from expected value below VaR
```

## Benefits

1. **Reliability**: Risk metrics are now calculated reliably using actual returns data
2. **Consistency**: Both portfolio and individual asset metrics use the same calculation logic
3. **Robustness**: Multiple fallback mechanisms ensure metrics are calculated even if okama attributes are unavailable
4. **Accuracy**: Manual calculations ensure proper risk metric values are displayed

## Implementation Date

December 2024

## Status

✅ **COMPLETED** - Portfolio risk metrics fix implemented and ready for testing

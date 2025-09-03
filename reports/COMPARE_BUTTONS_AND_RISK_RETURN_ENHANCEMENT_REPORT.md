# Compare Buttons and Risk/Return Enhancement Report

## Summary

Implemented conditional button rendering for the `/compare` command and added a new portfolio-only action "Risk / Return" that produces a CAGR chart.

## Changes

- Hid buttons for mixed comparisons (portfolios + assets):
  - 📉 Drawdowns
  - 💰 Dividends
  - 🔗 Correlation Matrix

- Added new button for portfolio-only comparisons:
  - 📊 Risk / Return (callback: `risk_return_compare`)

- Implemented handler `_handle_risk_return_compare_button` to build a CAGR visualization:
  - Primary: uses `ok.AssetList(...).plot_assets(kind="cagr")` and applies unified styling.
  - Fallback: computes CAGR for each portfolio and renders a bar chart via `chart_styles.create_bar_chart`.

## Files Modified

- `bot.py`
  - Conditional keyboard in `compare_command` based on composition of `expanded_symbols`.
  - New callback branch for `risk_return_compare`.
  - New method `_handle_risk_return_compare_button`.

## User Impact

- When comparing a portfolio with assets together, only the main comparison chart is shown (no drawdowns/dividends/correlation buttons) to avoid unsupported flows.
- When comparing only portfolios, a new "📊 Risk / Return" button appears, generating a CAGR-centric chart.

## Testing Notes

1. Portfolio + Asset: `/compare PF_1 SPY.US`
   - Expect: No drawdowns/dividends/correlation buttons. No Risk/Return button.

2. Portfolio + Portfolio: `/compare PF_1 PF_2`
   - Expect: Drawdowns/Dividends/Correlation buttons present.
   - Expect: New "📊 Risk / Return" button present.
   - Press Risk/Return: chart renders; if okama plotting fails, fallback bar renders.

3. Assets only: `/compare SPY.US QQQ.US`
   - Expect: Drawdowns/Dividends/Correlation buttons present.
   - No Risk/Return button.

## Notes

- Caption lengths are truncated via `_truncate_caption`.
- All changes follow existing styles and do not alter unrelated functionality.


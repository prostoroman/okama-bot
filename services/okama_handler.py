"""
Okama Handler

Executes data retrieval and computations for intents:
- asset_single
- asset_compare
- portfolio
- inflation
- macro (delegates to single/compare behaviors)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import logging
import io

import numpy as np
import pandas as pd
import okama as ok

logger = logging.getLogger(__name__)


def _compute_metrics_from_prices(prices: pd.Series, risk_free_rate_annual: float = 0.0) -> Dict[str, Any]:
    # Convert prices to periodic returns (monthly if index is Period/Date)
    returns = prices.pct_change().dropna()
    if returns.empty:
        return {"cagr": None, "volatility": None, "sharpe": None, "max_drawdown": None}

    # CAGR
    n_years = max(1e-9, (prices.index[-1] - prices.index[0]).days / 365.25) if hasattr(prices.index[0], "to_pydatetime") else len(returns) / 12.0
    total_return = (prices.iloc[-1] / prices.iloc[0]) - 1.0
    cagr = (1.0 + total_return) ** (1.0 / n_years) - 1.0 if total_return > -0.9999 else None

    # Volatility annualized (assume daily if many points, else monthly)
    periods_per_year = 252 if len(returns) > 200 else (12 if len(returns) > 20 else 52)
    vol = float(np.std(returns, ddof=1)) * np.sqrt(periods_per_year)

    # Sharpe
    mean_return = float(np.mean(returns)) * periods_per_year
    sharpe = (mean_return - risk_free_rate_annual) / vol if vol > 0 else None

    # Max drawdown
    cummax = prices.cummax()
    drawdowns = prices / cummax - 1.0
    max_dd = float(drawdowns.min()) if len(drawdowns) else None

    return {
        "cagr": cagr,
        "volatility": vol,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "total_return": total_return,
    }


class OkamaHandler:
    def get_single_asset(self, ticker: str, base_currency: Optional[str] = None) -> Dict[str, Any]:
        asset = ok.Asset(ticker)
        price: pd.Series = asset.price
        info = {
            "ticker": ticker,
            "currency": getattr(asset, "currency", None),
            "name": getattr(asset, "name", None),
        }
        metrics = _compute_metrics_from_prices(price)
        info.update({
            "prices": price,
            "metrics": metrics,
        })
        return info

    def get_multiple_assets(self, tickers: List[str]) -> Dict[str, Any]:
        assets = [ok.Asset(t) for t in tickers]
        prices_df = pd.concat([a.price.rename(t) for a, t in zip(assets, tickers)], axis=1).dropna(how="all")
        returns_df = prices_df.pct_change().dropna(how="all")
        # Align columns
        prices_df = prices_df.dropna()
        returns_df = returns_df.dropna()
        metrics = {}
        for t in tickers:
            if t in prices_df:
                metrics[t] = _compute_metrics_from_prices(prices_df[t])
        corr = returns_df.corr().fillna(0.0) if not returns_df.empty else pd.DataFrame()
        return {
            "tickers": tickers,
            "prices": prices_df,
            "returns": returns_df,
            "metrics": metrics,
            "correlation": corr,
        }

    def get_portfolio(self, tickers: List[str], weights: Optional[List[float]] = None) -> Dict[str, Any]:
        if not tickers:
            raise ValueError("No tickers provided for portfolio")
        n = len(tickers)
        if not weights or len(weights) != n:
            weights = [1.0 / n] * n
        portfolio = ok.Portfolio(assets=tickers, weights=weights)
        # Portfolio performance
        prices: pd.Series = portfolio.nav
        ret = prices.pct_change().dropna()
        metrics = _compute_metrics_from_prices(prices)
        # Efficient frontier via okama
        try:
            ef = ok.EfficientFrontier(assets=tickers)
            frontier = ef.efficient_frontier()
        except Exception:
            frontier = None
        return {
            "tickers": tickers,
            "weights": weights,
            "portfolio_prices": prices,
            "portfolio_returns": ret,
            "metrics": metrics,
            "frontier": frontier,
        }

    def get_inflation(self, country: str = "US") -> Dict[str, Any]:
        # Okama supports inflation data via ok.Inflation? Fallback: use Asset INFL namespace
        # Try standard CPI tickers
        candidates = ["US.INFL", "RUS.INFL", "EU.INFL"]
        sel = candidates[0]
        for c in candidates:
            if country.lower().startswith("ru") and "RUS" in c:
                sel = c
            if country.lower().startswith("eu") and "EU" in c:
                sel = c
        try:
            a = ok.Asset(sel)
            cpi = a.price
        except Exception:
            # Fallback empty
            cpi = pd.Series(dtype=float)
        return {"ticker": sel, "cpi": cpi}


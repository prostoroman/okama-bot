"""
Report Builder

Builds charts and tables for analysis results. Returns PNG bytes for images and
simple text tables for Telegram delivery.
"""

from __future__ import annotations

from typing import Dict, List, Tuple, Any, Optional
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


class ReportBuilder:
    def _fig_to_png(self, fig) -> bytes:
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=160)
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def build_single_asset_report(self, info: Dict[str, Any]) -> Tuple[str, List[bytes]]:
        lines = []
        name = info.get("name") or info.get("ticker")
        metrics = info.get("metrics", {})
        lines.append(f"Актив: {name} ({info.get('ticker')})")
        lines.append(f"Валюта: {info.get('currency')}")
        if metrics:
            lines.append("Метрики:")
            lines.append(self._format_metrics(metrics))

        images: List[bytes] = []
        prices: pd.Series = info.get("prices")
        if isinstance(prices, pd.Series) and not prices.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(prices.index, prices.values, label="Цена")
            ax.set_title(f"Динамика цены: {name}")
            ax.legend()
            ax.grid(True, alpha=0.3)
            images.append(self._fig_to_png(fig))
        return "\n".join(lines), images

    def build_multi_asset_report(self, result: Dict[str, Any]) -> Tuple[str, List[bytes]]:
        tickers = result.get("tickers", [])
        lines = ["Сравнение активов:", ", ".join(tickers)]
        # Table for metrics
        metrics: Dict[str, Any] = result.get("metrics", {})
        if metrics:
            lines.append("\nМетрики:")
            lines.append(self._format_metrics_table(metrics))
        # Correlation
        corr = result.get("correlation")
        if isinstance(corr, pd.DataFrame) and not corr.empty:
            lines.append("\nКорреляции:")
            lines.append(corr.round(2).to_string())

        images: List[bytes] = []
        prices_df: pd.DataFrame = result.get("prices")
        if isinstance(prices_df, pd.DataFrame) and not prices_df.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            prices_df.dropna().plot(ax=ax)
            ax.set_title("Динамика цен")
            ax.grid(True, alpha=0.3)
            images.append(self._fig_to_png(fig))
        returns_df: pd.DataFrame = result.get("returns")
        if isinstance(returns_df, pd.DataFrame) and not returns_df.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            (1 + returns_df).cumprod().plot(ax=ax)
            ax.set_title("Накопленная доходность")
            ax.grid(True, alpha=0.3)
            images.append(self._fig_to_png(fig))
        return "\n".join(lines), images

    def build_portfolio_report(self, result: Dict[str, Any]) -> Tuple[str, List[bytes]]:
        tickers = result.get("tickers", [])
        weights = result.get("weights", [])
        metrics = result.get("metrics", {})
        lines = ["Портфель:", ", ".join(f"{t}:{w:.2f}" for t, w in zip(tickers, weights))]
        if metrics:
            lines.append("\nМетрики:")
            lines.append(self._format_metrics(metrics))
        images: List[bytes] = []
        prices: pd.Series = result.get("portfolio_prices")
        if isinstance(prices, pd.Series) and not prices.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(prices.index, prices.values)
            ax.set_title("Стоимость портфеля")
            ax.grid(True, alpha=0.3)
            images.append(self._fig_to_png(fig))
        frontier = result.get("frontier")
        if isinstance(frontier, pd.DataFrame) and not frontier.empty and {"vol", "ret"}.issubset(frontier.columns):
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(frontier["vol"], frontier["ret"], s=8)
            ax.set_xlabel("Риск (волатильность)")
            ax.set_ylabel("Доходность")
            ax.set_title("Efficient Frontier")
            ax.grid(True, alpha=0.3)
            images.append(self._fig_to_png(fig))
        return "\n".join(lines), images

    def build_inflation_report(self, result: Dict[str, Any]) -> Tuple[str, List[bytes]]:
        lines = [f"Инфляция: {result.get('ticker')}"]
        images: List[bytes] = []
        cpi: pd.Series = result.get("cpi")
        if isinstance(cpi, pd.Series) and not cpi.empty:
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.plot(cpi.index, cpi.values)
            ax.set_title("Индекс потребительских цен (CPI)")
            ax.grid(True, alpha=0.3)
            images.append(self._fig_to_png(fig))
        return "\n".join(lines), images

    def _format_metrics(self, m: Dict[str, Any]) -> str:
        parts = []
        if m.get("cagr") is not None:
            parts.append(f"CAGR: {m['cagr']*100:.2f}%")
        if m.get("volatility") is not None:
            parts.append(f"Волатильность: {m['volatility']*100:.2f}%")
        if m.get("sharpe") is not None:
            parts.append(f"Sharpe: {m['sharpe']:.2f}")
        if m.get("max_drawdown") is not None:
            parts.append(f"Макс. просадка: {m['max_drawdown']*100:.2f}%")
        if m.get("total_return") is not None:
            parts.append(f"Общая доходность: {m['total_return']*100:.2f}%")
        return "; ".join(parts) if parts else "Нет данных"

    def _format_metrics_table(self, metrics: Dict[str, Dict[str, Any]]) -> str:
        rows = []
        for t, m in metrics.items():
            rows.append({
                "Тикер": t,
                "CAGR,%": f"{(m.get('cagr') or 0)*100:.2f}",
                "Волатильность,%": f"{(m.get('volatility') or 0)*100:.2f}",
                "Sharpe": f"{(m.get('sharpe') or 0):.2f}",
                "Макс. просадка,%": f"{(m.get('max_drawdown') or 0)*100:.2f}",
            })
        if not rows:
            return "Нет данных"
        df = pd.DataFrame(rows)
        return df.to_string(index=False)


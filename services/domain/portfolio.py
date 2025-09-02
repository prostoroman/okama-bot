from __future__ import annotations

from typing import List, Optional
import io

from services.chart_styles import chart_styles


class Portfolio:
    """Domain object wrapping okama.Portfolio with a clean API."""

    def __init__(self, symbols: List[str], weights: Optional[List[float]] = None, currency: Optional[str] = None) -> None:
        self.symbols = [s.upper() for s in (symbols or [])]
        self.weights = self._normalize_weights(weights, len(self.symbols))
        self.currency = currency
        self._portfolio = None  # Lazy

    @staticmethod
    def _normalize_weights(weights: Optional[List[float]], count: int) -> List[float]:
        if count <= 0:
            return []
        if not weights or len(weights) != count:
            return [1.0 / count] * count
        if any((w is None) or (w <= 0) for w in weights):
            return [1.0 / count] * count
        total = float(sum(weights))
        if total <= 0:
            return [1.0 / count] * count
        return [float(w) / total for w in weights]

    @staticmethod
    def _create_portfolio(symbols: List[str], weights: List[float], currency: Optional[str] = None):
        import okama as ok
        try:
            if currency is not None:
                return ok.Portfolio(assets=symbols, weights=weights, ccy=currency)
            return ok.Portfolio(assets=symbols, weights=weights)
        except TypeError:
            if currency is not None:
                try:
                    return ok.Portfolio(assets=symbols, weights=weights, currency=currency)
                except Exception:
                    return ok.Portfolio(assets=symbols, weights=weights)
            return ok.Portfolio(assets=symbols, weights=weights)

    def wealth_chart_png(self) -> bytes:
        if self._portfolio is None:
            self._portfolio = self._create_portfolio(self.symbols, self.weights, self.currency)
        data = self._portfolio.wealth_index
        fig, ax = chart_styles.create_portfolio_wealth_chart(data=data, symbols=self.symbols, currency=self.currency)
        buf = io.BytesIO()
        chart_styles.save_figure(fig, buf)
        chart_styles.cleanup_figure(fig)
        return buf.getvalue()

    @property
    def wealth_index(self):
        if self._portfolio is None:
            self._portfolio = self._create_portfolio(self.symbols, self.weights, self.currency)
        return self._portfolio.wealth_index

    @property
    def wealth_index_with_assets(self):
        if self._portfolio is None:
            self._portfolio = self._create_portfolio(self.symbols, self.weights, self.currency)
        return self._portfolio.wealth_index_with_assets


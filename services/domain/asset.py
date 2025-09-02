from __future__ import annotations

from typing import Any, Dict, Optional
import io

from services.chart_styles import chart_styles


class Asset:
    """Domain object for working with single assets via okama.

    This class is framework-agnostic and can be used from bots or web apps.
    """

    def __init__(self, symbol: str, currency: Optional[str] = None) -> None:
        self.symbol = symbol.upper()
        self.currency = currency
        self._asset = None  # Lazy

    @staticmethod
    def _create_asset(symbol: str, currency: Optional[str] = None):
        import okama as ok
        try:
            if currency is not None:
                return ok.Asset(symbol, ccy=currency)
            return ok.Asset(symbol)
        except TypeError:
            if currency is not None:
                try:
                    return ok.Asset(symbol, currency)
                except Exception:
                    return ok.Asset(symbol)
            return ok.Asset(symbol)

    def to_dict(self) -> Dict[str, Any]:
        return {"symbol": self.symbol, "currency": self.currency}

    def price_chart_png(self) -> bytes:
        if self._asset is None:
            self._asset = self._create_asset(self.symbol, self.currency)
        series = self._asset.close_prices()
        fig, ax = chart_styles.create_price_chart(series=series, symbol=self.symbol)
        buf = io.BytesIO()
        chart_styles.save_figure(fig, buf)
        chart_styles.cleanup_figure(fig)
        return buf.getvalue()

    def dividends_chart_png(self) -> Optional[bytes]:
        if self._asset is None:
            self._asset = self._create_asset(self.symbol, self.currency)
        try:
            divs = self._asset.dividends
        except Exception:
            return None
        if divs is None:
            return None
        fig, ax = chart_styles.create_dividends_chart(dividends=divs, symbol=self.symbol)
        buf = io.BytesIO()
        chart_styles.save_figure(fig, buf)
        chart_styles.cleanup_figure(fig)
        return buf.getvalue()


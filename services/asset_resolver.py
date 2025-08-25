"""
Asset Resolver

Maps user-provided asset names/tickers to Okama-compatible tickers and classifies
their asset class. Also validates availability in Okama.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional
import re
import logging
import okama as ok

logger = logging.getLogger(__name__)


ASSET_CLASS_SUFFIXES = [
    "US", "MOEX", "COMM", "INDX", "FX", "INFL", "CBR", "CC", "LSE",
    "RATE", "RATIO", "RE", "XAMS", "XETR", "XFRA", "XSTU", "XTAE", "PF", "PIF"
]


COMMON_NAME_TO_TICKER: Dict[str, str] = {
    # English
    "apple": "AAPL.US",
    "tesla": "TSLA.US",
    "microsoft": "MSFT.US",
    "google": "GOOGL.US",
    "amazon": "AMZN.US",
    "s&p": "SPX.INDX",
    "sp500": "SPX.INDX",
    "nasdaq": "IXIC.INDX",
    "gold": "XAU.COMM",
    "silver": "XAG.COMM",
    "oil": "BRENT.COMM",
    "brent": "BRENT.COMM",
    "wti": "CL.COMM",
    "eurusd": "EURUSD.FX",
    "gbpusd": "GBPUSD.FX",
    # Russian
    "сбер": "SBER.MOEX",
    "сбербанк": "SBER.MOEX",
    "газпром": "GAZP.MOEX",
    "лукойл": "LKOH.MOEX",
    "золото": "XAU.COMM",
    "серебро": "XAG.COMM",
    "нефть": "BRENT.COMM",
    "ртс": "RTSI.INDX",
    "мосбиржа": "RGBITR.INDX",
}


@dataclass
class ResolvedAsset:
    raw: str
    ticker: str
    asset_class: str
    valid: bool
    name: Optional[str] = None


class AssetResolver:
    """Resolve asset mentions to Okama tickers and classes, validate availability."""

    def resolve(self, raw_assets: List[str]) -> List[ResolvedAsset]:
        resolved: List[ResolvedAsset] = []
        for token in raw_assets:
            candidate = self._normalize_candidate(token)
            ticker, asset_class, valid = self._resolve_one(candidate)
            name = None
            if valid:
                try:
                    a = ok.Asset(ticker)
                    name = getattr(a, "name", None)
                except Exception:
                    pass
            resolved.append(ResolvedAsset(raw=token, ticker=ticker, asset_class=asset_class, valid=valid, name=name))
        return resolved

    def _normalize_candidate(self, token: str) -> str:
        t = token.strip().upper()
        # Map common names
        key = re.sub(r"\s+", "", t.lower())
        if key in COMMON_NAME_TO_TICKER:
            return COMMON_NAME_TO_TICKER[key]
        # Keep as-is, later try suffixes
        return t

    def _resolve_one(self, candidate: str) -> (str, str, bool):
        # If candidate already has .SUFFIX
        if "." in candidate:
            symbol, suffix = candidate.rsplit(".", 1)
            if suffix in ASSET_CLASS_SUFFIXES:
                ticker = f"{symbol}.{suffix}"
                return ticker, suffix, self._is_valid(ticker)
        # Try common suffixes order
        for suffix in ["US", "MOEX", "INDX", "COMM", "FX", "INFL"]:
            ticker = f"{candidate}.{suffix}" if "." not in candidate else candidate
            if self._is_valid(ticker):
                return ticker, suffix, True
        # Try as given without suffix (some okama assets might be bare)
        if self._is_valid(candidate):
            return candidate, "UNKNOWN", True
        # Fallback to mapping if partial match exists
        for k, v in COMMON_NAME_TO_TICKER.items():
            if k in candidate.lower():
                return v, v.rsplit(".", 1)[-1], self._is_valid(v)
        # Unresolved
        return candidate, "UNKNOWN", False

    def _is_valid(self, ticker: str) -> bool:
        try:
            ok.Asset(ticker)  # Will raise if invalid
            return True
        except Exception:
            return False


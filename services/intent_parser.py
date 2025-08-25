"""
Intent Parser module

Determines user's intent and extracts high-level entities from free-form text.

Intents supported:
- asset_single: information about one asset
- asset_compare: compare multiple assets
- portfolio: portfolio analysis
- inflation: inflation data
- macro: macro instruments (FX, commodities, indexes)
- chat: fallback general chat

This parser is rule-based and language-aware (RU/EN keywords). It returns a
structured result which is further resolved by asset_resolver.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class ParsedIntent:
    intent: str
    raw_assets: List[str]
    options: Dict[str, str]


class IntentParser:
    """Lightweight intent parser with heuristics for investment queries."""

    _ASSET_TOKEN_PATTERN = re.compile(r"\b([A-Za-zА-Яа-я0-9]{2,}[./]?[A-Za-z]{0,5})\b")

    def parse(self, text: str) -> ParsedIntent:
        message = text.strip()
        lower = message.lower()

        # Extract possible asset tokens (tickers, names). Actual resolution happens later
        raw_assets = self._extract_raw_assets(message)

        # Detect portfolio intent
        if any(k in lower for k in [
            "портфель", "portfolio", "веса", "weights", "ребаланс", "rebalance", "efficient frontier", "эффективная граница"
        ]):
            return ParsedIntent(intent="portfolio", raw_assets=raw_assets, options=self._extract_options(lower))

        # Inflation intent
        if any(k in lower for k in ["инфляц", "inflation", "cpi"]):
            return ParsedIntent(intent="inflation", raw_assets=raw_assets, options=self._extract_options(lower))

        # Compare intent
        if any(k in lower for k in ["compare", "сравн", "vs", "против"]):
            return ParsedIntent(intent="asset_compare", raw_assets=raw_assets, options=self._extract_options(lower))

        # Macro buckets by keywords
        if any(k in lower for k in ["fx", "валют", "currency", "forex"]):
            return ParsedIntent(intent="macro", raw_assets=raw_assets, options={"class": "FX"})
        if any(k in lower for k in ["commodit", "сырь", "товар", "gold", "oil", "нефть", "золото", "серебро"]):
            return ParsedIntent(intent="macro", raw_assets=raw_assets, options={"class": "COMM"})
        if any(k in lower for k in ["index", "индекс", "индексы", "s&p", "nasdaq", "moex", "рцб", "rts"]):
            return ParsedIntent(intent="macro", raw_assets=raw_assets, options={"class": "INDX"})

        # Asset single vs multi (if multiple clear assets without explicit compare -> compare)
        if len(raw_assets) > 1:
            return ParsedIntent(intent="asset_compare", raw_assets=raw_assets, options=self._extract_options(lower))
        if len(raw_assets) == 1:
            return ParsedIntent(intent="asset_single", raw_assets=raw_assets, options=self._extract_options(lower))

        # Default to chat
        return ParsedIntent(intent="chat", raw_assets=[], options={})

    def _extract_raw_assets(self, text: str) -> List[str]:
        # Split by commas and common separators first to catch phrases like "AAPL, MSFT vs GOOG"
        tokens = re.split(r"[\s,;]+", text)
        candidates: List[str] = []
        for token in tokens:
            token_clean = token.strip().strip("()[]{}:;,.!?\"'`")
            if not token_clean:
                continue
            if self._looks_like_symbol(token_clean) or self._looks_like_name(token_clean):
                candidates.append(token_clean)
        # Deduplicate preserving order
        seen = set()
        result = []
        for c in candidates:
            if c.lower() not in seen:
                seen.add(c.lower())
                result.append(c)
        return result[:20]

    def _looks_like_symbol(self, token: str) -> bool:
        # Okama symbols often look like TICKER.NS where NS in {US, MOEX, INDX, COMM, FX, INFL}
        return bool(re.match(r"^[A-Za-z0-9]{1,8}(\.[A-Za-z]{2,6})?$", token))

    def _looks_like_name(self, token: str) -> bool:
        # Catch common asset name words (Apple, Tesla, Сбербанк)
        return bool(re.match(r"^[A-Za-zА-Яа-я][A-Za-zА-Яа-я0-9\-]{2,}$", token))

    def _extract_options(self, lower_text: str) -> Dict[str, str]:
        options: Dict[str, str] = {}
        # Base currency extraction (e.g., in USD/EUR/RUB)
        if "usd" in lower_text:
            options["base_currency"] = "USD"
        if "eur" in lower_text:
            options["base_currency"] = "EUR"
        if any(k in lower_text for k in ["rub", "руб", "р","₽"]):
            options["base_currency"] = "RUB"
        # Period hints
        m = re.search(r"(\d{4})\s*[-–]\s*(\d{4})", lower_text)
        if m:
            options["period"] = f"{m.group(1)}-{m.group(2)}"
        elif "ytd" in lower_text:
            options["period"] = "YTD"
        elif "1y" in lower_text or "1 г" in lower_text or "1 год" in lower_text:
            options["period"] = "1Y"
        elif "3y" in lower_text or "3 г" in lower_text:
            options["period"] = "3Y"
        elif "5y" in lower_text or "5 л" in lower_text or "5 лет" in lower_text:
            options["period"] = "5Y"
        return options


"""
User context persistence utilities.

Provides a simple, thread-safe JSON-backed store to persist user-specific context
between bot invocations. Designed to be framework-agnostic and reusable in other
apps (e.g., web) by exposing a clean interface.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict, Optional


class JSONUserContextStore:
    """Thread-safe JSON-backed user context store.

    Schema is flexible; callers can store arbitrary JSON-serializable values
    per user_id. This class ensures file-level locking and atomic writes.
    """

    def __init__(self, filepath: str = "/workspace/.user_context.json") -> None:
        self._filepath = filepath
        self._lock = threading.RLock()
        # Ensure directory exists
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)
        # Lazily created on first write; attempt to load now for validation
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        with self._lock:
            try:
                if os.path.exists(self._filepath) and os.path.getsize(self._filepath) > 0:
                    with open(self._filepath, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                        if isinstance(raw, dict):
                            self._data = raw  # type: ignore[assignment]
                        else:
                            # Reset to empty if corrupted type
                            self._data = {}
                else:
                    self._data = {}
            except Exception:
                # Be resilient to malformed files
                self._data = {}

    def _atomic_write(self) -> None:
        with self._lock:
            tmp_path = f"{self._filepath}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2, sort_keys=True)
            os.replace(tmp_path, self._filepath)

    def get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Return context dict for user, creating default if missing."""
        key = str(user_id)
        with self._lock:
            ctx = self._data.get(key)
            if ctx is None:
                ctx = {
                    "last_assets": [],
                    "last_analysis_type": None,
                    "last_period": None,
                    "conversation_history": [],
                    "preferences": {},
                    "portfolio_count": 0,
                    # {symbol: {symbols, weights, currency, created_at, description, portfolio_symbol}}
                    "saved_portfolios": {},
                    # Common volatile runtime keys used by buttons
                    "current_symbols": [],
                    "current_currency": None,
                    "current_currency_info": None,
                }
                self._data[key] = ctx
                self._atomic_write()
            return ctx

    def update_user_context(self, user_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update and persist fields for a user's context. Returns updated dict."""
        key = str(user_id)
        with self._lock:
            ctx = self.get_user_context(user_id)
            ctx.update(kwargs)
            # Trim conversation history if present
            conv = ctx.get("conversation_history")
            if isinstance(conv, list) and len(conv) > 10:
                ctx["conversation_history"] = conv[-10:]
            self._data[key] = ctx
            self._atomic_write()
            return ctx

    def add_conversation_entry(self, user_id: int, message: str, response: str) -> None:
        """Append a conversation record and persist."""
        entry = {
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "message": message,
            "response": (response or "")[:200],
        }
        key = str(user_id)
        with self._lock:
            ctx = self.get_user_context(user_id)
            history = ctx.get("conversation_history")
            if not isinstance(history, list):
                history = []
            history.append(entry)
            if len(history) > 10:
                history = history[-10:]
            ctx["conversation_history"] = history
            self._data[key] = ctx
            self._atomic_write()

    def clear(self) -> None:
        """Clear all contexts (useful for tests)."""
        with self._lock:
            self._data = {}
            self._atomic_write()


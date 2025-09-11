"""
User context persistence utilities.

Provides a simple, thread-safe in-memory store to persist user-specific context
between bot invocations within a single session. Designed to be framework-agnostic 
and reusable in other apps (e.g., web) by exposing a clean interface.

Note: This implementation uses in-memory storage only, suitable for ephemeral
environments like Render where filesystem persistence is not reliable.
"""

from __future__ import annotations

import threading
from typing import Any, Dict, Optional
from datetime import datetime


class InMemoryUserContextStore:
    """Thread-safe in-memory user context store.

    Schema is flexible; callers can store arbitrary JSON-serializable values
    per user_id. This class ensures thread-safe operations without filesystem dependencies.
    
    Note: Data is lost on application restart, but this is acceptable for ephemeral
    environments where filesystem persistence is not reliable.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

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
                    # Compare command context
                    "compare_first_symbol": None,
                    "compare_base_symbol": None,
                    "waiting_for_compare": False,
                }
                self._data[key] = ctx
            return ctx

    def update_user_context(self, user_id: int, **kwargs: Any) -> Dict[str, Any]:
        """Update fields for a user's context. Returns updated dict."""
        key = str(user_id)
        with self._lock:
            ctx = self.get_user_context(user_id)
            ctx.update(kwargs)
            # Trim conversation history if present
            conv = ctx.get("conversation_history")
            if isinstance(conv, list) and len(conv) > 10:
                ctx["conversation_history"] = conv[-10:]
            self._data[key] = ctx
            return ctx

    def add_conversation_entry(self, user_id: int, message: str, response: str) -> None:
        """Append a conversation record."""
        entry = {
            "timestamp": datetime.now().isoformat(),
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

    def clear(self) -> None:
        """Clear all contexts (useful for tests)."""
        with self._lock:
            self._data = {}

    def get_all_users(self) -> list[int]:
        """Get list of all user IDs that have context."""
        with self._lock:
            return [int(key) for key in self._data.keys()]

    def remove_user(self, user_id: int) -> bool:
        """Remove context for a specific user. Returns True if user existed."""
        key = str(user_id)
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False


# Alias for backward compatibility
JSONUserContextStore = InMemoryUserContextStore


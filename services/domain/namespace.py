from __future__ import annotations

from typing import List
import okama as ok


class Namespace:
    """Domain object for working with okama namespaces."""

    @staticmethod
    def list_namespaces() -> dict:
        return ok.namespaces

    @staticmethod
    def symbols_in(namespace: str) -> List[str]:
        df = ok.symbols_in_namespace(namespace)
        # Try common structures
        try:
            if hasattr(df, "__getitem__"):
                col = df["symbol"]
                try:
                    return list(col.astype(str))
                except Exception:
                    return list(col)
        except Exception:
            pass
        # iloc fallback
        try:
            col0 = df.iloc[:, 0]
            try:
                return list(col0.astype(str))
            except Exception:
                return list(col0)
        except Exception:
            pass
        # As a very last resort return empty
        return []


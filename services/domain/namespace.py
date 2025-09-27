from __future__ import annotations

from typing import List
import logging

from services.okama_service import okama_service

logger = logging.getLogger(__name__)


class Namespace:
    """Domain object for working with okama namespaces."""

    @staticmethod
    def list_namespaces() -> dict:
        """Get list of available namespaces with retry logic."""
        try:
            return okama_service.get_namespaces()
        except Exception as e:
            logger.error(f"Failed to get OKAMA namespaces: {e}")
            raise e

    @staticmethod
    def symbols_in(namespace: str) -> List[str]:
        """Get symbols in a namespace with retry logic and error handling."""
        try:
            df = okama_service.symbols_in_namespace(namespace)
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
        except Exception as e:
            logger.error(f"Failed to get symbols in namespace {namespace}: {e}")
            raise e


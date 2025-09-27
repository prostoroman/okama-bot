"""
OKAMA Service Module
Robust wrapper for OKAMA API calls with retry logic and error handling
"""

import time
import logging
from typing import Any, Dict, List, Optional, Union
from functools import wraps
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from services.cached_data_service import cached_data_service

logger = logging.getLogger(__name__)


class OkamaService:
    """
    Service wrapper for OKAMA API calls with retry logic and error handling.
    Handles 502 errors and other API failures gracefully.
    """
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 1.0):
        """
        Initialize OKAMA service with retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Backoff factor for exponential backoff
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[502, 503, 504, 429],  # Retry on these status codes
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result or raises last exception
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if it's a retryable error
                if not self._is_retryable_error(e):
                    logger.error(f"Non-retryable error in OKAMA call: {e}")
                    raise e
                
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor * (2 ** attempt)
                    logger.warning(f"OKAMA API call failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                    logger.info(f"Retrying in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"OKAMA API call failed after {self.max_retries + 1} attempts: {e}")
        
        raise last_exception
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Check if an error is retryable.
        
        Args:
            error: Exception to check
            
        Returns:
            True if error is retryable, False otherwise
        """
        error_str = str(error).lower()
        
        # Check for specific retryable error patterns
        retryable_patterns = [
            '502',
            '503', 
            '504',
            '429',
            'timeout',
            'connection',
            'max retries exceeded',
            'too many',
            'bad gateway',
            'service unavailable',
            'gateway timeout'
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)
    
    def create_asset(self, symbol: str, currency: Optional[str] = None):
        """
        Create an OKAMA Asset with retry logic.
        
        Args:
            symbol: Asset symbol
            currency: Optional currency
            
        Returns:
            OKAMA Asset object
            
        Raises:
            Exception: If all retry attempts fail
        """
        import okama as ok
        
        def _create():
            if currency is not None:
                return ok.Asset(symbol, ccy=currency)
            return ok.Asset(symbol)
        
        return self._retry_with_backoff(_create)
    
    def create_asset_list(self, symbols: List[str], currency: Optional[str] = None, 
                         inflation: bool = True, first_date: Optional[str] = None, 
                         last_date: Optional[str] = None):
        """
        Create an OKAMA AssetList with retry logic and fallback.
        
        Args:
            symbols: List of asset symbols
            currency: Optional currency
            inflation: Whether to include inflation
            first_date: Optional start date
            last_date: Optional end date
            
        Returns:
            OKAMA AssetList object
            
        Raises:
            Exception: If all retry attempts fail and no fallback is available
        """
        import okama as ok
        
        def _create():
            kwargs = {'inflation': inflation}
            if currency:
                kwargs['ccy'] = currency
            if first_date:
                kwargs['first_date'] = first_date
            if last_date:
                kwargs['last_date'] = last_date
            
            return ok.AssetList(symbols, **kwargs)
        
        try:
            return self._retry_with_backoff(_create)
        except Exception as e:
            # If API fails completely, try to provide helpful error message
            if cached_data_service.can_provide_fallback():
                logger.warning(f"OKAMA API failed, but cached data is available: {e}")
                # Re-raise with more helpful message
                raise Exception(f"{cached_data_service.get_fallback_error_message()}")
            else:
                logger.error(f"OKAMA API failed and no fallback available: {e}")
                raise e
    
    def search_assets(self, query: str):
        """
        Search assets in OKAMA database with retry logic.
        
        Args:
            query: Search query
            
        Returns:
            Search results DataFrame
            
        Raises:
            Exception: If all retry attempts fail
        """
        import okama as ok
        
        def _search():
            return ok.search(query)
        
        return self._retry_with_backoff(_search)
    
    def get_namespaces(self):
        """
        Get available namespaces with retry logic.
        
        Returns:
            Namespaces dictionary
            
        Raises:
            Exception: If all retry attempts fail
        """
        import okama as ok
        
        def _get():
            return ok.namespaces
        
        return self._retry_with_backoff(_get)
    
    def symbols_in_namespace(self, namespace: str):
        """
        Get symbols in a namespace with retry logic.
        
        Args:
            namespace: Namespace name
            
        Returns:
            Symbols DataFrame
            
        Raises:
            Exception: If all retry attempts fail
        """
        import okama as ok
        
        def _get():
            return ok.symbols_in_namespace(namespace)
        
        return self._retry_with_backoff(_get)
    
    def create_rate(self, symbol: str):
        """
        Create an OKAMA Rate object with retry logic.
        
        Args:
            symbol: Rate symbol
            
        Returns:
            OKAMA Rate object
            
        Raises:
            Exception: If all retry attempts fail
        """
        import okama as ok
        
        def _create():
            return ok.Rate(symbol)
        
        return self._retry_with_backoff(_create)
    
    def is_api_available(self) -> bool:
        """
        Check if OKAMA API is available.
        
        Returns:
            True if API is available, False otherwise
        """
        try:
            # Try a simple operation to test API availability
            self.get_namespaces()
            return True
        except Exception as e:
            logger.warning(f"OKAMA API availability check failed: {e}")
            return False
    
    def get_api_status(self) -> Dict[str, Any]:
        """
        Get detailed API status information.
        
        Returns:
            Dictionary with API status information
        """
        status = {
            'available': False,
            'error': None,
            'response_time': None,
            'fallback_available': cached_data_service.can_provide_fallback()
        }
        
        try:
            start_time = time.time()
            self.get_namespaces()
            end_time = time.time()
            
            status['available'] = True
            status['response_time'] = end_time - start_time
            
        except Exception as e:
            status['error'] = str(e)
        
        return status
    
    def update_cache_on_success(self, asset_data: Dict[str, Any] = None, namespace_data: Dict[str, Any] = None):
        """
        Update cache when successful API calls are made.
        
        Args:
            asset_data: Asset data to cache
            namespace_data: Namespace data to cache
        """
        try:
            if asset_data or namespace_data:
                cached_data_service.update_cache(asset_data or {}, namespace_data or {})
                logger.info("Cache updated with successful API data")
        except Exception as e:
            logger.warning(f"Could not update cache: {e}")


# Global instance for use throughout the application
okama_service = OkamaService()


def with_okama_retry(func):
    """
    Decorator to add OKAMA retry logic to any function.
    
    Usage:
        @with_okama_retry
        def my_okama_function():
            import okama as ok
            return ok.some_function()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return okama_service._retry_with_backoff(func, *args, **kwargs)
    return wrapper

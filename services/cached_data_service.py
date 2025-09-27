"""
Cached Data Service
Provides fallback data when OKAMA API is unavailable
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)


class CachedDataService:
    """
    Service that provides cached financial data as fallback when OKAMA API is unavailable.
    """
    
    def __init__(self, cache_file: str = "/var/data/okama_cache.json"):
        """
        Initialize the cached data service.
        
        Args:
            cache_file: Path to the cache file
        """
        self.cache_file = cache_file
        self.cache_data = self._load_cache()
        self.cache_expiry_hours = 24  # Cache expires after 24 hours
        
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache data from file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    logger.info(f"Loaded cache with {len(cache_data.get('assets', {}))} assets")
                    return cache_data
        except Exception as e:
            logger.warning(f"Could not load cache file: {e}")
        
        return {
            'assets': {},
            'namespaces': {},
            'last_updated': None
        }
    
    def _save_cache(self):
        """Save cache data to file."""
        try:
            # Ensure the directory exists
            cache_dir = os.path.dirname(self.cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
                logger.info(f"Created cache directory: {cache_dir}")
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
            logger.info("Cache saved successfully")
        except Exception as e:
            logger.warning(f"Could not save cache file: {e}")
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self.cache_data.get('last_updated'):
            return False
        
        try:
            last_updated = datetime.fromisoformat(self.cache_data['last_updated'])
            expiry_time = last_updated + timedelta(hours=self.cache_expiry_hours)
            return datetime.now() < expiry_time
        except Exception:
            return False
    
    def update_cache(self, asset_data: Dict[str, Any], namespace_data: Dict[str, Any]):
        """
        Update cache with new data.
        
        Args:
            asset_data: Asset information to cache
            namespace_data: Namespace information to cache
        """
        self.cache_data['assets'].update(asset_data)
        self.cache_data['namespaces'].update(namespace_data)
        self.cache_data['last_updated'] = datetime.now().isoformat()
        self._save_cache()
    
    def get_cached_asset_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached asset information.
        
        Args:
            symbol: Asset symbol
            
        Returns:
            Cached asset information or None
        """
        if not self._is_cache_valid():
            logger.info("Cache is expired, cannot provide fallback data")
            return None
        
        return self.cache_data['assets'].get(symbol)
    
    def get_cached_namespaces(self) -> Optional[Dict[str, Any]]:
        """
        Get cached namespaces.
        
        Returns:
            Cached namespaces or None
        """
        if not self._is_cache_valid():
            logger.info("Cache is expired, cannot provide fallback data")
            return None
        
        return self.cache_data['namespaces']
    
    def get_fallback_error_message(self) -> str:
        """
        Get a fallback error message when OKAMA API is unavailable.
        
        Returns:
            User-friendly error message
        """
        if self._is_cache_valid():
            return ("Сервис OKAMA временно недоступен. "
                   "Используются кэшированные данные, которые могут быть неактуальными. "
                   "Попробуйте повторить запрос позже для получения актуальных данных.")
        else:
            return ("Сервис OKAMA временно недоступен и кэшированные данные устарели. "
                   "Попробуйте повторить запрос через несколько минут. "
                   "Если проблема сохраняется, возможно, ведутся технические работы.")
    
    def can_provide_fallback(self) -> bool:
        """
        Check if fallback data is available.
        
        Returns:
            True if fallback data is available, False otherwise
        """
        return self._is_cache_valid() and bool(self.cache_data.get('assets'))


# Global instance
cached_data_service = CachedDataService()

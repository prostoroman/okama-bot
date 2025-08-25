"""
Asset Service for Okama Finance Bot

This service provides methods for retrieving financial asset information
using the Okama library.
"""

import logging
from typing import Dict, Any, Optional
import okama as ok

logger = logging.getLogger(__name__)


class AssetService:
    """Service for retrieving asset information using Okama library"""
    
    def __init__(self):
        """Initialize the AssetService"""
        self.logger = logging.getLogger(__name__)
    
    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive asset information
        
        Args:
            symbol: Asset symbol (e.g., 'VOO.US', 'SPY.US')
            
        Returns:
            Dictionary containing asset information or error
        """
        try:
            self.logger.info(f"Getting asset info for {symbol}")
            
            # Create asset object
            asset = ok.Asset(symbol)
            
            # Get basic info
            info = {
                'name': getattr(asset, 'name', 'N/A'),
                'country': getattr(asset, 'country', 'N/A'),
                'exchange': getattr(asset, 'exchange', 'N/A'),
                'currency': getattr(asset, 'currency', 'N/A'),
                'type': getattr(asset, 'type', 'N/A'),
                'isin': getattr(asset, 'isin', 'N/A'),
                'first_date': getattr(asset, 'first_date', 'N/A'),
                'last_date': getattr(asset, 'last_date', 'N/A'),
                'period_length': 'N/A'
            }
            
            # Calculate period length if dates are available
            if info['first_date'] != 'N/A' and info['last_date'] != 'N/A':
                try:
                    from datetime import datetime
                    first = asset.first_date
                    last = asset.last_date
                    if hasattr(first, 'year') and hasattr(last, 'year'):
                        years = last.year - first.year
                        info['period_length'] = f"{years} лет"
                except:
                    pass
            
            # Get current price
            try:
                price_data = asset.price
                if price_data is not None and len(price_data) > 0:
                    info['current_price'] = price_data.iloc[-1]
            except:
                info['current_price'] = 'N/A'
            
            # Get performance metrics
            try:
                # Annual return
                annual_return = asset.get_annual_return()
                if annual_return is not None:
                    info['annual_return'] = f"{annual_return:.2%}"
                else:
                    info['annual_return'] = 'N/A'
            except:
                info['annual_return'] = 'N/A'
            
            try:
                # Total return
                total_return = asset.get_total_return()
                if total_return is not None:
                    info['total_return'] = f"{total_return:.2%}"
                else:
                    info['total_return'] = 'N/A'
            except:
                info['total_return'] = 'N/A'
            
            try:
                # Volatility
                volatility = asset.get_volatility()
                if volatility is not None:
                    info['volatility'] = f"{volatility:.2%}"
                else:
                    info['volatility'] = 'N/A'
            except:
                info['volatility'] = 'N/A'
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting asset info for {symbol}: {str(e)}")
            return {'error': f"Failed to get asset info: {str(e)}"}
    
    def get_asset_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current asset price
        
        Args:
            symbol: Asset symbol (e.g., 'VOO.US', 'SPY.US')
            
        Returns:
            Dictionary containing price information or error
        """
        try:
            self.logger.info(f"Getting asset price for {symbol}")
            
            # Create asset object
            asset = ok.Asset(symbol)
            
            # Get price data
            price_data = asset.price
            
            if price_data is None or len(price_data) == 0:
                return {'error': 'No price data available'}
            
            # Get latest price
            latest_price = price_data.iloc[-1]
            latest_date = price_data.index[-1]
            
            info = {
                'price': latest_price,
                'currency': getattr(asset, 'currency', ''),
                'timestamp': str(latest_date)
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting asset price for {symbol}: {str(e)}")
            return {'error': f"Failed to get asset price: {str(e)}"}
    
    def get_asset_dividends(self, symbol: str) -> Dict[str, Any]:
        """
        Get asset dividend history
        
        Args:
            symbol: Asset symbol (e.g., 'VOO.US', 'SPY.US')
            
        Returns:
            Dictionary containing dividend information or error
        """
        try:
            self.logger.info(f"Getting asset dividends for {symbol}")
            
            # Create asset object
            asset = ok.Asset(symbol)
            
            # Get dividend data
            dividend_data = asset.dividends
            
            if dividend_data is None or len(dividend_data) == 0:
                return {'error': 'No dividend data available'}
            
            # Convert to dictionary format
            dividends = {}
            for date, amount in dividend_data.items():
                dividends[str(date)] = amount
            
            info = {
                'currency': getattr(asset, 'currency', ''),
                'total_periods': len(dividend_data),
                'dividends': dividends
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting asset dividends for {symbol}: {str(e)}")
            return {'error': f"Failed to get asset dividends: {str(e)}"}

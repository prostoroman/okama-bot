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
        
        # Known working asset symbols for suggestions
        self.known_assets = {
            'US': ['VOO.US', 'SPY.US', 'QQQ.US', 'AGG.US', 'AAPL.US', 'TSLA.US', 'MSFT.US'],
            'INDX': ['RGBITR.INDX', 'MCFTR.INDX', 'SPX.INDX', 'IXIC.INDX'],
            'COMM': ['GC.COMM', 'SI.COMM', 'CL.COMM', 'BRENT.COMM'],
            'FX': ['EURUSD.FX', 'GBPUSD.FX', 'USDJPY.FX'],
            'MOEX': ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX'],
            'LSE': ['VOD.LSE', 'HSBA.LSE', 'BP.LSE']
        }
    
    def _get_asset_suggestions(self, symbol: str) -> str:
        """Get suggestions for alternative assets when the requested one is not found"""
        # Extract the namespace from the symbol (e.g., 'CC' from 'BTC.CC')
        if '.' in symbol:
            namespace = symbol.split('.')[-1]
        else:
            namespace = 'US'  # Default to US stocks
        
        suggestions = []
        
        # Add suggestions from the same namespace
        if namespace in self.known_assets:
            suggestions.extend(self.known_assets[namespace][:3])  # First 3 suggestions
        
        # Add suggestions from other popular namespaces
        if namespace != 'US' and 'US' in self.known_assets:
            suggestions.extend(self.known_assets['US'][:2])
        
        if namespace != 'INDX' and 'INDX' in self.known_assets:
            suggestions.extend(self.known_assets['INDX'][:2])
        
        if suggestions:
            return f"Попробуйте эти доступные активы:\n" + "\n".join([f"• {s}" for s in suggestions])
        else:
            return "Попробуйте популярные активы: VOO.US, SPY.US, RGBITR.INDX, GC.COMM"
    
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
            error_msg = str(e)
            self.logger.error(f"Error getting asset info for {symbol}: {error_msg}")
            
            # Check if it's a "not found" error
            if "not found" in error_msg.lower() or "404" in error_msg:
                suggestions = self._get_asset_suggestions(symbol)
                return {
                    'error': f"Актив {symbol} не найден в базе данных Okama.\n\n{suggestions}",
                    'suggestions': suggestions
                }
            else:
                return {'error': f"Ошибка при получении информации об активе: {error_msg}"}
    
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
            error_msg = str(e)
            self.logger.error(f"Error getting asset price for {symbol}: {error_msg}")
            
            # Check if it's a "not found" error
            if "not found" in error_msg.lower() or "404" in error_msg:
                suggestions = self._get_asset_suggestions(symbol)
                return {
                    'error': f"Актив {symbol} не найден в базе данных Okama.\n\n{suggestions}",
                    'suggestions': suggestions
                }
            else:
                return {'error': f"Ошибка при получении цены: {error_msg}"}
    
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
            error_msg = str(e)
            self.logger.error(f"Error getting asset dividends for {symbol}: {error_msg}")
            
            # Check if it's a "not found" error
            if "not found" in error_msg.lower() or "404" in error_msg:
                suggestions = self._get_asset_suggestions(symbol)
                return {
                    'error': f"Актив {symbol} не найден в базе данных Okama.\n\n{suggestions}",
                    'suggestions': suggestions
                }
            else:
                return {'error': f"Ошибка при получении дивидендов: {error_msg}"}

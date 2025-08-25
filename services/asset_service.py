import okama as ok
import pandas as pd
from typing import Dict, Optional

class AssetService:
    """Simple service for getting information about a single asset"""
    
    def __init__(self):
        pass
    
    def get_asset_info(self, symbol: str) -> Dict:
        """
        Get general information about a single asset
        
        Args:
            symbol (str): Asset symbol (e.g., "VOO.US")
            
        Returns:
            Dict: Asset information including basic details and metrics
        """
        try:
            # Create asset object
            asset = ok.Asset(symbol)
            
            # Get basic asset information
            asset_info = {
                'symbol': symbol,
                'name': asset.name,
                'country': asset.country,
                'exchange': asset.exchange,
                'currency': asset.currency,
                'type': asset.type,
                'isin': asset.isin,
                'first_date': asset.first_date,
                'last_date': asset.last_date,
                'period_length': asset.period_length
            }
            
            # Get live price (20 min delay)
            try:
                asset_info['current_price'] = asset.price
            except Exception as e:
                asset_info['current_price'] = f"Error: {str(e)}"
            
            # Get dividends history (last 10 entries)
            try:
                dividends = asset.dividends.tail(10)
                asset_info['recent_dividends'] = dividends.to_dict()
            except Exception as e:
                asset_info['recent_dividends'] = f"Error: {str(e)}"
            
            # Get basic performance metrics
            try:
                # Annual return (CAGR)
                if hasattr(asset, 'get_cagr'):
                    cagr = asset.get_cagr()
                    asset_info['annual_return'] = f"{cagr:.2%}" if isinstance(cagr, (int, float)) else 'N/A'
                else:
                    asset_info['annual_return'] = 'N/A'
            except Exception as e:
                asset_info['annual_return'] = f"Error: {str(e)}"
            
            try:
                # Total return
                if hasattr(asset, 'get_cumulative_return'):
                    total_return = asset.get_cumulative_return()
                    asset_info['total_return'] = f"{total_return:.2%}" if isinstance(total_return, (int, float)) else 'N/A'
                else:
                    asset_info['total_return'] = 'N/A'
            except Exception as e:
                asset_info['total_return'] = f"Error: {str(e)}"
            
            try:
                # Volatility
                if hasattr(asset, 'ror') and asset.ror is not None:
                    volatility = asset.ror.std() * (12 ** 0.5)  # Annualize monthly volatility
                    asset_info['volatility'] = f"{volatility:.2%}"
                else:
                    asset_info['volatility'] = 'N/A'
            except Exception as e:
                asset_info['volatility'] = f"Error: {str(e)}"
            
            return asset_info
            
        except Exception as e:
            return {
                'symbol': symbol,
                'error': f"Failed to get asset information: {str(e)}"
            }
    
    def get_asset_price(self, symbol: str) -> Dict:
        """
        Get current price of an asset
        
        Args:
            symbol (str): Asset symbol
            
        Returns:
            Dict: Price information
        """
        try:
            asset = ok.Asset(symbol)
            price = asset.price
            
            return {
                'symbol': symbol,
                'price': price,
                'currency': asset.currency,
                'timestamp': 'Live (20 min delay)'
            }
        except Exception as e:
            return {
                'symbol': symbol,
                'error': f"Failed to get price: {str(e)}"
            }
    
    def get_asset_dividends(self, symbol: str, periods: int = 10) -> Dict:
        """
        Get dividend history for an asset
        
        Args:
            symbol (str): Asset symbol
            periods (int): Number of recent periods to return
            
        Returns:
            Dict: Dividend information
        """
        try:
            asset = ok.Asset(symbol)
            dividends = asset.dividends.tail(periods)
            
            return {
                'symbol': symbol,
                'dividends': dividends.to_dict(),
                'total_periods': len(dividends),
                'currency': asset.currency
            }
        except Exception as e:
            return {
                'symbol': symbol,
                'error': f"Failed to get dividends: {str(e)}"
            }

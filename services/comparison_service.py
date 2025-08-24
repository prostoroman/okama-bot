import okama as ok
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from typing import List, Dict, Tuple
import warnings

warnings.filterwarnings('ignore')

class ComparisonService:
    """Service for asset comparison analysis"""
    
    def __init__(self):
        self.plt_style = 'seaborn-v0_8'
        plt.style.use(self.plt_style)
    
    def compare_assets(self, symbols: List[str]) -> Tuple[Dict, bytes]:
        """Compare multiple assets and generate comparison chart using correct Okama v1.5.0 API"""
        try:
            assets_data = {}
            comparison_metrics = {}
            
            for symbol in symbols:
                try:
                    asset = ok.Asset(symbol)
                    
                    # Try to get price data with fallback using correct Okama v1.5.0 attributes
                    price_data = None
                    if hasattr(asset, 'close_monthly') and asset.close_monthly is not None:
                        price_data = asset.close_monthly
                    elif hasattr(asset, 'close_daily') and asset.close_daily is not None:
                        price_data = asset.close_daily
                    elif hasattr(asset, 'adj_close') and asset.adj_close is not None:
                        price_data = asset.adj_close
                    elif hasattr(asset, 'nav_ts') and asset.nav_ts is not None:
                        price_data = asset.nav_ts
                    
                    if price_data is not None and hasattr(price_data, 'empty') and not price_data.empty:
                        assets_data[symbol] = price_data
                    else:
                        print(f"⚠️ No valid price data found for {symbol}")
                    
                    # Get asset metrics with fallback handling using correct methods
                    comparison_metrics[symbol] = {
                        'total_return': self._get_asset_metric(asset, 'get_cumulative_return'),
                        'annual_return': self._get_asset_metric(asset, 'get_cagr'),
                        'volatility': self._get_asset_volatility(asset),
                        'sharpe_ratio': self._get_asset_metric(asset, 'get_sharpe_ratio'),
                        'max_drawdown': self._get_asset_drawdown(asset)
                    }
                except Exception as e:
                    comparison_metrics[symbol] = {'error': str(e)}
            
            # Create comparison chart
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Price comparison (normalized) - only if we have price data
            if assets_data:
                for symbol, prices in assets_data.items():
                    if hasattr(prices, 'empty') and not prices.empty and hasattr(prices, 'iloc'):
                        try:
                            normalized_prices = prices / prices.iloc[0] * 100
                            normalized_prices.plot(ax=ax1, label=symbol, linewidth=2)
                        except Exception as e:
                            print(f"⚠️ Error plotting prices for {symbol}: {e}")
                
                ax1.set_title('Asset Price Comparison (Normalized to 100)')
                ax1.set_ylabel('Normalized Price')
                ax1.legend()
                ax1.grid(True)
            else:
                # No price data available
                ax1.text(0.5, 0.5, 'Price data not available\nfor comparison', 
                         ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('Asset Price Comparison (No Data)')
                ax1.set_ylabel('Normalized Price')
            
            # Risk-return scatter
            returns = []
            volatilities = []
            labels = []
            
            for symbol, metrics in comparison_metrics.items():
                if 'error' not in metrics:
                    annual_return = metrics.get('annual_return', 0)
                    volatility = metrics.get('volatility', 0)
                    if annual_return != 0 and volatility != 0:
                        returns.append(annual_return)
                        volatilities.append(volatility)
                        labels.append(symbol)
            
            if returns and volatilities and len(returns) >= 2:
                ax2.scatter(volatilities, returns, s=100, alpha=0.7)
                for i, label in enumerate(labels):
                    ax2.annotate(label, (volatilities[i], returns[i]), 
                               xytext=(5, 5), textcoords='offset points')
                
                ax2.set_xlabel('Volatility')
                ax2.set_ylabel('Annual Return')
                ax2.set_title('Risk-Return Profile')
                ax2.grid(True)
            else:
                # Not enough data for scatter plot
                ax2.text(0.5, 0.5, 'Insufficient data for\nrisk-return analysis', 
                         ha='center', va='center', transform=ax2.transAxes)
                ax2.set_xlabel('Volatility')
                ax2.set_ylabel('Annual Return')
                ax2.set_title('Risk-Return Profile (No Data)')
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return comparison_metrics, img_buffer.getvalue()
        except Exception as e:
            raise Exception(f"Error comparing assets: {str(e)}")
    
    def _get_asset_metric(self, asset: ok.Asset, method_name: str) -> float:
        """Get asset metric using specified method with error handling"""
        try:
            if hasattr(asset, method_name):
                method = getattr(asset, method_name)
                if callable(method):
                    result = method()
                    if isinstance(result, (int, float)) and not pd.isna(result):
                        return result
                    elif hasattr(result, 'iloc') and not result.empty:
                        return result.iloc[-1]
                    else:
                        return 0.0
                else:
                    return 0.0
            else:
                return 0.0
        except Exception as e:
            print(f"Error getting {method_name} for asset: {e}")
            return 0.0
    
    def _get_asset_volatility(self, asset: ok.Asset) -> float:
        """Get asset volatility from returns data"""
        try:
            if hasattr(asset, 'ror') and asset.ror is not None:
                if hasattr(asset.ror, 'empty') and not asset.ror.empty:
                    return asset.ror.std() * np.sqrt(12)  # Annualize monthly volatility
                elif hasattr(asset.ror, '__len__') and len(asset.ror) > 0:
                    return np.std(asset.ror) * np.sqrt(12)
            return 0.0
        except Exception as e:
            print(f"Error calculating volatility: {e}")
            return 0.0
    
    def _get_asset_drawdown(self, asset: ok.Asset) -> float:
        """Get asset maximum drawdown"""
        try:
            if hasattr(asset, 'drawdowns') and asset.drawdowns is not None:
                if hasattr(asset.drawdowns, 'empty') and not asset.drawdowns.empty:
                    return asset.drawdowns.min()
                elif hasattr(asset.drawdowns, '__len__') and len(asset.drawdowns) > 0:
                    return np.min(asset.drawdowns)
            return 0.0
        except Exception as e:
            print(f"Error getting drawdown: {e}")
            return 0.0

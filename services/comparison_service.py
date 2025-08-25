import okama as ok
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from typing import List, Dict, Tuple
import warnings

# Optional dependency for crypto fallback via Yahoo Finance
try:
    import yfinance as yf
except Exception:  # ImportError or runtime issues
    yf = None

warnings.filterwarnings('ignore')

class ComparisonService:
    """Service for asset comparison analysis"""
    
    def __init__(self):
        self.plt_style = 'seaborn-v0_8'
        plt.style.use(self.plt_style)
    
    def _resolve_symbol(self, symbol: str) -> Tuple[str, ok.Asset]:
        """Try to resolve a potentially unsupported ticker to a working Okama symbol.
        Returns a tuple of (resolved_symbol, okama_asset). Raises last error if all fail.
        """
        # Ordered candidates to try
        candidates = [symbol]
        
        # If looks like crypto with .CC suffix, try common Yahoo-style tickers
        if symbol.endswith('.CC') and len(symbol) > 3:
            base = symbol.rsplit('.CC', 1)[0]
            # Typical candidates for crypto in many data sources (Yahoo et al.)
            # Avoid dot-suffixed currency (e.g., .USD, .USDT) because Okama treats it as a namespace
            # and avoid USDT variants which are not valid Okama namespaces.
            candidates.extend([
                f"{base}-USD",
                base,
            ])
        
        last_error: Exception | None = None
        for candidate in candidates:
            try:
                asset = ok.Asset(candidate)
                return candidate, asset
            except Exception as e:  # keep trying
                last_error = e
                continue
        
        # If nothing worked, raise the last seen error
        if last_error is not None:
            raise last_error
        raise Exception(f"Unable to resolve symbol: {symbol}")
    
    def compare_assets(self, symbols: List[str]) -> Tuple[Dict, bytes]:
        """Compare multiple assets and generate comparison chart using correct Okama v1.5.0 API"""
        try:
            assets_data = {}
            comparison_metrics = {}
            
            for symbol in symbols:
                try:
                    # Resolve symbol to something Okama understands (handles BTC.CC/ETH.CC, etc.)
                    resolved_symbol, asset = self._resolve_symbol(symbol)
                    
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
                        # Store under the original requested symbol for user-facing labels
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
                    # Okama path failed. For crypto namespace (.CC) attempt Yahoo Finance fallback.
                    if isinstance(symbol, str) and symbol.endswith('.CC'):
                        base = symbol.rsplit('.CC', 1)[0]
                        yf_symbol = f"{base}-USD"
                        if yf is None:
                            comparison_metrics[symbol] = {'error': f"Crypto fallback requires yfinance. Install yfinance to support {symbol}. Original error: {e}"}
                            continue
                        try:
                            df = yf.download(yf_symbol, period='max', interval='1d', progress=False, auto_adjust=False)
                            if df is not None and hasattr(df, 'empty') and not df.empty and 'Close' in df.columns:
                                prices = df['Close'].dropna()
                                if not prices.empty:
                                    assets_data[symbol] = prices
                                    comparison_metrics[symbol] = self._compute_metrics_from_prices(prices)
                                    continue
                            comparison_metrics[symbol] = {'error': f"No price data from Yahoo for {symbol} ({yf_symbol})"}
                        except Exception as yf_err:
                            comparison_metrics[symbol] = {'error': f"{str(e)} | Yahoo fallback error: {yf_err}"}
                    else:
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

    def _compute_metrics_from_prices(self, prices: pd.Series) -> Dict[str, float]:
        """Compute basic metrics from a price series using daily data.
        This is used as a fallback for assets not supported by Okama (e.g., crypto via Yahoo Finance).
        """
        try:
            prices = prices.dropna()
            if prices.empty:
                return {
                    'total_return': 0.0,
                    'annual_return': 0.0,
                    'volatility': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0
                }

            # Basic returns
            total_return = float(prices.iloc[-1] / prices.iloc[0] - 1.0)

            # CAGR using calendar time
            try:
                start = prices.index[0]
                end = prices.index[-1]
                num_days = (end - start).days if hasattr(end, 'to_pydatetime') or hasattr(end, 'tzinfo') else len(prices)
                years = max(num_days / 365.25, 1e-9)
            except Exception:
                years = max(len(prices) / 252.0, 1e-9)
            annual_return = float((prices.iloc[-1] / prices.iloc[0]) ** (1.0 / years) - 1.0)

            # Daily returns
            r = prices.pct_change().dropna()
            if r.empty:
                volatility = 0.0
                sharpe = 0.0
            else:
                mean_daily = float(r.mean())
                std_daily = float(r.std())
                volatility = float(std_daily * np.sqrt(252.0))
                sharpe = float((mean_daily / std_daily) * np.sqrt(252.0)) if std_daily > 0 else 0.0

            # Max drawdown
            running_max = prices.cummax()
            drawdowns = (prices / running_max - 1.0)
            max_drawdown = float(drawdowns.min()) if not drawdowns.empty else 0.0

            return {
                'total_return': total_return,
                'annual_return': annual_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe,
                'max_drawdown': max_drawdown
            }
        except Exception:
            return {
                'total_return': 0.0,
                'annual_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }
    
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

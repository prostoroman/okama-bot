import okama as ok
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import io
from typing import List, Dict, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class OkamaService:
    """Service class for Okama library operations"""
    
    def __init__(self):
        self.plt_style = 'seaborn-v0_8'
        plt.style.use(self.plt_style)
        
    def create_portfolio(self, symbols: List[str], weights: Optional[List[float]] = None) -> ok.Portfolio:
        """Create a portfolio with given symbols and weights"""
        try:
            if weights is None:
                weights = [1.0 / len(symbols)] * len(symbols)
            
            portfolio = ok.Portfolio(symbols, weights=weights)
            
            # Debug: Print available attributes and methods
            print(f"Portfolio created successfully for symbols: {symbols}")
            print(f"Portfolio type: {type(portfolio)}")
            print(f"Available attributes: {[attr for attr in dir(portfolio) if not attr.startswith('_')]}")
            
            # Check if key attributes exist
            key_attrs = ['total_return', 'mean_return', 'volatility', 'sharpe_ratio', 'max_drawdown', 'cumulative_returns']
            for attr in key_attrs:
                if hasattr(portfolio, attr):
                    print(f"✓ {attr}: {getattr(portfolio, attr)}")
                else:
                    print(f"✗ {attr}: Not available")
            
            return portfolio
        except Exception as e:
            raise Exception(f"Error creating portfolio: {str(e)}")
    
    def get_portfolio_performance(self, portfolio: ok.Portfolio) -> Dict:
        """Get comprehensive portfolio performance metrics"""
        try:
            # Get portfolio statistics using the correct Okama API
            stats = portfolio.stats
            
            # Basic metrics - using the correct attribute names
            metrics = {
                'total_return': portfolio.cumulative_returns.iloc[-1] if not portfolio.cumulative_returns.empty else 0,
                'annual_return': portfolio.mean_return if hasattr(portfolio, 'mean_return') else stats.get('mean_return', 0),
                'volatility': portfolio.volatility if hasattr(portfolio, 'volatility') else stats.get('volatility', 0),
                'sharpe_ratio': portfolio.sharpe_ratio if hasattr(portfolio, 'sharpe_ratio') else stats.get('sharpe_ratio', 0),
                'max_drawdown': portfolio.max_drawdown if hasattr(portfolio, 'max_drawdown') else stats.get('max_drawdown', 0),
                'var_95': portfolio.var_95 if hasattr(portfolio, 'var_95') else stats.get('var_95', 0),
                'cvar_95': portfolio.cvar_95 if hasattr(portfolio, 'cvar_95') else stats.get('cvar_95', 0)
            }
            
            # Convert to more readable format
            formatted_metrics = {}
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    if 'return' in key or 'ratio' in key:
                        formatted_metrics[key] = f"{value:.2%}"
                    elif 'volatility' in key or 'drawdown' in key or 'var' in key:
                        formatted_metrics[key] = f"{value:.2%}"
                    else:
                        formatted_metrics[key] = f"{value:.4f}"
                else:
                    formatted_metrics[key] = str(value)
            
            return formatted_metrics
        except Exception as e:
            # Fallback to basic portfolio data if stats method fails
            try:
                print(f"Primary method failed, trying fallback: {e}")
                
                # Try to get basic portfolio information
                if hasattr(portfolio, 'cumulative_returns') and not portfolio.cumulative_returns.empty:
                    total_return = portfolio.cumulative_returns.iloc[-1]
                else:
                    total_return = 0
                
                # Try to get other metrics from available attributes
                metrics = {
                    'total_return': total_return,
                    'annual_return': getattr(portfolio, 'mean_return', 0),
                    'volatility': getattr(portfolio, 'volatility', 0),
                    'sharpe_ratio': getattr(portfolio, 'sharpe_ratio', 0),
                    'max_drawdown': getattr(portfolio, 'max_drawdown', 0),
                    'var_95': getattr(portfolio, 'var_95', 0),
                    'cvar_95': getattr(portfolio, 'cvar_95', 0)
                }
                
                # Format metrics
                formatted_metrics = {}
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        if 'return' in key or 'ratio' in key:
                            formatted_metrics[key] = f"{value:.2%}"
                        elif 'volatility' in key or 'drawdown' in key or 'var' in key:
                            formatted_metrics[key] = f"{value:.2%}"
                        else:
                            formatted_metrics[key] = f"{value:.4f}"
                    else:
                        formatted_metrics[key] = str(value)
                
                return formatted_metrics
                
            except Exception as fallback_error:
                print(f"Fallback method also failed: {fallback_error}")
                # Return basic portfolio info
                return {
                    'total_return': 'N/A',
                    'annual_return': 'N/A',
                    'volatility': 'N/A',
                    'sharpe_ratio': 'N/A',
                    'max_drawdown': 'N/A',
                    'var_95': 'N/A',
                    'cvar_95': 'N/A',
                    'note': 'Limited metrics available'
                }
    
    def generate_performance_chart(self, portfolio: ok.Portfolio) -> bytes:
        """Generate portfolio performance chart"""
        try:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Cumulative returns
            portfolio.cumulative_returns.plot(ax=ax1, title='Cumulative Returns')
            ax1.set_ylabel('Cumulative Return')
            ax1.grid(True)
            
            # Rolling volatility
            portfolio.rolling_volatility.plot(ax=ax2, title='Rolling Volatility (30 days)')
            ax2.set_ylabel('Volatility')
            ax2.set_xlabel('Date')
            ax2.grid(True)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except Exception as e:
            raise Exception(f"Error generating performance chart: {str(e)}")
    
    def generate_correlation_matrix(self, symbols: List[str]) -> bytes:
        """Generate correlation matrix heatmap"""
        try:
            print(f"Generating correlation matrix for symbols: {symbols}")
            
            # Get historical data for symbols
            data = {}
            failed_symbols = []
            
            for symbol in symbols:
                try:
                    print(f"Processing symbol: {symbol}")
                    asset = ok.Asset(symbol)
                    print(f"Asset created successfully for {symbol}")
                    
                    if hasattr(asset, 'price_ts'):
                        price_data = asset.price_ts
                        print(f"Price data for {symbol}: {type(price_data)}, length: {len(price_data) if hasattr(price_data, '__len__') else 'N/A'}")
                        
                        if not price_data.empty if hasattr(price_data, 'empty') else len(price_data) > 0:
                            data[symbol] = price_data
                            print(f"✓ Added {symbol} to correlation data")
                        else:
                            print(f"✗ {symbol} has empty price data")
                            failed_symbols.append(f"{symbol} (empty data)")
                    else:
                        print(f"✗ {symbol} has no price_ts attribute")
                        failed_symbols.append(f"{symbol} (no price_ts)")
                        
                except Exception as e:
                    print(f"✗ Error processing {symbol}: {e}")
                    failed_symbols.append(f"{symbol} (error: {str(e)})")
                    continue
            
            print(f"Successfully processed symbols: {list(data.keys())}")
            print(f"Failed symbols: {failed_symbols}")
            
            if len(data) < 2:
                error_msg = f"Need at least 2 valid symbols for correlation matrix. "
                error_msg += f"Processed: {len(data)}, Failed: {len(failed_symbols)}. "
                error_msg += f"Failed symbols: {', '.join(failed_symbols)}"
                raise Exception(error_msg)
            
            # Create DataFrame and calculate correlation
            df = pd.DataFrame(data)
            correlation_matrix = df.corr()
            
            # Create heatmap
            plt.figure(figsize=(10, 8))
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                       square=True, linewidths=0.5, cbar_kws={"shrink": .8})
            plt.title('Asset Correlation Matrix')
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except Exception as e:
            raise Exception(f"Error generating correlation matrix: {str(e)}")
    
    def generate_efficient_frontier(self, symbols: List[str]) -> bytes:
        """Generate efficient frontier plot"""
        try:
            print(f"Generating efficient frontier for symbols: {symbols}")
            
            # Create efficient frontier
            ef = ok.EfficientFrontier(symbols)
            print(f"EfficientFrontier created successfully")
            
            # Generate efficient frontier
            ef_points = ef.efficient_frontier_points
            print(f"Efficient frontier points: {type(ef_points)}, length: {len(ef_points) if hasattr(ef_points, '__len__') else 'N/A'}")
            
            plt.figure(figsize=(12, 8))
            plt.scatter(ef_points['Risk'], ef_points['Return'], alpha=0.6, s=50)
            plt.plot(ef_points['Risk'], ef_points['Return'], 'b-', linewidth=2)
            
            # Mark individual assets
            for i, symbol in enumerate(symbols):
                try:
                    asset = ok.Asset(symbol)
                    plt.scatter(asset.volatility, asset.mean_return, 
                              s=100, marker='o', label=symbol, alpha=0.8)
                except:
                    continue
            
            plt.xlabel('Volatility (Risk)')
            plt.ylabel('Expected Return')
            plt.title('Efficient Frontier')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except Exception as e:
            raise Exception(f"Error generating efficient frontier: {str(e)}")
    
    def compare_assets(self, symbols: List[str]) -> Tuple[Dict, bytes]:
        """Compare multiple assets and generate comparison chart"""
        try:
            assets_data = {}
            comparison_metrics = {}
            
            for symbol in symbols:
                try:
                    asset = ok.Asset(symbol)
                    assets_data[symbol] = asset.price_ts
                    
                    # Get asset metrics with fallback handling
                    comparison_metrics[symbol] = {
                        'total_return': getattr(asset, 'total_return', 0),
                        'annual_return': getattr(asset, 'mean_return', 0),
                        'volatility': getattr(asset, 'volatility', 0),
                        'sharpe_ratio': getattr(asset, 'sharpe_ratio', 0),
                        'max_drawdown': getattr(asset, 'max_drawdown', 0)
                    }
                except Exception as e:
                    comparison_metrics[symbol] = {'error': str(e)}
            
            # Create comparison chart
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Price comparison (normalized)
            for symbol, prices in assets_data.items():
                if not prices.empty:
                    normalized_prices = prices / prices.iloc[0] * 100
                    normalized_prices.plot(ax=ax1, label=symbol, linewidth=2)
            
            ax1.set_title('Asset Price Comparison (Normalized to 100)')
            ax1.set_ylabel('Normalized Price')
            ax1.legend()
            ax1.grid(True)
            
            # Risk-return scatter
            returns = []
            volatilities = []
            labels = []
            
            for symbol, metrics in comparison_metrics.items():
                if 'error' not in metrics:
                    returns.append(metrics['annual_return'])
                    volatilities.append(metrics['volatility'])
                    labels.append(symbol)
            
            if returns and volatilities:
                ax2.scatter(volatilities, returns, s=100, alpha=0.7)
                for i, label in enumerate(labels):
                    ax2.annotate(label, (volatilities[i], returns[i]), 
                               xytext=(5, 5), textcoords='offset points')
            
            ax2.set_xlabel('Volatility')
            ax2.set_ylabel('Annual Return')
            ax2.set_title('Risk-Return Profile')
            ax2.grid(True)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return comparison_metrics, img_buffer.getvalue()
        except Exception as e:
            raise Exception(f"Error comparing assets: {str(e)}")
    
    def get_asset_info(self, symbol: str) -> Dict:
        """Get basic information about an asset"""
        try:
            asset = ok.Asset(symbol)
            return {
                'symbol': symbol,
                'total_return': f"{getattr(asset, 'total_return', 0):.2%}",
                'annual_return': f"{getattr(asset, 'mean_return', 0):.2%}",
                'volatility': f"{getattr(asset, 'volatility', 0):.2%}",
                'sharpe_ratio': f"{getattr(asset, 'sharpe_ratio', 0):.2f}",
                'max_drawdown': f"{getattr(asset, 'max_drawdown', 0):.2%}",
                'var_95': f"{getattr(asset, 'var_95', 0):.2%}",
                'cvar_95': f"{getattr(asset, 'cvar_95', 0):.2%}"
            }
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    def test_okama_integration(self, symbols: List[str]) -> Dict:
        """Test method to debug Okama integration issues"""
        try:
            print(f"Testing Okama integration with symbols: {symbols}")
            
            # Test individual assets
            asset_info = {}
            for symbol in symbols:
                try:
                    asset = ok.Asset(symbol)
                    print(f"\nAsset {symbol}:")
                    print(f"  Type: {type(asset)}")
                    print(f"  Available attributes: {[attr for attr in dir(asset) if not attr.startswith('_')]}")
                    
                    # Test key attributes
                    key_attrs = ['total_return', 'mean_return', 'volatility', 'sharpe_ratio', 'max_drawdown']
                    for attr in key_attrs:
                        if hasattr(asset, attr):
                            value = getattr(asset, attr)
                            print(f"  ✓ {attr}: {value}")
                        else:
                            print(f"  ✗ {attr}: Not available")
                    
                    asset_info[symbol] = "OK"
                except Exception as e:
                    print(f"  ✗ Error with {symbol}: {e}")
                    asset_info[symbol] = f"Error: {str(e)}"
            
            # Test portfolio creation
            try:
                portfolio = ok.Portfolio(symbols)
                print(f"\nPortfolio created successfully:")
                print(f"  Type: {type(portfolio)}")
                print(f"  Available attributes: {[attr for attr in dir(portfolio) if not attr.startswith('_')]}")
                
                # Test portfolio methods
                if hasattr(portfolio, 'stats'):
                    try:
                        stats = portfolio.stats
                        print(f"  ✓ stats method: {stats}")
                    except Exception as e:
                        print(f"  ✗ stats method error: {e}")
                
                if hasattr(portfolio, 'cumulative_returns'):
                    try:
                        cum_returns = portfolio.cumulative_returns
                        print(f"  ✓ cumulative_returns: {type(cum_returns)}")
                        if hasattr(cum_returns, 'iloc'):
                            print(f"    Last value: {cum_returns.iloc[-1] if not cum_returns.empty else 'Empty'}")
                    except Exception as e:
                        print(f"  ✗ cumulative_returns error: {e}")
                
                portfolio_info = "OK"
            except Exception as e:
                print(f"  ✗ Portfolio creation error: {e}")
                portfolio_info = f"Error: {str(e)}"
            
            return {
                'assets': asset_info,
                'portfolio': portfolio_info,
                'okama_version': ok.__version__ if hasattr(ok, '__version__') else 'Unknown'
            }
            
        except Exception as e:
            return {'error': f"Test failed: {str(e)}"}

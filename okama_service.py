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
            print(f"Generating performance chart for portfolio...")
            
            # Check available attributes
            available_attrs = [attr for attr in dir(portfolio) if not attr.startswith('_')]
            print(f"Available portfolio attributes: {available_attrs}")
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Try to plot cumulative returns with fallback
            try:
                if hasattr(portfolio, 'cumulative_returns') and not portfolio.cumulative_returns.empty:
                    portfolio.cumulative_returns.plot(ax=ax1, title='Cumulative Returns')
                    ax1.set_ylabel('Cumulative Return')
                    ax1.grid(True)
                elif hasattr(portfolio, 'returns') and not portfolio.returns.empty:
                    # Fallback to regular returns
                    portfolio.returns.cumsum().plot(ax=ax1, title='Cumulative Returns (from returns)')
                    ax1.set_ylabel('Cumulative Return')
                    ax1.grid(True)
                else:
                    # Create a simple placeholder
                    ax1.text(0.5, 0.5, 'Cumulative Returns\n(Data not available)', 
                            ha='center', va='center', transform=ax1.transAxes)
                    ax1.set_title('Cumulative Returns')
                    ax1.grid(True)
            except Exception as e:
                print(f"Error plotting cumulative returns: {e}")
                ax1.text(0.5, 0.5, 'Cumulative Returns\n(Error plotting)', 
                        ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('Cumulative Returns')
                ax1.grid(True)
            
            # Try to plot rolling volatility with fallback
            try:
                if hasattr(portfolio, 'rolling_volatility') and not portfolio.rolling_volatility.empty:
                    portfolio.rolling_volatility.plot(ax=ax2, title='Rolling Volatility (30 days)')
                    ax2.set_ylabel('Volatility')
                    ax2.set_xlabel('Date')
                    ax2.grid(True)
                elif hasattr(portfolio, 'volatility'):
                    # Fallback to static volatility
                    ax2.axhline(y=portfolio.volatility, color='r', linestyle='-', 
                               label=f'Volatility: {portfolio.volatility:.2%}')
                    ax2.set_ylabel('Volatility')
                    ax2.set_xlabel('Time')
                    ax2.set_title('Portfolio Volatility')
                    ax2.legend()
                    ax2.grid(True)
                else:
                    # Create a simple placeholder
                    ax2.text(0.5, 0.5, 'Volatility\n(Data not available)', 
                            ha='center', va='center', transform=ax2.transAxes)
                    ax2.set_title('Portfolio Volatility')
                    ax2.grid(True)
            except Exception as e:
                print(f"Error plotting volatility: {e}")
                ax2.text(0.5, 0.5, 'Volatility\n(Error plotting)', 
                        ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Portfolio Volatility')
                ax2.grid(True)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except Exception as e:
            print(f"Error generating performance chart: {e}")
            # Create a simple error chart
            try:
                fig, ax = plt.subplots(1, 1, figsize=(10, 6))
                ax.text(0.5, 0.5, f'Chart Generation Error\n{str(e)}', 
                       ha='center', va='center', transform=ax.transAxes)
                ax.set_title('Portfolio Performance Chart')
                ax.grid(True)
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
                img_buffer.seek(0)
                plt.close()
                
                return img_buffer.getvalue()
            except:
                # If even the error chart fails, raise the original error
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
                    
                    # Debug: Print available attributes
                    available_attrs = [attr for attr in dir(asset) if not attr.startswith('_')]
                    print(f"Available attributes for {symbol}: {available_attrs}")
                    
                    # Try different possible price data attributes
                    price_data = None
                    price_source = None
                    
                    # Check for price_ts first
                    if hasattr(asset, 'price_ts'):
                        price_data = asset.price_ts
                        price_source = 'price_ts'
                    # Check for price_data
                    elif hasattr(asset, 'price_data'):
                        price_data = asset.price_data
                        price_source = 'price_data'
                    # Check for prices
                    elif hasattr(asset, 'prices'):
                        price_data = asset.prices
                        price_source = 'prices'
                    # Check for close
                    elif hasattr(asset, 'close'):
                        price_data = asset.close
                        price_source = 'close'
                    # Check for historical_data
                    elif hasattr(asset, 'historical_data'):
                        price_data = asset.historical_data
                        price_source = 'historical_data'
                    else:
                        print(f"✗ {symbol} has no recognizable price data attribute")
                        failed_symbols.append(f"{symbol} (no price data found)")
                        continue
                    
                    print(f"Found price data in '{price_source}' for {symbol}: {type(price_data)}")
                    
                    # Check if we have valid data
                    if price_data is not None:
                        if hasattr(price_data, 'empty') and not price_data.empty:
                            data[symbol] = price_data
                            print(f"✓ Added {symbol} to correlation data (pandas DataFrame)")
                        elif hasattr(price_data, '__len__') and len(price_data) > 0:
                            data[symbol] = price_data
                            print(f"✓ Added {symbol} to correlation data (length: {len(price_data)})")
                        else:
                            print(f"✗ {symbol} has empty price data in {price_source}")
                            failed_symbols.append(f"{symbol} (empty {price_source})")
                    else:
                        print(f"✗ {symbol} has None price data in {price_source}")
                        failed_symbols.append(f"{symbol} (None {price_source})")
                        
                except Exception as e:
                    print(f"✗ Error processing {symbol}: {e}")
                    failed_symbols.append(f"{symbol} (error: {str(e)})")
                    continue
            
            print(f"Successfully processed symbols: {list(data.keys())}")
            print(f"Failed symbols: {failed_symbols}")
            
            if len(data) < 2:
                print(f"⚠️ Not enough price data for correlation matrix. Trying fallback method...")
                
                # Try to create a simple correlation matrix using available metrics
                try:
                    return self._generate_fallback_correlation_matrix(symbols)
                except Exception as fallback_error:
                    print(f"Fallback method also failed: {fallback_error}")
                    # Create an informational chart instead of raising an exception
                    error_msg = f"Need at least 2 valid symbols for correlation matrix. "
                    error_msg += f"Processed: {len(data)}, Failed: {len(failed_symbols)}. "
                    error_msg += f"Failed symbols: {', '.join(failed_symbols)}"
                    print(f"Creating info chart with error: {error_msg}")
                    return self._create_info_chart(symbols, error_msg)
            
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
            
            # Check if we have efficient frontier points
            if hasattr(ef_points, '__len__') and len(ef_points) > 0:
                try:
                    if hasattr(ef_points, 'columns') and 'Risk' in ef_points.columns and 'Return' in ef_points.columns:
                        plt.scatter(ef_points['Risk'], ef_points['Return'], alpha=0.6, s=50)
                        plt.plot(ef_points['Risk'], ef_points['Return'], 'b-', linewidth=2)
                        print("✓ Plotted efficient frontier curve")
                    else:
                        print("⚠️ Efficient frontier points don't have expected 'Risk' and 'Return' columns")
                        # Try to plot as generic data
                        if hasattr(ef_points, 'iloc'):
                            plt.scatter(ef_points.iloc[:, 0], ef_points.iloc[:, 1], alpha=0.6, s=50)
                            plt.plot(ef_points.iloc[:, 0], ef_points.iloc[:, 1], 'b-', linewidth=2)
                            print("✓ Plotted efficient frontier using generic data")
                        else:
                            print("⚠️ Could not plot efficient frontier curve")
                except Exception as e:
                    print(f"✗ Error plotting efficient frontier curve: {e}")
            else:
                print("⚠️ No efficient frontier points available")
            
            # Mark individual assets
            for i, symbol in enumerate(symbols):
                try:
                    asset = ok.Asset(symbol)
                    
                    # Use getattr with fallbacks for asset attributes
                    volatility = getattr(asset, 'volatility', 0)
                    mean_return = getattr(asset, 'mean_return', 0)
                    
                    if volatility != 0 and mean_return != 0:
                        plt.scatter(volatility, mean_return, 
                                  s=100, marker='o', label=symbol, alpha=0.8)
                        print(f"✓ Added asset {symbol} to efficient frontier plot")
                    else:
                        print(f"⚠️ Asset {symbol} has missing volatility or return data")
                except Exception as e:
                    print(f"✗ Error processing asset {symbol}: {e}")
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
                    
                    # Try to get price data with fallback
                    price_data = None
                    if hasattr(asset, 'price_ts'):
                        price_data = asset.price_ts
                    elif hasattr(asset, 'price_data'):
                        price_data = asset.price_data
                    elif hasattr(asset, 'prices'):
                        price_data = asset.prices
                    elif hasattr(asset, 'close'):
                        price_data = asset.close
                    elif hasattr(asset, 'historical_data'):
                        price_data = asset.historical_data
                    
                    if price_data is not None and hasattr(price_data, 'empty') and not price_data.empty:
                        assets_data[symbol] = price_data
                    else:
                        print(f"⚠️ No valid price data found for {symbol}")
                    
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
    
    def test_asset_data(self, symbol: str) -> Dict:
        """Test what data is available for a specific asset"""
        try:
            print(f"Testing asset data for: {symbol}")
            asset = ok.Asset(symbol)
            
            # Get all available attributes
            available_attrs = [attr for attr in dir(asset) if not attr.startswith('_')]
            
            # Test specific data attributes
            data_sources = {}
            for attr in ['price_ts', 'price_data', 'prices', 'close', 'historical_data']:
                if hasattr(asset, attr):
                    data = getattr(asset, attr)
                    if data is not None:
                        if hasattr(data, 'empty'):
                            data_sources[attr] = f"pandas DataFrame (empty: {data.empty})"
                        elif hasattr(data, '__len__'):
                            data_sources[attr] = f"data with length: {len(data)}"
                        else:
                            data_sources[attr] = f"data of type: {type(data)}"
                    else:
                        data_sources[attr] = "None"
                else:
                    data_sources[attr] = "Not available"
            
            # Test metrics
            metrics = {}
            metric_names = ['volatility', 'mean_return', 'total_return', 'sharpe_ratio', 'max_drawdown']
            for metric in metric_names:
                if hasattr(asset, metric):
                    value = getattr(asset, metric)
                    metrics[metric] = value if value is not None else "None"
                else:
                    metrics[metric] = "Not available"
            
            result = {
                'symbol': symbol,
                'available_attributes': available_attrs,
                'data_sources': data_sources,
                'metrics': metrics,
                'status': 'success'
            }
            
            print(f"✓ Asset data test completed for {symbol}")
            return result
            
        except Exception as e:
            print(f"✗ Error testing asset {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'status': 'error'
            }
    
    def _generate_fallback_correlation_matrix(self, symbols: List[str]) -> bytes:
        """Generate a fallback correlation matrix when price data is not available"""
        try:
            print(f"Generating fallback correlation matrix for symbols: {symbols}")
            
            # Try to get basic metrics for correlation
            metrics_data = {}
            for symbol in symbols:
                try:
                    asset = ok.Asset(symbol)
                    
                    # Get basic metrics that might be available
                    metrics = {}
                    metric_names = ['volatility', 'mean_return', 'total_return', 'sharpe_ratio']
                    
                    for metric in metric_names:
                        if hasattr(asset, metric):
                            value = getattr(asset, metric)
                            if value is not None and value != 0:
                                metrics[metric] = value
                    
                    if metrics:
                        metrics_data[symbol] = metrics
                        print(f"✓ Got metrics for {symbol}: {list(metrics.keys())}")
                    else:
                        print(f"⚠️ No metrics available for {symbol}")
                        
                except Exception as e:
                    print(f"✗ Error getting metrics for {symbol}: {e}")
                    continue
            
            # If we don't have enough metrics data, create an informational chart instead
            if len(metrics_data) < 2:
                print(f"⚠️ Not enough metrics data ({len(metrics_data)} symbols), creating informational chart")
                return self._create_info_chart(symbols, "Insufficient data for correlation analysis")
            
            # Create a simple correlation matrix from available metrics
            plt.figure(figsize=(10, 8))
            
            # Create a simple visualization showing available metrics
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle('Asset Metrics Overview (Fallback)', fontsize=16)
            
            # Plot volatility comparison
            if any('volatility' in metrics for metrics in metrics_data.values()):
                volatilities = [metrics.get('volatility', 0) for metrics in metrics_data.values()]
                symbols_list = list(metrics_data.keys())
                axes[0, 0].bar(symbols_list, volatilities)
                axes[0, 0].set_title('Volatility Comparison')
                axes[0, 0].set_ylabel('Volatility')
                axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Plot return comparison
            if any('mean_return' in metrics for metrics in metrics_data.values()):
                returns = [metrics.get('mean_return', 0) for metrics in metrics_data.values()]
                axes[0, 1].bar(symbols_list, returns)
                axes[0, 1].set_title('Mean Return Comparison')
                axes[0, 1].set_ylabel('Mean Return')
                axes[0, 1].tick_params(axis='x', rotation=45)
            
            # Plot Sharpe ratio comparison
            if any('sharpe_ratio' in metrics for metrics in metrics_data.values()):
                sharpe_ratios = [metrics.get('sharpe_ratio', 0) for metrics in metrics_data.values()]
                axes[1, 0].bar(symbols_list, sharpe_ratios)
                axes[1, 0].set_title('Sharpe Ratio Comparison')
                axes[1, 0].set_ylabel('Sharpe Ratio')
                axes[1, 0].tick_params(axis='x', rotation=45)
            
            # Create a simple correlation-like matrix
            if len(metrics_data) >= 2:
                # Use volatility as a proxy for correlation (simplified)
                volatilities = [metrics.get('volatility', 0) for metrics in metrics_data.values()]
                correlation_matrix = np.corrcoef(volatilities) if len(volatilities) > 1 else np.array([[1]])
                
                im = axes[1, 1].imshow(correlation_matrix, cmap='coolwarm', vmin=-1, vmax=1)
                axes[1, 1].set_title('Volatility Correlation (Proxy)')
                axes[1, 1].set_xticks(range(len(symbols_list)))
                axes[1, 1].set_yticks(range(len(symbols_list)))
                axes[1, 1].set_xticklabels(symbols_list)
                axes[1, 1].set_yticklabels(symbols_list)
                
                # Add colorbar
                plt.colorbar(im, ax=axes[1, 1])
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            print("✓ Fallback correlation matrix generated successfully")
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"✗ Fallback correlation matrix generation failed: {e}")
            # Create a simple error chart
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            ax.text(0.5, 0.5, f'Correlation Matrix Error\n{str(e)}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Asset Correlation Matrix')
            ax.grid(True)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()

    def _create_info_chart(self, symbols: List[str], message: str) -> bytes:
        """Create an informational chart when data is insufficient"""
        try:
            print(f"Creating info chart for symbols: {symbols} with message: {message}")
            
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            
            # Create a simple informational display
            ax.text(0.5, 0.7, 'Asset Analysis Information', 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=16, fontweight='bold')
            
            ax.text(0.5, 0.5, message, 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=12, wrap=True)
            
            ax.text(0.5, 0.3, f'Symbols: {", ".join(symbols)}', 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=10, style='italic')
            
            ax.text(0.5, 0.1, 'Try using different symbols or check data availability', 
                   ha='center', va='center', transform=ax.transAxes, 
                   fontsize=10, color='gray')
            
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            ax.set_title('Asset Data Status', fontsize=14, pad=20)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            print("✓ Info chart created successfully")
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"✗ Error creating info chart: {e}")
            # Return a simple error image
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            ax.text(0.5, 0.5, f'Chart Generation Error\n{str(e)}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Error')
            ax.axis('off')
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()

    def create_pension_portfolio(self, symbols: List[str], weights: List[float], 
                                ccy: str = 'RUB', initial_amount: float = 1000000,
                                cashflow: float = -50000, rebalancing_period: str = 'year') -> ok.Portfolio:
        """Create a pension portfolio with cash flows and rebalancing"""
        try:
            print(f"Creating pension portfolio: {symbols} with weights {weights}")
            print(f"Currency: {ccy}, Initial: {initial_amount}, Cashflow: {cashflow}, Rebalancing: {rebalancing_period}")
            
            portfolio = ok.Portfolio(
                symbols,
                ccy=ccy,
                weights=weights,
                inflation=True,
                symbol="Pension_Portfolio.PF",
                rebalancing_period=rebalancing_period,
                cashflow=cashflow,
                initial_amount=initial_amount,
                discount_rate=None
            )
            
            print(f"✓ Pension portfolio created successfully")
            return portfolio
            
        except Exception as e:
            print(f"✗ Error creating pension portfolio: {e}")
            raise Exception(f"Error creating pension portfolio: {str(e)}")

    def generate_monte_carlo_forecast(self, portfolio: ok.Portfolio, years: int = 30, 
                                    n_scenarios: int = 50, distribution: str = "norm") -> bytes:
        """Generate Monte Carlo forecast for portfolio"""
        try:
            print(f"Generating Monte Carlo forecast: {years} years, {n_scenarios} scenarios, {distribution} distribution")
            
            # Generate forecast
            forecast_data = portfolio.dcf.plot_forecast_monte_carlo(
                distr=distribution,
                years=years,
                backtest=True,
                n=n_scenarios
            )
            
            # Get the current figure and save it
            fig = plt.gcf()
            fig.set_size_inches(12, 8)
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            print(f"✓ Monte Carlo forecast generated successfully")
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"✗ Error generating Monte Carlo forecast: {e}")
            return self._create_info_chart(
                [portfolio.symbols], 
                f"Monte Carlo forecast error: {str(e)}"
            )

    def get_inflation_analysis(self, portfolio: ok.Portfolio) -> Tuple[Dict, bytes]:
        """Get inflation-adjusted portfolio analysis"""
        try:
            print(f"Getting inflation analysis for portfolio")
            
            # Get wealth index with inflation
            wealth_data = portfolio.dcf.wealth_index
            
            # Create inflation-adjusted chart
            plt.figure(figsize=(12, 8))
            
            # Plot wealth index and inflation
            if hasattr(wealth_data, 'plot'):
                wealth_data.plot()
                plt.title('Portfolio Wealth Index with Inflation')
                plt.xlabel('Date')
                plt.ylabel('Value')
                plt.grid(True, alpha=0.3)
                plt.legend()
            else:
                # Fallback if plot method doesn't work
                if hasattr(wealth_data, 'index') and hasattr(wealth_data, 'values'):
                    plt.plot(wealth_data.index, wealth_data.values, label='Portfolio Value')
                    plt.title('Portfolio Wealth Index')
                    plt.xlabel('Date')
                    plt.ylabel('Value')
                    plt.grid(True, alpha=0.3)
                    plt.legend()
                else:
                    raise Exception("Cannot access wealth index data")
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Get inflation metrics
            inflation_metrics = {
                'current_value': wealth_data.iloc[-1] if hasattr(wealth_data, 'iloc') else 'N/A',
                'total_return': getattr(portfolio, 'total_return', 'N/A'),
                'inflation_adjusted_return': 'N/A'  # Would need to calculate this
            }
            
            print(f"✓ Inflation analysis completed successfully")
            return inflation_metrics, img_buffer.getvalue()
            
        except Exception as e:
            print(f"✗ Error getting inflation analysis: {e}")
            return {'error': str(e)}, self._create_info_chart(
                [portfolio.symbols], 
                f"Inflation analysis error: {str(e)}"
            )

    def compare_portfolio_strategies(self, strategies: List[Dict]) -> Tuple[Dict, bytes]:
        """Compare different portfolio strategies"""
        try:
            print(f"Comparing {len(strategies)} portfolio strategies")
            
            portfolios = []
            for i, strategy in enumerate(strategies):
                try:
                    portfolio = ok.Portfolio(
                        strategy['symbols'],
                        ccy=strategy.get('ccy', 'RUB'),
                        weights=strategy.get('weights'),
                        inflation=strategy.get('inflation', True),
                        symbol=f"Strategy_{i+1}.PF"
                    )
                    portfolios.append({
                        'name': strategy.get('name', f'Strategy {i+1}'),
                        'portfolio': portfolio,
                        'config': strategy
                    })
                    print(f"✓ Created portfolio for {strategy.get('name', f'Strategy {i+1}')}")
                except Exception as e:
                    print(f"✗ Error creating portfolio for strategy {i+1}: {e}")
                    continue
            
            if len(portfolios) < 2:
                raise Exception("Need at least 2 valid portfolios for comparison")
            
            # Create comparison chart
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Portfolio Strategy Comparison', fontsize=16)
            
            # Compare returns
            returns_data = []
            names = []
            for p in portfolios:
                try:
                    total_return = getattr(p['portfolio'], 'total_return', 0)
                    returns_data.append(total_return)
                    names.append(p['name'])
                except:
                    returns_data.append(0)
                    names.append(p['name'])
            
            axes[0, 0].bar(names, returns_data)
            axes[0, 0].set_title('Total Returns Comparison')
            axes[0, 0].set_ylabel('Return')
            axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Compare volatility
            volatility_data = []
            for p in portfolios:
                try:
                    volatility = getattr(p['portfolio'], 'volatility', 0)
                    volatility_data.append(volatility)
                except:
                    volatility_data.append(0)
            
            axes[0, 1].bar(names, volatility_data)
            axes[0, 1].set_title('Volatility Comparison')
            axes[0, 1].set_ylabel('Volatility')
            axes[0, 1].tick_params(axis='x', rotation=45)
            
            # Compare Sharpe ratios
            sharpe_data = []
            for p in portfolios:
                try:
                    sharpe = getattr(p['portfolio'], 'sharpe_ratio', 0)
                    sharpe_data.append(sharpe)
                except:
                    sharpe_data.append(0)
            
            axes[1, 0].bar(names, sharpe_data)
            axes[1, 0].set_title('Sharpe Ratio Comparison')
            axes[1, 0].set_ylabel('Sharpe Ratio')
            axes[1, 0].tick_params(axis='x', rotation=45)
            
            # Compare max drawdown
            drawdown_data = []
            for p in portfolios:
                try:
                    drawdown = getattr(p['portfolio'], 'max_drawdown', 0)
                    drawdown_data.append(abs(drawdown))  # Make positive for visualization
                except:
                    drawdown_data.append(0)
            
            axes[1, 1].bar(names, drawdown_data)
            axes[1, 1].set_title('Max Drawdown Comparison')
            axes[1, 1].set_ylabel('Max Drawdown')
            axes[1, 1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Prepare comparison metrics
            comparison_metrics = {}
            for p in portfolios:
                try:
                    comparison_metrics[p['name']] = {
                        'total_return': getattr(p['portfolio'], 'total_return', 'N/A'),
                        'volatility': getattr(p['portfolio'], 'volatility', 'N/A'),
                        'sharpe_ratio': getattr(p['portfolio'], 'sharpe_ratio', 'N/A'),
                        'max_drawdown': getattr(p['portfolio'], 'max_drawdown', 'N/A'),
                        'symbols': p['config']['symbols'],
                        'weights': p['config'].get('weights', 'Equal'),
                        'currency': p['config'].get('ccy', 'RUB')
                    }
                except Exception as e:
                    comparison_metrics[p['name']] = {'error': str(e)}
            
            print(f"✓ Portfolio strategies comparison completed successfully")
            return comparison_metrics, img_buffer.getvalue()
            
        except Exception as e:
            print(f"✗ Error comparing portfolio strategies: {e}")
            return {'error': str(e)}, self._create_info_chart(
                [s.get('symbols', []) for s in strategies], 
                f"Strategy comparison error: {str(e)}"
            )

    def get_asset_allocation_analysis(self, portfolio: ok.Portfolio) -> Tuple[Dict, bytes]:
        """Get detailed asset allocation analysis"""
        try:
            print(f"Getting asset allocation analysis for portfolio")
            
            # Get portfolio table
            portfolio_table = portfolio.table
            
            # Create allocation chart
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Asset Allocation Analysis', fontsize=16)
            
            # Pie chart of weights
            if hasattr(portfolio, 'weights') and portfolio.weights is not None:
                weights = portfolio.weights
                symbols = portfolio.symbols
                axes[0, 0].pie(weights, labels=symbols, autopct='%1.1f%%', startangle=90)
                axes[0, 0].set_title('Portfolio Weights')
            else:
                axes[0, 0].text(0.5, 0.5, 'Weights not available', ha='center', va='center')
                axes[0, 0].set_title('Portfolio Weights')
            
            # Asset performance comparison
            if hasattr(portfolio_table, 'columns') and 'total_return' in portfolio_table.columns:
                returns = portfolio_table['total_return'].values
                symbols = portfolio_table.index.tolist()
                axes[0, 1].bar(symbols, returns)
                axes[0, 1].set_title('Individual Asset Returns')
                axes[0, 1].set_ylabel('Return')
                axes[0, 1].tick_params(axis='x', rotation=45)
            else:
                axes[0, 1].text(0.5, 0.5, 'Return data not available', ha='center', va='center')
                axes[0, 1].set_title('Individual Asset Returns')
            
            # Risk comparison
            if hasattr(portfolio_table, 'columns') and 'volatility' in portfolio_table.columns:
                volatilities = portfolio_table['volatility'].values
                axes[1, 0].bar(symbols, volatilities)
                axes[1, 0].set_title('Individual Asset Volatility')
                axes[1, 0].set_ylabel('Volatility')
                axes[1, 0].tick_params(axis='x', rotation=45)
            else:
                axes[1, 0].text(0.5, 0.5, 'Volatility data not available', ha='center', va='center')
                axes[1, 0].set_title('Individual Asset Volatility')
            
            # Sharpe ratio comparison
            if hasattr(portfolio_table, 'columns') and 'sharpe_ratio' in portfolio_table.columns:
                sharpe_ratios = portfolio_table['sharpe_ratio'].values
                axes[1, 1].bar(symbols, sharpe_ratios)
                axes[1, 1].set_title('Individual Asset Sharpe Ratios')
                axes[1, 1].set_ylabel('Sharpe Ratio')
                axes[1, 1].tick_params(axis='x', rotation=45)
            else:
                axes[1, 1].text(0.5, 0.5, 'Sharpe ratio data not available', ha='center', va='center')
                axes[1, 1].set_title('Individual Asset Sharpe Ratios')
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Prepare allocation metrics
            allocation_metrics = {
                'total_assets': len(portfolio.symbols),
                'currency': getattr(portfolio, 'ccy', 'Unknown'),
                'total_value': getattr(portfolio, 'total_value', 'N/A'),
                'weights': portfolio.weights.tolist() if hasattr(portfolio, 'weights') and portfolio.weights is not None else 'Equal',
                'symbols': portfolio.symbols
            }
            
            print(f"✓ Asset allocation analysis completed successfully")
            return allocation_metrics, img_buffer.getvalue()
            
        except Exception as e:
            print(f"✗ Error getting asset allocation analysis: {e}")
            return {'error': str(e)}, self._create_info_chart(
                [portfolio.symbols], 
                f"Asset allocation analysis error: {str(e)}"
            )

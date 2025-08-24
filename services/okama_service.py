import okama as ok
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from typing import List, Dict, Tuple, Optional
import warnings

# Import specialized services
from .correlation_service import CorrelationService
from .frontier_service import FrontierService
from .comparison_service import ComparisonService
from .pension_service import PensionService
from .monte_carlo_service import MonteCarloService
from .allocation_service import AllocationService

warnings.filterwarnings('ignore')

class OkamaServiceV2:
    """Updated service class for Okama library operations - Modular structure for v1.5.0"""
    
    def __init__(self):
        self.plt_style = 'seaborn-v0_8'
        plt.style.use(self.plt_style)
        
        # Initialize specialized services
        self.correlation_service = CorrelationService()
        self.frontier_service = FrontierService()
        self.comparison_service = ComparisonService()
        self.pension_service = PensionService()
        self.monte_carlo_service = MonteCarloService()
        self.allocation_service = AllocationService()
        
    def create_portfolio(self, symbols: List[str], weights: Optional[List[float]] = None, 
                        ccy: str = 'RUB', inflation: bool = True) -> ok.Portfolio:
        """Create a portfolio with given symbols and weights using correct Okama v1.5.0 API"""
        try:
            if weights is None:
                weights = [1.0 / len(symbols)] * len(symbols)
            
            # Use correct Portfolio constructor with inflation parameter
            portfolio = ok.Portfolio(
                symbols, 
                weights=weights, 
                ccy=ccy,
                inflation=inflation
            )
            
            print(f"✓ Portfolio created successfully for symbols: {symbols}")
            print(f"Portfolio type: {type(portfolio)}")
            
            return portfolio
        except Exception as e:
            raise Exception(f"Error creating portfolio: {str(e)}")
    
    def get_portfolio_performance(self, portfolio: ok.Portfolio) -> Dict:
        """Get comprehensive portfolio performance metrics using correct Okama v1.5.0 methods"""
        try:
            # Use the correct methods from Okama v1.5.0
            metrics = {
                'total_return': self._get_metric_safely(portfolio, 'get_cumulative_return'),
                'annual_return': self._get_metric_safely(portfolio, 'get_cagr'),
                'volatility': self._calculate_portfolio_volatility(portfolio),
                'sharpe_ratio': self._get_metric_safely(portfolio, 'get_sharpe_ratio'),
                'sortino_ratio': self._get_metric_safely(portfolio, 'get_sortino_ratio'),
                'max_drawdown': self._get_max_drawdown(portfolio),
                'var_95': self._get_metric_safely(portfolio, 'get_var_historic'),
                'cvar_95': self._get_metric_safely(portfolio, 'get_cvar_historic')
            }
            
            # Convert to more readable format
            formatted_metrics = {}
            for key, value in metrics.items():
                if isinstance(value, (int, float)) and not pd.isna(value):
                    if 'return' in key or 'ratio' in key:
                        formatted_metrics[key] = f"{value:.2%}"
                    elif 'volatility' in key or 'drawdown' in key or 'var' in key:
                        formatted_metrics[key] = f"{value:.2%}"
                    else:
                        formatted_metrics[key] = f"{value:.4f}"
                else:
                    formatted_metrics[key] = 'N/A'
            
            return formatted_metrics
        except Exception as e:
            print(f"Error getting portfolio performance: {e}")
            return self._get_fallback_metrics(portfolio)
    
    def _get_metric_safely(self, portfolio: ok.Portfolio, method_name: str) -> float:
        """Get portfolio metric using specified method with error handling"""
        try:
            if hasattr(portfolio, method_name):
                method = getattr(portfolio, method_name)
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
            print(f"Error getting {method_name}: {e}")
            return 0.0
    
    def _calculate_portfolio_volatility(self, portfolio: ok.Portfolio) -> float:
        """Calculate portfolio volatility from returns data"""
        try:
            if hasattr(portfolio, 'assets_ror') and portfolio.assets_ror is not None:
                # Calculate portfolio volatility from monthly returns
                portfolio_returns = portfolio.assets_ror.sum(axis=1)
                return portfolio_returns.std() * np.sqrt(12)  # Annualize monthly volatility
            else:
                return 0.0
        except Exception as e:
            print(f"Error calculating volatility: {e}")
            return 0.0
    
    def _get_max_drawdown(self, portfolio: ok.Portfolio) -> float:
        """Get maximum drawdown from portfolio data"""
        try:
            if hasattr(portfolio, 'drawdowns') and portfolio.drawdowns is not None:
                return portfolio.drawdowns.min()
            else:
                return 0.0
        except Exception as e:
            print(f"Error getting max drawdown: {e}")
            return 0.0
    
    def _get_fallback_metrics(self, portfolio: ok.Portfolio) -> Dict:
        """Fallback method for getting basic portfolio metrics"""
        try:
            # Try to get basic information
            basic_metrics = {}
            
            if hasattr(portfolio, 'get_cumulative_return'):
                try:
                    cum_return = portfolio.get_cumulative_return()
                    basic_metrics['total_return'] = f"{cum_return:.2%}" if isinstance(cum_return, (int, float)) else 'N/A'
                except:
                    basic_metrics['total_return'] = 'N/A'
            
            if hasattr(portfolio, 'get_cagr'):
                try:
                    cagr = portfolio.get_cagr()
                    basic_metrics['annual_return'] = f"{cagr:.2%}" if isinstance(cagr, (int, float)) else 'N/A'
                except:
                    basic_metrics['annual_return'] = 'N/A'
            
            # Fill missing metrics
            for metric in ['volatility', 'sharpe_ratio', 'max_drawdown', 'var_95', 'cvar_95']:
                if metric not in basic_metrics:
                    basic_metrics[metric] = 'N/A'
            
            return basic_metrics
            
        except Exception as e:
            print(f"Fallback method failed: {e}")
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
        """Generate portfolio performance chart using correct Okama v1.5.0 data sources"""
        try:
            print(f"Generating performance chart for portfolio...")
            
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Plot cumulative returns using correct data source
            try:
                if hasattr(portfolio, 'get_cumulative_return'):
                    cumulative_data = portfolio.get_cumulative_return()
                    if hasattr(cumulative_data, 'plot'):
                        cumulative_data.plot(ax=ax1, title='Cumulative Returns')
                        ax1.set_ylabel('Cumulative Return')
                        ax1.grid(True)
                        print("✓ Successfully plotted cumulative returns")
                    else:
                        # Handle case where cumulative_data is not a pandas Series
                        if hasattr(cumulative_data, '__len__'):
                            ax1.plot(range(len(cumulative_data)), cumulative_data, title='Cumulative Returns')
                            ax1.set_ylabel('Cumulative Return')
                            ax1.grid(True)
                            print("✓ Successfully plotted cumulative returns (array)")
                        else:
                            raise Exception("Cannot plot cumulative returns data")
                else:
                    raise Exception("No cumulative returns method available")
                    
            except Exception as e:
                print(f"✗ Error plotting cumulative returns: {e}")
                ax1.text(0.5, 0.5, f'Cumulative Returns\n(Error: {str(e)[:50]}...)', 
                        ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title('Cumulative Returns - Error')
                ax1.grid(True)
            
            # Plot drawdowns using correct data source
            try:
                if hasattr(portfolio, 'drawdowns') and portfolio.drawdowns is not None:
                    portfolio.drawdowns.plot(ax=ax2, title='Portfolio Drawdowns')
                    ax2.set_ylabel('Drawdown')
                    ax2.set_xlabel('Date')
                    ax2.grid(True)
                    print("✓ Successfully plotted drawdowns")
                else:
                    # Try to calculate drawdowns from cumulative returns
                    if hasattr(portfolio, 'get_cumulative_return'):
                        try:
                            cum_returns = portfolio.get_cumulative_return()
                            if hasattr(cum_returns, '__len__') and len(cum_returns) > 1:
                                # Calculate drawdowns
                                peak = np.maximum.accumulate(cum_returns)
                                drawdown = (cum_returns - peak) / peak
                                ax2.plot(drawdown, title='Portfolio Drawdowns (Calculated)')
                                ax2.set_ylabel('Drawdown')
                                ax2.set_xlabel('Time')
                                ax2.grid(True)
                                print("✓ Successfully plotted calculated drawdowns")
                            else:
                                raise Exception("Insufficient data for drawdown calculation")
                        except Exception as calc_error:
                            print(f"⚠️ Error calculating drawdowns: {calc_error}")
                            raise calc_error
                    else:
                        raise Exception("No drawdown data available")
                        
            except Exception as e:
                print(f"✗ Error plotting drawdowns: {e}")
                ax2.text(0.5, 0.5, f'Drawdowns\n(Error: {str(e)[:50]}...)', 
                        ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title('Portfolio Drawdowns - Error')
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
            return self._create_error_chart(f"Performance chart error: {str(e)}")
    
    def _create_error_chart(self, error_message: str) -> bytes:
        """Create a simple error chart when chart generation fails"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            ax.text(0.5, 0.5, f'Chart Generation Error\n{error_message}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Portfolio Performance Chart')
            ax.grid(True)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except:
            # If even the error chart fails, return a simple placeholder
            return self._create_placeholder_image()
    
    def _create_placeholder_image(self) -> bytes:
        """Create a simple placeholder image when all else fails"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            ax.text(0.5, 0.5, 'Chart Unavailable\nPlease try again later', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Chart Placeholder')
            ax.axis('off')
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except:
            # Return empty bytes if everything fails
            return b''
    
    def get_asset_info(self, symbol: str) -> Dict:
        """Get basic information about an asset using correct Okama v1.5.0 API"""
        try:
            asset = ok.Asset(symbol)
            
            # Get metrics using correct methods
            metrics = {}
            
            # Try to get CAGR
            try:
                if hasattr(asset, 'get_cagr'):
                    cagr = asset.get_cagr()
                    metrics['annual_return'] = f"{cagr:.2%}" if isinstance(cagr, (int, float)) else 'N/A'
                else:
                    metrics['annual_return'] = 'N/A'
            except:
                metrics['annual_return'] = 'N/A'
            
            # Try to get cumulative return
            try:
                if hasattr(asset, 'get_cumulative_return'):
                    cum_return = asset.get_cumulative_return()
                    metrics['total_return'] = f"{cum_return:.2%}" if isinstance(cum_return, (int, float)) else 'N/A'
                else:
                    metrics['total_return'] = 'N/A'
            except:
                metrics['total_return'] = 'N/A'
            
            # Try to get volatility
            try:
                if hasattr(asset, 'ror') and asset.ror is not None:
                    volatility = asset.ror.std() * np.sqrt(12)  # Annualize monthly volatility
                    metrics['volatility'] = f"{volatility:.2%}"
                else:
                    metrics['volatility'] = 'N/A'
            except:
                metrics['volatility'] = 'N/A'
            
            # Try to get Sharpe ratio
            try:
                if hasattr(asset, 'get_sharpe_ratio'):
                    sharpe = asset.get_sharpe_ratio()
                    metrics['sharpe_ratio'] = f"{sharpe:.2f}" if isinstance(sharpe, (int, float)) else 'N/A'
                else:
                    metrics['sharpe_ratio'] = 'N/A'
            except:
                metrics['sharpe_ratio'] = 'N/A'
            
            # Try to get max drawdown
            try:
                if hasattr(asset, 'drawdowns') and asset.drawdowns is not None:
                    max_dd = asset.drawdowns.min()
                    metrics['max_drawdown'] = f"{max_dd:.2%}" if isinstance(max_dd, (int, float)) else 'N/A'
                else:
                    metrics['max_drawdown'] = 'N/A'
            except:
                metrics['max_drawdown'] = 'N/A'
            
            # Try to get VaR and CVaR
            try:
                if hasattr(asset, 'get_var_historic'):
                    var = asset.get_var_historic()
                    metrics['var_95'] = f"{var:.2%}" if isinstance(var, (int, float)) else 'N/A'
                else:
                    metrics['var_95'] = 'N/A'
            except:
                metrics['var_95'] = 'N/A'
            
            try:
                if hasattr(asset, 'get_cvar_historic'):
                    cvar = asset.get_cvar_historic()
                    metrics['cvar_95'] = f"{cvar:.2%}" if isinstance(cvar, (int, float)) else 'N/A'
                else:
                    metrics['cvar_95'] = 'N/A'
            except:
                metrics['cvar_95'] = 'N/A'
            
            return {
                'symbol': symbol,
                **metrics
            }
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}
    
    # Delegate to specialized services
    def generate_correlation_matrix(self, symbols: List[str]) -> bytes:
        """Generate correlation matrix using specialized service"""
        return self.correlation_service.generate_correlation_matrix(symbols)
    
    def generate_efficient_frontier(self, symbols: List[str]) -> bytes:
        """Generate efficient frontier using specialized service"""
        return self.frontier_service.generate_efficient_frontier(symbols)
    
    def compare_assets(self, symbols: List[str]) -> Tuple[Dict, bytes]:
        """Compare assets using specialized service"""
        return self.comparison_service.compare_assets(symbols)
    
    def create_pension_portfolio(self, symbols: List[str], weights: Optional[List[float]] = None, 
                                ccy: str = 'RUB', initial_amount: float = 1000000,
                                cashflow: float = -50000, rebalancing_period: str = 'year') -> ok.Portfolio:
        """Create pension portfolio using specialized service"""
        return self.pension_service.create_pension_portfolio(symbols, weights, ccy, initial_amount, cashflow, rebalancing_period)
    
    def get_inflation_analysis(self, portfolio: ok.Portfolio) -> Tuple[Dict, bytes]:
        """Get inflation analysis using specialized service"""
        return self.pension_service.get_inflation_analysis(portfolio)
    
    def generate_monte_carlo_forecast(self, portfolio: ok.Portfolio, years: int = 30, 
                                    n_scenarios: int = 50, distribution: str = "norm") -> bytes:
        """Generate Monte Carlo forecast using specialized service"""
        return self.monte_carlo_service.generate_monte_carlo_forecast(portfolio, years, n_scenarios, distribution)
    
    def get_asset_allocation_analysis(self, portfolio: ok.Portfolio) -> Tuple[Dict, bytes]:
        """Get asset allocation analysis using specialized service"""
        return self.allocation_service.get_asset_allocation_analysis(portfolio)
    
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
                    
                    # Test key methods
                    key_methods = ['get_cagr', 'get_cumulative_return', 'get_sharpe_ratio', 'get_var_historic', 'get_cvar_historic']
                    for method in key_methods:
                        if hasattr(asset, method):
                            try:
                                value = getattr(asset, method)()
                                print(f"  ✓ {method}: {value}")
                            except Exception as e:
                                print(f"  ⚠️ {method} error: {e}")
                        else:
                            print(f"  ✗ {method}: Not available")
                    
                    asset_info[symbol] = "OK"
                except Exception as e:
                    print(f"  ✗ Error with {symbol}: {e}")
                    asset_info[symbol] = f"Error: {str(e)}"
            
            # Test portfolio creation
            try:
                portfolio = ok.Portfolio(symbols, inflation=True)
                print(f"\nPortfolio created successfully:")
                print(f"  Type: {type(portfolio)}")
                print(f"  Available methods: {[m for m in dir(portfolio) if not m.startswith('_') and callable(getattr(portfolio, m))]}")
                
                # Test portfolio methods
                test_methods = ['get_cagr', 'get_cumulative_return', 'get_sharpe_ratio', 'get_var_historic', 'get_cvar_historic']
                for method in test_methods:
                    if hasattr(portfolio, method):
                        try:
                            result = getattr(portfolio, method)()
                            print(f"  ✓ {method}: {result}")
                        except Exception as e:
                            print(f"  ⚠️ {method} error: {e}")
                    else:
                        print(f"  ✗ {method}: Not available")
                
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
    
    def debug_portfolio_data(self, portfolio: ok.Portfolio) -> Dict:
        """Debug method to inspect what data is available in a portfolio"""
        try:
            print(f"Debugging portfolio data availability...")
            
            debug_info = {
                'portfolio_type': type(portfolio).__name__,
                'available_attributes': [],
                'available_methods': [],
                'data_sources': {},
                'errors': []
            }
            
            # Get all available attributes and methods
            all_attrs = [attr for attr in dir(portfolio) if not attr.startswith('_')]
            debug_info['available_attributes'] = [attr for attr in all_attrs if not callable(getattr(portfolio, attr))]
            debug_info['available_methods'] = [attr for attr in all_attrs if callable(getattr(portfolio, attr))]
            
            # Test key data attributes
            key_attrs = [
                'close_monthly', 'assets_ror', 'drawdowns', 'annual_return_ts',
                'assets_weights', 'currencies', 'currency'
            ]
            
            for attr in key_attrs:
                try:
                    if hasattr(portfolio, attr):
                        value = getattr(portfolio, attr)
                        if value is not None:
                            if hasattr(value, 'empty'):
                                debug_info['data_sources'][attr] = {
                                    'type': type(value).__name__,
                                    'empty': value.empty,
                                    'shape': value.shape if hasattr(value, 'shape') else 'N/A',
                                    'length': len(value) if hasattr(value, '__len__') else 'N/A'
                                }
                            else:
                                debug_info['data_sources'][attr] = {
                                    'type': type(value).__name__,
                                    'value': str(value)[:100] if value is not None else 'None'
                                }
                        else:
                            debug_info['data_sources'][attr] = {'type': 'None', 'value': 'None'}
                    else:
                        debug_info['data_sources'][attr] = {'type': 'Not available', 'value': 'N/A'}
                except Exception as e:
                    debug_info['errors'].append(f"Error testing {attr}: {str(e)}")
                    debug_info['data_sources'][attr] = {'type': 'Error', 'error': str(e)}
            
            print(f"✓ Portfolio data debugging completed")
            return debug_info
            
        except Exception as e:
            print(f"✗ Error debugging portfolio data: {e}")
            return {'error': str(e)}

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
            return portfolio
        except Exception as e:
            raise Exception(f"Error creating portfolio: {str(e)}")
    
    def get_portfolio_performance(self, portfolio: ok.Portfolio) -> Dict:
        """Get comprehensive portfolio performance metrics"""
        try:
            # Basic metrics
            metrics = {
                'total_return': portfolio.total_return,
                'annual_return': portfolio.mean_return,
                'volatility': portfolio.volatility,
                'sharpe_ratio': portfolio.sharpe_ratio,
                'max_drawdown': portfolio.max_drawdown,
                'var_95': portfolio.var_95,
                'cvar_95': portfolio.cvar_95
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
            raise Exception(f"Error getting portfolio performance: {str(e)}")
    
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
            # Get historical data for symbols
            data = {}
            for symbol in symbols:
                try:
                    asset = ok.Asset(symbol)
                    data[symbol] = asset.price_ts
                except:
                    continue
            
            if len(data) < 2:
                raise Exception("Need at least 2 valid symbols for correlation matrix")
            
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
            # Create efficient frontier
            ef = ok.EfficientFrontier(symbols)
            
            # Generate efficient frontier
            ef_points = ef.efficient_frontier_points
            
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
                    comparison_metrics[symbol] = {
                        'total_return': asset.total_return,
                        'annual_return': asset.mean_return,
                        'volatility': asset.volatility,
                        'sharpe_ratio': asset.sharpe_ratio,
                        'max_drawdown': asset.max_drawdown
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
                'total_return': f"{asset.total_return:.2%}",
                'annual_return': f"{asset.mean_return:.2%}",
                'volatility': f"{asset.volatility:.2%}",
                'sharpe_ratio': f"{asset.sharpe_ratio:.2f}",
                'max_drawdown': f"{asset.max_drawdown:.2%}",
                'var_95': f"{asset.var_95:.2%}",
                'cvar_95': f"{asset.cvar_95:.2%}"
            }
        except Exception as e:
            return {'symbol': symbol, 'error': str(e)}

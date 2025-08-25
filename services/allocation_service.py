import okama as ok
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from typing import List, Dict, Tuple
import warnings

warnings.filterwarnings('ignore')

class AllocationService:
    """Service for asset allocation analysis"""
    
    def __init__(self):
        self.plt_style = 'seaborn-v0_8'
        plt.style.use(self.plt_style)
    
    def get_asset_allocation_analysis(self, portfolio: ok.Portfolio) -> Tuple[Dict, bytes]:
        """Get detailed asset allocation analysis using correct Okama v1.5.0 API"""
        try:

            
            # Get portfolio table if available
            portfolio_table = None
            if hasattr(portfolio, 'table'):
                portfolio_table = portfolio.table
            
            # Create allocation chart
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Asset Allocation Analysis', fontsize=16)
            
            # Pie chart of weights
            if hasattr(portfolio, 'assets_weights') and portfolio.assets_weights is not None:
                weights = portfolio.assets_weights
                symbols = portfolio.symbols
                
                # Handle different weight formats
                if hasattr(weights, 'values'):
                    weights_values = weights.values
                elif hasattr(weights, '__len__'):
                    weights_values = weights
                else:
                    weights_values = [1/len(symbols)] * len(symbols)
                
                axes[0, 0].pie(weights_values, labels=symbols, autopct='%1.1f%%', startangle=90)
                axes[0, 0].set_title('Portfolio Weights')

            else:
                # Equal weights fallback
                symbols = portfolio.symbols
                equal_weights = [1/len(symbols)] * len(symbols)
                axes[0, 0].pie(equal_weights, labels=symbols, autopct='%1.1f%%', startangle=90)
                axes[0, 0].set_title('Portfolio Weights (Equal)')

            
            # Asset performance comparison
            if portfolio_table is not None and hasattr(portfolio_table, 'columns'):
                if 'total_return' in portfolio_table.columns:
                    returns = portfolio_table['total_return'].values
                    axes[0, 1].bar(symbols, returns)
                    axes[0, 1].set_title('Individual Asset Returns')
                    axes[0, 1].set_ylabel('Return')
                    axes[0, 1].tick_params(axis='x', rotation=45)

                else:
                    # Try to get returns from individual assets
                    returns = self._get_individual_returns(portfolio)
                    if returns:
                        axes[0, 1].bar(symbols, returns)
                        axes[0, 1].set_title('Individual Asset Returns')
                        axes[0, 1].set_ylabel('Return')
                        axes[0, 1].tick_params(axis='x', rotation=45)

                    else:
                        axes[0, 1].text(0.5, 0.5, 'Return data not available', ha='center', va='center')
                        axes[0, 1].set_title('Individual Asset Returns')
            else:
                # Try to get returns from individual assets
                returns = self._get_individual_returns(portfolio)
                if returns:
                    axes[0, 1].bar(symbols, returns)
                    axes[0, 1].set_title('Individual Asset Returns')
                    axes[0, 1].set_ylabel('Return')
                    axes[0, 1].tick_params(axis='x', rotation=45)
                    
                else:
                    axes[0, 1].text(0.5, 0.5, 'Return data not available', ha='center', va='center')
                    axes[0, 1].set_title('Individual Asset Returns')
            
            # Risk comparison
            volatilities = self._get_individual_volatilities(portfolio)
            if volatilities:
                axes[1, 0].bar(symbols, volatilities)
                axes[1, 0].set_title('Individual Asset Volatility')
                axes[1, 0].set_ylabel('Volatility')
                axes[1, 0].tick_params(axis='x', rotation=45)

            else:
                axes[1, 0].text(0.5, 0.5, 'Volatility data not available', ha='center', va='center')
                axes[1, 0].set_title('Individual Asset Volatility')
            
            # Sharpe ratio comparison
            sharpe_ratios = self._get_individual_sharpe_ratios(portfolio)
            if sharpe_ratios:
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
                'currency': getattr(portfolio, 'currency', 'Unknown'),
                'total_value': 'N/A',  # Would need to calculate from data
                'weights': self._get_portfolio_weights(portfolio),
                'symbols': portfolio.symbols
            }
            

            return allocation_metrics, img_buffer.getvalue()
            
        except Exception as e:
            return {'error': str(e)}, self._create_error_chart(f"Asset allocation analysis error: {str(e)}")
    
    def _get_individual_returns(self, portfolio: ok.Portfolio) -> List[float]:
        """Get individual asset returns"""
        try:
            returns = []
            for symbol in portfolio.symbols:
                try:
                    asset = ok.Asset(symbol)
                    if hasattr(asset, 'get_cumulative_return'):
                        cum_return = asset.get_cumulative_return()
                        if isinstance(cum_return, (int, float)) and not pd.isna(cum_return):
                            returns.append(cum_return)
                        elif hasattr(cum_return, 'iloc') and not cum_return.empty:
                            returns.append(cum_return.iloc[-1])
                        else:
                            returns.append(0.0)
                    else:
                        returns.append(0.0)
                except:
                    returns.append(0.0)
            return returns
        except:
            return []
    
    def _get_individual_volatilities(self, portfolio: ok.Portfolio) -> List[float]:
        """Get individual asset volatilities"""
        try:
            volatilities = []
            for symbol in portfolio.symbols:
                try:
                    asset = ok.Asset(symbol)
                    if hasattr(asset, 'ror') and asset.ror is not None:
                        if hasattr(asset.ror, 'empty') and not asset.ror.empty:
                            vol = asset.ror.std() * np.sqrt(12)  # Annualize
                            volatilities.append(vol)
                        elif hasattr(asset.ror, '__len__') and len(asset.ror) > 0:
                            vol = np.std(asset.ror) * np.sqrt(12)
                            volatilities.append(vol)
                        else:
                            volatilities.append(0.0)
                    else:
                        volatilities.append(0.0)
                except:
                    volatilities.append(0.0)
            return volatilities
        except:
            return []
    
    def _get_individual_sharpe_ratios(self, portfolio: ok.Portfolio) -> List[float]:
        """Get individual asset Sharpe ratios"""
        try:
            sharpe_ratios = []
            for symbol in portfolio.symbols:
                try:
                    asset = ok.Asset(symbol)
                    if hasattr(asset, 'get_sharpe_ratio'):
                        sharpe = asset.get_sharpe_ratio()
                        if isinstance(sharpe, (int, float)) and not pd.isna(sharpe):
                            sharpe_ratios.append(sharpe)
                        else:
                            sharpe_ratios.append(0.0)
                    else:
                        sharpe_ratios.append(0.0)
                except:
                    sharpe_ratios.append(0.0)
            return sharpe_ratios
        except:
            return []
    
    def _get_portfolio_weights(self, portfolio: ok.Portfolio) -> List[float]:
        """Get portfolio weights"""
        try:
            if hasattr(portfolio, 'assets_weights') and portfolio.assets_weights is not None:
                weights = portfolio.assets_weights
                if hasattr(weights, 'values'):
                    return weights.values.tolist()
                elif hasattr(weights, '__len__'):
                    return list(weights)
                else:
                    return [1/len(portfolio.symbols)] * len(portfolio.symbols)
            else:
                return [1/len(portfolio.symbols)] * len(portfolio.symbols)
        except:
            return [1/len(portfolio.symbols)] * len(portfolio.symbols)
    
    def _create_error_chart(self, error_message: str) -> bytes:
        """Create a simple error chart when chart generation fails"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            ax.text(0.5, 0.5, f'Chart Generation Error\n{error_message}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Asset Allocation Analysis')
            ax.grid(True)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except:
            # Return empty bytes if everything fails
            return b''

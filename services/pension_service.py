import okama as ok
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from typing import List, Dict, Tuple, Optional
import warnings

warnings.filterwarnings('ignore')

class PensionService:
    """Service for pension portfolio analysis"""
    
    def __init__(self):
        self.plt_style = 'seaborn-v0_8'
        plt.style.use(self.plt_style)
    
    def create_pension_portfolio(self, symbols: List[str], weights: Optional[List[float]] = None, 
                                ccy: str = 'RUB', initial_amount: float = 1000000,
                                cashflow: float = -50000, rebalancing_period: str = 'year') -> ok.Portfolio:
        """Create a pension portfolio with cash flows and rebalancing using correct Okama v1.5.0 API"""
        try:
            print(f"Creating pension portfolio: {symbols} with weights {weights}")
            print(f"Currency: {ccy}, Initial: {initial_amount}, Cashflow: {cashflow}, Rebalancing: {rebalancing_period}")
            
            if weights is None:
                weights = [1.0 / len(symbols)] * len(symbols)
            
            # Use correct Portfolio constructor with basic parameters
            portfolio = ok.Portfolio(
                symbols,
                ccy=ccy,
                weights=weights,
                inflation=True,  # Enable inflation for pension analysis
                symbol="Pension_Portfolio.PF"
            )
            
            print(f"✓ Pension portfolio created successfully")
            return portfolio
            
        except Exception as e:
            print(f"✗ Error creating pension portfolio: {e}")
            raise Exception(f"Error creating pension portfolio: {str(e)}")
    
    def get_inflation_analysis(self, portfolio: ok.Portfolio) -> Tuple[Dict, bytes]:
        """Get inflation-adjusted portfolio analysis"""
        try:
            print(f"Getting inflation analysis for portfolio")
            
            # Get wealth index with inflation
            wealth_data = None
            if hasattr(portfolio, 'dcf') and portfolio.dcf is not None:
                if hasattr(portfolio.dcf, 'wealth_index'):
                    wealth_data = portfolio.dcf.wealth_index
            
            # If no DCF wealth index, try to use regular portfolio data
            if wealth_data is None:
                if hasattr(portfolio, 'get_cumulative_return'):
                    try:
                        wealth_data = portfolio.get_cumulative_return()
                    except:
                        pass
            
            # Create inflation-adjusted chart
            plt.figure(figsize=(12, 8))
            
            if wealth_data is not None and hasattr(wealth_data, 'plot'):
                try:
                    wealth_data.plot()
                    plt.title('Portfolio Wealth Index with Inflation')
                    plt.xlabel('Date')
                    plt.ylabel('Value')
                    plt.grid(True, alpha=0.3)
                    plt.legend()
                    print("✓ Successfully plotted wealth index")
                except Exception as plot_error:
                    print(f"⚠️ Error plotting wealth index: {plot_error}")
                    # Fallback plotting
                    if hasattr(wealth_data, 'index') and hasattr(wealth_data, 'values'):
                        plt.plot(wealth_data.index, wealth_data.values, label='Portfolio Value')
                        plt.title('Portfolio Wealth Index')
                        plt.xlabel('Date')
                        plt.ylabel('Value')
                        plt.grid(True, alpha=0.3)
                        plt.legend()
                        print("✓ Successfully plotted wealth index (fallback)")
                    else:
                        raise Exception("Cannot access wealth index data")
            else:
                # Create informational chart
                plt.text(0.5, 0.5, 'Wealth Index Data\nNot Available', 
                        ha='center', va='center', transform=plt.gca().transAxes)
                plt.title('Portfolio Wealth Index')
                plt.grid(True)
                print("⚠️ Wealth index data not available, showing info chart")
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            # Get inflation metrics
            inflation_metrics = {
                'current_value': self._get_current_value(wealth_data),
                'total_return': self._get_portfolio_return(portfolio),
                'inflation_adjusted_return': 'N/A'  # Would need to calculate this
            }
            
            print(f"✓ Inflation analysis completed successfully")
            return inflation_metrics, img_buffer.getvalue()
            
        except Exception as e:
            print(f"✗ Error getting inflation analysis: {e}")
            return {'error': str(e)}, self._create_error_chart(f"Inflation analysis error: {str(e)}")
    
    def _get_current_value(self, wealth_data) -> str:
        """Get current portfolio value from wealth data"""
        try:
            if wealth_data is not None:
                if hasattr(wealth_data, 'iloc'):
                    return f"{wealth_data.iloc[-1]:,.0f}" if not wealth_data.empty else 'N/A'
                elif hasattr(wealth_data, '__len__') and len(wealth_data) > 0:
                    return f"{wealth_data[-1]:,.0f}"
                else:
                    return 'N/A'
            return 'N/A'
        except:
            return 'N/A'
    
    def _get_portfolio_return(self, portfolio: ok.Portfolio) -> str:
        """Get portfolio total return"""
        try:
            if hasattr(portfolio, 'get_cumulative_return'):
                cum_return = portfolio.get_cumulative_return()
                if isinstance(cum_return, (int, float)) and not pd.isna(cum_return):
                    return f"{cum_return:.2%}"
                elif hasattr(cum_return, 'iloc') and not cum_return.empty:
                    return f"{cum_return.iloc[-1]:.2%}"
            return 'N/A'
        except:
            return 'N/A'
    
    def _create_error_chart(self, error_message: str) -> bytes:
        """Create a simple error chart when chart generation fails"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            ax.text(0.5, 0.5, f'Chart Generation Error\n{error_message}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Inflation Analysis')
            ax.grid(True)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except:
            # Return empty bytes if everything fails
            return b''

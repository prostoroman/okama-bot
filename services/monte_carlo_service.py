import okama as ok
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from typing import List, Dict
import warnings

warnings.filterwarnings('ignore')

class MonteCarloService:
    """Service for Monte Carlo portfolio forecasting"""
    
    def __init__(self):
        self.plt_style = 'seaborn-v0_8'
        plt.style.use(self.plt_style)
    
    def generate_monte_carlo_forecast(self, portfolio: ok.Portfolio, years: int = 30, 
                                    n_scenarios: int = 50, distribution: str = "norm") -> bytes:
        """Generate Monte Carlo forecast for portfolio using correct Okama v1.5.0 API"""
        try:
            print(f"Generating Monte Carlo forecast: {years} years, {n_scenarios} scenarios, {distribution} distribution")
            
            # Check if portfolio has DCF capabilities
            if not hasattr(portfolio, 'dcf') or portfolio.dcf is None:
                print("⚠️ Portfolio does not have DCF capabilities, trying alternative method")
                return self._generate_alternative_forecast(portfolio, years, n_scenarios, distribution)
            
            # Generate forecast using DCF method
            try:
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
                
                print(f"✓ Monte Carlo forecast generated successfully using DCF method")
                return img_buffer.getvalue()
                
            except Exception as dcf_error:
                print(f"⚠️ DCF Monte Carlo method failed: {dcf_error}")
                return self._generate_alternative_forecast(portfolio, years, n_scenarios, distribution)
            
        except Exception as e:
            print(f"✗ Error generating Monte Carlo forecast: {e}")
            return self._create_error_chart(f"Monte Carlo forecast error: {str(e)}")
    
    def _generate_alternative_forecast(self, portfolio: ok.Portfolio, years: int, 
                                     n_scenarios: int, distribution: str) -> bytes:
        """Generate alternative forecast when DCF method is not available"""
        try:
            print(f"Generating alternative forecast method")
            
            # Get portfolio returns data
            returns_data = None
            if hasattr(portfolio, 'assets_ror') and portfolio.assets_ror is not None:
                returns_data = portfolio.assets_ror.sum(axis=1)  # Portfolio returns
            elif hasattr(portfolio, 'ror') and portfolio.ror is not None:
                returns_data = portfolio.ror
            
            if returns_data is None:
                raise Exception("No returns data available for forecasting")
            
            # Calculate basic statistics
            mean_return = returns_data.mean() * 12  # Annualize monthly returns
            volatility = returns_data.std() * np.sqrt(12)  # Annualize monthly volatility
            
            # Generate Monte Carlo scenarios
            np.random.seed(42)  # For reproducibility
            
            if distribution == "norm":
                # Normal distribution
                random_returns = np.random.normal(mean_return, volatility, (years, n_scenarios))
            elif distribution == "lognorm":
                # Log-normal distribution
                log_mean = np.log(1 + mean_return) - 0.5 * volatility**2
                random_returns = np.random.lognormal(log_mean, volatility, (years, n_scenarios)) - 1
            else:
                # Default to normal
                random_returns = np.random.normal(mean_return, volatility, (years, n_scenarios))
            
            # Calculate cumulative returns
            cumulative_returns = np.cumprod(1 + random_returns, axis=0)
            
            # Create forecast chart
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            
            # Plot individual scenarios
            for i in range(min(n_scenarios, 20)):  # Show first 20 scenarios
                ax1.plot(range(1, years + 1), cumulative_returns[:, i], 
                         alpha=0.3, color='blue', linewidth=0.5)
            
            # Plot mean scenario
            mean_scenario = np.mean(cumulative_returns, axis=1)
            ax1.plot(range(1, years + 1), mean_scenario, 
                     color='red', linewidth=2, label='Mean Scenario')
            
            # Plot confidence intervals
            percentile_95 = np.percentile(cumulative_returns, 95, axis=1)
            percentile_5 = np.percentile(cumulative_returns, 5, axis=1)
            ax1.fill_between(range(1, years + 1), percentile_5, percentile_95, 
                            alpha=0.2, color='red', label='90% Confidence Interval')
            
            ax1.set_title(f'Monte Carlo Portfolio Forecast ({n_scenarios} scenarios)')
            ax1.set_xlabel('Years')
            ax1.set_ylabel('Portfolio Value (Multiple of Initial)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # Plot distribution of final values
            final_values = cumulative_returns[-1, :]
            ax2.hist(final_values, bins=30, alpha=0.7, color='blue', edgecolor='black')
            ax2.axvline(mean_scenario[-1], color='red', linestyle='--', 
                        label=f'Mean: {mean_scenario[-1]:.2f}x')
            ax2.axvline(np.median(final_values), color='green', linestyle='--', 
                        label=f'Median: {np.median(final_values):.2f}x')
            
            ax2.set_title('Distribution of Final Portfolio Values')
            ax2.set_xlabel('Portfolio Value (Multiple of Initial)')
            ax2.set_ylabel('Frequency')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save to bytes
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            print(f"✓ Alternative Monte Carlo forecast generated successfully")
            return img_buffer.getvalue()
            
        except Exception as e:
            print(f"✗ Alternative forecast method failed: {e}")
            return self._create_error_chart(f"Alternative forecast error: {str(e)}")
    
    def _create_error_chart(self, error_message: str) -> bytes:
        """Create a simple error chart when chart generation fails"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            ax.text(0.5, 0.5, f'Chart Generation Error\n{error_message}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Monte Carlo Forecast')
            ax.grid(True)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except:
            # Return empty bytes if everything fails
            return b''

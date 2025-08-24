import okama as ok
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
from typing import List, Dict
import warnings

warnings.filterwarnings('ignore')

class FrontierService:
    """Service for efficient frontier analysis"""
    
    def __init__(self):
        self.plt_style = 'seaborn-v0_8'
        plt.style.use(self.plt_style)
    
    def generate_efficient_frontier(self, symbols: List[str]) -> bytes:
        """Generate efficient frontier plot using correct Okama v1.5.0 API"""
        try:
            print(f"Generating efficient frontier for symbols: {symbols}")
            
            # Create efficient frontier with inflation=True to avoid errors
            ef = ok.EfficientFrontier(symbols, inflation=True)
            print(f"EfficientFrontier created successfully")
            
            # Get efficient frontier points
            ef_points = ef.ef_points
            print(f"Efficient frontier points: {type(ef_points)}, shape: {ef_points.shape if hasattr(ef_points, 'shape') else 'N/A'}")
            
            plt.figure(figsize=(12, 8))
            
            # Check if we have efficient frontier points
            if hasattr(ef_points, 'shape') and ef_points.shape[0] > 0:
                try:
                    # Check for expected columns
                    if hasattr(ef_points, 'columns'):
                        if 'Risk' in ef_points.columns and 'Mean return' in ef_points.columns:
                            plt.scatter(ef_points['Risk'], ef_points['Mean return'], alpha=0.6, s=50)
                            plt.plot(ef_points['Risk'], ef_points['Mean return'], 'b-', linewidth=2)
                            print("✓ Plotted efficient frontier curve")
                        elif 'Risk' in ef_points.columns and 'CAGR' in ef_points.columns:
                            plt.scatter(ef_points['Risk'], ef_points['CAGR'], alpha=0.6, s=50)
                            plt.plot(ef_points['Risk'], ef_points['CAGR'], 'b-', linewidth=2)
                            print("✓ Plotted efficient frontier curve using CAGR")
                        else:
                            # Try to plot using first two numeric columns
                            numeric_cols = ef_points.select_dtypes(include=[np.number]).columns
                            if len(numeric_cols) >= 2:
                                plt.scatter(ef_points[numeric_cols[0]], ef_points[numeric_cols[1]], alpha=0.6, s=50)
                                plt.plot(ef_points[numeric_cols[0]], ef_points[numeric_cols[1]], 'b-', linewidth=2)
                                print(f"✓ Plotted efficient frontier using columns: {numeric_cols[0]}, {numeric_cols[1]}")
                            else:
                                raise Exception("No suitable numeric columns found")
                    else:
                        # Handle case where ef_points is not a DataFrame
                        if hasattr(ef_points, 'iloc'):
                            plt.scatter(ef_points.iloc[:, 0], ef_points.iloc[:, 1], alpha=0.6, s=50)
                            plt.plot(ef_points.iloc[:, 0], ef_points.iloc[:, 1], 'b-', linewidth=2)
                            print("✓ Plotted efficient frontier using generic data")
                        else:
                            raise Exception("Cannot access efficient frontier data")
                except Exception as e:
                    print(f"✗ Error plotting efficient frontier curve: {e}")
                    raise e
            else:
                print("⚠️ No efficient frontier points available")
                raise Exception("No efficient frontier points available")
            
            # Mark individual assets
            for i, symbol in enumerate(symbols):
                try:
                    asset = ok.Asset(symbol)
                    
                    # Get asset metrics using correct methods
                    volatility = 0
                    mean_return = 0
                    
                    # Try to get volatility from returns
                    if hasattr(asset, 'ror') and asset.ror is not None:
                        try:
                            volatility = asset.ror.std() * np.sqrt(12)  # Annualize monthly volatility
                        except:
                            pass
                    
                    # Try to get mean return
                    if hasattr(asset, 'get_cagr'):
                        try:
                            cagr = asset.get_cagr()
                            if isinstance(cagr, (int, float)) and not pd.isna(cagr):
                                mean_return = cagr
                            elif hasattr(cagr, 'iloc'):
                                mean_return = cagr.iloc[-1] if not cagr.empty else 0
                        except:
                            pass
                    
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
            print(f"✗ Error generating efficient frontier: {e}")
            return self._create_error_chart(f"Efficient frontier error: {str(e)}")
    
    def _create_error_chart(self, error_message: str) -> bytes:
        """Create a simple error chart when chart generation fails"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            ax.text(0.5, 0.5, f'Chart Generation Error\n{error_message}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Efficient Frontier')
            ax.grid(True)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except:
            # Return empty bytes if everything fails
            return b''

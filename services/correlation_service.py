import okama as ok
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io
from typing import List, Dict
import warnings

warnings.filterwarnings('ignore')

class CorrelationService:
    """Service for asset correlation analysis"""
    
    def __init__(self):
        self.plt_style = 'seaborn-v0_8'
        plt.style.use(self.plt_style)
    
    def generate_correlation_matrix(self, symbols: List[str]) -> bytes:
        """Generate correlation matrix heatmap using correct Okama v1.5.0 API"""
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
                    
                    # Use correct price data attribute from Okama v1.5.0
                    price_data = None
                    price_source = None
                    
                    # Check for close_monthly first (most reliable in v1.5.0)
                    if hasattr(asset, 'close_monthly') and asset.close_monthly is not None:
                        price_data = asset.close_monthly
                        price_source = 'close_monthly'
                    # Check for close_daily
                    elif hasattr(asset, 'close_daily') and asset.close_daily is not None:
                        price_data = asset.close_daily
                        price_source = 'close_daily'
                    # Check for adj_close
                    elif hasattr(asset, 'adj_close') and asset.adj_close is not None:
                        price_data = asset.adj_close
                        price_source = 'adj_close'
                    # Check for nav_ts (for ETFs)
                    elif hasattr(asset, 'nav_ts') and asset.nav_ts is not None:
                        price_data = asset.nav_ts
                        price_source = 'nav_ts'
                    else:
                        print(f"✗ {symbol} has no recognizable price data attribute")
                        failed_symbols.append(f"{symbol} (no price data found)")
                        continue
                    
                    print(f"Found price data in '{price_source}' for {symbol}: {type(price_data)}")
                    
                    # Check if we have valid data
                    if price_data is not None:
                        if hasattr(price_data, 'empty') and not price_data.empty:
                            data[symbol] = price_data
                            print(f"✓ Added {symbol} to correlation data (pandas Series)")
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
                return self._generate_fallback_correlation_matrix(symbols)
            
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
                    metric_names = ['ror', 'close_monthly', 'close_daily']
                    
                    for metric in metric_names:
                        if hasattr(asset, metric):
                            value = getattr(asset, metric)
                            if value is not None:
                                if hasattr(value, 'empty') and not value.empty:
                                    metrics[metric] = value
                                elif hasattr(value, '__len__') and len(value) > 0:
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
            
            # Plot volatility comparison if available
            if any('ror' in metrics for metrics in metrics_data.values()):
                volatilities = []
                symbols_list = []
                for symbol, metrics in metrics_data.items():
                    if 'ror' in metrics:
                        try:
                            vol = metrics['ror'].std() * np.sqrt(12)  # Annualize
                            volatilities.append(vol)
                            symbols_list.append(symbol)
                        except:
                            continue
                
                if volatilities:
                    axes[0, 0].bar(symbols_list, volatilities)
                    axes[0, 0].set_title('Volatility Comparison')
                    axes[0, 0].set_ylabel('Volatility')
                    axes[0, 0].tick_params(axis='x', rotation=45)
            
            # Plot return comparison if available
            if any('ror' in metrics for metrics in metrics_data.values()):
                returns = []
                symbols_list = []
                for symbol, metrics in metrics_data.items():
                    if 'ror' in metrics:
                        try:
                            ret = metrics['ror'].mean() * 12  # Annualize
                            returns.append(ret)
                            symbols_list.append(symbol)
                        except:
                            continue
                
                if returns:
                    axes[0, 1].bar(symbols_list, returns)
                    axes[0, 1].set_title('Mean Return Comparison')
                    axes[0, 1].set_ylabel('Mean Return')
                    axes[0, 1].tick_params(axis='x', rotation=45)
            
            # Create a simple correlation-like matrix
            if len(metrics_data) >= 2:
                # Use volatility as a proxy for correlation (simplified)
                volatilities = []
                symbols_list = []
                for symbol, metrics in metrics_data.items():
                    if 'ror' in metrics:
                        try:
                            vol = metrics['ror'].std() * np.sqrt(12)
                            volatilities.append(vol)
                            symbols_list.append(symbol)
                        except:
                            continue
                
                if len(volatilities) > 1:
                    correlation_matrix = np.corrcoef(volatilities)
                    
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
            return self._create_error_chart(f"Correlation matrix error: {str(e)}")
    
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
            return self._create_error_chart(f"Info chart error: {str(e)}")
    
    def _create_error_chart(self, error_message: str) -> bytes:
        """Create a simple error chart when chart generation fails"""
        try:
            fig, ax = plt.subplots(1, 1, figsize=(10, 6))
            ax.text(0.5, 0.5, f'Chart Generation Error\n{error_message}', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Asset Correlation Matrix')
            ax.grid(True)
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            return img_buffer.getvalue()
        except:
            # Return empty bytes if everything fails
            return b''

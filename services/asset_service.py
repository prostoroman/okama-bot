"""
Asset Service for Okama Finance Bot

This service provides methods for retrieving financial asset information
using the Okama library.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import okama as ok
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class AssetService:
    """Service for retrieving asset information using Okama library"""
    
    def __init__(self):
        """Initialize the AssetService"""
        self.logger = logging.getLogger(__name__)
        
        # Known working asset symbols for suggestions
        self.known_assets = {
            'US': ['VOO.US', 'SPY.US', 'QQQ.US', 'AGG.US', 'AAPL.US', 'TSLA.US', 'MSFT.US'],
            'INDX': ['RGBITR.INDX', 'MCFTR.INDX', 'SPX.INDX', 'IXIC.INDX'],
            'COMM': ['GC.COMM', 'SI.COMM', 'CL.COMM', 'BRENT.COMM'],
            'FX': ['EURUSD.FX', 'GBPUSD.FX', 'USDJPY.FX'],
            'MOEX': ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX'],
            'LSE': ['VOD.LSE', 'HSBA.LSE', 'BP.LSE']
        }
    
    def _get_asset_suggestions(self, symbol: str) -> str:
        """Get suggestions for alternative assets when the requested one is not found"""
        # Extract the namespace from the symbol (e.g., 'CC' from 'BTC.CC')
        if '.' in symbol:
            namespace = symbol.split('.')[-1]
        else:
            namespace = 'US'  # Default to US stocks
        
        suggestions = []
        
        # Add suggestions from the same namespace
        if namespace in self.known_assets:
            suggestions.extend(self.known_assets[namespace][:3])  # First 3 suggestions
        
        # Add suggestions from other popular namespaces
        if namespace != 'US' and 'US' in self.known_assets:
            suggestions.extend(self.known_assets['US'][:2])
        
        if namespace != 'INDX' and 'INDX' in self.known_assets:
            suggestions.extend(self.known_assets['INDX'][:2])
        
        if suggestions:
            return f"Попробуйте эти доступные активы:\n" + "\n".join([f"• {s}" for s in suggestions])
        else:
            return "Попробуйте популярные активы: VOO.US, SPY.US, RGBITR.INDX, GC.COMM"
    
    def get_asset_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive asset information
        
        Args:
            symbol: Asset symbol (e.g., 'VOO.US', 'SPY.US')
            
        Returns:
            Dictionary containing asset information or error
        """
        try:
            self.logger.info(f"Getting asset info for {symbol}")
            
            # Create asset object
            asset = ok.Asset(symbol)
            
            # Get basic info
            info = {
                'name': getattr(asset, 'name', 'N/A'),
                'country': getattr(asset, 'country', 'N/A'),
                'exchange': getattr(asset, 'exchange', 'N/A'),
                'currency': getattr(asset, 'currency', 'N/A'),
                'type': getattr(asset, 'type', 'N/A'),
                'isin': getattr(asset, 'isin', 'N/A'),
                'first_date': getattr(asset, 'first_date', 'N/A'),
                'last_date': getattr(asset, 'last_date', 'N/A'),
                'period_length': 'N/A'
            }
            
            # Calculate period length if dates are available
            if info['first_date'] != 'N/A' and info['last_date'] != 'N/A':
                try:
                    from datetime import datetime
                    first = asset.first_date
                    last = asset.last_date
                    if hasattr(first, 'year') and hasattr(last, 'year'):
                        years = last.year - first.year
                        info['period_length'] = f"{years} лет"
                except:
                    pass
            
            # Get current price
            try:
                price_info = self.get_asset_price(symbol)
                price_val = price_info.get('price') if isinstance(price_info, dict) else None
                if isinstance(price_val, (int, float)):
                    try:
                        import numpy as np
                    except Exception:
                        np = None
                    price_val_float = float(price_val)
                    is_finite = (np is not None and np.isfinite(price_val_float)) or (
                        np is None and not (price_val_float != price_val_float or price_val_float in (float('inf'), float('-inf')))
                    )
                    if is_finite:
                        info['current_price'] = price_val_float
                    else:
                        info['current_price'] = None
                else:
                    info['current_price'] = None
            except:
                info['current_price'] = None
            
            # Get performance metrics
            try:
                # Annual return
                annual_return = asset.get_annual_return()
                if annual_return is not None:
                    info['annual_return'] = f"{annual_return:.2%}"
                else:
                    info['annual_return'] = 'N/A'
            except:
                info['annual_return'] = 'N/A'
            
            try:
                # Total return
                total_return = asset.get_total_return()
                if total_return is not None:
                    info['total_return'] = f"{total_return:.2%}"
                else:
                    info['total_return'] = 'N/A'
            except:
                info['total_return'] = 'N/A'
            
            try:
                # Volatility
                volatility = asset.get_volatility()
                if volatility is not None:
                    info['volatility'] = f"{volatility:.2%}"
                else:
                    info['volatility'] = 'N/A'
            except:
                info['volatility'] = 'N/A'
            
            # Try to generate a monthly price dynamics chart for the full available period
            try:
                series_for_plot = None
                try:
                    import pandas as pd  # type: ignore
                except Exception:
                    pd = None  # type: ignore
                raw = getattr(asset, 'price', None)
                if pd is not None and hasattr(raw, 'iloc') and hasattr(raw, 'index') and len(raw) > 1:
                    if getattr(raw, 'ndim', 1) == 1:
                        series_for_plot = raw.dropna()
                    else:
                        df_non_nan = raw.dropna(how='all') if hasattr(raw, 'dropna') else raw
                        if len(df_non_nan) > 0 and hasattr(df_non_nan, 'columns'):
                            try:
                                first_col = df_non_nan.columns[0]
                                series_for_plot = df_non_nan[first_col].dropna()
                            except Exception:
                                series_for_plot = None
                if series_for_plot is not None and len(series_for_plot) > 1:
                    # Convert PeriodIndex (monthly) to Timestamp if needed
                    try:
                        if hasattr(series_for_plot.index, 'to_timestamp'):
                            series_for_plot = series_for_plot.copy()
                            series_for_plot.index = series_for_plot.index.to_timestamp()
                    except Exception:
                        pass
                    # Ensure monthly frequency if index is datetime-like
                    try:
                        inferred = getattr(series_for_plot.index, 'inferred_type', None)
                        if inferred and 'datetime' in str(inferred).lower():
                            series_for_plot = series_for_plot.resample('M').last().dropna()
                    except Exception:
                        pass
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(series_for_plot.index, series_for_plot.values, color='#1f77b4', linewidth=2)
                    ax.set_title(f'Динамика цены по месяцам: {symbol}', fontsize=12)
                    ax.set_xlabel('Дата')
                    ax.set_ylabel(f'Цена ({getattr(asset, "currency", "")})')
                    ax.grid(True, linestyle='--', alpha=0.3)
                    fig.tight_layout()
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    info['chart'] = buf.getvalue()
            except Exception:
                # Silently ignore plotting errors
                pass
            
            return info
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error getting asset info for {symbol}: {error_msg}")
            
            # Check if it's a "not found" error
            if "not found" in error_msg.lower() or "404" in error_msg:
                suggestions = self._get_asset_suggestions(symbol)
                return {
                    'error': f"Актив {symbol} не найден в базе данных Okama.\n\n{suggestions}",
                    'suggestions': suggestions
                }
            else:
                return {'error': f"Ошибка при получении информации об активе: {error_msg}"}
    
    def get_asset_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current asset price
        
        Args:
            symbol: Asset symbol (e.g., 'VOO.US', 'SPY.US')
            
        Returns:
            Dictionary containing price information or error
        """
        try:
            self.logger.info(f"Getting asset price for {symbol}")
            
            # Create asset object
            asset = ok.Asset(symbol)
            
            # Get price data
            price_data = asset.price
            
            # Helper: try MOEX ISS fallback before returning an error
            def _maybe_moex_fallback(error_message: str) -> Dict[str, Any]:
                if symbol.upper().endswith('.MOEX'):
                    fallback = self._fetch_moex_price(symbol)
                    if fallback is not None:
                        price_value, ts = fallback
                        return {
                            'price': price_value,
                            'currency': 'RUB',
                            'timestamp': ts
                        }
                return {'error': error_message}
            
            # Check if price_data is valid and has data
            if price_data is None:
                return _maybe_moex_fallback('No price data available')
            
            # Handle different types of price data
            if hasattr(price_data, 'iloc') and hasattr(price_data, 'index'):
                try:
                    import pandas as pd  # Local import to avoid hard dependency at module import time
                except Exception:
                    pd = None
                
                # Guard empty
                if len(price_data) == 0:
                    return _maybe_moex_fallback('No price data available')
                
                # If Series: take last valid non-NaN
                if getattr(price_data, 'ndim', 1) == 1:
                    series = price_data
                    try:
                        series_non_nan = series.dropna()
                    except Exception:
                        # Fallback if dropna is not available or fails
                        series_non_nan = series[~series.isna()] if hasattr(series, 'isna') else series
                    if len(series_non_nan) == 0:
                        return _maybe_moex_fallback('No price data available')
                    latest_price = series_non_nan.iloc[-1]
                    latest_date = series_non_nan.index[-1]
                else:
                    # DataFrame: take last row with any valid value, then pick the last non-NaN cell
                    df = price_data
                    try:
                        df_non_nan = df.dropna(how='all')
                    except Exception:
                        df_non_nan = df
                    if len(df_non_nan) == 0:
                        return _maybe_moex_fallback('No price data available')
                    last_date = df_non_nan.index[-1]
                    last_row = df_non_nan.iloc[-1]
                    # Prefer the last non-NaN value in the row
                    try:
                        non_nan_values = last_row.dropna()
                    except Exception:
                        non_nan_values = last_row[last_row.notna()] if hasattr(last_row, 'notna') else last_row
                    if hasattr(non_nan_values, 'empty') and non_nan_values.empty:
                        # As a fallback, stack and take the very last valid value across the frame
                        try:
                            stacked = df_non_nan.stack().dropna()
                            if len(stacked) == 0:
                                return _maybe_moex_fallback('No price data available')
                            latest_price = stacked.iloc[-1]
                            latest_date = stacked.index[-1][0]
                        except Exception:
                            return _maybe_moex_fallback('Invalid price data format')
                    else:
                        latest_price = non_nan_values.iloc[-1] if hasattr(non_nan_values, 'iloc') else non_nan_values
                        latest_date = last_date
            elif isinstance(price_data, (int, float)):
                # It's a single price value
                latest_price = price_data
                latest_date = datetime.now()
            else:
                # Try to convert to list/array and find last finite numeric value
                try:
                    # Support numpy arrays, lists, tuples, etc.
                    sequence_like = price_data
                    # Determine length
                    length = len(sequence_like)
                    if length == 0:
                        return _maybe_moex_fallback('No price data available')
                    
                    # Local import for numpy if available
                    try:
                        import numpy as np
                    except Exception:
                        np = None
                    
                    latest_price = None
                    # Iterate backwards to find last finite numeric
                    for idx in range(length - 1, -1, -1):
                        candidate = sequence_like[idx]
                        # Unwrap numpy/pandas scalar
                        try:
                            if hasattr(candidate, 'item'):
                                candidate = candidate.item()
                        except Exception:
                            pass
                        # Check numeric and finiteness
                        if isinstance(candidate, (int, float)):
                            if np is not None:
                                if np.isfinite(float(candidate)):
                                    latest_price = float(candidate)
                                    break
                            else:
                                # Fallback finiteness check
                                val = float(candidate)
                                if not (val != val or val in (float('inf'), float('-inf'))):
                                    latest_price = val
                                    break
                    if latest_price is None:
                        return _maybe_moex_fallback('No valid price value available')
                    latest_date = getattr(asset, 'last_date', datetime.now())
                except (TypeError, IndexError):
                    return _maybe_moex_fallback('Invalid price data format')
            
            # Normalize scalar to float and guard NaN/inf
            try:
                import numpy as np
            except Exception:
                np = None
            
            try:
                # Extract python scalar if it's a numpy/pandas scalar
                if hasattr(latest_price, 'item'):
                    latest_price = latest_price.item()
            except Exception:
                pass
            
            # Convert to float if possible
            try:
                latest_price_float = float(latest_price)
            except (TypeError, ValueError):
                return _maybe_moex_fallback('Invalid price value')
            
            # Check for NaN or infinite
            if (np is not None and not np.isfinite(latest_price_float)) or (np is None and (latest_price_float != latest_price_float or latest_price_float in (float('inf'), float('-inf')))):
                return _maybe_moex_fallback('No valid price value available')
            
            info = {
                'price': latest_price_float,
                'currency': getattr(asset, 'currency', ''),
                'timestamp': str(latest_date)
            }
            
            # Try to generate a price chart from the historical series if available
            try:
                series_for_plot = None
                try:
                    import pandas as pd  # type: ignore
                except Exception:
                    pd = None  # type: ignore
                raw = asset.price
                if pd is not None and hasattr(raw, 'iloc') and hasattr(raw, 'index') and len(raw) > 1:
                    if getattr(raw, 'ndim', 1) == 1:
                        series_for_plot = raw.dropna()
                    else:
                        df_non_nan = raw.dropna(how='all') if hasattr(raw, 'dropna') else raw
                        if len(df_non_nan) > 0 and hasattr(df_non_nan, 'columns'):
                            try:
                                first_col = df_non_nan.columns[0]
                                series_for_plot = df_non_nan[first_col].dropna()
                            except Exception:
                                series_for_plot = None
                if series_for_plot is not None and len(series_for_plot) > 1:
                    # Convert PeriodIndex to Timestamp if needed
                    try:
                        if hasattr(series_for_plot.index, 'to_timestamp'):
                            series_for_plot = series_for_plot.copy()
                            series_for_plot.index = series_for_plot.index.to_timestamp()
                    except Exception:
                        pass
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.plot(series_for_plot.index, series_for_plot.values, color='#1f77b4', linewidth=2)
                    ax.set_title(f'Динамика цены: {symbol}', fontsize=12)
                    ax.set_xlabel('Дата')
                    ax.set_ylabel(f'Цена ({getattr(asset, "currency", "")})')
                    ax.grid(True, linestyle='--', alpha=0.3)
                    fig.tight_layout()
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    info['chart'] = buf.getvalue()
            except Exception:
                # Silently ignore plotting errors
                pass
            
            return info
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error getting asset price for {symbol}: {error_msg}")
            
            # Check if it's a "not found" error
            if "not found" in error_msg.lower() or "404" in error_msg:
                suggestions = self._get_asset_suggestions(symbol)
                return {
                    'error': f"Актив {symbol} не найден в базе данных Okama.\n\n{suggestions}",
                    'suggestions': suggestions
                }
            else:
                return {'error': f"Ошибка при получении цены: {error_msg}"}
    
    def _fetch_moex_price(self, symbol: str) -> Optional[tuple[float, str]]:
        """
        Fetch current price from Moscow Exchange ISS API as a fallback.
        Returns (price, timestamp_str) or None if not available.
        """
        try:
            import requests
            base = symbol.split('.')[0].upper()
            # First, try marketdata LAST
            md_urls = [
                f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{base}.json?iss.only=marketdata&iss.meta=off&iss.json=extended&marketdata.columns=SECID,LAST,UPDATETIME",
                f"https://iss.moex.com/iss/engines/stock/markets/shares/securities/{base}.json?iss.only=marketdata&iss.meta=off&iss.json=extended&marketdata.columns=SECID,LAST,UPDATETIME"
            ]
            for url in md_urls:
                resp = requests.get(url, timeout=5)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                rows = None
                if isinstance(data, list):
                    for table in data:
                        if isinstance(table, dict) and 'marketdata' in table:
                            rows = table['marketdata']
                            break
                elif isinstance(data, dict):
                    if 'marketdata' in data and 'data' in data['marketdata']:
                        rows = data['marketdata']['data']
                if rows and isinstance(rows, list) and len(rows) > 0:
                    first = rows[0]
                    if isinstance(first, dict):
                        last = first.get('LAST')
                        ts = first.get('UPDATETIME') or ''
                    else:
                        try:
                            last = first[1]
                            ts = first[2]
                        except Exception:
                            last = None
                            ts = ''
                    if last is not None:
                        try:
                            price = float(last)
                            return price, str(ts)
                        except Exception:
                            pass
            
            # If no marketdata, try daily candles (interval=24)
            candles_url = f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities/{base}/candles.json?interval=24&iss.meta=off"
            resp = requests.get(candles_url, timeout=10)
            if resp.status_code == 200:
                d = resp.json()
                if isinstance(d, dict) and 'candles' in d:
                    cols = d['candles'].get('columns') or []
                    data = d['candles'].get('data') or []
                    if data and cols:
                        try:
                            close_idx = cols.index('close') if 'close' in cols else 1
                            end_idx = cols.index('end') if 'end' in cols else 7
                        except Exception:
                            close_idx, end_idx = 1, 7
                        last_row = data[-1]
                        try:
                            price = float(last_row[close_idx])
                            ts = str(last_row[end_idx])
                            return price, ts
                        except Exception:
                            pass
            
            # If candles not available, try history CLOSE
            hist_url = f"https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/{base}.json?iss.meta=off"
            resp = requests.get(hist_url, timeout=10)
            if resp.status_code == 200:
                d = resp.json()
                if isinstance(d, dict) and 'history' in d:
                    cols = d['history'].get('columns') or []
                    data = d['history'].get('data') or []
                    if data and cols:
                        try:
                            close_idx = cols.index('CLOSE') if 'CLOSE' in cols else cols.index('LEGALCLOSEPRICE')
                        except Exception:
                            close_idx = None
                        try:
                            date_idx = cols.index('TRADEDATE')
                        except Exception:
                            date_idx = None
                        if close_idx is not None and date_idx is not None:
                            last_row = data[-1]
                            try:
                                price = float(last_row[close_idx])
                                ts = str(last_row[date_idx])
                                return price, ts
                            except Exception:
                                pass
            return None
        except Exception:
            return None
    
    def get_asset_dividends(self, symbol: str) -> Dict[str, Any]:
        """
        Get asset dividend history
        
        Args:
            symbol: Asset symbol (e.g., 'VOO.US', 'SPY.US')
            
        Returns:
            Dictionary containing dividend information or error
        """
        try:
            self.logger.info(f"Getting asset dividends for {symbol}")
            
            # Create asset object
            asset = ok.Asset(symbol)
            
            # Get dividend data
            dividend_data = asset.dividends
            
            # Check if dividend_data is valid and has data
            if dividend_data is None:
                return {'error': 'No dividend data available'}
            
            # Handle different types of dividend data
            if hasattr(dividend_data, 'iloc') and hasattr(dividend_data, 'index'):
                # It's a pandas Series/DataFrame
                if len(dividend_data) == 0:
                    return {'error': 'No dividend data available'}
            elif isinstance(dividend_data, (int, float)):
                # It's a single value
                if dividend_data == 0:
                    return {'error': 'No dividend data available'}
            else:
                # Try to check length
                try:
                    if len(dividend_data) == 0:
                        return {'error': 'No dividend data available'}
                except (TypeError, AttributeError):
                    return {'error': 'Invalid dividend data format'}
            
            # Convert to dictionary format
            dividends = {}
            if hasattr(dividend_data, 'items'):
                # It's a pandas Series or dict-like object
                for date, amount in dividend_data.items():
                    dividends[str(date)] = amount
            elif hasattr(dividend_data, 'iloc') and hasattr(dividend_data, 'index'):
                # It's a pandas Series
                for i in range(len(dividend_data)):
                    date = dividend_data.index[i]
                    amount = dividend_data.iloc[i]
                    dividends[str(date)] = amount
            else:
                # Fallback for other types
                dividends['current'] = dividend_data
            
            # Calculate total periods based on data type
            if hasattr(dividend_data, '__len__'):
                try:
                    total_periods = len(dividend_data)
                except (TypeError, AttributeError):
                    total_periods = 1
            else:
                total_periods = 1
            
            info = {
                'currency': getattr(asset, 'currency', ''),
                'total_periods': total_periods,
                'dividends': dividends
            }
            
            # Try to generate a dividends chart from the historical series if available
            try:
                series_for_plot = None
                try:
                    import pandas as pd  # type: ignore
                except Exception:
                    pd = None  # type: ignore
                raw = dividend_data
                if pd is not None and hasattr(raw, 'iloc') and hasattr(raw, 'index') and len(raw) > 0:
                    # Ensure Series
                    if getattr(raw, 'ndim', 1) == 1:
                        series_for_plot = raw.dropna()
                    else:
                        # If DataFrame, try first column
                        df_non_nan = raw.dropna(how='all') if hasattr(raw, 'dropna') else raw
                        if len(df_non_nan) > 0 and hasattr(df_non_nan, 'columns'):
                            try:
                                first_col = df_non_nan.columns[0]
                                series_for_plot = df_non_nan[first_col].dropna()
                            except Exception:
                                series_for_plot = None
                if series_for_plot is not None and len(series_for_plot) > 0:
                    # Keep only positive values and take last 30 for readability
                    try:
                        series_for_plot = series_for_plot[series_for_plot > 0]
                    except Exception:
                        pass
                    if len(series_for_plot) > 30:
                        series_for_plot = series_for_plot.iloc[-30:]
                    # Convert PeriodIndex to Timestamp if needed
                    try:
                        if hasattr(series_for_plot.index, 'to_timestamp'):
                            series_for_plot = series_for_plot.copy()
                            series_for_plot.index = series_for_plot.index.to_timestamp()
                    except Exception:
                        pass
                    fig, ax = plt.subplots(figsize=(10, 4))
                    ax.bar(series_for_plot.index, series_for_plot.values, color='#2ca02c')
                    ax.set_title(f'Дивиденды: {symbol}', fontsize=12)
                    ax.set_xlabel('Дата')
                    ax.set_ylabel(f'Сумма ({getattr(asset, "currency", "")})')
                    ax.grid(True, axis='y', linestyle='--', alpha=0.3)
                    fig.autofmt_xdate()
                    fig.tight_layout()
                    buf = io.BytesIO()
                    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                    plt.close(fig)
                    info['chart'] = buf.getvalue()
            except Exception:
                # Silently ignore plotting errors
                pass
            
            return info
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error getting asset dividends for {symbol}: {error_msg}")
            
            # Check if it's a "not found" error
            if "not found" in error_msg.lower() or "404" in error_msg:
                suggestions = self._get_asset_suggestions(symbol)
                return {
                    'error': f"Актив {symbol} не найден в базе данных Okama.\n\n{suggestions}",
                    'suggestions': suggestions
                }
            else:
                return {'error': f"Ошибка при получении дивидендов: {error_msg}"}

"""
Asset Service for Okama Finance Bot

This service provides methods for retrieving financial asset information
using the Okama library.
"""

import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
import okama as ok
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class AssetService:

    def _add_copyright_signature(self, ax):
        """Добавить копирайт подпись к графику"""
        ax.text(0.02, -0.15, '________________________________________________________________________________________________________________',
               transform=ax.transAxes, color='grey', alpha=0.7, fontsize=10)
        ax.text(0.02, -0.25, '   ©Цбот                                                                               Source: okama   ',
               transform=ax.transAxes, fontsize=12, color='grey', alpha=0.7)
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
    
    def resolve_symbol_or_isin(self, identifier: str) -> Dict[str, Union[str, Any]]:
        """
        Resolve user-provided identifier to an okama-compatible ticker.

        Supports:
        - Ticker in okama format (e.g., 'AAPL.US', 'SBER.MOEX')
        - Plain ticker (e.g., 'AAPL') – returned uppercased as-is
        - ISIN (e.g., 'US0378331005') – tries to resolve via MOEX ISS for Russian listings

        Returns dict: { 'symbol': str, 'type': 'ticker'|'isin', 'source': str }
        or { 'error': str } on failure.
        """
        try:
            raw = (identifier or '').strip()
            if not raw:
                return { 'error': 'Пустой идентификатор актива' }

            upper = raw.upper()

            # If already okama-style ticker like XXX.SUFFIX
            if '.' in upper and len(upper.split('.')) == 2 and all(part for part in upper.split('.')):
                return { 'symbol': upper, 'type': 'ticker', 'source': 'input' }

            # Detect ISIN: 2 letters + 9 alnum + 1 digit (simplified)
            def _looks_like_isin(val: str) -> bool:
                if len(val) != 12:
                    return False
                if not (val[0:2].isalpha() and val[0:2].isupper()):
                    return False
                if not val[-1].isdigit():
                    return False
                mid = val[2:11]
                return mid.isalnum()

            if _looks_like_isin(upper):
                # Try resolve via MOEX ISS (works for instruments listed on MOEX)
                moex_symbol = self._try_resolve_isin_via_moex(upper)
                if moex_symbol:
                    return { 'symbol': moex_symbol, 'type': 'isin', 'source': 'moex' }
                else:
                    return {
                        'error': (
                            f"Не удалось определить тикер по ISIN {upper}. "
                            "Поддерживается разрешение ISIN только для бумаг, торгующихся на MOEX. "
                            "Попробуйте указать тикер в формате AAPL.US или SBER.MOEX."
                        )
                    }

            # Plain ticker without suffix – return upper-case; upstream may guess suffix
            return { 'symbol': upper, 'type': 'ticker', 'source': 'plain' }

        except Exception as e:
            return { 'error': f"Ошибка при разборе идентификатора: {str(e)}" }

    def _try_resolve_isin_via_moex(self, isin: str) -> Optional[str]:
        """
        Attempt to resolve ISIN to MOEX SECID using MOEX ISS API and return okama ticker SECID.MOEX
        Returns None if not found.
        """
        try:
            import requests  # Local import to avoid mandatory dependency at module import
        except Exception:
            return None

        try:
            url = f"https://iss.moex.com/iss/securities.json?isin={isin}&iss.meta=off"
            resp = requests.get(url, timeout=8)
            if resp.status_code != 200:
                return None
            data = resp.json()
            # The payload contains 'securities': { 'columns': [...], 'data': [[...], ...] }
            sec = data.get('securities') if isinstance(data, dict) else None
            if not sec:
                return None
            columns = sec.get('columns') or []
            rows = sec.get('data') or []
            if not columns or not rows:
                return None
            try:
                secid_idx = columns.index('SECID') if 'SECID' in columns else None
                isin_idx = columns.index('ISIN') if 'ISIN' in columns else None
            except Exception:
                secid_idx = None
                isin_idx = None
            if secid_idx is None:
                return None
            # Prefer exact ISIN match if column present
            for row in rows:
                try:
                    if isin_idx is not None and isinstance(row, list) and len(row) > max(secid_idx, isin_idx):
                        if str(row[isin_idx]).upper() != isin:
                            continue
                    secid = row[secid_idx]
                    if isinstance(secid, str) and secid:
                        return f"{secid.upper()}.MOEX"
                except Exception:
                    continue
            # Fallback: take first row
            first = rows[0]
            if isinstance(first, list) and len(first) > secid_idx and isinstance(first[secid_idx], str):
                return f"{first[secid_idx].upper()}.MOEX"
            return None
        except Exception:
            return None

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
    
    def get_asset_info(self, symbol: str) -> Dict[str, Union[str, Any]]:
        """
        Get comprehensive asset information
        
        Args:
            symbol: Asset symbol (e.g., 'VOO.US', 'SPY.US')
            
        Returns:
            Dictionary containing asset information or error
        """
        try:
            # Resolve identifier (ticker or ISIN) to okama symbol
            resolved = self.resolve_symbol_or_isin(symbol)
            if 'error' in resolved:
                return {'error': resolved['error']}
            symbol = resolved['symbol']
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
                self.logger.info(f"Attempting to generate chart for {symbol}")
                series_for_plot = None
                try:
                    import pandas as pd  # type: ignore
                except Exception as pd_error:
                    self.logger.warning(f"Pandas import failed for {symbol}: {pd_error}")
                    pd = None  # type: ignore
                
                raw = getattr(asset, 'price', None)
                self.logger.info(f"Raw price data type for {symbol}: {type(raw)}")
                
                if pd is not None and hasattr(raw, 'iloc') and hasattr(raw, 'index') and len(raw) > 1:
                    self.logger.info(f"Price data has {len(raw)} points for {symbol}")
                    if getattr(raw, 'ndim', 1) == 1:
                        series_for_plot = raw.dropna()
                        self.logger.info(f"1D series created for {symbol}, length: {len(series_for_plot)}")
                    else:
                        df_non_nan = raw.dropna(how='all') if hasattr(raw, 'dropna') else raw
                        if len(df_non_nan) > 0 and hasattr(df_non_nan, 'columns'):
                            try:
                                first_col = df_non_nan.columns[0]
                                series_for_plot = df_non_nan[first_col].dropna()
                                self.logger.info(f"Column series created for {symbol}, length: {len(series_for_plot)}")
                            except Exception as col_error:
                                self.logger.warning(f"Failed to get first column for {symbol}: {col_error}")
                                series_for_plot = None
                else:
                    self.logger.warning(f"Price data not suitable for plotting for {symbol}: type={type(raw)}, has_iloc={hasattr(raw, 'iloc') if raw is not None else False}, has_index={hasattr(raw, 'index') if raw is not None else False}, length={len(raw) if raw is not None else 0}")
                
                if series_for_plot is not None and len(series_for_plot) > 1:
                    self.logger.info(f"Creating chart for {symbol} with {len(series_for_plot)} data points")
                    
                    # Convert PeriodIndex (monthly) to Timestamp if needed
                    try:
                        if hasattr(series_for_plot.index, 'to_timestamp'):
                            series_for_plot = series_for_plot.copy()
                            series_for_plot.index = series_for_plot.index.to_timestamp()
                            self.logger.info(f"Converted PeriodIndex to Timestamp for {symbol}")
                    except Exception as ts_error:
                        self.logger.warning(f"Failed to convert PeriodIndex for {symbol}: {ts_error}")
                    
                    # Ensure monthly frequency if index is datetime-like
                    try:
                        inferred = getattr(series_for_plot.index, 'inferred_type', None)
                        if inferred and 'datetime' in str(inferred).lower():
                            series_for_plot = series_for_plot.resample('M').last().dropna()
                            self.logger.info(f"Resampled to monthly frequency for {symbol}, new length: {len(series_for_plot)}")
                    except Exception as resample_error:
                        self.logger.warning(f"Failed to resample for {symbol}: {resample_error}")
                    
                    # Create the plot
                    try:
                        plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
                        fig, ax = plt.subplots(figsize=(10, 4))
                        ax.plot(series_for_plot.index, series_for_plot.values, color='#1f77b4', linewidth=2)
                        ax.set_title(f'Динамика цены по месяцам: {symbol}', fontsize=12)
                        ax.set_xlabel('Дата')
                        ax.set_ylabel(f'Цена ({getattr(asset, "currency", "")})')
                        ax.grid(True, linestyle='--', alpha=0.3)
                        fig.tight_layout()
                        
                        # Save to buffer
                        buf = io.BytesIO()
                        fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                        plt.close(fig)
                        
                        chart_bytes = buf.getvalue()
                        if chart_bytes and len(chart_bytes) > 1000:  # Ensure chart is not empty
                            info['chart'] = chart_bytes
                            self.logger.info(f"Chart generated successfully for {symbol}, size: {len(chart_bytes)} bytes")
                        else:
                            self.logger.warning(f"Generated chart is too small for {symbol}, size: {len(chart_bytes)} bytes")
                            info['chart'] = None
                            
                    except Exception as plot_error:
                        self.logger.error(f"Failed to create plot for {symbol}: {plot_error}")
                        info['chart'] = None
                else:
                    self.logger.warning(f"Not enough data for chart for {symbol}: series_for_plot={series_for_plot is not None}, length={len(series_for_plot) if series_for_plot is not None else 0}")
                    info['chart'] = None
                    
            except Exception as chart_error:
                self.logger.error(f"Chart generation failed for {symbol}: {chart_error}")
                info['chart'] = None
            
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
    
    def get_asset_price(self, symbol: str) -> Dict[str, Union[str, Any]]:
        """
        Get current asset price
        
        Args:
            symbol: Asset symbol (e.g., 'VOO.US', 'SPY.US')
            
        Returns:
            Dictionary containing price information or error
        """
        try:
            # Resolve identifier (ticker or ISIN) to okama symbol
            resolved = self.resolve_symbol_or_isin(symbol)
            if 'error' in resolved:
                return {'error': resolved['error']}
            symbol = resolved['symbol']
            self.logger.info(f"Getting asset price for {symbol}")
            
            # Create asset object
            asset = ok.Asset(symbol)
            
            # Get price data
            price_data = asset.price
            
            # Helper: try MOEX ISS fallback before returning an error
            def _maybe_moex_fallback(error_message: str) -> Dict[str, Union[str, Any]]:
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
            
            # Handle NaN values - try to get price from adj_close or close_monthly
            if isinstance(price_data, float) and (price_data != price_data or price_data in (float('inf'), float('-inf'))):
                # price_data is NaN or infinite, try fallback to adj_close
                if hasattr(asset, 'adj_close') and asset.adj_close is not None and len(asset.adj_close) > 0:
                    try:
                        # Get last valid price from adj_close
                        adj_close_clean = asset.adj_close.dropna()
                        if len(adj_close_clean) > 0:
                            latest_price = adj_close_clean.iloc[-1]
                            latest_date = adj_close_clean.index[-1]
                            return {
                                'price': float(latest_price),
                                'currency': getattr(asset, 'currency', ''),
                                'timestamp': str(latest_date)
                            }
                    except Exception as e:
                        self.logger.warning(f"Failed to get price from adj_close for {symbol}: {e}")
                
                # If adj_close failed, try close_monthly
                if hasattr(asset, 'close_monthly') and asset.close_monthly is not None and len(asset.close_monthly) > 0:
                    try:
                        # Get last valid price from close_monthly
                        monthly_clean = asset.close_monthly.dropna()
                        if len(monthly_clean) > 0:
                            latest_price = monthly_clean.iloc[-1]
                            latest_date = monthly_clean.index[-1]
                            return {
                                'price': float(latest_price),
                                'currency': getattr(asset, 'currency', ''),
                                'timestamp': str(latest_date)
                            }
                    except Exception as e:
                        self.logger.warning(f"Failed to get price from close_monthly for {symbol}: {e}")
                
                # If all fallbacks failed, try MOEX ISS
                return _maybe_moex_fallback('Price data is NaN, fallbacks failed')
            
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
                    plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
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
    
    def get_asset_price_history(self, symbol: str, period: str = '1Y') -> Dict[str, Union[str, Any]]:
        """
        Get asset price history and create two price charts
        
        Args:
            symbol: Asset symbol (e.g., 'VOO.US', 'SPY.US')
            period: Time period for history (e.g., '1Y', '2Y', '5Y', 'MAX')
            
        Returns:
            Dictionary containing price history and two charts or error
        """
        try:
            # Resolve identifier (ticker or ISIN) to okama symbol
            resolved = self.resolve_symbol_or_isin(symbol)
            if 'error' in resolved:
                return {'error': resolved['error']}
            symbol = resolved['symbol']
            self.logger.info(f"Getting asset price history for {symbol} for period {period}")
            
            # Create asset object
            asset = ok.Asset(symbol)
            
            # Get currency from asset
            currency = getattr(asset, 'currency', '')
            
            # Initialize charts dictionary
            charts = {}
            price_data_info = {}
            
            # Filter data by period for each chart type
            adj_close_data = None
            monthly_data = None

            if hasattr(asset, 'adj_close'):
                adj_close_data = asset.adj_close
            if hasattr(asset, 'close_monthly'):
                monthly_data = asset.close_monthly

            if adj_close_data is not None and len(adj_close_data) > 0:
                # Daily data - always show 1 year for better detail
                filtered_adj_close = self._filter_data_by_period(adj_close_data, '1Y')
                adj_close_chart = self.create_price_chart(
                    filtered_adj_close, symbol, '1Y', currency, 
                    f"Дневные цены (adj_close): {symbol}"
                )
                if adj_close_chart:
                    charts['adj_close'] = adj_close_chart
                    price_data_info['adj_close'] = {
                        'data_points': len(filtered_adj_close),
                        'start_date': str(filtered_adj_close.index[0])[:10],
                        'end_date': str(filtered_adj_close.index[-1])[:10],
                        'period': '1Y',
                        'currency': currency,
                        'current_price': float(filtered_adj_close.iloc[-1]),
                        'start_price': float(filtered_adj_close.iloc[0]),
                        'min_price': float(filtered_adj_close.min()),
                        'max_price': float(filtered_adj_close.max())
                    }
            
            if monthly_data is not None and len(monthly_data) > 0:
                # Monthly data - always show 10 years for long-term trends
                filtered_monthly = self._filter_data_by_period(monthly_data, '10Y')
                monthly_chart = self.create_price_chart(
                    filtered_monthly, symbol, '10Y', currency,
                    f"Месячные цены (close_monthly): {symbol}"
                )
                if monthly_chart:
                    charts['close_monthly'] = monthly_chart
                    price_data_info['close_monthly'] = {
                        'data_points': len(filtered_monthly),
                        'start_date': str(filtered_monthly.index[0])[:10],
                        'end_date': str(filtered_monthly.index[-1])[:10],
                        'period': '10Y',
                        'currency': currency,
                        'current_price': float(filtered_monthly.iloc[-1]),
                        'start_price': float(filtered_monthly.iloc[0]),
                        'min_price': float(filtered_monthly.min()),
                        'max_price': float(filtered_monthly.max())
                    }
            
            # If no charts were created, try fallback methods
            if not charts:
                self.logger.warning(f"Could not get price data for period {period}, using fallback methods")
                
                # Try to get any available price data
                fallback_data = None
                fallback_period = '1Y'  # Default for fallback
                
                if hasattr(asset, 'price') and asset.price is not None:
                    fallback_data = asset.price
                    if hasattr(fallback_data, '__len__') and len(fallback_data) > 5:
                        # If it's daily data, show 1 year
                        if hasattr(fallback_data.index, 'freq') and 'M' not in str(fallback_data.index.freq):
                            fallback_period = '1Y'
                        else:
                            # If it's monthly data, show 10 years
                            fallback_period = '10Y'
                        
                        filtered_fallback = self._filter_data_by_period(fallback_data, fallback_period)
                        fallback_chart = self.create_price_chart(
                            filtered_fallback, symbol, fallback_period, currency,
                            f"Цены ({fallback_period}): {symbol}"
                        )
                        if fallback_chart:
                            charts['fallback'] = fallback_chart
                            price_data_info['fallback'] = {
                                'data_points': len(filtered_fallback),
                                'start_date': str(filtered_fallback.index[0])[:10],
                                'end_date': str(filtered_fallback.index[-1])[:10],
                                'period': fallback_period,
                                'currency': currency,
                                'current_price': float(filtered_fallback.iloc[-1]),
                                'start_price': float(filtered_fallback.iloc[0]),
                                'min_price': float(filtered_fallback.min()),
                                'max_price': float(filtered_fallback.max())
                            }
            
            # Check if we have any charts
            if not charts:
                return {'error': 'Не удалось создать ни одного графика'}
            
            # Convert charts dictionary to list for consistent return format
            charts_list = []
            if 'adj_close' in charts:
                charts_list.append(charts['adj_close'])
            if 'close_monthly' in charts:
                charts_list.append(charts['close_monthly'])
            if 'fallback' in charts:
                charts_list.append(charts['fallback'])
            
            # Prepare response data
            response_data = {
                'symbol': symbol,
                'currency': currency,
                'period': period,
                'charts': charts_list,  # List of chart bytes
                'price_data': price_data_info
            }
            
            return response_data
                
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error getting asset price history for {symbol}: {error_msg}")
            
            # Check if it's a "not found" error
            if "not found" in error_msg.lower() or "404" in error_msg:
                suggestions = self._get_asset_suggestions(symbol)
                return {
                    'error': f"Актив {symbol} не найден в базе данных Okama.\n\n{suggestions}",
                    'suggestions': suggestions
                }
            else:
                return {'error': f"Ошибка при получении истории цен: {error_msg}"}
    
    def create_price_chart(self, price_data, symbol: str, period: str, currency: str, chart_title: str) -> Optional[bytes]:
        """
        Create a price chart from price data
        
        Args:
            price_data: Pandas Series with price data
            symbol: Asset symbol
            period: Time period
            currency: Currency
            chart_title: Title for the chart
            
        Returns:
            Chart image as bytes or None if failed
        """
        try:
            import pandas as pd
            
            # Ensure we have a pandas Series
            if getattr(price_data, 'ndim', 1) == 1:
                series_for_plot = price_data.dropna()
            else:
                # If DataFrame, take first column
                df_non_nan = price_data.dropna(how='all')
                if len(df_non_nan) > 0 and hasattr(df_non_nan, 'columns'):
                    first_col = df_non_nan.columns[0]
                    series_for_plot = df_non_nan[first_col].dropna()
                else:
                    return None
            
            if len(series_for_plot) < 2:
                return None
            
            # Convert PeriodIndex to Timestamp if needed
            try:
                if hasattr(series_for_plot.index, 'to_timestamp'):
                    series_for_plot = series_for_plot.copy()
                    series_for_plot.index = series_for_plot.index.to_timestamp()
            except Exception:
                pass
            
            # Handle PeriodIndex dates for statistics
            try:
                start_date = series_for_plot.index[0]
                end_date = series_for_plot.index[-1]
                
                # Convert Period to string representation if needed
                if hasattr(start_date, 'strftime'):
                    start_date_str = start_date.strftime('%Y-%m-%d')
                else:
                    start_date_str = str(start_date)
                
                if hasattr(end_date, 'strftime'):
                    end_date_str = end_date.strftime('%Y-%m-%d')
                else:
                    end_date_str = str(end_date)
                    
            except Exception as e:
                self.logger.warning(f"Could not process dates: {e}")
                start_date_str = "N/A"
                end_date_str = "N/A"
            
            # Create the price chart
            fig, ax = chart_styles.create_figure(figsize=(12, 6))
            
            # Apply base style
            chart_styles.apply_base_style(fig, ax)
            
            # Plot price line with spline interpolation
            chart_styles.plot_smooth_line(ax, series_for_plot.index, series_for_plot.values, 
                                        color='#1f77b4', alpha=0.8)
            
            # Add current price annotation
            current_price = series_for_plot.iloc[-1]
            current_date = series_for_plot.index[-1]
            ax.annotate(f'{current_price:.2f}', 
                       xy=(current_date, current_price),
                       xytext=(10, 10), textcoords='offset points',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                       fontsize=10, fontweight='bold')
            
            # Customize chart
            ax.set_title(f'{chart_title}: {symbol} ({period})', fontsize=chart_styles.title_config['fontsize'], 
                       fontweight=chart_styles.title_config['fontweight'])
            ax.set_xlabel('Дата', fontsize=chart_styles.axis_config['label_fontsize'])
            ax.set_ylabel(f'Цена ({currency})', fontsize=chart_styles.axis_config['label_fontsize'])
            
            # Format x-axis dates
            fig.autofmt_xdate()
            
            # Add some statistics
            start_price = series_for_plot.iloc[0]
            if start_price != 0:
                price_change = ((current_price - start_price) / start_price) * 100
            else:
                price_change = 0.0
                
            stats_text = f'Изменение: {price_change:+.2f}%\n'
            stats_text += f'Мин: {series_for_plot.min():.2f}\n'
            stats_text += f'Макс: {series_for_plot.max():.2f}'
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
                   verticalalignment='top', fontsize=10,
                   bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8))
            
            fig.tight_layout()
            
            # Save chart to bytes
            buf = io.BytesIO()
            chart_styles.save_figure(fig, buf)
            chart_styles.cleanup_figure(fig)
            
            return buf.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error creating price chart: {e}")
            return None
    
    def _fetch_moex_price(self, symbol: str) -> Optional[tuple]:
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
    
    def get_asset_dividends(self, symbol: str) -> Dict[str, Union[str, Any]]:
        """
        Get asset dividend history
        
        Args:
            symbol: Asset symbol (e.g., 'VOO.US', 'SPY.US')
            
        Returns:
            Dictionary containing dividend information or error
        """
        try:
            # Resolve identifier (ticker or ISIN) to okama symbol
            resolved = self.resolve_symbol_or_isin(symbol)
            if 'error' in resolved:
                return {'error': resolved['error']}
            symbol = resolved['symbol']
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
            
            # Convert to dictionary format with only actual payout dates (> 0)
            dividends = {}
            try:
                import math
            except Exception:
                math = None
            def _is_positive_number(value):
                try:
                    if hasattr(value, 'item'):
                        value = value.item()
                except Exception:
                    pass
                if isinstance(value, (int, float)):
                    if math is not None:
                        try:
                            return float(value) > 0 and math.isfinite(float(value))
                        except Exception:
                            return False
                    else:
                        v = float(value)
                        return v > 0 and not (v != v or v in (float('inf'), float('-inf')))
                return False

            if hasattr(dividend_data, 'items'):
                # It's a pandas Series or dict-like object
                for date, amount in dividend_data.items():
                    if _is_positive_number(amount):
                        dividends[str(date)] = float(amount)
            elif hasattr(dividend_data, 'iloc') and hasattr(dividend_data, 'index'):
                # It's a pandas Series
                for i in range(len(dividend_data)):
                    date = dividend_data.index[i]
                    amount = dividend_data.iloc[i]
                    if _is_positive_number(amount):
                        dividends[str(date)] = float(amount)
            else:
                # Fallback for other types
                if _is_positive_number(dividend_data):
                    dividends['current'] = float(dividend_data)
            
            # Calculate payout count based on filtered dividends
            total_periods = len(dividends)
            
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
                    plt.style.use('fivethirtyeight')  # Use fivethirtyeight style
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

    def _filter_data_by_period(self, data, period: str):
        """
        Filter data by specified period
        
        Args:
            data: Pandas Series with price data
            period: Time period (e.g., '1Y', '2Y', '5Y', 'MAX')
            
        Returns:
            Filtered data series
        """
        try:
            if period == 'MAX':
                return data
            
            # Parse period
            import re
            match = re.match(r'(\d+)([YMD])', period.upper())
            if not match:
                # Default period depends on data type
                if hasattr(data.index, 'freq') and 'M' in str(data.index.freq):
                    # Monthly data - default to 10 years
                    return data.tail(120)  # Last 120 months (10 years)
                else:
                    # Daily data - default to 1 year
                    return data.tail(365)  # Last 365 days (1 year)
            
            number, unit = match.groups()
            number = int(number)
            
            # Calculate how many data points to take
            if unit == 'Y':
                # For monthly data, take last N*12 months
                # For daily data, take last N*365 days
                if hasattr(data.index, 'freq') and 'M' in str(data.index.freq):
                    # Monthly data
                    points_to_take = number * 12
                else:
                    # Daily data
                    points_to_take = number * 365
            elif unit == 'M':
                if hasattr(data.index, 'freq') and 'M' in str(data.index.freq):
                    # Monthly data
                    points_to_take = number
                else:
                    # Daily data
                    points_to_take = number * 30
            elif unit == 'D':
                if hasattr(data.index, 'freq') and 'M' in str(data.index.freq):
                    # Monthly data - take at least 1 month
                    points_to_take = max(1, number // 30)
                else:
                    # Daily data
                    points_to_take = number
            else:
                # Default depends on data type
                if hasattr(data.index, 'freq') and 'M' in str(data.index.freq):
                    # Monthly data - default to 10 years
                    points_to_take = 120
                else:
                    # Daily data - default to 1 year
                    points_to_take = 365
            
            # Take last N points
            if len(data) > points_to_take:
                return data.tail(points_to_take)
            else:
                return data
                
        except Exception as e:
            self.logger.warning(f"Error filtering data by period {period}: {e}")
            return data

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
from .chart_styles import chart_styles

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
        
        # Import random for random examples
        import random
        self.random = random
    
    def resolve_symbol_or_isin(self, identifier: str) -> Dict[str, Union[str, Any]]:
        """
        Resolve user-provided identifier to an okama-compatible ticker.

        Supports:
        - Ticker in okama format (e.g., 'AAPL.US', 'SBER.MOEX')
        - Plain ticker (e.g., 'AAPL') – automatically adds appropriate namespace
        - ISIN (e.g., 'US0378331005') – tries to resolve via MOEX ISS for Russian listings

        Returns dict: { 'symbol': str, 'type': 'ticker'|'isin', 'source': str }
        or { 'error': str } on failure.
        """
        try:
            raw = (identifier or '').strip()
            if not raw:
                return {'error': 'Пустой идентификатор актива'}

            upper = raw.upper()

            # If already okama-style ticker like XXX.SUFFIX
            if '.' in upper and len(upper.split('.')) == 2 and all(part for part in upper.split('.')):
                return {'symbol': upper, 'type': 'ticker', 'source': 'input'}

            if self._looks_like_isin(upper):
                # For ISIN, return the ISIN itself as symbol for direct Asset creation
                return {'symbol': upper, 'type': 'isin', 'source': 'direct_isin'}

            # Plain ticker without suffix – try to guess the appropriate namespace
            guessed_symbol = self._guess_namespace(upper)
            if guessed_symbol:
                return {'symbol': guessed_symbol, 'type': 'ticker', 'source': 'guessed'}
            else:
                return {'symbol': upper, 'type': 'ticker', 'source': 'plain'}

        except Exception as e:
            return {'error': f"Ошибка при разборе идентификатора: {str(e)}"}

    def _looks_like_isin(self, val: str) -> bool:
        """
        Check if string looks like an ISIN code
        
        Args:
            val: String to check
            
        Returns:
            True if string matches ISIN format
        """
        if len(val) != 12:
            return False
        if not (val[0:2].isalpha() and val[0:2].isupper()):
            return False
        if not val[-1].isdigit():
            return False
        mid = val[2:11]
        return mid.isalnum()

    def _guess_namespace(self, ticker: str) -> Optional[str]:
        """
        Guess the appropriate namespace for a plain ticker based on known patterns
        """
        # Common Russian stocks (MOEX)
        russian_stocks = {
            'SBER', 'GAZP', 'LKOH', 'GMKN', 'YNDX', 'MGNT', 'VTBR', 'ROSN', 'NVTK', 'TATN',
            'SNGS', 'SNGSP', 'CHMF', 'PLZL', 'POLY', 'RUAL', 'RUALR', 'MTSS', 'MVID', 'OZON'
        }
        
        # Common US stocks
        us_stocks = {
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC',
            'KO', 'DIS', 'MCD', 'SBUX', 'NKE', 'ADBE', 'CRM', 'VOO', 'SPY', 'QQQ', 'AGG'
        }
        
        # Common indices
        indices = {
            'SPX', 'IXIC', 'DJI', 'RTSI', 'IMOEX', 'RGBITR', 'MCFTR'
        }
        
        # Common commodities
        commodities = {
            'GC', 'SI', 'CL', 'BRENT', 'HG', 'ZC', 'ZS', 'ZW'
        }
        
        # Common currencies
        currencies = {
            'EUR', 'USD', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'NZD', 'RUB', 'CNY'
        }
        
        # Common crypto
        crypto = {
            'BTC', 'ETH', 'XRP', 'ADA', 'DOT', 'LINK', 'LTC', 'BCH'
        }
        
        if ticker in russian_stocks:
            return f"{ticker}.MOEX"
        elif ticker in us_stocks:
            return f"{ticker}.US"
        elif ticker in indices:
            return f"{ticker}.INDX"
        elif ticker in commodities:
            return f"{ticker}.COMM"
        elif ticker in currencies:
            return f"{ticker}.FX"
        elif ticker in crypto:
            return f"{ticker}.CC"
        
        # If no match found, return None (will use plain ticker)
        return None

    def search_by_isin(self, isin: str) -> Optional[str]:
        """
        Search for asset by ISIN using okama.Asset.search("") or direct creation
        
        Args:
            isin: ISIN code to search for
            
        Returns:
            Okama ticker if found, None otherwise
        """
        try:
            # First try to create asset directly with ISIN
            try:
                asset = ok.Asset(isin=isin)
                # If successful, return the ISIN as the symbol
                return isin
            except Exception as direct_error:
                self.logger.debug(f"Direct ISIN creation failed for {isin}: {direct_error}")
            
            # Fallback to search method
            search_results = ok.Asset.search(isin)
            
            if not search_results or len(search_results) == 0:
                return None
            
            # Look for exact ISIN match first
            for result in search_results:
                if hasattr(result, 'isin') and result.isin and result.isin.upper() == isin.upper():
                    # Return the ticker in okama format
                    if hasattr(result, 'ticker'):
                        return result.ticker
                    elif hasattr(result, 'symbol'):
                        return result.symbol
            
            # If no exact match, return the first result
            first_result = search_results[0]
            if hasattr(first_result, 'ticker'):
                return first_result.ticker
            elif hasattr(first_result, 'symbol'):
                return first_result.symbol
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error searching ISIN {isin} via okama.Asset.search: {e}")
            return None

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
            
            # Create asset object - try direct ISIN creation first
            try:
                if self._looks_like_isin(symbol):
                    # Try to create asset directly with ISIN
                    asset = ok.Asset(isin=symbol)
                else:
                    # Use regular symbol
                    asset = ok.Asset(symbol)
            except Exception as e:
                # Fallback to regular symbol creation
                try:
                    asset = ok.Asset(symbol)
                except Exception as fallback_error:
                    return {'error': f"Не удалось создать актив {symbol}: {str(fallback_error)}"}
            
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
            
            # For ISIN assets, add all available attributes
            if self._looks_like_isin(symbol):
                # Get all attributes of the asset object
                asset_attributes = {}
                for attr in dir(asset):
                    if not attr.startswith('_') and not callable(getattr(asset, attr)):
                        try:
                            value = getattr(asset, attr)
                            # Convert to string if it's not a basic type
                            if not isinstance(value, (str, int, float, bool, type(None))):
                                value = str(value)
                            asset_attributes[attr] = value
                        except Exception:
                            asset_attributes[attr] = 'Error getting attribute'
                
                info['asset_attributes'] = asset_attributes
            
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
                    
                    # Create the plot using chart_styles
                    try:
                        from services.chart_styles import chart_styles
                        
                        fig, ax = chart_styles.create_price_chart(
                            series_for_plot, symbol, getattr(asset, "currency", ""), 
                            period='monthly',
                            copyright=False
                        )
                        
                        # Save to buffer
                        buf = io.BytesIO()
                        chart_styles.save_figure(fig, buf)
                        chart_styles.cleanup_figure(fig)
                        
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
            
            # Create asset object - try direct ISIN creation first
            try:
                if self._looks_like_isin(symbol):
                    # Try to create asset directly with ISIN
                    asset = ok.Asset(isin=symbol)
                else:
                    # Use regular symbol
                    asset = ok.Asset(symbol)
            except Exception as e:
                # Fallback to regular symbol creation
                try:
                    asset = ok.Asset(symbol)
                except Exception as fallback_error:
                    return {'error': f"Не удалось создать актив {symbol}: {str(fallback_error)}"}
            
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
                if not hasattr(price_data, '__len__') or len(price_data) == 0:
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
                    
                    # Create the plot using chart_styles
                    try:
                        from services.chart_styles import chart_styles
                        
                        fig, ax = chart_styles.create_price_chart(
                            series_for_plot, symbol, getattr(asset, "currency", ""), 
                            period='',
                            copyright=False
                        )
                        
                        buf = io.BytesIO()
                        chart_styles.save_figure(fig, buf)
                        chart_styles.cleanup_figure(fig)
                        info['chart'] = buf.getvalue()
                    except Exception:
                        # Silently ignore plotting errors
                        pass
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
            moex_daily_series = None
            
            # Filter data by period for each chart type
            adj_close_data = None
            monthly_data = None

            if hasattr(asset, 'adj_close'):
                adj_close_data = asset.adj_close
            if hasattr(asset, 'close_monthly'):
                monthly_data = asset.close_monthly

            if (
                adj_close_data is not None
                and hasattr(adj_close_data, 'iloc')
                and hasattr(adj_close_data, 'index')
                and len(adj_close_data) > 0
            ):
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
            
            if (
                monthly_data is not None
                and hasattr(monthly_data, 'iloc')
                and hasattr(monthly_data, 'index')
                and len(monthly_data) > 0
            ):
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
                    if (
                        not isinstance(fallback_data, (int, float))
                        and hasattr(fallback_data, '__len__')
                        and len(fallback_data) > 5
                    ):
                        # If it's daily data, show 1 year
                        if (
                            hasattr(fallback_data, 'index')
                            and hasattr(fallback_data.index, 'freq')
                            and 'M' not in str(fallback_data.index.freq)
                        ):
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

                # Extra fallback for MOEX symbols: fetch daily close history via MOEX ISS
                try:
                    if symbol.upper().endswith('.MOEX'):
                        moex_daily_series = self._fetch_moex_daily_history(symbol, period_days=365)
                        if moex_daily_series is not None and len(moex_daily_series) > 5:
                            moex_chart = self.create_price_chart(
                                moex_daily_series, symbol, '1Y', currency,
                                f"Дневные цены (MOEX ISS): {symbol}"
                            )
                            if moex_chart:
                                charts['moex_daily'] = moex_chart
                                price_data_info['moex_daily'] = {
                                    'data_points': len(moex_daily_series),
                                    'start_date': str(moex_daily_series.index[0])[:10],
                                    'end_date': str(moex_daily_series.index[-1])[:10],
                                    'period': '1Y',
                                    'currency': currency,
                                    'current_price': float(moex_daily_series.iloc[-1]),
                                    'start_price': float(moex_daily_series.iloc[0]),
                                    'min_price': float(moex_daily_series.min()),
                                    'max_price': float(moex_daily_series.max())
                                }
                except Exception as moex_fallback_error:
                    self.logger.warning(f"MOEX daily history fallback failed for {symbol}: {moex_fallback_error}")
            
            # Check if we have any charts
            if not charts:
                return {'error': 'Не удалось создать ни одного графика'}
            
            # Prepare response data with charts as dictionary for better identification
            response_data = {
                'symbol': symbol,
                'currency': currency,
                'period': period,
                'charts': charts,  # Keep as dictionary with chart types
                'price_data': price_data_info
            }
            
            # Add actual price data for the bot to use
            if (
                adj_close_data is not None
                and hasattr(adj_close_data, 'iloc')
                and hasattr(adj_close_data, 'index')
                and len(adj_close_data) > 0
            ):
                # Use daily data for the bot's chart creation
                filtered_adj_close = self._filter_data_by_period(adj_close_data, '1Y')
                response_data['prices'] = filtered_adj_close
            elif (
                monthly_data is not None
                and hasattr(monthly_data, 'iloc')
                and hasattr(monthly_data, 'index')
                and len(monthly_data) > 0
            ):
                # Fallback to monthly data if no daily data
                filtered_monthly = self._filter_data_by_period(monthly_data, '10Y')
                response_data['prices'] = filtered_monthly
            elif (
                moex_daily_series is not None
                and hasattr(moex_daily_series, '__len__')
                and len(moex_daily_series) > 0
            ):
                # Use MOEX daily series if available
                response_data['prices'] = moex_daily_series
            elif 'fallback' in price_data_info:
                # Use fallback data if available
                fallback_data = asset.price
                if (
                    not isinstance(fallback_data, (int, float))
                    and hasattr(fallback_data, '__len__')
                    and len(fallback_data) > 5
                ):
                    fallback_period = '1Y' if (
                        hasattr(fallback_data, 'index') and hasattr(fallback_data.index, 'freq') and 'M' not in str(fallback_data.index.freq)
                    ) else '10Y'
                    filtered_fallback = self._filter_data_by_period(fallback_data, fallback_period)
                    response_data['prices'] = filtered_fallback
            
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
        Create a price chart from price data using standardized chart_styles
        
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
            
            self.logger.info(f"Creating price chart for {symbol} using standardized chart_styles")
            
            # Ensure we have a pandas Series
            if getattr(price_data, 'ndim', 1) == 1:
                series_for_plot = price_data.dropna()
                self.logger.debug(f"Created series from 1D data, length: {len(series_for_plot)}")
            else:
                # If DataFrame, take first column
                df_non_nan = price_data.dropna(how='all')
                if len(df_non_nan) > 0 and hasattr(df_non_nan, 'columns'):
                    first_col = df_non_nan.columns[0]
                    series_for_plot = df_non_nan[first_col].dropna()
                    self.logger.debug(f"Created series from DataFrame column {first_col}, length: {len(series_for_plot)}")
                else:
                    self.logger.error("No valid data found in DataFrame")
                    return None
            
            if len(series_for_plot) < 2:
                self.logger.error(f"Insufficient data points: {len(series_for_plot)}")
                return None
            
            # Handle large numbers by converting to float64
            try:
                series_for_plot = series_for_plot.astype('float64')
                self.logger.info(f"Successfully converted series to float64")
            except (OverflowError, ValueError) as e:
                self.logger.warning(f"Overflow error converting to float64: {e}")
                # Try to handle large numbers by scaling down if necessary
                try:
                    max_val = series_for_plot.max()
                    if max_val > 1e15:  # Very large numbers
                        scale_factor = 1000
                        series_for_plot = series_for_plot / scale_factor
                        self.logger.info(f"Scaled down values by factor {scale_factor}")
                    else:
                        # Safely convert values to float, handling Period objects
                        safe_values = []
                        for x in series_for_plot.values:
                            try:
                                if hasattr(x, 'to_timestamp'):
                                    try:
                                        x = x.to_timestamp()
                                    except Exception:
                                        x = str(x)
                                safe_values.append(float(x))
                            except Exception:
                                # Fallback to 0.0 if conversion fails
                                safe_values.append(0.0)
                        series_for_plot = pd.Series(safe_values, index=series_for_plot.index)
                except Exception as scale_error:
                    self.logger.error(f"Failed to handle large numbers: {scale_error}")
                    return None
            
            # Convert PeriodIndex to Timestamp if needed
            try:
                if hasattr(series_for_plot.index, 'to_timestamp'):
                    series_for_plot = series_for_plot.copy()
                    series_for_plot.index = series_for_plot.index.to_timestamp()
            except Exception:
                pass
            
            # Create standardized price chart using chart_styles
            fig, ax = chart_styles.create_price_chart(
                data=series_for_plot,
                symbol=symbol,
                currency=currency,
                period=period,
                copyright=False
            )
            
            # Save chart to bytes using standardized method
            try:
                buf = io.BytesIO()
                chart_styles.save_figure(fig, buf)
                chart_styles.cleanup_figure(fig)
                
                buf.seek(0)
                result = buf.getvalue()
                self.logger.info(f"Chart saved successfully, bytes length: {len(result)}")
                return result
                
            except Exception as save_error:
                self.logger.error(f"Error saving chart: {save_error}")
                raise
            
        except Exception as e:
            self.logger.error(f"Error creating price chart: {e}")
            return None

    def _fetch_moex_daily_history(self, symbol: str, period_days: int = 365):
        """
        Fetch daily close history for MOEX shares via ISS API as pandas Series.
        Returns Series indexed by date with float close prices, or None on failure.
        """
        try:
            import requests
            import pandas as pd
            from datetime import datetime, timedelta

            base = symbol.split('.')[0].upper()
            since = (datetime.now() - timedelta(days=period_days + 7)).strftime('%Y-%m-%d')

            # Try candles endpoint first (interval=24)
            candles_url = (
                f"https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/"
                f"securities/{base}/candles.json?interval=24&from={since}&iss.meta=off"
            )
            try:
                resp = requests.get(candles_url, timeout=10)
                if resp.status_code == 200:
                    d = resp.json()
                    if isinstance(d, dict) and 'candles' in d:
                        cols = d['candles'].get('columns') or []
                        rows = d['candles'].get('data') or []
                        if rows and cols:
                            try:
                                close_idx = cols.index('close') if 'close' in cols else 1
                            except Exception:
                                close_idx = 1
                            # prefer 'end' as candle end time, fallback to 7th column
                            try:
                                date_idx = cols.index('end') if 'end' in cols else 7
                            except Exception:
                                date_idx = 7

                            dates = []
                            values = []
                            for row in rows:
                                try:
                                    dt = pd.to_datetime(row[date_idx]).date()
                                    val = float(row[close_idx])
                                    dates.append(dt)
                                    values.append(val)
                                except Exception:
                                    continue
                            if dates:
                                s = pd.Series(values, index=pd.to_datetime(dates))
                                s = s.sort_index().last(f'{period_days}D')
                                return s
            except Exception:
                pass

            # Fallback: history endpoint with pagination
            history_base = (
                f"https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/"
                f"securities/{base}.json?from={since}&iss.meta=off"
            )
            start = 0
            all_dates = []
            all_values = []
            for _ in range(20):  # up to ~2000 rows
                url = f"{history_base}&start={start}"
                resp = requests.get(url, timeout=10)
                if resp.status_code != 200:
                    break
                d = resp.json()
                if not isinstance(d, dict) or 'history' not in d:
                    break
                cols = d['history'].get('columns') or []
                rows = d['history'].get('data') or []
                if not rows:
                    break
                try:
                    if 'CLOSE' in cols:
                        close_idx = cols.index('CLOSE')
                    elif 'LEGALCLOSEPRICE' in cols:
                        close_idx = cols.index('LEGALCLOSEPRICE')
                    else:
                        close_idx = None
                    date_idx = cols.index('TRADEDATE') if 'TRADEDATE' in cols else None
                except Exception:
                    close_idx = None
                    date_idx = None

                if close_idx is None or date_idx is None:
                    break

                for row in rows:
                    try:
                        dt = pd.to_datetime(row[date_idx]).date()
                        val = float(row[close_idx])
                        all_dates.append(dt)
                        all_values.append(val)
                    except Exception:
                        continue

                start += len(rows)

            if all_dates:
                import pandas as pd  # reimport for scope
                s = pd.Series(all_values, index=pd.to_datetime(all_dates))
                s = s.sort_index().last(f'{period_days}D')
                return s if len(s) > 0 else None

            return None
        except Exception:
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
                from services.chart_styles import chart_styles
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
                    # Create standardized dividends chart using chart_styles
                    fig, ax = chart_styles.create_dividends_chart(
                        data=series_for_plot, symbol=symbol, currency=getattr(asset, "currency", "")
                    )
                    
                    # Save chart using standardized method
                    buf = io.BytesIO()
                    chart_styles.save_figure(fig, buf)
                    chart_styles.cleanup_figure(fig)
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

    def get_random_examples(self, count: int = 3) -> list:
        """
        Get random examples of asset symbols for user suggestions
        
        Args:
            count: Number of examples to return
            
        Returns:
            List of random asset symbols
        """
        try:
            all_examples = []
            for category, symbols in self.known_assets.items():
                all_examples.extend(symbols)
            
            # Shuffle and return requested number
            self.random.shuffle(all_examples)
            return all_examples[:count]
        except Exception as e:
            self.logger.error(f"Error getting random examples: {e}")
            # Fallback to basic examples
            return ['SBER.MOEX', 'SPY.US', 'AAPL.US'][:count]

    def is_likely_asset_symbol(self, text: str) -> bool:
        """
        Check if text looks like an asset symbol
        
        Args:
            text: Text to check
            
        Returns:
            True if text looks like an asset symbol
        """
        try:
            if not text or not isinstance(text, str):
                return False
            
            text = text.strip().upper()
            
            # Check if it's already in okama format (XXX.SUFFIX)
            if '.' in text and len(text.split('.')) == 2:
                return True
            
            # Check if it looks like a plain ticker (3-5 letters, all uppercase)
            if len(text) >= 2 and len(text) <= 6 and text.isalpha():
                return True
            
            # Check if it looks like an ISIN using the dedicated method
            if self._looks_like_isin(text):
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Error checking if text is asset symbol: {e}")
            return False

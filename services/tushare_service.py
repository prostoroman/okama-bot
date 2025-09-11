import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from config import Config

class TushareService:
    """Service class for Tushare API integration for Chinese stock exchanges"""
    
    def __init__(self):
        """Initialize Tushare service with API key"""
        self.api_key = Config.TUSHARE_API_KEY
        if not self.api_key:
            raise ValueError("TUSHARE_API_KEY is required")
        
        # Set API token
        ts.set_token(self.api_key)
        self.pro = ts.pro_api()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Exchange mappings
        self.exchange_mappings = {
            'SSE': '.SH',      # Shanghai Stock Exchange
            'SZSE': '.SZ',     # Shenzhen Stock Exchange  
            'BSE': '.BJ',      # Beijing Stock Exchange
            'HKEX': '.HK'      # Hong Kong Stock Exchange
        }
        
        # Symbol patterns for validation
        self.symbol_patterns = {
            'SSE': r'^[0-9]{6}\.SH$',      # 600000.SH, 000001.SH
            'SZSE': r'^[0-9]{6}\.SZ$',     # 000001.SZ, 399005.SZ
            'BSE': r'^[0-9]{6}\.BJ$',      # 900001.BJ, 800001.BJ
            'HKEX': r'^[0-9]{5}\.HK$'      # 00001.HK, 00700.HK
        }
    
    def is_tushare_symbol(self, symbol: str) -> bool:
        """Check if symbol belongs to Chinese exchanges supported by Tushare"""
        import re
        for pattern in self.symbol_patterns.values():
            if re.match(pattern, symbol):
                return True
        return False
    
    def get_exchange_from_symbol(self, symbol: str) -> Optional[str]:
        """Get exchange code from symbol"""
        for exchange, suffix in self.exchange_mappings.items():
            if symbol.endswith(suffix):
                return exchange
        return None
    
    def _is_index_symbol(self, symbol: str) -> bool:
        """Check if symbol is an index (not a stock)"""
        # Known index symbols
        index_symbols = {
            '000001.SH',  # Shanghai Composite Index
            '399001.SZ',  # Shenzhen Component Index
            '399005.SZ',  # Shenzhen Small & Medium Enterprise Board Index
            '399006.SZ',  # ChiNext Index
            '899050.BJ',  # Beijing Stock Exchange 50 Index
        }
        
        # Also check if symbol ends with .BJ (Beijing Stock Exchange indices)
        if symbol.endswith('.BJ'):
            return True
            
        return symbol in index_symbols
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get basic information about a symbol"""
        try:
            exchange = self.get_exchange_from_symbol(symbol)
            if not exchange:
                return {"error": "Unsupported exchange"}
            
            # Extract symbol code without suffix
            symbol_code = symbol.split('.')[0]
            
            if exchange == 'HKEX':
                # For Hong Kong, use different approach
                return self._get_hk_stock_info(symbol_code)
            else:
                # For mainland China exchanges
                return self._get_mainland_stock_info(symbol_code, exchange)
                
        except Exception as e:
            error_msg = str(e)
            # Handle specific API permission errors
            if "权限" in error_msg or "permission" in error_msg.lower():
                return {"error": "API权限不足. Пожалуйста, проверьте ваш Tushare API ключ и убедитесь, что у вас есть доступ к данным."}
            elif "404" in error_msg or "not found" in error_msg.lower():
                return {"error": f"Символ {symbol} не найден в базе данных Tushare"}
            else:
                self.logger.error(f"Error getting symbol info for {symbol}: {e}")
                return {"error": f"Ошибка получения данных: {error_msg}"}
    
    def _get_mainland_stock_info(self, symbol_code: str, exchange: str) -> Dict[str, Any]:
        """Get stock information for mainland China exchanges"""
        try:
            # Get stock basic info
            df = self.pro.stock_basic(exchange='', list_status='L')
            
            # Debug: Check if DataFrame is empty or missing columns
            if df.empty:
                self.logger.error(f"stock_basic returned empty DataFrame for symbol {symbol_code}")
                return {"error": "No stock data available"}
            
            if 'symbol' not in df.columns:
                self.logger.error(f"stock_basic missing 'symbol' column. Available columns: {df.columns.tolist()}")
                return {"error": "Missing symbol column"}
            
            # Find matching stock
            stock_info = df[df['symbol'] == symbol_code]
            if stock_info.empty:
                # Log available symbols for debugging
                available_symbols = df[df['symbol'].str.contains(symbol_code[:3], na=False)]['symbol'].head(10).tolist()
                self.logger.warning(f"Stock {symbol_code} not found in {exchange}. Available similar symbols: {available_symbols}")
                # Try to find as index if not found as stock
                return self._get_index_info(symbol_code, exchange)
            
            info = stock_info.iloc[0].to_dict()
            
            # Use English name if available, otherwise fall back to Chinese name
            if 'enname' in info and info['enname'] and info['enname'].strip() and info['enname'] != 'N/A':
                info['english_name'] = info['enname']  # Preserve English name
                info['name'] = info['enname']  # Use English name as primary name
            else:
                # For mainland Chinese stocks, keep Chinese name as primary, no English fallback
                info['english_name'] = info.get('name', symbol_code)  # Use Chinese name as fallback
                info['name'] = info.get('name', symbol_code)  # Keep Chinese name as primary
            
            # Get additional metrics
            try:
                # Get 1 year of data for calculations
                daily_data = self.pro.daily(
                    ts_code=info['ts_code'],
                    start_date=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                
                if not daily_data.empty:
                    latest = daily_data.iloc[0]
                    info.update({
                        'current_price': latest['close'],
                        'change': latest['change'],
                        'pct_chg': latest['pct_chg'],
                        'volume': latest['vol'],
                        'amount': latest['amount']
                    })
                    
                    # Calculate annual return and volatility
                    if len(daily_data) > 1:
                        # Calculate returns
                        daily_data = daily_data.sort_values('trade_date')
                        daily_data['returns'] = daily_data['close'].pct_change().dropna()
                        
                        # Annual return (CAGR)
                        if len(daily_data) > 30:  # Need at least 30 days
                            total_return = (daily_data['close'].iloc[-1] / daily_data['close'].iloc[0]) - 1
                            days = len(daily_data)
                            annual_return = (1 + total_return) ** (365 / days) - 1
                            info['annual_return'] = annual_return
                            
                            # Volatility (annualized)
                            volatility = daily_data['returns'].std() * (365 ** 0.5)
                            info['volatility'] = volatility
                            
            except Exception as e:
                self.logger.warning(f"Could not get price data: {e}")
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting mainland stock info: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}
    
    def _get_hk_stock_info(self, symbol_code: str) -> Dict[str, Any]:
        """Get stock information for Hong Kong exchange"""
        try:
            # Get HK stock basic info with English names
            try:
                df = self.pro.hk_basic(
                    fields='ts_code,name,enname,list_date'
                )
            except Exception:
                # Fallback to basic fields if enname is not available
                df = self.pro.hk_basic(
                    fields='ts_code,name,list_date'
                )
            
            # Find matching stock by ts_code
            ts_code = f"{symbol_code}.HK"
            stock_info = df[df['ts_code'] == ts_code]
            if stock_info.empty:
                return {"error": "Stock not found"}
            
            info = stock_info.iloc[0].to_dict()
            
            # Use English name if available, otherwise fall back to Chinese name
            if 'enname' in info and info['enname'] and info['enname'].strip() and info['enname'] != 'N/A':
                info['english_name'] = info['enname']  # Preserve English name
                info['name'] = info['enname']  # Use English name as primary name
            else:
                # For Hong Kong stocks, keep Chinese name as primary, no English fallback
                info['english_name'] = info.get('name', symbol_code)  # Use Chinese name as fallback
                info['name'] = info.get('name', symbol_code)  # Keep Chinese name as primary

            # Add missing fields for consistency
            info.update({
                'exchange': 'HKEX',
                'area': 'Hong Kong',
                'industry': 'N/A'  # HK basic doesn't provide industry info
            })
            
            # Get additional metrics
            try:
                daily_data = self.pro.hk_daily(
                    ts_code=info['ts_code'],
                    start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                
                if not daily_data.empty:
                    latest = daily_data.iloc[0]
                    info.update({
                        'current_price': latest['close'],
                        'change': latest['change'],
                        'pct_chg': latest['pct_chg'],
                        'volume': latest['vol'],
                        'amount': latest['amount']
                    })
            except Exception as e:
                self.logger.warning(f"Could not get HK price data: {e}")
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting HK stock info: {e}")
            return {"error": str(e)}
    
    def _get_index_info(self, symbol_code: str, exchange: str) -> Dict[str, Any]:
        """Get index information for Chinese exchanges"""
        try:
            # Get index basic info
            df = self.pro.index_basic()
            
            # Find matching index by ts_code
            # Map exchange to suffix
            exchange_suffix = self.exchange_mappings.get(exchange, f'.{exchange}')
            ts_code = f"{symbol_code}{exchange_suffix}"
            index_info = df[df['ts_code'] == ts_code]
            if index_info.empty:
                # Provide more helpful error message with available indices
                available_indices = df[df['ts_code'].str.contains(exchange_suffix, na=False)]
                if len(available_indices) > 0:
                    available_list = available_indices['ts_code'].head(5).tolist()
                    return {"error": f"Index {symbol_code}{exchange_suffix} not found. Available {exchange} indices: {', '.join(available_list)}"}
                else:
                    return {"error": f"Index {symbol_code}{exchange_suffix} not found. No {exchange} indices available in database."}
            
            info = index_info.iloc[0].to_dict()
            
            # Add exchange and other fields for consistency
            info.update({
                'exchange': exchange,
                'area': 'China',
                'industry': 'Index',
                'list_date': info.get('base_date', 'N/A')
            })
            
            # Get additional metrics
            try:
                daily_data = self.pro.index_daily(
                    ts_code=info['ts_code'],
                    start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
                    end_date=datetime.now().strftime('%Y%m%d')
                )
                
                if not daily_data.empty:
                    latest = daily_data.iloc[0]
                    info.update({
                        'current_price': latest['close'],
                        'change': latest['change'],
                        'pct_chg': latest['pct_chg'],
                        'volume': latest['vol'],
                        'amount': latest['amount']
                    })
            except Exception as e:
                self.logger.warning(f"Could not get index price data: {e}")
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting index info: {e}")
            return {"error": str(e)}
    
    def get_daily_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get daily price data for a symbol"""
        try:
            exchange = self.get_exchange_from_symbol(symbol)
            if not exchange:
                raise ValueError("Unsupported exchange")
            
            # Default date range
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            
            if exchange == 'HKEX':
                # Hong Kong data
                df = self.pro.hk_daily(
                    ts_code=symbol,  # Use full symbol like 00001.HK
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                # Check if this is an index symbol
                if self._is_index_symbol(symbol):
                    # Use index_daily for index symbols
                    df = self.pro.index_daily(
                        ts_code=symbol,  # Use full symbol like 000001.SH
                        start_date=start_date,
                        end_date=end_date
                    )
                else:
                    # Mainland China stock data - use the original symbol format
                    df = self.pro.daily(
                        ts_code=symbol,  # Use full symbol like 600026.SH
                        start_date=start_date,
                        end_date=end_date
                    )
            
            if df.empty:
                return pd.DataFrame()
            
            # Convert date column
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            df = df.sort_values('trade_date')
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error getting daily data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_daily_data_by_days(self, ts_code: str, days: int) -> pd.DataFrame:
        """Get daily price data for a symbol for specified number of days"""
        try:
            # Calculate start date based on days
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            # Get data using the existing method
            return self.get_daily_data(ts_code, start_date, end_date)
            
        except Exception as e:
            self.logger.error(f"Error getting daily data for {ts_code} for {days} days: {e}")
            return pd.DataFrame()
    
    def get_monthly_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """Get monthly price data for a symbol"""
        try:
            exchange = self.get_exchange_from_symbol(symbol)
            if not exchange:
                raise ValueError("Unsupported exchange")
            
            # Default date range
            if not end_date:
                end_date = datetime.now().strftime('%Y%m%d')
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y%m%d')
            
            # Check if this is an index symbol
            if self._is_index_symbol(symbol):
                # For indices, we need to use daily data and resample to monthly
                # since Tushare doesn't have a direct monthly index data endpoint
                daily_df = self.get_daily_data(symbol, start_date, end_date)
                if daily_df.empty:
                    return pd.DataFrame()
                
                # Resample to monthly (last trading day of each month)
                daily_df = daily_df.set_index('trade_date')
                monthly_df = daily_df.resample('ME').last()  # Use 'ME' instead of deprecated 'M'
                monthly_df = monthly_df.reset_index()
                monthly_df['trade_date'] = monthly_df['trade_date'].dt.strftime('%Y%m%d')
                
                return monthly_df
            else:
                # For Hong Kong stocks, use daily data and resample to monthly
                # since Tushare doesn't have a direct monthly endpoint for HKEX
                if exchange == 'HKEX':
                    daily_df = self.get_daily_data(symbol, start_date, end_date)
                    if daily_df.empty:
                        return pd.DataFrame()
                    
                    # Resample to monthly (last trading day of each month)
                    daily_df = daily_df.set_index('trade_date')
                    # Use monthly resampling for HK stocks
                    monthly_df = daily_df.resample('ME').last()  # Monthly data
                    monthly_df = monthly_df.reset_index()
                    monthly_df['trade_date'] = monthly_df['trade_date'].dt.strftime('%Y%m%d')
                    
                    return monthly_df
                else:
                    # Use regular monthly method for mainland China stocks
                    df = self.pro.monthly(
                        ts_code=symbol,  # Use full symbol like 600026.SH
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if df.empty:
                        return pd.DataFrame()
                    
                    # Convert date column
                    df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                    df = df.sort_values('trade_date')
                    
                    return df
            
        except Exception as e:
            self.logger.error(f"Error getting monthly data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_dividend_data(self, symbol: str) -> pd.DataFrame:
        """Get comprehensive dividend data for a symbol"""
        try:
            exchange = self.get_exchange_from_symbol(symbol)
            if not exchange:
                raise ValueError("Unsupported exchange")
            
            symbol_code = symbol.split('.')[0]
            
            if exchange == 'HKEX':
                # Hong Kong dividend data - get more comprehensive data
                df = self.pro.hk_dividend(
                    ts_code=f"{symbol_code}.HK",
                    fields='ts_code,ann_date,div_proc_date,stk_div_date,cash_div_tax,cash_div_before_tax,stk_div,stk_bo_rate,stk_co_rate,cash_div_after_tax'
                )
            else:
                # Mainland China dividend data - get more comprehensive data
                df = self.pro.dividend(
                    ts_code=f"{symbol_code}.{exchange}",
                    fields='ts_code,ann_date,div_proc_date,stk_div_date,cash_div_tax,cash_div_before_tax,stk_div,stk_bo_rate,stk_co_rate,cash_div_after_tax'
                )
            
            if df.empty:
                return pd.DataFrame()
            
            # Convert date columns
            df['ann_date'] = pd.to_datetime(df['ann_date'], format='%Y%m%d', errors='coerce')
            df['div_proc_date'] = pd.to_datetime(df['div_proc_date'], format='%Y%m%d', errors='coerce')
            df['stk_div_date'] = pd.to_datetime(df['stk_div_date'], format='%Y%m%d', errors='coerce')
            
            # Fill NaN values with 0 for numeric columns
            numeric_columns = ['cash_div_tax', 'cash_div_before_tax', 'stk_div', 'stk_bo_rate', 'stk_co_rate', 'cash_div_after_tax']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].fillna(0)
            
            return df.sort_values('ann_date', ascending=False)
            
        except Exception as e:
            self.logger.error(f"Error getting dividend data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_rating_data(self, symbol: str) -> pd.DataFrame:
        """Get rating data for a symbol (if available)"""
        try:
            exchange = self.get_exchange_from_symbol(symbol)
            if not exchange:
                raise ValueError("Unsupported exchange")
            
            symbol_code = symbol.split('.')[0]
            
            # Try to get rating data - this method may not be available for all symbols
            try:
                if exchange == 'HKEX':
                    # Hong Kong rating data
                    df = self.pro.hk_rating(
                        ts_code=f"{symbol_code}.HK"
                    )
                else:
                    # Mainland China rating data
                    df = self.pro.rating(
                        ts_code=f"{symbol_code}.{exchange}"
                    )
                
                if df.empty:
                    return pd.DataFrame()
                
                # Convert date columns
                if 'rating_date' in df.columns:
                    df['rating_date'] = pd.to_datetime(df['rating_date'], format='%Y%m%d', errors='coerce')
                
                return df.sort_values('rating_date', ascending=False)
                
            except Exception as e:
                # Rating data might not be available for this symbol
                self.logger.warning(f"Rating data not available for {symbol}: {e}")
                return pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error getting rating data for {symbol}: {e}")
            return pd.DataFrame()
    
    def search_symbols(self, query: str, exchange: str = None) -> List[Dict[str, Any]]:
        """Search for symbols by name or code"""
        try:
            results = []
            
            if exchange == 'HKEX':
                # Search Hong Kong stocks
                df = self.pro.hk_basic(
                    fields='ts_code,symbol,name,area,industry,list_date'
                )
                if not query.isdigit():
                    # Search by name
                    df = df[df['name'].str.contains(query, case=False, na=False)]
                else:
                    # Search by symbol
                    df = df[df['symbol'].str.contains(query, na=False)]
                
                for _, row in df.head(10).iterrows():
                    results.append({
                        'symbol': f"{row['symbol']}.HK",
                        'name': row['name'],
                        'exchange': 'HKEX',
                        'industry': row.get('industry', ''),
                        'list_date': row.get('list_date', '')
                    })
            else:
                # Search mainland China stocks
                df = self.pro.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,symbol,name,area,industry,list_date'
                )
                
                if not query.isdigit():
                    # Search by name
                    df = df[df['name'].str.contains(query, case=False, na=False)]
                else:
                    # Search by symbol
                    df = df[df['symbol'].str.contains(query, na=False)]
                
                for _, row in df.head(10).iterrows():
                    # Determine exchange from ts_code
                    ts_code = row['ts_code']
                    if ts_code.endswith('.SH'):
                        exchange_suffix = 'SH'
                    elif ts_code.endswith('.SZ'):
                        exchange_suffix = 'SZ'
                    elif ts_code.endswith('.BJ'):
                        exchange_suffix = 'BJ'
                    else:
                        continue
                    
                    results.append({
                        'symbol': f"{row['symbol']}.{exchange_suffix}",
                        'name': row['name'],
                        'exchange': exchange_suffix,
                        'industry': row.get('industry', ''),
                        'list_date': row.get('list_date', '')
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching symbols: {e}")
            return []
    
    def search_symbols_english(self, query: str, exchange: str = None) -> List[Dict[str, Any]]:
        """Search for symbols by English name or code"""
        try:
            results = []
            
            if exchange == 'HKEX':
                # Search Hong Kong stocks with English names
                try:
                    df = self.pro.hk_basic(
                        fields='ts_code,symbol,name,enname,area,industry,list_date'
                    )
                    
                    if not query.isdigit():
                        # Search by English name first, then by Chinese name if no English results
                        english_results = df[df['enname'].str.contains(query, case=False, na=False)]
                        if len(english_results) > 0:
                            df = english_results
                        else:
                            # Fallback to Chinese name search
                            df = df[df['name'].str.contains(query, case=False, na=False)]
                    else:
                        # Search by symbol
                        df = df[df['symbol'].str.contains(query, na=False)]
                    
                    for _, row in df.head(15).iterrows():  # Increased limit
                        # Use English name if available, otherwise Chinese name
                        name = row.get('enname') if row.get('enname') and row.get('enname').strip() else row.get('name')
                        if name:
                            results.append({
                                'symbol': f"{row['symbol']}.HK",
                                'name': name,
                                'exchange': 'HKEX',
                                'industry': row.get('industry', ''),
                                'list_date': row.get('list_date', '')
                            })
                except Exception as e:
                    self.logger.warning(f"HKEX English search failed, falling back to basic search: {e}")
                    # Fallback to basic search
                    return self.search_symbols(query, exchange)
                    
            else:
                # Search mainland China stocks with English names
                try:
                    df = self.pro.stock_basic(
                        exchange='',
                        list_status='L',
                        fields='ts_code,symbol,name,enname,area,industry,list_date'
                    )
                    
                    if not query.isdigit():
                        # Search by English name first, then by Chinese name if no English results
                        english_results = df[df['enname'].str.contains(query, case=False, na=False)]
                        if len(english_results) > 0:
                            df = english_results
                        else:
                            # Fallback to Chinese name search
                            df = df[df['name'].str.contains(query, case=False, na=False)]
                    else:
                        # Search by symbol
                        df = df[df['symbol'].str.contains(query, na=False)]
                    
                    for _, row in df.head(15).iterrows():  # Increased limit
                        # Determine exchange from ts_code
                        ts_code = row['ts_code']
                        if ts_code.endswith('.SH'):
                            exchange_suffix = 'SH'
                        elif ts_code.endswith('.SZ'):
                            exchange_suffix = 'SZ'
                        elif ts_code.endswith('.BJ'):
                            exchange_suffix = 'BJ'
                        else:
                            continue
                        
                        # Use English name if available, otherwise Chinese name
                        name = row.get('enname') if row.get('enname') and row.get('enname').strip() else row.get('name')
                        if name:
                            results.append({
                                'symbol': f"{row['symbol']}.{exchange_suffix}",
                                'name': name,
                                'exchange': exchange_suffix,
                                'industry': row.get('industry', ''),
                                'list_date': row.get('list_date', '')
                            })
                except Exception as e:
                    self.logger.warning(f"Mainland China English search failed, falling back to basic search: {e}")
                    # Fallback to basic search
                    return self.search_symbols(query, exchange)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching symbols with English names: {e}")
            return []
    
    def get_exchange_symbols(self, exchange: str) -> List[Dict[str, Any]]:
        """Get all symbols for a specific exchange with detailed information"""
        try:
            symbols_data = []
            
            if exchange == 'HKEX':
                # Get HKEX symbols with English names only
                df = self.pro.hk_basic(fields='ts_code,name,enname,list_date')
                for _, row in df.iterrows():
                    # Use only English name, skip if not available
                    english_name = row.get('enname')
                    if not (english_name and english_name.strip()):
                        continue
                    name = english_name
                    symbols_data.append({
                        'symbol': row['ts_code'],  # Already includes .HK suffix
                        'name': name,
                        'currency': 'HKD',
                        'list_date': row.get('list_date', 'N/A')
                    })
            elif exchange == 'SSE':
                # Get SSE symbols with English names only
                try:
                    df = self.pro.stock_basic(exchange='SSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use only English name, skip if not available
                        english_name = row.get('enname')
                        if not (english_name and english_name.strip()):
                            continue
                        name = english_name
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SH",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception as e:
                    self.logger.warning(f"Could not get English names for SSE: {e}")
                    # Skip SSE if English names are not available
                    pass
            elif exchange == 'SZSE':
                # Get SZSE symbols with English names only
                try:
                    df = self.pro.stock_basic(exchange='SZSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use only English name, skip if not available
                        english_name = row.get('enname')
                        if not (english_name and english_name.strip()):
                            continue
                        name = english_name
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SZ",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception as e:
                    self.logger.warning(f"Could not get English names for SZSE: {e}")
                    # Skip SZSE if English names are not available
                    pass
            elif exchange == 'BSE':
                # Get BSE symbols with English names only
                try:
                    df = self.pro.stock_basic(exchange='BSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use only English name, skip if not available
                        english_name = row.get('enname')
                        if not (english_name and english_name.strip()):
                            continue
                        name = english_name
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.BJ",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception as e:
                    self.logger.warning(f"Could not get English names for BSE: {e}")
                    # Skip BSE if English names are not available
                    pass
            
            return symbols_data[:100]  # Limit to first 100 symbols for display
            
        except Exception as e:
            error_msg = str(e)
            # Handle specific API permission errors
            if "权限" in error_msg or "permission" in error_msg.lower():
                self.logger.error(f"API permission error for exchange {exchange}: {e}")
                raise Exception("API权限不足. Пожалуйста, проверьте ваш Tushare API ключ и убедитесь, что у вас есть доступ к данным.")
            else:
                self.logger.error(f"Error getting symbols for exchange {exchange}: {e}")
                raise Exception(f"Ошибка получения символов для биржи {exchange}: {error_msg}")
    
    def get_exchange_symbols_count(self, exchange: str) -> int:
        """Get total count of symbols for a specific exchange"""
        try:
            if exchange == 'HKEX':
                df = self.pro.hk_basic(fields='symbol')
                return len(df)
            elif exchange == 'SSE':
                df = self.pro.stock_basic(exchange='SSE', list_status='L', fields='symbol')
                return len(df)
            elif exchange == 'SZSE':
                df = self.pro.stock_basic(exchange='SZSE', list_status='L', fields='symbol')
                return len(df)
            elif exchange == 'BSE':
                df = self.pro.stock_basic(exchange='BSE', list_status='L', fields='symbol')
                return len(df)
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error getting symbol count for exchange {exchange}: {e}")
            return 0
    
    def get_exchange_symbols_full(self, exchange: str) -> List[Dict[str, Any]]:
        """Get ALL symbols for a specific exchange (no limit) for Excel export"""
        try:
            symbols_data = []
            
            if exchange == 'HKEX':
                # Get HKEX symbols with English names only
                df = self.pro.hk_basic(fields='ts_code,name,enname,list_date')
                for _, row in df.iterrows():
                    # Use only English name, skip if not available
                    english_name = row.get('enname')
                    if not (english_name and english_name.strip()):
                        continue
                    name = english_name
                    symbols_data.append({
                        'symbol': row['ts_code'],  # Already includes .HK suffix
                        'name': name,
                        'currency': 'HKD',
                        'list_date': row.get('list_date', 'N/A')
                    })
            elif exchange == 'SSE':
                # Get SSE symbols with English names only
                try:
                    df = self.pro.stock_basic(exchange='SSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use only English name, skip if not available
                        english_name = row.get('enname')
                        if not (english_name and english_name.strip()):
                            continue
                        name = english_name
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SH",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception as e:
                    self.logger.warning(f"Could not get English names for SSE: {e}")
                    # Skip SSE if English names are not available
                    pass
            elif exchange == 'SZSE':
                # Get SZSE symbols with English names only
                try:
                    df = self.pro.stock_basic(exchange='SZSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use only English name, skip if not available
                        english_name = row.get('enname')
                        if not (english_name and english_name.strip()):
                            continue
                        name = english_name
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SZ",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception as e:
                    self.logger.warning(f"Could not get English names for SZSE: {e}")
                    # Skip SZSE if English names are not available
                    pass
            elif exchange == 'BSE':
                # Get BSE symbols with English names only
                try:
                    df = self.pro.stock_basic(exchange='BSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use only English name, skip if not available
                        english_name = row.get('enname')
                        if not (english_name and english_name.strip()):
                            continue
                        name = english_name
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.BJ",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception as e:
                    self.logger.warning(f"Could not get English names for BSE: {e}")
                    # Skip BSE if English names are not available
                    pass
            
            return symbols_data  # No limit for Excel export
            
        except Exception as e:
            error_msg = str(e)
            # Handle specific API permission errors
            if "权限" in error_msg or "permission" in error_msg.lower():
                self.logger.error(f"API permission error for exchange {exchange}: {e}")
                raise Exception("API权限不足. Пожалуйста, проверьте ваш Tushare API ключ и убедитесь, что у вас есть доступ к данным.")
            else:
                self.logger.error(f"Error getting symbols for exchange {exchange}: {e}")
                raise Exception(f"Ошибка получения символов для биржи {exchange}: {error_msg}")

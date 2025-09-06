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
            # Get stock basic info with English names
            try:
                df = self.pro.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,symbol,name,enname,area,industry,list_date'
                )
            except Exception:
                # Fallback to basic fields if enname is not available
                df = self.pro.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,symbol,name,area,industry,list_date'
                )
            
            # Find matching stock
            stock_info = df[df['symbol'] == symbol_code]
            if stock_info.empty:
                return {"error": "Stock not found"}
            
            info = stock_info.iloc[0].to_dict()
            
            # Use English name if available, otherwise fall back to Chinese name
            if 'enname' in info and info['enname']:
                info['name'] = info['enname']
            
            # Get additional metrics
            try:
                daily_data = self.pro.daily(
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
                self.logger.warning(f"Could not get price data: {e}")
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting mainland stock info: {e}")
            return {"error": str(e)}
    
    def _get_hk_stock_info(self, symbol_code: str) -> Dict[str, Any]:
        """Get stock information for Hong Kong exchange"""
        try:
            # Get HK stock basic info
            df = self.pro.hk_basic(
                fields='ts_code,name,list_date'
            )
            
            # Find matching stock by ts_code
            ts_code = f"{symbol_code}.HK"
            stock_info = df[df['ts_code'] == ts_code]
            if stock_info.empty:
                return {"error": "Stock not found"}
            
            info = stock_info.iloc[0].to_dict()
            
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
                # Mainland China data - use the original symbol format
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
            
            if exchange == 'HKEX':
                # Hong Kong monthly data
                df = self.pro.hk_monthly(
                    ts_code=symbol,  # Use full symbol like 00001.HK
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                # Mainland China monthly data - use the original symbol format
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
        """Get dividend data for a symbol"""
        try:
            exchange = self.get_exchange_from_symbol(symbol)
            if not exchange:
                raise ValueError("Unsupported exchange")
            
            symbol_code = symbol.split('.')[0]
            
            if exchange == 'HKEX':
                # Hong Kong dividend data
                df = self.pro.hk_dividend(
                    ts_code=f"{symbol_code}.HK"
                )
            else:
                # Mainland China dividend data
                df = self.pro.dividend(
                    ts_code=f"{symbol_code}.{exchange}"
                )
            
            if df.empty:
                return pd.DataFrame()
            
            # Convert date column
            df['ann_date'] = pd.to_datetime(df['ann_date'], format='%Y%m%d')
            df['div_proc_date'] = pd.to_datetime(df['div_proc_date'], format='%Y%m%d')
            df['stk_div_date'] = pd.to_datetime(df['stk_div_date'], format='%Y%m%d')
            
            return df.sort_values('ann_date')
            
        except Exception as e:
            self.logger.error(f"Error getting dividend data for {symbol}: {e}")
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
    
    def get_exchange_symbols(self, exchange: str) -> List[Dict[str, Any]]:
        """Get all symbols for a specific exchange with detailed information"""
        try:
            symbols_data = []
            
            if exchange == 'HKEX':
                # Get HKEX symbols with English names
                df = self.pro.hk_basic(fields='ts_code,name,enname,list_date')
                for _, row in df.iterrows():
                    # Use English name if available, otherwise fall back to Chinese name
                    name = row.get('enname') or row.get('name', 'N/A')
                    symbols_data.append({
                        'symbol': row['ts_code'],  # Already includes .HK suffix
                        'name': name,
                        'currency': 'HKD',
                        'list_date': row.get('list_date', 'N/A')
                    })
            elif exchange == 'SSE':
                # Try to get English names for SSE
                try:
                    df = self.pro.stock_basic(exchange='SSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use English name if available, otherwise fall back to Chinese name
                        name = row.get('enname') or row.get('name', 'N/A')
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SH",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception:
                    # Fallback to basic fields if enname is not available
                    df = self.pro.stock_basic(exchange='SSE', list_status='L', fields='symbol,name,list_date')
                    for _, row in df.iterrows():
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SH",
                            'name': row.get('name', 'N/A'),
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
            elif exchange == 'SZSE':
                # Try to get English names for SZSE
                try:
                    df = self.pro.stock_basic(exchange='SZSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use English name if available, otherwise fall back to Chinese name
                        name = row.get('enname') or row.get('name', 'N/A')
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SZ",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception:
                    # Fallback to basic fields if enname is not available
                    df = self.pro.stock_basic(exchange='SZSE', list_status='L', fields='symbol,name,list_date')
                    for _, row in df.iterrows():
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SZ",
                            'name': row.get('name', 'N/A'),
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
            elif exchange == 'BSE':
                # Try to get English names for BSE
                try:
                    df = self.pro.stock_basic(exchange='BSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use English name if available, otherwise fall back to Chinese name
                        name = row.get('enname') or row.get('name', 'N/A')
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.BJ",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception:
                    # Fallback to basic fields if enname is not available
                    df = self.pro.stock_basic(exchange='BSE', list_status='L', fields='symbol,name,list_date')
                    for _, row in df.iterrows():
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.BJ",
                            'name': row.get('name', 'N/A'),
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
            
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
                # Get HKEX symbols with English names
                df = self.pro.hk_basic(fields='ts_code,name,enname,list_date')
                for _, row in df.iterrows():
                    # Use English name if available, otherwise fall back to Chinese name
                    name = row.get('enname') or row.get('name', 'N/A')
                    symbols_data.append({
                        'symbol': row['ts_code'],  # Already includes .HK suffix
                        'name': name,
                        'currency': 'HKD',
                        'list_date': row.get('list_date', 'N/A')
                    })
            elif exchange == 'SSE':
                # Try to get English names for SSE
                try:
                    df = self.pro.stock_basic(exchange='SSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use English name if available, otherwise fall back to Chinese name
                        name = row.get('enname') or row.get('name', 'N/A')
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SH",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception:
                    # Fallback to basic fields if enname is not available
                    df = self.pro.stock_basic(exchange='SSE', list_status='L', fields='symbol,name,list_date')
                    for _, row in df.iterrows():
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SH",
                            'name': row.get('name', 'N/A'),
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
            elif exchange == 'SZSE':
                # Try to get English names for SZSE
                try:
                    df = self.pro.stock_basic(exchange='SZSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use English name if available, otherwise fall back to Chinese name
                        name = row.get('enname') or row.get('name', 'N/A')
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SZ",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception:
                    # Fallback to basic fields if enname is not available
                    df = self.pro.stock_basic(exchange='SZSE', list_status='L', fields='symbol,name,list_date')
                    for _, row in df.iterrows():
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.SZ",
                            'name': row.get('name', 'N/A'),
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
            elif exchange == 'BSE':
                # Try to get English names for BSE
                try:
                    df = self.pro.stock_basic(exchange='BSE', list_status='L', fields='symbol,name,enname,list_date')
                    for _, row in df.iterrows():
                        # Use English name if available, otherwise fall back to Chinese name
                        name = row.get('enname') or row.get('name', 'N/A')
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.BJ",
                            'name': name,
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
                except Exception:
                    # Fallback to basic fields if enname is not available
                    df = self.pro.stock_basic(exchange='BSE', list_status='L', fields='symbol,name,list_date')
                    for _, row in df.iterrows():
                        symbols_data.append({
                            'symbol': f"{row['symbol']}.BJ",
                            'name': row.get('name', 'N/A'),
                            'currency': 'CNY',
                            'list_date': row.get('list_date', 'N/A')
                        })
            
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

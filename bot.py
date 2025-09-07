# Standard library imports
import sys
import logging
import os
import json
import threading
import re
import traceback
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, List, Optional, Any, Union
import io
from datetime import datetime
import tempfile

# Load environment variables from config.env
try:
    from dotenv import load_dotenv
    load_dotenv('config.env')
except ImportError:
    pass  # dotenv not available, use system environment variables

# Configure matplotlib for headless environments without filesystem dependencies
# Note: No filesystem configuration needed for in-memory operations

# Third-party imports
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import okama as ok

# Configure matplotlib backend for headless environments (CI/CD)
if os.getenv('DISPLAY') is None and os.getenv('MPLBACKEND') is None:
    matplotlib.use('Agg')

# Suppress matplotlib warnings for missing CJK glyphs
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')

# Optional imports
try:
    import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    print("Warning: tabulate library not available. Using simple text formatting.")

# Telegram imports
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Check Python version compatibility
if sys.version_info < (3, 7):
    print("ERROR: Python 3.7+ required. Current version:", sys.version)
    raise RuntimeError("Python 3.7+ required")

# Local imports
from config import Config
from services.yandexgpt_service import YandexGPTService
from services.tushare_service import TushareService
from services.gemini_service import GeminiService
from services.simple_chart_analysis import SimpleChartAnalysisService

from services.chart_styles import chart_styles
from services.context_store import JSONUserContextStore

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Health check for deployment
def health_check():
    """Simple health check for deployment"""
    logger.info(f"✅ Environment: {'PRODUCTION' if os.getenv('PRODUCTION') else 'LOCAL'}")
    logger.info(f"✅ Python version: {sys.version}")
    logger.info(f"✅ Bot token configured: {'Yes' if Config.TELEGRAM_BOT_TOKEN else 'No'}")
    return True

class ShansAi:
    """Telegram bot for financial analysis with Okama library"""
    
    def __init__(self):
        """Initialize the bot with required services"""
        Config.validate()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize services
        self.yandexgpt_service = YandexGPTService()
        self.chart_styles = chart_styles
        
        # Initialize Tushare service if API key is available
        try:
            self.tushare_service = TushareService()
        except ValueError:
            self.tushare_service = None
            self.logger.warning("Tushare service not initialized - API key not provided")
        
        # Initialize Gemini service for chart analysis
        try:
            self.gemini_service = GeminiService()
            if self.gemini_service.is_available():
                self.logger.info("Gemini service initialized successfully")
            else:
                self.logger.warning("Gemini service not available - check credentials")
                # Log detailed status for debugging
                status = self.gemini_service.get_service_status()
                self.logger.info(f"Gemini status: {status}")
        except Exception as e:
            self.gemini_service = None
            self.logger.warning(f"Gemini service not initialized: {e}")
        
        # Initialize simple chart analysis as fallback
        try:
            self.simple_analysis_service = SimpleChartAnalysisService()
            self.logger.info("Simple chart analysis service initialized as fallback")
        except Exception as e:
            self.simple_analysis_service = None
            self.logger.warning(f"Simple analysis service not initialized: {e}")
        
        # Known working asset symbols for suggestions
        self.known_assets = {
            'US': ['VOO.US', 'SPY.US', 'QQQ.US', 'AGG.US', 'AAPL.US', 'TSLA.US', 'MSFT.US'],
            'INDX': ['RGBITR.INDX', 'MCFTR.INDX', 'SPX.INDX', 'IXIC.INDX'],
            'COMM': ['GC.COMM', 'SI.COMM', 'CL.COMM', 'BRENT.COMM'],
            'FX': ['EURUSD.FX', 'GBPUSD.FX', 'USDJPY.FX'],
            'MOEX': ['SBER.MOEX', 'GAZP.MOEX', 'LKOH.MOEX'],
            'LSE': ['VOD.LSE', 'HSBA.LSE', 'BP.LSE'],
            'SSE': ['600000.SH', '000001.SH'],
            'SZSE': ['000001.SZ', '399005.SZ'],
            'BSE': ['900001.BJ', '800001.BJ'],
            'HKEX': ['00001.HK', '00700.HK']
        }
        
        # User session storage (in-memory for fast access)
        self.user_sessions = {}
        # Persistent context store
        self.context_store = JSONUserContextStore()
        
        # User history management
        self.user_history: Dict[int, List[dict]] = {}       # chat_id -> list[{"role": "...", "parts": [str]}]
        self.context_enabled: Dict[int, bool] = {}          # chat_id -> bool
        self.MAX_HISTORY_MESSAGES = 20
        self.MAX_TELEGRAM_CHUNK = 4000
        


    # --- Asset Service Methods ---
    
    def resolve_symbol_or_isin(self, identifier: str) -> Dict[str, Union[str, Any]]:
        """
        Resolve user-provided identifier to an okama-compatible ticker.

        Supports:
        - Ticker in okama format (e.g., 'AAPL.US', 'SBER.MOEX')
        - Plain ticker (e.g., 'AAPL') – automatically adds appropriate namespace
        - ISIN (e.g., 'US0378331005') – tries to resolve via okama search
        - Company names (e.g., 'Apple', 'Tesla') – searches via okama search

        Returns dict: { 'symbol': str, 'type': 'ticker'|'isin'|'company_name', 'source': str }
        or { 'error': str } on failure.
        """
        try:
            raw = (identifier or '').strip()
            if not raw:
                return {'error': 'Пустой идентификатор актива'}

            upper = raw.upper()

            # If already okama-style ticker like XXX.SUFFIX
            if '.' in upper and len(upper.split('.')) == 2 and all(part for part in upper.split('.')):
                # Check if it's a Chinese exchange symbol
                if self.tushare_service and self.tushare_service.is_tushare_symbol(upper):
                    return {'symbol': upper, 'type': 'ticker', 'source': 'tushare'}
                else:
                    return {'symbol': upper, 'type': 'ticker', 'source': 'input'}

            if self._looks_like_isin(upper):
                # For ISIN, search for the corresponding symbol
                try:
                    import okama as ok
                    search_result = ok.search(upper)
                    if len(search_result) > 0:
                        # Found the asset, use the first result
                        symbol = search_result.iloc[0]['symbol']
                        return {'symbol': symbol, 'type': 'isin', 'source': 'okama_search'}
                    else:
                        # ISIN not found, return error
                        return {'error': f'ISIN {upper} не найден в базе данных okama'}
                except Exception as e:
                    # Search failed, return error
                    return {'error': f'Ошибка поиска ISIN {upper}: {str(e)}'}

            # Try to search for company name or plain ticker
            try:
                import okama as ok
                search_result = ok.search(raw)  # Use original case for better search
                if len(search_result) > 0:
                    # Found the asset, select the best result
                    symbol = self._select_best_search_result(search_result, raw)
                    name = search_result.iloc[0].get('name', '')
                    
                    # Determine type based on input
                    if self._looks_like_ticker(raw):
                        input_type = 'ticker'
                    else:
                        input_type = 'company_name'
                    
                    return {
                        'symbol': symbol, 
                        'type': input_type, 
                        'source': 'okama_search',
                        'name': name
                    }
                else:
                    # Not found in Okama, try Tushare if available
                    if self.tushare_service:
                        tushare_results = self.tushare_service.search_symbols(raw)
                        if tushare_results:
                            # Return the first result
                            result = tushare_results[0]
                            return {
                                'symbol': result['symbol'],
                                'type': 'ticker',
                                'source': 'tushare_search',
                                'name': result['name']
                            }
                    
                    # Not found, try as plain ticker
                    if self._looks_like_ticker(raw):
                        return {'symbol': upper, 'type': 'ticker', 'source': 'plain'}
                    else:
                        return {'error': f'"{raw}" не найден в базе данных okama и tushare'}
            except Exception as e:
                # Search failed, try as plain ticker
                if self._looks_like_ticker(raw):
                    return {'symbol': upper, 'type': 'ticker', 'source': 'plain'}
                else:
                    return {'error': f'Ошибка поиска "{raw}": {str(e)}'}

        except Exception as e:
            return {'error': f"Ошибка при разборе идентификатора: {str(e)}"}

    def determine_data_source(self, symbol: str) -> str:
        """
        Determine which data source to use (okama or tushare) based on symbol
        
        Args:
            symbol: Symbol in format like 'AAPL.US' or '600000.SH'
            
        Returns:
            'tushare' for Chinese exchanges, 'okama' for others
        """
        if not self.tushare_service:
            return 'okama'
        
        return 'tushare' if self.tushare_service.is_tushare_symbol(symbol) else 'okama'

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

    def _looks_like_ticker(self, val: str) -> bool:
        """
        Check if string looks like a ticker symbol
        
        Args:
            val: String to check
            
        Returns:
            True if string looks like a ticker
        """
        if not val or len(val) < 1:
            return False
        
        # Ticker should be mostly alphanumeric, 1-5 characters
        if len(val) > 5:
            return False
        
        # Should be mostly uppercase letters and numbers
        if not val.isalnum():
            return False
        
        # Should start with a letter
        if not val[0].isalpha():
            return False
        
        return True

    def _select_best_search_result(self, search_result, original_input: str) -> str:
        """
        Select the best symbol from search results based on priority and relevance
        
        Args:
            search_result: DataFrame with search results
            original_input: Original user input
            
        Returns:
            Best symbol string
        """
        # Allowed exchanges from okama configuration (all official namespaces)
        allowed_exchanges = ['US', 'LSE', 'XETR', 'XFRA', 'XSTU', 'XAMS', 'MOEX', 'XTAE', 'PIF', 'FX', 'CC', 'INDX', 'COMM', 'RE', 'CBR', 'PF', 'INFL', 'RATE', 'RATIO']
        
        # Priority order for exchanges (subset of allowed exchanges)
        priority_exchanges = ['US', 'MOEX', 'LSE', 'XETR', 'XFRA', 'XAMS']
        
        # First, try to find exact match with priority exchanges
        for _, row in search_result.iterrows():
            symbol = row['symbol']
            name = row.get('name', '').lower()
            
            # Check if symbol matches original input exactly (case-insensitive)
            if symbol.split('.')[0].upper() == original_input.upper():
                if '.' in symbol and symbol.split('.')[-1] in priority_exchanges:
                    return symbol
        
        # Second, try to find name match with priority exchanges
        original_lower = original_input.lower()
        for _, row in search_result.iterrows():
            symbol = row['symbol']
            name = row.get('name', '').lower()
            
            # Check if name contains original input or vice versa
            if (original_lower in name or name in original_lower) and len(name) > 3:
                if '.' in symbol and symbol.split('.')[-1] in priority_exchanges:
                    return symbol
        
        # Third, try to find any result with priority exchanges
        for exchange in priority_exchanges:
            for _, row in search_result.iterrows():
                symbol = row['symbol']
                if '.' in symbol and symbol.split('.')[-1] == exchange:
                    return symbol
        
        # Fourth, try to find any result with allowed exchanges
        for exchange in allowed_exchanges:
            for _, row in search_result.iterrows():
                symbol = row['symbol']
                if '.' in symbol and symbol.split('.')[-1] == exchange:
                    # Verify the symbol is actually supported by okama
                    try:
                        ok.Asset(symbol)
                        return symbol
                    except Exception:
                        continue  # Skip this symbol if it's not supported
        
        # If no allowed exchange found, try the first result
        first_symbol = search_result.iloc[0]['symbol']
        try:
            ok.Asset(first_symbol)
            return first_symbol
        except Exception:
            # If even the first result fails, return it anyway (will be handled by caller)
            return first_symbol



    def get_random_examples(self, count: int = 3) -> list:
        """Get random examples from known assets"""
        import random
        all_assets = []
        for assets in self.known_assets.values():
            all_assets.extend(assets)
        return random.sample(all_assets, min(count, len(all_assets)))

    async def _handle_error(self, update: Update, error: Exception, context: str = "Unknown operation") -> None:
        """Общая функция для обработки ошибок"""
        error_msg = f"❌ Ошибка в {context}: {str(error)}"
        self.logger.error(f"{error_msg} - {traceback.format_exc()}")
        
        try:
            await self._send_message_safe(update, error_msg)
        except Exception as send_error:
            self.logger.error(f"Failed to send error message: {send_error}")
            # Try to send a simple error message
            try:
                if hasattr(update, 'message') and update.message is not None:
                    await update.message.reply_text("Произошла ошибка при обработке запроса")
            except Exception as final_error:
                self.logger.error(f"Final error message sending failed: {final_error}")
        
    def _check_existing_portfolio(self, symbols: List[str], weights: List[float], saved_portfolios: Dict) -> Optional[str]:
        """
        Проверяет, существует ли портфель с такими же активами и пропорциями.
        
        Args:
            symbols: Список символов активов
            weights: Список весов активов
            saved_portfolios: Словарь сохраненных портфелей
            
        Returns:
            Символ существующего портфеля или None, если не найден
        """
        # Нормализуем веса для сравнения (сумма = 1.0)
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        for portfolio_symbol, portfolio_info in saved_portfolios.items():
            existing_symbols = portfolio_info.get('symbols', [])
            existing_weights = portfolio_info.get('weights', [])
            
            # Проверяем количество активов
            if len(symbols) != len(existing_symbols):
                continue
                
            # Проверяем, что все символы совпадают (с учетом регистра)
            if set(symbol.upper() for symbol in symbols) != set(symbol.upper() for symbol in existing_symbols):
                continue
                
            # Нормализуем существующие веса
            existing_total = sum(existing_weights)
            if existing_total == 0:
                continue
            normalized_existing_weights = [w / existing_total for w in existing_weights]
            
            # Проверяем, что веса совпадают с точностью до 0.001
            weight_matches = True
            for i, (new_weight, existing_weight) in enumerate(zip(normalized_weights, normalized_existing_weights)):
                if abs(new_weight - existing_weight) > 0.001:
                    weight_matches = False
                    break
                    
            if weight_matches:
                return portfolio_symbol
                
        return None

    def _parse_portfolio_data(self, portfolio_data_str: str) -> tuple[list, list]:
        """Parse portfolio data string with weights (symbol:weight,symbol:weight)"""
        try:
            if not portfolio_data_str or not portfolio_data_str.strip():
                return [], []
                
            symbols = []
            weights = []
            
            for item in portfolio_data_str.split(','):
                item = item.strip()
                if not item:  # Skip empty items
                    continue
                    
                if ':' in item:
                    symbol, weight_str = item.split(':', 1)
                    symbol = symbol.strip()
                    if symbol:  # Only add non-empty symbols
                        symbols.append(symbol)
                        weights.append(float(weight_str.strip()))
                else:
                    # Fallback: treat as symbol without weight
                    symbols.append(item)
                    weights.append(1.0 / len([x for x in portfolio_data_str.split(',') if x.strip()]))
            
            return symbols, weights
        except Exception as e:
            self.logger.error(f"Error parsing portfolio data: {e}")
            return [], []

    def _normalize_or_equalize_weights(self, symbols: list, weights: list) -> list:
        """Return valid weights for okama: normalize if close to 1, else equal weights.

        - If weights list is empty or length mismatch with symbols, fallback to equal weights.
        - If any weight is non-positive, fallback to equal weights.
        - If sum differs from 1.0 beyond small epsilon, normalize to sum=1.0.
        """
        try:
            if not symbols:
                return []

            num_assets = len(symbols)

            # Fallback to equal weights when missing or invalid length
            if not weights or len(weights) != num_assets:
                return [1.0 / num_assets] * num_assets

            # Validate positivity
            if any((w is None) or (w <= 0) for w in weights):
                return [1.0 / num_assets] * num_assets

            total = sum(weights)
            if total <= 0:
                return [1.0 / num_assets] * num_assets

            # If already ~1 within tolerance, keep; else normalize precisely
            if abs(total - 1.0) <= 1e-6:
                return [float(w) for w in weights]

            normalized = [float(w) / total for w in weights]

            # Guard against numerical drift
            norm_total = sum(normalized)
            if abs(norm_total - 1.0) > 1e-9:
                # Final correction by scaling the first element
                diff = 1.0 - norm_total
                normalized[0] += diff
            return normalized
        except Exception:
            # Safe fallback
            return [1.0 / len(symbols)] * len(symbols) if symbols else []

    def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Получить контекст пользователя (с поддержкой персистентности)."""
        # Load from persistent store, and mirror into memory for hot path
        ctx = self.context_store.get_user_context(user_id)
        self.user_sessions[user_id] = ctx
        return ctx
    
    def _update_user_context(self, user_id: int, **kwargs):
        """Обновить контекст пользователя (и сохранить)."""
        # Update persistent store; keep in-memory mirror in sync
        updated = self.context_store.update_user_context(user_id, **kwargs)
        self.user_sessions[user_id] = updated
    
    def _add_to_conversation_history(self, user_id: int, message: str, response: str):
        """Добавить сообщение в историю разговора (с сохранением)."""
        self.context_store.add_conversation_entry(user_id, message, response)
        # Refresh in-memory cache
        self.user_sessions[user_id] = self.context_store.get_user_context(user_id)
    
    def _get_context_summary(self, user_id: int) -> str:
        """Получить краткое резюме контекста пользователя"""
        context = self._get_user_context(user_id)
        summary = []
        
        if context['last_assets']:
            summary.append(f"Последние активы: {', '.join(context['last_assets'][-3:])}")
        
        if context['last_period']:
            summary.append(f"Период: {context['last_period']}")
        
        return "; ".join(summary) if summary else "Новый пользователь"
    
    def _get_currency_by_symbol(self, symbol: str) -> tuple[str, str]:
        """
        Определить валюту по символу с учетом китайских бирж
        
        Returns:
            tuple: (currency, currency_info)
        """
        try:
            if '.' in symbol:
                namespace = symbol.split('.')[1]
                
                # Китайские биржи
                if namespace == 'HK':
                    return "HKD", f"автоматически определена по бирже HKEX ({symbol})"
                elif namespace == 'SH':
                    return "CNY", f"автоматически определена по бирже SSE ({symbol})"
                elif namespace == 'SZ':
                    return "CNY", f"автоматически определена по бирже SZSE ({symbol})"
                elif namespace == 'BJ':
                    return "CNY", f"автоматически определена по бирже BSE ({symbol})"
                
                # Другие биржи
                elif namespace == 'MOEX':
                    return "RUB", f"автоматически определена по бирже MOEX ({symbol})"
                elif namespace == 'US':
                    return "USD", f"автоматически определена по бирже US ({symbol})"
                elif namespace == 'LSE':
                    return "GBP", f"автоматически определена по бирже LSE ({symbol})"
                elif namespace == 'FX':
                    return "USD", f"автоматически определена по бирже FX ({symbol})"
                elif namespace == 'COMM':
                    return "USD", f"автоматически определена по бирже COMM ({symbol})"
                elif namespace == 'INDX':
                    return "USD", f"автоматически определена по бирже INDX ({symbol})"
                else:
                    return "USD", f"автоматически определена по умолчанию ({symbol})"
            else:
                return "USD", f"автоматически определена по умолчанию ({symbol})"
        except Exception as e:
            self.logger.warning(f"Could not determine currency for {symbol}: {e}")
            return "USD", f"автоматически определена по умолчанию ({symbol})"
    
    def _get_inflation_ticker_by_currency(self, currency: str) -> str:
        """
        Получить тикер инфляции по валюте
        
        Returns:
            str: тикер инфляции (например, 'CNY.INFL' для CNY)
        """
        inflation_mapping = {
            'USD': 'US.INFL',
            'RUB': 'RUS.INFL', 
            'EUR': 'EU.INFL',
            'GBP': 'GB.INFL',
            'CNY': 'CNY.INFL',  # Китайская инфляция
            'HKD': 'US.INFL'    # Гонконгская инфляция (приводим к USD)
        }
        return inflation_mapping.get(currency, 'US.INFL')
    
    def _is_chinese_symbol(self, symbol: str) -> bool:
        """
        Проверить, является ли символ китайским
        
        Returns:
            bool: True если символ китайский
        """
        if not self.tushare_service:
            return False
        return self.tushare_service.is_tushare_symbol(symbol)
    
    def _get_chinese_symbol_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Получить данные китайского символа через Tushare
        
        Returns:
            Dict с данными символа или None
        """
        if not self.tushare_service or not self._is_chinese_symbol(symbol):
            return None
        
        try:
            # Получаем базовую информацию о символе
            symbol_info = self.tushare_service.get_symbol_info(symbol)
            if symbol_info:
                return symbol_info
        except Exception as e:
            self.logger.warning(f"Could not get Chinese symbol data for {symbol}: {e}")
        
        return None
    
    async def _create_hybrid_chinese_comparison(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """
        Создать гибридное сравнение китайских символов
        - Максимальный период по датам
        - Данные по CNY.INFL из okama
        - Скрытые xlabel и ylabel
        - Заголовок: Сравнение название тикеров, биржа, валюта
        """
        try:
            self.logger.info(f"Creating hybrid comparison for Chinese symbols: {symbols}")
            
            # Определяем валюту по первому символу
            currency, currency_info = self._get_currency_by_symbol(symbols[0])
            inflation_ticker = self._get_inflation_ticker_by_currency(currency)
            
            # Получаем данные китайских символов через Tushare (максимальный период)
            chinese_data = {}
            all_dates = set()
            
            for symbol in symbols:
                if self._is_chinese_symbol(symbol):
                    try:
                        symbol_info = self.tushare_service.get_symbol_info(symbol)
                        # Получаем месячные данные для лучшего отображения
                        historical_data = self.tushare_service.get_monthly_data(symbol, start_date='19900101')
                        
                        if not historical_data.empty:
                            # Устанавливаем дату как индекс
                            historical_data = historical_data.set_index('trade_date')
                            chinese_data[symbol] = {
                                'info': symbol_info,
                                'data': historical_data
                            }
                            all_dates.update(historical_data.index)
                            self.logger.info(f"Got monthly data for Chinese symbol {symbol}: {len(historical_data)} records")
                    except Exception as e:
                        self.logger.warning(f"Could not get data for Chinese symbol {symbol}: {e}")
            
            if not chinese_data:
                await self._send_message_safe(update, 
                    f"❌ Не удалось получить данные для китайских символов: {', '.join(symbols)}")
                return
            
            # Получаем данные по инфляции из okama для CNY активов
            inflation_data = None
            self.logger.info(f"Currency: {currency}, inflation_ticker: {inflation_ticker}")
            self.logger.info(f"Condition check: currency == 'CNY' = {currency == 'CNY'}, inflation_ticker == 'CNY.INFL' = {inflation_ticker == 'CNY.INFL'}")
            
            if currency == 'CNY' and inflation_ticker == 'CNY.INFL':
                try:
                    import okama as ok
                    self.logger.info(f"Creating okama Asset for {inflation_ticker}")
                    inflation_asset = ok.Asset(inflation_ticker)
                    self.logger.info(f"Got inflation asset, wealth_index type: {type(inflation_asset.wealth_index)}")
                    # Получаем месячные данные инфляции для соответствия основным данным
                    inflation_data = inflation_asset.wealth_index.resample('M').last()
                    self.logger.info(f"Got monthly inflation data for {inflation_ticker}: {len(inflation_data)} records")
                    self.logger.info(f"Inflation data sample: {inflation_data.head()}")
                except Exception as e:
                    self.logger.warning(f"Could not get inflation data for {inflation_ticker}: {e}")
                    import traceback
                    self.logger.warning(f"Inflation error traceback: {traceback.format_exc()}")
            else:
                self.logger.info(f"Skipping inflation data: currency={currency}, inflation_ticker={inflation_ticker}")
            
            # Подготавливаем данные для стандартного метода сравнения
            comparison_data = {}
            symbols_list = []
            
            for symbol, data_dict in chinese_data.items():
                historical_data = data_dict['data']
                symbol_info = data_dict['info']
                
                if not historical_data.empty:
                    # Нормализуем данные к базовому значению (1000) как в okama
                    normalized_data = historical_data['close'] / historical_data['close'].iloc[0] * 1000
                    
                    # Получаем английское название символа для легенды
                    symbol_name = symbol_info.get('name', symbol)
                    # Приоритет английскому названию если доступно
                    if 'enname' in symbol_info and symbol_info['enname'] and symbol_info['enname'].strip():
                        symbol_name = symbol_info['enname']
                    
                    self.logger.info(f"Symbol {symbol}: name='{symbol_info.get('name', 'N/A')}', enname='{symbol_info.get('enname', 'N/A')}', final='{symbol_name}'")
                    
                    symbols_list.append(symbol)
                    
                    if len(symbol_name) > 30:
                        symbol_name = symbol_name[:27] + "..."
                    
                    # Добавляем в данные для сравнения
                    comparison_data[f"{symbol} - {symbol_name}"] = normalized_data
            
            # Добавляем данные по инфляции если доступны
            if inflation_data is not None and not inflation_data.empty:
                # Нормализуем инфляцию к базовому значению (1000)
                normalized_inflation = inflation_data / inflation_data.iloc[0] * 1000
                self.logger.info(f"Adding inflation line: {len(normalized_inflation)} points, range: {normalized_inflation.min():.2f} - {normalized_inflation.max():.2f}")
                comparison_data[f"{inflation_ticker} - Inflation"] = normalized_inflation
            else:
                self.logger.warning(f"Inflation data is None or empty: {inflation_data is None}, {inflation_data.empty if inflation_data is not None else 'N/A'}")
            
            # Создаем DataFrame для стандартного метода сравнения
            import pandas as pd
            comparison_df = pd.DataFrame(comparison_data)
            
            # Формируем заголовок
            title_parts = ["Comparison"]
            if symbols_list:
                symbols_str = ", ".join(symbols_list)
                title_parts.append(symbols_str)
            title_parts.append(f"Currency: {currency}")
            title = ", ".join(title_parts)
            
            # Используем стандартный метод создания графика сравнения
            fig, ax = self.chart_styles.create_comparison_chart(
                data=comparison_df,
                symbols=list(comparison_data.keys()),
                currency=currency,
                title=title,
                xlabel='',  # Скрываем подпись оси X
                ylabel=''   # Скрываем подпись оси Y
            )
            
            # Сохраняем график в bytes
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Очищаем matplotlib
            import matplotlib.pyplot as plt
            plt.close(fig)
            
            # Создаем caption
            caption = f"📈 Сравнение: {', '.join(symbols)}\n\n"
            caption += f"💱 Валюта: {currency} ({currency_info})\n"
            caption += f"📊 Инфляция: {inflation_ticker}\n"

            
            # Отправляем график
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_bytes,
                caption=caption
            )
            
            self.logger.info(f"Successfully created hybrid comparison for {len(symbols)} Chinese symbols")
            
        except Exception as e:
            self.logger.error(f"Error creating hybrid Chinese comparison: {e}")
            await self._send_message_safe(update, f"❌ Ошибка при создании гибридного сравнения: {str(e)}")
    
    # =======================
    # Вспомогательные функции для истории
    # =======================






    def _split_text(self, text: str):
        for i in range(0, len(text), self.MAX_TELEGRAM_CHUNK):
            yield text[i:i + self.MAX_TELEGRAM_CHUNK]

    async def send_long_message(self, update: Update, text: str):
        if not text:
            text = "Пустой ответ."
        if hasattr(update, 'message') and update.message is not None:
            for chunk in self._split_text(text):
                await update.message.reply_text(chunk)
    
    def _escape_markdown(self, text: str) -> str:
        """Escape special Markdown characters"""
        if not text:
            return text
        
        # Escape special Markdown characters
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text

    def _format_describe_table(self, asset_list) -> str:
        """Format ok.AssetList.describe() data with adaptive formatting for Telegram"""
        try:
            if not TABULATE_AVAILABLE:
                # Fallback to simple text formatting if tabulate is not available
                return self._format_describe_table_simple(asset_list)
            
            # Get describe data
            describe_data = asset_list.describe()
            
            if describe_data is None or describe_data.empty:
                return "📊 Данные для сравнения недоступны"
            
            # Count columns (assets) to choose best format
            num_assets = len(describe_data.columns)
            
            if num_assets <= 2:
                # For 1-2 assets, use pipe format (most readable)
                markdown_table = tabulate.tabulate(
                    describe_data, 
                    headers='keys', 
                    tablefmt='pipe',
                    floatfmt='.2f'
                )
                return f"📊 **Статистика активов:**\n```\n{markdown_table}\n```"
            
            elif num_assets <= 4:
                # For 3-4 assets, use simple format (compact but readable)
                markdown_table = tabulate.tabulate(
                    describe_data, 
                    headers='keys', 
                    tablefmt='simple',
                    floatfmt='.2f'
                )
                return f"📊 **Статистика активов:**\n```\n{markdown_table}\n```"
            
            else:
                # For 5+ assets, use vertical format (most mobile-friendly)
                return self._format_describe_table_vertical(describe_data)
            
        except Exception as e:
            self.logger.error(f"Error formatting describe table: {e}")
            return "📊 Ошибка при формировании таблицы статистики"
    
    def _format_describe_table_simple(self, asset_list) -> str:
        """Simple text formatting fallback for describe table with adaptive formatting"""
        try:
            describe_data = asset_list.describe()
            
            if describe_data is None or describe_data.empty:
                return "📊 Данные для сравнения недоступны"
            
            # Count columns (assets) to choose best format
            num_assets = len(describe_data.columns)
            
            if num_assets <= 2:
                # For 1-2 assets, use simple table format
                return self._format_simple_table(describe_data)
            elif num_assets <= 4:
                # For 3-4 assets, use compact table format
                return self._format_compact_table(describe_data)
            else:
                # For 5+ assets, use vertical format
                return self._format_describe_table_vertical(describe_data)
            
        except Exception as e:
            self.logger.error(f"Error in simple describe table formatting: {e}")
            return "📊 Ошибка при формировании таблицы статистики"
    
    def _format_simple_table(self, describe_data) -> str:
        """Format as simple markdown table"""
        try:
            result = ["📊 **Статистика активов:**\n"]
            
            # Get column names (asset symbols)
            columns = describe_data.columns.tolist()
            
            # Get row names (metrics)
            rows = describe_data.index.tolist()
            
            # Create simple table
            header = "| Метрика | " + " | ".join([f"`{col}`" for col in columns]) + " |"
            separator = "|" + "|".join([" --- " for _ in range(len(columns) + 1)]) + "|"
            
            result.append(f"```\n{header}\n{separator}")
            
            # Data rows
            for row in rows:
                row_data = [str(row)]
                for col in columns:
                    value = describe_data.loc[row, col]
                    if isinstance(value, (int, float)):
                        if pd.isna(value):
                            row_data.append("N/A")
                        else:
                            row_data.append(f"{value:.2f}")
                    else:
                        row_data.append(str(value))
                
                result.append("| " + " | ".join(row_data) + " |")
            
            result.append("```")
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error in simple table formatting: {e}")
            return "📊 Ошибка при формировании таблицы"
    
    def _format_compact_table(self, describe_data) -> str:
        """Format as compact table"""
        try:
            result = ["📊 **Статистика активов:**\n"]
            
            # Get column names (asset symbols)
            columns = describe_data.columns.tolist()
            
            # Get row names (metrics)
            rows = describe_data.index.tolist()
            
            # Create compact table
            header = "Metric".ljust(20) + " | " + " | ".join([col.ljust(8) for col in columns])
            separator = "-" * len(header)
            
            result.append(f"```\n{header}\n{separator}")
            
            # Data rows
            for row in rows:
                row_str = str(row).ljust(20) + " | "
                values = []
                for col in columns:
                    value = describe_data.loc[row, col]
                    if pd.isna(value):
                        values.append("N/A".ljust(8))
                    elif isinstance(value, (int, float)):
                        values.append(f"{value:.2f}".ljust(8))
                    else:
                        values.append(str(value).ljust(8))
                row_str += " | ".join(values)
                result.append(row_str)
            
            result.append("```")
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error in compact table formatting: {e}")
            return "📊 Ошибка при формировании таблицы"
    
    def _format_describe_table_vertical(self, describe_data) -> str:
        """Format describe data in vertical format for mobile-friendly display"""
        try:
            result = ["📊 **Статистика активов:**\n"]
            
            # Get column names (asset symbols)
            columns = describe_data.columns.tolist()
            
            # Get row names (metrics)
            rows = describe_data.index.tolist()
            
            # Create vertical format - one metric per line
            for row in rows:
                result.append(f"📊 **{row}:**")
                for col in columns:
                    value = describe_data.loc[row, col]
                    if pd.isna(value):
                        result.append(f"  • `{col}`: N/A")
                    elif isinstance(value, (int, float)):
                        result.append(f"  • `{col}`: {value:.2f}")
                    else:
                        result.append(f"  • `{col}`: {value}")
                result.append("")  # Empty line between metrics
            
            return "\n".join(result)
            
        except Exception as e:
            self.logger.error(f"Error in vertical describe table formatting: {e}")
            return "📊 Ошибка при формировании таблицы статистики"

    async def _send_message_safe(self, update: Update, text: str, parse_mode: str = 'Markdown', reply_markup=None):
        """Безопасная отправка сообщения с автоматическим разбиением на части - исправлено для обработки None"""
        try:
            # Проверяем, что update и message не None
            if update is None:
                self.logger.error("Cannot send message: update is None")
                return
            
            if not hasattr(update, 'message') or update.message is None:
                self.logger.error("Cannot send message: update.message is None")
                return
            
            # Проверяем, что text действительно является строкой
            if not isinstance(text, str):
                self.logger.warning(f"_send_message_safe received non-string data: {type(text)}")
                text = str(text)
            
            # Проверяем длину строки
            if len(text) <= 4000:
                self.logger.info(f"Sending message with reply_markup: {reply_markup is not None}")
                if reply_markup:
                    self.logger.info(f"Reply markup type: {type(reply_markup)}")
                    self.logger.info(f"Reply markup content: {reply_markup.to_dict() if hasattr(reply_markup, 'to_dict') else 'No to_dict method'}")
                await update.message.reply_text(text, parse_mode=parse_mode, reply_markup=reply_markup)
            else:
                # Для длинных сообщений с кнопками отправляем первую часть с кнопками
                if reply_markup:
                    first_part = text[:4000]
                    await update.message.reply_text(first_part, parse_mode=parse_mode, reply_markup=reply_markup)
                    # Остальную часть отправляем без кнопок
                    remaining_text = text[4000:]
                    if remaining_text:
                        await self.send_long_message(update, remaining_text)
                else:
                    await self.send_long_message(update, text)
        except Exception as e:
            self.logger.error(f"Error in _send_message_safe: {e}")
            # Fallback: попробуем отправить как обычный текст
            try:
                if hasattr(update, 'message') and update.message is not None:
                    await update.message.reply_text(f"Ошибка форматирования: {str(text)[:1000]}...")
            except Exception as fallback_error:
                self.logger.error(f"Fallback message sending failed: {fallback_error}")
                try:
                    if hasattr(update, 'message') and update.message is not None:
                        await update.message.reply_text("Произошла ошибка при отправке сообщения")
                except Exception as final_error:
                    self.logger.error(f"Final fallback message sending failed: {final_error}")
    
    def _truncate_caption(self, text: Any) -> str:
        """Обрезать подпись до допустимой длины Telegram.
        Гарантирует, что длина не превышает Config.MAX_CAPTION_LENGTH.
        """
        try:
            if text is None:
                return ""
            if not isinstance(text, str):
                text = str(text)
            max_len = getattr(Config, 'MAX_CAPTION_LENGTH', 1024)
            if len(text) <= max_len:
                return text
            ellipsis = "…"
            if max_len > len(ellipsis):
                return text[: max_len - len(ellipsis)] + ellipsis
            return text[:max_len]
        except Exception as e:
            self.logger.error(f"Error truncating caption: {e}")
            safe_text = "" if text is None else str(text)
            return safe_text[:1024]
    
    async def _send_additional_charts(self, update: Update, context: ContextTypes.DEFAULT_TYPE, asset_list, symbols: list, currency: str):
        """Отправить дополнительные графики анализа (drawdowns, dividend yield)"""
        try:
            # Send typing indicator
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Create drawdowns chart
            await self._create_drawdowns_chart(update, context, asset_list, symbols, currency)
            
            # Create dividend yield chart if available
            await self._create_dividend_yield_chart(update, context, asset_list, symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error creating additional charts: {e}")
            await self._send_message_safe(update, f"⚠️ Не удалось создать дополнительные графики: {str(e)}")
    

    
    async def _create_drawdowns_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, asset_list, symbols: list, currency: str):
        """Создать график drawdowns"""
        try:
            # Check if drawdowns data is available
            if not hasattr(asset_list, 'drawdowns') or asset_list.drawdowns.empty:
                await self._send_message_safe(update, "ℹ️ Данные о drawdowns недоступны для выбранных активов")
                return
            
            # Create drawdowns chart using chart_styles
            fig, ax = chart_styles.create_drawdowns_chart(
                asset_list.drawdowns, symbols, currency
            )
            
            # Save chart to bytes with memory optimization
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(fig)
            
            # Send drawdowns chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=io.BytesIO(img_bytes),
                caption=self._truncate_caption(f"📉 График Drawdowns для {len(symbols)} активов\n\nПоказывает периоды падения активов и их восстановление")
            )
            
        except Exception as e:
            self.logger.error(f"Error creating drawdowns chart: {e}")
            await self._send_message_safe(update, f"⚠️ Не удалось создать график drawdowns: {str(e)}")
    
    async def _create_dividend_yield_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, asset_list, symbols: list, currency: str):
        """Создать график dividend yield"""
        try:
            # Check if dividend yield data is available
            if not hasattr(asset_list, 'dividend_yield') or asset_list.dividend_yield.empty:
                await self._send_message_safe(update, "ℹ️ Данные о дивидендной доходности недоступны для выбранных активов")
                return
            
            # Create dividend yield chart using chart_styles
            fig, ax = chart_styles.create_dividend_yield_chart(
                asset_list.dividend_yield, symbols
            )
            
            # Save chart to bytes with memory optimization
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(fig)
            
            # Send dividend yield chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=io.BytesIO(img_bytes),
                caption=self._truncate_caption(f"💰 График дивидендной доходности для {len(symbols)} активов\n\nПоказывает историю дивидендных выплат и доходность")
            )
            
        except Exception as e:
            self.logger.error(f"Error creating dividend yield chart: {e}")
            await self._send_message_safe(update, f"⚠️ Не удалось создать график дивидендной доходности: {str(e)}")
    
    async def _create_correlation_matrix(self, update: Update, context: ContextTypes.DEFAULT_TYPE, asset_list, symbols: list):
        """Создать корреляционную матрицу активов"""
        try:
            self.logger.info(f"Starting correlation matrix creation for symbols: {symbols}")
            
            # Check if assets_ror data is available
            if not hasattr(asset_list, 'assets_ror'):
                self.logger.warning("assets_ror attribute does not exist")
                await self._send_message_safe(update, "ℹ️ Данные о доходности активов недоступны для создания корреляционной матрицы")
                return
                
            if asset_list.assets_ror is None:
                self.logger.warning("assets_ror is None")
                await self._send_message_safe(update, "ℹ️ Данные о доходности активов недоступны для создания корреляционной матрицы")
                return
                
            if asset_list.assets_ror.empty:
                self.logger.warning("assets_ror is empty")
                await self._send_message_safe(update, "ℹ️ Данные о доходности активов недоступны для создания корреляционной матрицы")
                return
            
            # Get correlation matrix
            correlation_matrix = asset_list.assets_ror.corr()
            
            self.logger.info(f"Correlation matrix created successfully, shape: {correlation_matrix.shape}")
            
            if correlation_matrix.empty:
                self.logger.warning("Correlation matrix is empty")
                await self._send_message_safe(update, "ℹ️ Не удалось вычислить корреляционную матрицу")
                return
            
            # Create correlation matrix visualization using chart_styles
            fig, ax = chart_styles.create_correlation_matrix_chart(
                correlation_matrix
            )
            
            # Save chart to bytes with memory optimization
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(fig)
            
            # Send correlation matrix
            self.logger.info("Sending correlation matrix image...")
            await context.bot.send_photo(
                chat_id=update.effective_chat.id, 
                photo=io.BytesIO(img_bytes),
                caption=self._truncate_caption(f"🔗 Корреляционная матрица для {len(symbols)} активов\n\nПоказывает корреляцию между доходностями активов (от -1 до +1)\n\n• +1: полная положительная корреляция\n• 0: отсутствие корреляции\n• -1: полная отрицательная корреляция")
            )
            self.logger.info("Correlation matrix image sent successfully")
            
            plt.close(fig)
            
        except Exception as e:
            self.logger.error(f"Error creating correlation matrix: {e}")
            await self._send_message_safe(update, f"⚠️ Не удалось создать корреляционную матрицу: {str(e)}")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command with full help"""
        user = update.effective_user
        # Escape user input to prevent Markdown parsing issues
        user_name = user.first_name or "User"
        # Remove any special characters that could break Markdown
        user_name = user_name.replace("*", "").replace("_", "").replace("`", "").replace("[", "").replace("]", "")
        
        welcome_message = f"""
• Анализ активов (акции, облигации, товары, индексы, валюты) с графиками цен
• Сравнение нескольких активов с графиками накопленной доходности и учетом инфляции
• Анализ портфеля (веса, риски, доходность, прогнозы)

Основные команды:
/start — эта справка
/info [тикер] [период] — базовая информация об активе с графиком и анализом
/compare [символ1] [символ2] ... — сравнение активов с графиком накопленной доходности
/portfolio [символ1:доля1] [символ2:доля2] ... — создание портфеля с указанными весами
/list [название] — список пространств имен или символы в пространстве
/gemini_status — проверка статуса Gemini API для анализа графиков

Поддерживаемые форматы тикеров:
• US акции: AAPL.US, VOO.US, SPY.US, QQQ.US
• MOEX: SBER.MOEX, GAZP.MOEX, LKOH.MOEX
• Индексы: SPX.INDX, IXIC.INDX, RGBITR.INDX
• Товары: GC.COMM (золото), CL.COMM (нефть), SI.COMM (серебро)
• Валюты: EURUSD.FX, GBPUSD.FX, USDJPY.FX
• LSE: VOD.LSE, HSBA.LSE, BP.LSE

Примеры команд:
• `/compare SPY.US QQQ.US` - сравнить S&P 500 и NASDAQ
• `/compare SBER.MOEX,GAZP.MOEX` - сравнить Сбербанк и Газпром
• `/compare SPY.US, QQQ.US, VOO.US` - сравнить с пробелами после запятых
• `/compare GC.COMM CL.COMM` - сравнить золото и нефть
• `/compare VOO.US,BND.US,GC.COMM` - сравнить акции, облигации и золото

• `/portfolio SPY.US:0.5 QQQ.US:0.3 BND.US:0.2` - портфель 50% S&P 500, 30% NASDAQ, 20% облигации
• `/portfolio SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3` - российский портфель
Базовая валюта опрелеляется по первому символу в списке.

⚠️ Вся информация предоставляется исключительно в информационных целях и не является инвестиционными рекомендациями.

"""

        await self._send_message_safe(update, welcome_message)
    
    async def show_info_help(self, update: Update):
        """Показать справку по команде /info"""
        help_text = """📊 Команда /info - Информация об активе

Используйте команду `/info [тикер] [период]` для получения полной информации об активе.

Примеры:
• `/info AAPL.US` - информация об Apple
• `/info SBER.MOEX` - информация о Сбербанке
• `/info GC.COMM 5Y` - золото за 5 лет
• `/info SPX.INDX 10Y` - S&P 500 за 10 лет

Поддерживаемые периоды:
• 1Y, 2Y, 5Y, 10Y, MAX
• По умолчанию: 10Y для акций, 5Y для макро
"""
        
        await self._send_message_safe(update, help_text)
    
    async def show_namespace_help(self, update: Update):
        """Показать справку по команде /list"""
        help_text = """📚 Команда /list - Пространства имен

Используйте команду `/list` для просмотра всех доступных пространств имен.

• `/list US` - американские акции
• `/list MOEX` - российские акции
• `/list INDX` - мировые индексы
• `/list FX` - валютные пары
• `/list COMM` - товарные активы

"""
        
        await self._send_message_safe(update, help_text)
    
    async def _show_tushare_namespace_symbols(self, update: Update, context: ContextTypes.DEFAULT_TYPE, namespace: str, is_callback: bool = False):
        """Show symbols for Chinese exchanges using Tushare"""
        try:
            if not self.tushare_service:
                error_msg = "❌ Сервис Tushare недоступен"
                if is_callback:
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=error_msg
                    )
                else:
                    await self._send_message_safe(update, error_msg)
                return
            
            # Get symbols from Tushare
            try:
                symbols_data = self.tushare_service.get_exchange_symbols(namespace)
                total_count = self.tushare_service.get_exchange_symbols_count(namespace)
                
                if not symbols_data:
                    error_msg = f"❌ Символы для биржи '{namespace}' не найдены"
                    if is_callback:
                        await context.bot.send_message(
                            chat_id=update.callback_query.message.chat_id,
                            text=error_msg
                        )
                    else:
                        await self._send_message_safe(update, error_msg)
                    return
            except Exception as e:
                error_msg = f"❌ Ошибка при получении символов для '{namespace}': {str(e)}"
                if is_callback:
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=error_msg
                    )
                else:
                    await self._send_message_safe(update, error_msg)
                return
            
            # Format response
            exchange_names = {
                'SSE': 'Shanghai Stock Exchange',
                'SZSE': 'Shenzhen Stock Exchange', 
                'BSE': 'Beijing Stock Exchange',
                'HKEX': 'Hong Kong Stock Exchange'
            }
            
            response = f"📊 Биржа: {exchange_names.get(namespace, namespace)}\n\n"
            response += f"📈 Статистика:\n"
            response += f"• Всего символов: {total_count:,}\n"
            response += f"• Показываю: {len(symbols_data)}\n\n"
            
            # Show first 20 symbols with detailed info using TABULATE
            display_count = min(20, len(symbols_data))
            response += f"📋 Первые {display_count} символов:\n\n"
            
            # Prepare data for tabulate
            table_data = []
            headers = ["Символ", "Название"]
            
            for symbol_info in symbols_data[:display_count]:
                symbol = symbol_info['symbol']
                name = symbol_info['name']
                
                # Escape Markdown characters in company names
                escaped_name = self._escape_markdown(name)
                
                # No truncation for Chinese exchanges - show full names
                table_data.append([f"`{symbol}`", escaped_name])
            
            # Create table using tabulate with simple format to avoid Markdown conflicts
            table = tabulate.tabulate(table_data, headers=headers, tablefmt="simple")
            response += f"```\n{table}\n```\n"
            
            if len(symbols_data) > display_count:
                response += f"... и еще {len(symbols_data) - display_count} символов\n\n"
            
            response += f"💡 Используйте `/info <символ>` для получения подробной информации об активе"
            
            # Create keyboard with Excel export button
            keyboard = [
                [InlineKeyboardButton("📊 Выгрузить в Excel", callback_data=f"excel_namespace_{namespace}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if is_callback:
                await context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=response,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await self._send_message_safe(update, response, reply_markup=reply_markup)
                
        except Exception as e:
            error_msg = f"❌ Ошибка при получении данных для '{namespace}': {str(e)}"
            if is_callback:
                await context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=error_msg
                )
            else:
                await self._send_message_safe(update, error_msg)
    
    async def _show_namespace_symbols(self, update: Update, context: ContextTypes.DEFAULT_TYPE, namespace: str, is_callback: bool = False):
        """Единый метод для показа символов в пространстве имен"""
        try:
            # Check if it's a Chinese exchange
            chinese_exchanges = ['SSE', 'SZSE', 'BSE', 'HKEX']
            if namespace in chinese_exchanges:
                await self._show_tushare_namespace_symbols(update, context, namespace, is_callback)
                return
            
            symbols_df = ok.symbols_in_namespace(namespace)
            
            if symbols_df.empty:
                error_msg = f"❌ Пространство имен '{namespace}' не найдено или пусто"
                if is_callback:
                    # Для callback сообщений отправляем через context.bot
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=error_msg
                    )
                else:
                    await self._send_message_safe(update, error_msg)
                return
            
            # Show statistics first
            total_symbols = len(symbols_df)
            response = f"📊 {namespace}: {total_symbols}\n\n"


            
            # Prepare data for display - show top 30 or all if less than 30
            display_count = min(30, total_symbols)
            response += f"📋 Первые {display_count}:\n\n"
            
            # Prepare data for tabulate
            table_data = []
            headers = ["Символ", "Название"]
            
            for _, row in symbols_df.head(display_count).iterrows():
                symbol = row['symbol'] if pd.notna(row['symbol']) else 'N/A'
                name = row['name'] if pd.notna(row['name']) else 'N/A'
                
                # Escape Markdown characters in company names
                escaped_name = self._escape_markdown(name)
                
                # No truncation - show full names
                table_data.append([f"`{symbol}`", escaped_name])
            
            # Create table using tabulate with simple format to avoid Markdown conflicts
            if table_data:
                table = tabulate.tabulate(table_data, headers=headers, tablefmt="simple")
                response += f"```\n{table}\n```\n"
            
            # Добавляем кнопку для выгрузки Excel
            keyboard = [[
                InlineKeyboardButton(
                    f"📊 Полный список в Excel ({total_symbols})", 
                    callback_data=f"excel_namespace_{namespace}"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем сообщение с таблицей и кнопкой
            if is_callback:
                # Для callback сообщений отправляем через context.bot с кнопками
                await context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=response,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            else:
                await self._send_message_safe(update, response, reply_markup=reply_markup)
            
        except Exception as e:
            error_msg = f"❌ Ошибка при получении данных для '{namespace}': {str(e)}"
            if is_callback:
                # Для callback сообщений отправляем через context.bot
                await context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text=error_msg
                )
            else:
                await self._send_message_safe(update, error_msg)
    




    async def info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /info command - показывает ежедневный график с базовой информацией и AI анализом"""
        if not context.args:
            # Get random examples for user
            examples = self.get_random_examples(3)
            examples_text = ", ".join(examples)
            
            await self._send_message_safe(update, 
                f"📊 Информация об активе\n\n"
                f"Примеры: {examples_text}\n\n"
                f"Просто отправьте название инструмента")
            return
        
        symbol = context.args[0].upper()
        
        # Update user context
        user_id = update.effective_user.id
        self._update_user_context(user_id, 
                                last_assets=[symbol] + self._get_user_context(user_id).get('last_assets', []))
        
        await self._send_message_safe(update, f"📊 Получаю информацию об активе {symbol}...")
        
        try:
            # Get the resolved symbol from asset service
            resolved = self.resolve_symbol_or_isin(symbol)
            if 'error' in resolved:
                await self._send_message_safe(update, f"❌ Ошибка: {resolved['error']}")
                return
            
            resolved_symbol = resolved['symbol']
            
            # Determine data source
            data_source = self.determine_data_source(resolved_symbol)
            
            if data_source == 'tushare':
                # Use Tushare service for Chinese exchanges
                await self._handle_tushare_info(update, resolved_symbol)
            else:
                # Use Okama for other exchanges
                await self._handle_okama_info(update, resolved_symbol)
                
        except Exception as e:
            self.logger.error(f"Error in info command for {symbol}: {e}")
            await self._send_message_safe(update, f"❌ Ошибка: {str(e)}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages - treat as asset symbol for /info or portfolio for /portfolio"""
        if not update.message or not update.message.text:
            return
        
        text = update.message.text.strip()
        if not text:
            return
        
        user_id = update.effective_user.id
        user_context = self._get_user_context(user_id)
        
        # Debug: Log user context state
        self.logger.info(f"User {user_id} context: {user_context}")
        self.logger.info(f"Waiting for portfolio: {user_context.get('waiting_for_portfolio', False)}")
        self.logger.info(f"Input text: {text}")
        
        # Check if user is waiting for portfolio input
        if user_context.get('waiting_for_portfolio', False):
            self.logger.info(f"Processing as portfolio input: {text}")
            # Process as portfolio input
            await self._handle_portfolio_input(update, context, text)
            return
        
        # Check if user is waiting for compare input
        if user_context.get('waiting_for_compare', False):
            self.logger.info(f"Processing as compare input: {text}")
            # Process as compare input
            await self._handle_compare_input(update, context, text)
            return
        
        # Check if text contains multiple symbols (space or comma separated)
        # This allows users to send "SPY.US QQQ.US" directly as a comparison request
        symbols = []
        if ',' in text:
            # Handle comma-separated symbols
            for symbol_part in text.split(','):
                symbol_part = symbol_part.strip()
                if symbol_part:
                    if any(portfolio_indicator in symbol_part.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                        symbols.append(symbol_part)
                    else:
                        symbols.append(symbol_part.upper())
        elif ' ' in text:
            # Handle space-separated symbols
            for symbol in text.split():
                symbol = symbol.strip()
                if symbol:
                    if any(portfolio_indicator in symbol.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                        symbols.append(symbol)
                    else:
                        symbols.append(symbol.upper())
        
        # If we detected multiple symbols, treat as comparison request
        if len(symbols) >= 2:
            self.logger.info(f"Detected multiple symbols in message: {symbols}")
            # Process as compare input
            await self._handle_compare_input(update, context, text)
            return
        
        # Treat text as single asset symbol and process with /info logic
        symbol = text.upper()
        
        # Update user context
        self._update_user_context(user_id, 
                                last_assets=[symbol] + user_context.get('last_assets', []))
        
        await self._send_message_safe(update, f"📊 Получаю информацию об активе {symbol}...")
        
        try:
            # Get the resolved symbol from asset service
            resolved = self.resolve_symbol_or_isin(symbol)
            if 'error' in resolved:
                await self._send_message_safe(update, f"❌ Ошибка: {resolved['error']}")
                return
            
            resolved_symbol = resolved['symbol']
            
            # Determine data source
            data_source = self.determine_data_source(resolved_symbol)
            
            if data_source == 'tushare':
                # Use Tushare service for Chinese exchanges
                await self._handle_tushare_info(update, resolved_symbol)
            else:
                # Use Okama for other exchanges
                await self._handle_okama_info(update, resolved_symbol)
                
        except Exception as e:
            self.logger.error(f"Error in handle_message for {symbol}: {e}")
            await self._send_message_safe(update, f"❌ Ошибка: {str(e)}")

    async def _handle_okama_info(self, update: Update, symbol: str):
        """Handle info display for Okama assets"""
        try:
            # Получаем сырой вывод объекта ok.Asset
            try:
                asset = ok.Asset(symbol)
                info_text = f"{asset}"
            except Exception as e:
                info_text = f"Ошибка при получении информации об активе: {str(e)}"
            
            # Создаем кнопки для дополнительных функций
            keyboard = [
                [
                    InlineKeyboardButton("1Y", callback_data=f"daily_chart_{symbol}"),
                    InlineKeyboardButton("5Y", callback_data=f"monthly_chart_{symbol}"),
                    InlineKeyboardButton("All", callback_data=f"all_chart_{symbol}")
                ],
                [
                    InlineKeyboardButton("💵 Dividends", callback_data=f"dividends_{symbol}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем информацию с кнопками
            await self._send_message_safe(update, info_text, reply_markup=reply_markup)
            
        except Exception as e:
            self.logger.error(f"Error in _handle_okama_info for {symbol}: {e}")
            await self._send_message_safe(update, f"❌ Ошибка: {str(e)}")

    async def _handle_tushare_info(self, update: Update, symbol: str):
        """Handle info display for Tushare assets"""
        try:
            if not self.tushare_service:
                await self._send_message_safe(update, "❌ Сервис Tushare недоступен")
                return
            
            # Get symbol information from Tushare
            symbol_info = self.tushare_service.get_symbol_info(symbol)
            
            if 'error' in symbol_info:
                await self._send_message_safe(update, f"❌ Ошибка: {symbol_info['error']}")
                return
            
            # Format information
            info_text = f"📊 {symbol_info.get('name', 'N/A')} ({symbol})\n\n"
            info_text += f"🏢 Биржа: {symbol_info.get('exchange', 'N/A')}\n"
            info_text += f"🏭 Отрасль: {symbol_info.get('industry', 'N/A')}\n"
            info_text += f"📍 Регион: {symbol_info.get('area', 'N/A')}\n"
            info_text += f"📅 Дата листинга: {symbol_info.get('list_date', 'N/A')}\n"
            
            if 'current_price' in symbol_info:
                info_text += f"\n💰 Текущая цена: {symbol_info['current_price']:.2f}\n"
                if 'change' in symbol_info:
                    change_sign = "+" if symbol_info['change'] >= 0 else ""
                    info_text += f"📈 Изменение: {change_sign}{symbol_info['change']:.2f} ({symbol_info.get('pct_chg', 0):.2f}%)\n"
                if 'volume' in symbol_info:
                    info_text += f"📊 Объем: {symbol_info['volume']:,.0f}\n"
            
            # Создаем кнопки для дополнительных функций
            keyboard = [
                [
                    InlineKeyboardButton("📈 1Y", callback_data=f"tushare_daily_chart_{symbol}"),
                    InlineKeyboardButton("📅 5Y", callback_data=f"tushare_monthly_chart_{symbol}"),
                    InlineKeyboardButton("📊 All", callback_data=f"tushare_all_chart_{symbol}")
                ],
                [
                    InlineKeyboardButton("💵 Дивиденды", callback_data=f"tushare_dividends_{symbol}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Отправляем информацию с кнопками
            await self._send_message_safe(update, info_text, reply_markup=reply_markup)
            
        except Exception as e:
            self.logger.error(f"Error in _handle_tushare_info for {symbol}: {e}")
            await self._send_message_safe(update, f"❌ Ошибка: {str(e)}")

    async def _get_daily_chart(self, symbol: str) -> Optional[bytes]:
        """Получить ежедневный график за последний год используя ChartStyles"""
        try:
            import io
            
            def create_daily_chart():
                # Устанавливаем backend для headless режима
                import matplotlib
                matplotlib.use('Agg')
                
                asset = ok.Asset(symbol)
                
                # Получаем данные за последний год
                daily_data = asset.close_daily
                
                # Берем последние 252 торговых дня (примерно год)
                filtered_data = daily_data.tail(252)
                
                # Получаем информацию об активе для заголовка
                asset_name = getattr(asset, 'name', symbol)
                currency = getattr(asset, 'currency', '')
                
                # Используем ChartStyles для создания графика
                fig, ax = chart_styles.create_price_chart(
                    data=filtered_data,
                    symbol=symbol,
                    currency=currency,
                    period='1Y'
                )
                
                # Обновляем заголовок с нужным форматом
                title = f"{symbol} | {asset_name} | {currency} | 1Y"
                ax.set_title(title, **chart_styles.title)
                
                # Убираем подписи осей
                ax.set_xlabel('')
                ax.set_ylabel('')
                
                # Сохраняем в bytes
                output = io.BytesIO()
                chart_styles.save_figure(fig, output)
                output.seek(0)
                
                # Очистка
                chart_styles.cleanup_figure(fig)
                
                return output.getvalue()
            
            # Выполняем с таймаутом
            chart_data = await asyncio.wait_for(
                asyncio.to_thread(create_daily_chart),
                timeout=30.0
            )
            
            return chart_data
            
        except Exception as e:
            self.logger.error(f"Error getting daily chart for {symbol}: {e}")
            return None








    async def namespace_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list command"""
        try:
            
            if not context.args:
                # Show available namespaces
                namespaces = ok.namespaces
                
                # Prepare data for tabulate
                headers = ["Код", "Описание", "Категория"]
                namespace_data = []
                
                # Categorize namespaces for better organization
                categories = {
                    'Биржи': ['MOEX', 'US', 'LSE', 'XAMS', 'XETR', 'XFRA', 'XSTU', 'XTAE', 'SSE', 'SZSE', 'BSE', 'HKEX'],
                    'Индексы': ['INDX'],
                    'Валюты': ['FX', 'CBR'],
                    'Товары': ['COMM'],
                    'Криптовалюты': ['CC'],
                    'Инфляция': ['INFL'],
                    'Недвижимость': ['RE'],
                    'Портфели': ['PF', 'PIF'],
                    'Депозиты': ['RATE'],
                    'Коэффициенты': ['RATIO']
                }
                
                # Create categorized data
                for namespace, description in namespaces.items():
                    category = "Другое"
                    for cat_name, cat_namespaces in categories.items():
                        if namespace in cat_namespaces:
                            category = cat_name
                            break
                    
                    namespace_data.append([namespace, description, category])
                
                # Add Chinese exchanges manually (not in ok.namespaces)
                chinese_exchanges = {
                    'SSE': 'Shanghai Stock Exchange',
                    'SZSE': 'Shenzhen Stock Exchange', 
                    'BSE': 'Beijing Stock Exchange',
                    'HKEX': 'Hong Kong Stock Exchange'
                }
                
                for exchange_code, exchange_name in chinese_exchanges.items():
                    namespace_data.append([exchange_code, exchange_name, 'Биржи'])
                
                # Sort by category and then by namespace
                namespace_data.sort(key=lambda x: (x[2], x[0]))
                response = "📚 Доступные пространства имен (namespaces): {len(namespaces)}\n\n"
                
                # Create table using tabulate or fallback to simple format
                if TABULATE_AVAILABLE:
                    # Use plain format for best Telegram display
                    table = tabulate.tabulate(namespace_data, headers=headers, tablefmt="plain")
                    response += f"```\n{table}\n```\n\n"
                else:
                    # Fallback to simple text format
                    response += "Код | Описание | Категория\n"
                    response += "--- | --- | ---\n"
                    for row in namespace_data:
                        response += f"`{row[0]}` | {row[1]} | {row[2]}\n"
                    response += "\n"
                
                response += "💡 Используйте `/list <код>` для просмотра символов в конкретном пространстве"
                
                # Создаем кнопки для основных пространств имен
                keyboard = []
                
                # Основные биржи
                keyboard.append([
                    InlineKeyboardButton("🇺🇸 US", callback_data="namespace_US"),
                    InlineKeyboardButton("🇷🇺 MOEX", callback_data="namespace_MOEX"),
                    InlineKeyboardButton("🇬🇧 LSE", callback_data="namespace_LSE")
                ])
                
                # Европейские биржи
                keyboard.append([
                    InlineKeyboardButton("🇩🇪 XETR", callback_data="namespace_XETR"),
                    InlineKeyboardButton("🇫🇷 XFRA", callback_data="namespace_XFRA"),
                    InlineKeyboardButton("🇳🇱 XAMS", callback_data="namespace_XAMS")
                ])
                
                # Китайские биржи
                keyboard.append([
                    InlineKeyboardButton("🇨🇳 SSE", callback_data="namespace_SSE"),
                    InlineKeyboardButton("🇨🇳 SZSE", callback_data="namespace_SZSE"),
                    InlineKeyboardButton("🇨🇳 BSE", callback_data="namespace_BSE")
                ])
                
                keyboard.append([
                    InlineKeyboardButton("🇭🇰 HKEX", callback_data="namespace_HKEX")
                ])
                
                # Индексы и валюты
                keyboard.append([
                    InlineKeyboardButton("📊 INDX", callback_data="namespace_INDX"),
                    InlineKeyboardButton("💱 FX", callback_data="namespace_FX"),
                    InlineKeyboardButton("🏦 CBR", callback_data="namespace_CBR")
                ])
                
                # Товары и криптовалюты
                keyboard.append([
                    InlineKeyboardButton("🛢️ COMM", callback_data="namespace_COMM"),
                    InlineKeyboardButton("₿ CC", callback_data="namespace_CC"),
                    InlineKeyboardButton("🏠 RE", callback_data="namespace_RE")
                ])
                
                # Инфляция и депозиты
                keyboard.append([
                    InlineKeyboardButton("📈 INFL", callback_data="namespace_INFL"),
                    InlineKeyboardButton("💰 PIF", callback_data="namespace_PIF"),
                    InlineKeyboardButton("🏦 RATE", callback_data="namespace_RATE")
                ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await self._send_message_safe(update, response, reply_markup=reply_markup)
                
            else:
                # Show symbols in specific namespace
                namespace = context.args[0].upper()
                
                # Use the unified method that handles both okama and tushare
                await self._show_namespace_symbols(update, context, namespace, is_callback=False)
                    
        except ImportError:
            await self._send_message_safe(update, "❌ Библиотека okama не установлена")
        except Exception as e:
            self.logger.error(f"Error in namespace command: {e}")
            await self._send_message_safe(update, f"❌ Ошибка: {str(e)}")

    async def gemini_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /gemini_status command - check Gemini API status"""
        try:
            if not self.gemini_service:
                await self._send_message_safe(update, "❌ Gemini сервис не инициализирован")
                return
            
            status = self.gemini_service.get_service_status()
            
            status_text = "🤖 **Статус Gemini API**\n\n"
            
            # Service availability
            if status['available']:
                status_text += "✅ **Сервис доступен**\n"
            else:
                status_text += "❌ **Сервис недоступен**\n"
            
            # Library installation
            if status['library_installed']:
                status_text += "✅ **Библиотека установлена**\n"
            else:
                status_text += "❌ **Библиотека не установлена**\n"
            
            # API Key
            status_text += "\n🔑 **Настройки API ключа:**\n"
            
            if status['api_key_set']:
                status_text += f"✅ **API ключ установлен**\n"
                status_text += f"📏 Длина ключа: {status['api_key_length']} символов\n"
            else:
                status_text += "❌ **API ключ не установлен**\n"
            
            # Recommendations
            status_text += "\n💡 **Рекомендации:**\n"
            if not status['available']:
                if not status['library_installed']:
                    status_text += "• Установите библиотеку: `pip install requests`\n"
                if not status['api_key_set']:
                    status_text += "• Установите переменную окружения `GEMINI_API_KEY`\n"
                    status_text += "• Получите API ключ: https://aistudio.google.com/app/apikey\n"
            else:
                status_text += "• Сервис готов к работе! Используйте команду `/compare` для анализа графиков\n"
            
            await self._send_message_safe(update, status_text)
            
        except Exception as e:
            self.logger.error(f"Error in gemini_status command: {e}")
            await self._send_message_safe(update, f"❌ Ошибка при проверке статуса: {str(e)}")

    async def compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /compare command for comparing multiple assets"""
        try:
            if not context.args:
                # Get user's saved portfolios for help message
                user_id = update.effective_user.id
                user_context = self._get_user_context(user_id)
                saved_portfolios = user_context.get('saved_portfolios', {})
                
                # Get random examples for user
                examples = self.get_random_examples(3)
                examples_text = ", ".join(examples)
                
                help_text = "📊 Сравнение\n\n"
                help_text += f"Примеры активов: {examples_text}\n\n"

                # Add saved portfolios information
                if saved_portfolios:
                    help_text += "💾 Ваши сохраненные портфели:\n"
                    for portfolio_symbol, portfolio_info in saved_portfolios.items():
                        symbols = portfolio_info.get('symbols', [])
                        weights = portfolio_info.get('weights', [])
                        
                        # Create formatted portfolio string with symbols and weights
                        if symbols and weights and len(symbols) == len(weights):
                            portfolio_parts = []
                            for i, (symbol, weight) in enumerate(zip(symbols, weights)):
                                portfolio_parts.append(f"{symbol}:{weight:.1%}")
                            portfolio_str = ' '.join(portfolio_parts)
                        else:
                            portfolio_str = ', '.join(symbols)
                        
                        help_text += f"• {portfolio_symbol} ({portfolio_str})\n"
                    
                help_text += "\n\nПримеры:\n"
                help_text += "• `SPY.US QQQ.US` - сравнение символов с символами\n"
                help_text += "• `00001.HK 00005.HK` - сравнение гонконгских акций (гибридный подход)\n"
                help_text += "• `600000.SH 000001.SZ` - сравнение китайских акций (гибридный подход)\n"
                help_text += "• `portfolio_5642.PF portfolio_5642.PF` - сравнение двух портефелей\n"
                help_text += "• `portfolio_5642.PF MCFTR.INDX RGBITR.INDX` - смешанное сравнение\n\n"                                    
                help_text += "📋 Для просмотра всех портфелей используйте команду `/my`\n\n"
                help_text += "💡 Первый актив в списке определяет базовую валюту, если не определено→USD\n\n"
                help_text += "💬 Введите символы для сравнения:"
                
                await self._send_message_safe(update, help_text)
                
                # Set waiting flag for compare input
                self._update_user_context(user_id, waiting_for_compare=True)
                return

            # Extract symbols from command arguments
            # Support multiple formats: space-separated, comma-separated, and comma+space
            raw_args = ' '.join(context.args)  # Join all arguments into one string
            
            # Enhanced parsing logic for multiple formats
            if ',' in raw_args:
                # Handle comma-separated symbols (with or without spaces)
                # Split by comma and clean each symbol
                symbols = []
                for symbol_part in raw_args.split(','):
                    # Handle cases like "SPY.US, QQQ.US" (comma + space)
                    symbol_part = symbol_part.strip()
                    if symbol_part:  # Only add non-empty symbols
                        # Preserve original case for portfolio symbols, uppercase for regular assets
                        if any(portfolio_indicator in symbol_part.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                            symbols.append(symbol_part)  # Keep original case for portfolios
                        else:
                            symbols.append(symbol_part.upper())  # Uppercase for regular assets
                self.logger.info(f"Parsed comma-separated symbols: {symbols}")
            else:
                # Handle space-separated symbols (original behavior)
                symbols = []
                for arg in context.args:
                    # Check if argument contains multiple symbols separated by spaces
                    if ' ' in arg and not any(portfolio_indicator in arg.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                        # Split by spaces for regular assets
                        for symbol in arg.split():
                            symbol = symbol.strip()
                            if symbol:
                                symbols.append(symbol.upper())
                    else:
                        # Single symbol or portfolio
                        symbol = arg.strip()
                        if symbol:
                            # Preserve original case for portfolio symbols, uppercase for regular assets
                            if any(portfolio_indicator in symbol.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                                symbols.append(symbol)  # Keep original case for portfolios
                            else:
                                symbols.append(symbol.upper())  # Uppercase for regular assets
                self.logger.info(f"Parsed space-separated symbols: {symbols}")
            
            # Clean up symbols (remove empty strings and whitespace)
            symbols = [symbol for symbol in symbols if symbol.strip()]
            
            if len(symbols) < 2:
                await self._send_message_safe(update, "❌ Необходимо указать минимум 2 символа для сравнения")
                return
            
            if len(symbols) > 10:
                await self._send_message_safe(update, "❌ Максимум 10 символов для сравнения")
                return

            # Process portfolio symbols and expand them
            user_id = update.effective_user.id
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            # Log saved portfolios for debugging
            self.logger.info(f"User {user_id} has {len(saved_portfolios)} saved portfolios: {list(saved_portfolios.keys())}")
            
            expanded_symbols = []
            portfolio_descriptions = []
            portfolio_contexts = []  # Store portfolio context for buttons
            
            for symbol in symbols:
                # Log symbol being processed for debugging
                self.logger.info(f"Processing symbol: '{symbol}'")
                
                # Check if this is a saved portfolio symbol (various formats)
                # First check exact match, then check case-insensitive match
                is_portfolio = symbol in saved_portfolios
                
                # Additional check: avoid treating asset symbols as portfolios
                # If the symbol looks like an asset symbol (contains .), 
                # and there's no explicit portfolio indicator, treat it as asset
                if is_portfolio and ('.' in symbol and 
                    not any(indicator in symbol.upper() for indicator in ['PORTFOLIO_', 'PF_', '.PF', '.pf'])):
                    # This looks like an asset symbol, not a portfolio
                    is_portfolio = False
                
                if not is_portfolio:
                    # Check case-insensitive match for portfolio symbols
                    # But only for symbols that look like portfolio names (not asset symbols)
                    for portfolio_key in saved_portfolios.keys():
                        if (symbol.lower() == portfolio_key.lower() or
                            symbol.upper() == portfolio_key.upper()):
                            # Additional check: avoid treating asset symbols as portfolios
                            if ('.' in symbol and 
                                not any(indicator in symbol.upper() for indicator in ['PORTFOLIO_', 'PF_', '.PF', '.pf'])):
                                # This looks like an asset symbol, not a portfolio
                                is_portfolio = False
                                break
                            else:
                                # Use the exact key from saved_portfolios
                                symbol = portfolio_key
                                is_portfolio = True
                                break
                
                self.logger.info(f"Symbol '{symbol}' is_portfolio: {is_portfolio}, in saved_portfolios: {symbol in saved_portfolios}")
                
                if is_portfolio:
                    # This is a saved portfolio, expand it
                    portfolio_info = saved_portfolios[symbol]
                    
                    # Ensure we have the correct portfolio symbol from context
                    portfolio_symbol = portfolio_info.get('portfolio_symbol', symbol)
                    portfolio_symbols = portfolio_info['symbols']
                    portfolio_weights = portfolio_info['weights']
                    portfolio_currency = portfolio_info['currency']
                    
                    # Validate portfolio data
                    if not portfolio_symbols or not portfolio_weights:
                        self.logger.error(f"Invalid portfolio data for {symbol}: missing symbols or weights")
                        await self._send_message_safe(update, f"❌ Ошибка: неполные данные портфеля {symbol}")
                        return
                    
                    if len(portfolio_symbols) != len(portfolio_weights):
                        self.logger.error(f"Portfolio {symbol} has mismatched symbols and weights")
                        await self._send_message_safe(update, f"❌ Ошибка: несоответствие символов и весов в портфеле {symbol}")
                        return
                    
                    # Create portfolio using okama
                    try:
                        portfolio = ok.Portfolio(portfolio_symbols, weights=portfolio_weights, ccy=portfolio_currency)
                        
                        # Add portfolio wealth index to expanded symbols
                        expanded_symbols.append(portfolio.wealth_index)
                        
                        # Use the original symbol for description to maintain consistency
                        portfolio_descriptions.append(f"{symbol} ({', '.join(portfolio_symbols)})")
                        
                        # Store portfolio context for buttons - use descriptive name for display
                        portfolio_contexts.append({
                            'symbol': f"{symbol} ({', '.join(portfolio_symbols)})",  # Descriptive name with asset composition
                            'portfolio_symbols': portfolio_symbols,
                            'portfolio_weights': portfolio_weights,
                            'portfolio_currency': portfolio_currency,
                            'portfolio_object': portfolio
                        })
                        
                        self.logger.info(f"Expanded portfolio {symbol} with {len(portfolio_symbols)} assets")
                        self.logger.info(f"Portfolio currency: {portfolio_currency}, weights: {portfolio_weights}")
                        self.logger.info(f"DEBUG: Added portfolio description: '{symbol} ({', '.join(portfolio_symbols)})'")
                        
                    except Exception as e:
                        self.logger.error(f"Error expanding portfolio {symbol}: {e}")
                        await self._send_message_safe(update, f"❌ Ошибка при обработке портфеля {symbol}: {str(e)}")
                        return
                else:
                    # Regular asset symbol
                    expanded_symbols.append(symbol)
                    portfolio_descriptions.append(symbol)
                    portfolio_contexts.append({
                        'symbol': symbol,
                        'portfolio_symbols': [symbol],
                        'portfolio_weights': [1.0],
                        'portfolio_currency': None,  # Will be determined later
                        'portfolio_object': None
                    })
            
            # Update symbols list with expanded portfolio descriptions
            symbols = portfolio_descriptions
            
            # Debug logging for symbols and expanded_symbols
            self.logger.info(f"DEBUG: portfolio_descriptions: {portfolio_descriptions}")
            self.logger.info(f"DEBUG: symbols after update: {symbols}")
            self.logger.info(f"DEBUG: expanded_symbols types: {[type(s) for s in expanded_symbols]}")
            self.logger.info(f"DEBUG: expanded_symbols values: {expanded_symbols}")
            
            # Additional debug: check for any problematic symbols
            for i, desc in enumerate(portfolio_descriptions):
                self.logger.info(f"DEBUG: portfolio_descriptions[{i}]: '{desc}'")
            for i, exp_sym in enumerate(expanded_symbols):
                self.logger.info(f"DEBUG: expanded_symbols[{i}]: '{exp_sym}' (type: {type(exp_sym)})")
            
            await self._send_message_safe(update, f"🔄 Сравниваю активы: {', '.join(symbols)}...")

            # Create comparison using okama
            
            # Determine base currency from the first asset
            first_symbol = symbols[0]
            currency_info = ""
            try:
                # Extract the original symbol from the description (remove the asset list part)
                original_first_symbol = first_symbol.split(' (')[0] if ' (' in first_symbol else first_symbol
                
                # Check if first symbol is a portfolio symbol
                is_first_portfolio = original_first_symbol in saved_portfolios
                
                if not is_first_portfolio:
                    # Check case-insensitive match for portfolio symbols
                    for portfolio_key in saved_portfolios.keys():
                        if (original_first_symbol.lower() == portfolio_key.lower() or
                            original_first_symbol.upper() == portfolio_key.upper()):
                            original_first_symbol = portfolio_key
                            is_first_portfolio = True
                            break
                
                if is_first_portfolio:
                    # First symbol is a portfolio, use its currency
                    portfolio_info = saved_portfolios[original_first_symbol]
                    currency = portfolio_info.get('currency', 'USD')
                    currency_info = f"автоматически определена по портфелю ({original_first_symbol})"
                    self.logger.info(f"Using portfolio currency for {original_first_symbol}: {currency}")
                else:
                    # Use our new currency detection function
                    currency, currency_info = self._get_currency_by_symbol(first_symbol)
                    
                    self.logger.info(f"Auto-detected currency for {first_symbol}: {currency}")
                
            except Exception as e:
                self.logger.warning(f"Could not auto-detect currency, using USD: {e}")
                currency = "USD"
                currency_info = "по умолчанию (USD)"
            
            try:
                # Check if we have portfolios in the comparison
                has_portfolios = any(isinstance(symbol, (pd.Series, pd.DataFrame)) for symbol in expanded_symbols)
                
                if has_portfolios:
                    # We have portfolios, need to create proper comparison using ok.AssetList
                    self.logger.info("Creating comparison with portfolios using ok.AssetList")
                    
                    # Prepare assets list for ok.AssetList
                    assets_for_comparison = []
                    
                    for i, symbol in enumerate(expanded_symbols):
                        if isinstance(symbol, (pd.Series, pd.DataFrame)):
                            # This is a portfolio wealth index - we need to create portfolio object
                            portfolio_context = portfolio_contexts[i] if i < len(portfolio_contexts) else None
                            
                            if portfolio_context:
                                try:
                                    # Create portfolio object using okama
                                    portfolio = ok.Portfolio(
                                        portfolio_context['portfolio_symbols'], 
                                        weights=portfolio_context['portfolio_weights'], 
                                        ccy=portfolio_context['portfolio_currency']
                                    )
                                    assets_for_comparison.append(portfolio)
                                    self.logger.info(f"Added portfolio {portfolio_context['symbol']} to comparison")
                                except Exception as portfolio_error:
                                    self.logger.error(f"Error creating portfolio {portfolio_context['symbol']}: {portfolio_error}")
                                    await self._send_message_safe(update, f"❌ Ошибка при создании портфеля {portfolio_context['symbol']}: {str(portfolio_error)}")
                                    return
                            else:
                                self.logger.warning(f"No portfolio context found for index {i}, using generic portfolio")
                                # Create a generic portfolio if context is missing
                                try:
                                    # Extract symbols from the description
                                    desc = symbols[i]
                                    if ' (' in desc:
                                        portfolio_symbols = desc.split(' (')[1].rstrip(')').split(', ')
                                        portfolio_weights = [1.0/len(portfolio_symbols)] * len(portfolio_symbols)
                                        portfolio = ok.Portfolio(portfolio_symbols, weights=portfolio_weights, ccy=currency)
                                        assets_for_comparison.append(portfolio)
                                        self.logger.info(f"Added generic portfolio to comparison")
                                    else:
                                        self.logger.error(f"Could not extract portfolio symbols from description: {desc}")
                                        await self._send_message_safe(update, f"❌ Ошибка при обработке портфеля: {desc}")
                                        return
                                except Exception as e:
                                    self.logger.error(f"Error creating generic portfolio: {e}")
                                    await self._send_message_safe(update, f"❌ Ошибка при создании портфеля: {str(e)}")
                                    return
                        else:
                            # Regular asset symbol
                            assets_for_comparison.append(symbol)
                            self.logger.info(f"Added asset {symbol} to comparison")
                    
                    # Determine currency from first asset or portfolio
                    if assets_for_comparison:
                        first_asset = assets_for_comparison[0]
                        if hasattr(first_asset, 'currency'):
                            currency = first_asset.currency
                            currency_info = f"автоматически определена по первому активу/портфелю"
                        else:
                            # Try to determine from symbol
                            if '.' in str(first_asset):
                                namespace = str(first_asset).split('.')[1]
                                if namespace == 'MOEX':
                                    currency = "RUB"
                                    currency_info = f"автоматически определена по первому активу ({first_asset})"
                                elif namespace == 'US':
                                    currency = "USD"
                                    currency_info = f"автоматически определена по первому активу ({first_asset})"
                                elif namespace == 'LSE':
                                    currency = "GBP"
                                    currency_info = f"автоматически определена по первому активу ({first_asset})"
                                else:
                                    currency = "USD"
                                    currency_info = "по умолчанию (USD)"
                            else:
                                currency = "USD"
                                currency_info = "по умолчанию (USD)"
                    
                    # Check if we have Chinese symbols that need special handling
                    chinese_symbols = []
                    okama_symbols = []
                    
                    for symbol in symbols:
                        if self._is_chinese_symbol(symbol):
                            chinese_symbols.append(symbol)
                        else:
                            okama_symbols.append(symbol)
                    
                    # If we have Chinese symbols, use hybrid approach
                    if chinese_symbols:
                        self.logger.info(f"Found Chinese symbols: {chinese_symbols}")
                        
                        # Check if we have only Chinese symbols (pure Chinese comparison)
                        if len(chinese_symbols) == len(symbols):
                            # Pure Chinese comparison - use hybrid approach
                            await self._create_hybrid_chinese_comparison(update, context, chinese_symbols)
                            return
                        else:
                            # Mixed comparison - show message
                            await self._send_message_safe(update, 
                                f"⚠️ Смешанное сравнение (китайские + прочие символы) пока не поддерживается.\n"
                                f"Для сравнения только китайских символов используйте: /compare {' '.join(chinese_symbols)}\n\n"
                                f"Поддерживаемые символы для сравнения: {', '.join(okama_symbols) if okama_symbols else 'нет'}")
                            return
                    
                    # No Chinese symbols - use standard okama approach
                    self.logger.info(f"No Chinese symbols found, using standard okama comparison for: {symbols}")
                    
                    # Create comparison using ok.AssetList (proper way to compare portfolios with assets)
                    try:
                        self.logger.info(f"Creating AssetList with {len(assets_for_comparison)} assets/portfolios")
                        # Add inflation support for Chinese symbols
                        inflation_ticker = self._get_inflation_ticker_by_currency(currency)
                        comparison = ok.AssetList(assets_for_comparison, ccy=currency, inflation=True)
                        self.logger.info(f"Successfully created AssetList comparison with inflation ({inflation_ticker})")
                    except Exception as asset_list_error:
                        self.logger.error(f"Error creating AssetList: {asset_list_error}")
                        await self._send_message_safe(update, f"❌ Ошибка при создании сравнения: {str(asset_list_error)}")
                        return
                    
                else:
                    # Regular comparison without portfolios
                    self.logger.info("Creating regular comparison without portfolios")
                    
                    # Check if we have Chinese symbols that need special handling
                    chinese_symbols = []
                    okama_symbols = []
                    
                    for symbol in symbols:
                        if self._is_chinese_symbol(symbol):
                            chinese_symbols.append(symbol)
                        else:
                            okama_symbols.append(symbol)
                    
                    # If we have Chinese symbols, use hybrid approach
                    if chinese_symbols:
                        self.logger.info(f"Found Chinese symbols: {chinese_symbols}")
                        
                        # Check if we have only Chinese symbols (pure Chinese comparison)
                        if len(chinese_symbols) == len(symbols):
                            # Pure Chinese comparison - use hybrid approach
                            await self._create_hybrid_chinese_comparison(update, context, chinese_symbols)
                            return
                        else:
                            # Mixed comparison - show message
                            await self._send_message_safe(update, 
                                f"⚠️ Обнаружены китайские символы: {', '.join(chinese_symbols)}\n\n"
                                f"Смешанное сравнение (китайские + обычные символы) пока не поддерживается.\n"
                                f"Для сравнения только китайских символов используйте: /compare {' '.join(chinese_symbols)}\n\n"
                                f"Поддерживаемые символы для сравнения: {', '.join(okama_symbols) if okama_symbols else 'нет'}")
                            return
                    
                    # No Chinese symbols - use standard okama approach
                    self.logger.info(f"No Chinese symbols found, using standard okama comparison for: {symbols}")
                    
                    # Add inflation support for non-Chinese symbols
                    inflation_ticker = self._get_inflation_ticker_by_currency(currency)
                    comparison = ok.AssetList(symbols, ccy=currency, inflation=True)
                    self.logger.info(f"Successfully created regular comparison with inflation ({inflation_ticker})")
                
                # Store context for buttons - use clean portfolio symbols for current_symbols
                clean_symbols = []
                display_symbols = []
                for i, symbol in enumerate(symbols):
                    if isinstance(expanded_symbols[i], (pd.Series, pd.DataFrame)):
                        # This is a portfolio - use clean symbol from context
                        if i < len(portfolio_contexts):
                            clean_symbols.append(portfolio_contexts[i]['symbol'].split(' (')[0])  # Extract clean symbol
                            display_symbols.append(portfolio_contexts[i]['symbol'])  # Keep descriptive name
                        else:
                            clean_symbols.append(symbol)
                            display_symbols.append(symbol)
                    else:
                        # This is a regular asset - use original symbol from portfolio_descriptions
                        clean_symbols.append(symbol)
                        display_symbols.append(symbol)
                
                user_context['current_symbols'] = clean_symbols
                user_context['display_symbols'] = display_symbols  # Store descriptive names for display
                user_context['current_currency'] = currency
                user_context['last_analysis_type'] = 'comparison'
                user_context['portfolio_contexts'] = portfolio_contexts  # Store portfolio contexts
                user_context['expanded_symbols'] = expanded_symbols  # Store expanded symbols
                
                # Store describe table for AI analysis
                try:
                    describe_table = self._format_describe_table(comparison)
                    user_context['describe_table'] = describe_table
                except Exception as e:
                    self.logger.error(f"Error storing describe table: {e}")
                    user_context['describe_table'] = "📊 Данные для анализа недоступны"
                
                # Create comparison chart
                fig, ax = chart_styles.create_comparison_chart(
                    comparison.wealth_indexes, symbols, currency
                )
                
                # Save chart to bytes with memory optimization
                img_buffer = io.BytesIO()
                chart_styles.save_figure(fig, img_buffer)
                img_buffer.seek(0)
                img_bytes = img_buffer.getvalue()
                
                # Clear matplotlib cache to free memory
                chart_styles.cleanup_figure(fig)
                
                # Chart analysis is now only available via buttons
                
                # Create caption
                caption = f"Сравнение {', '.join(symbols)}\n\n"
                caption += f"Валюта: {currency} ({currency_info})\n"
                
                # Add inflation information for Chinese symbols
                if currency in ['CNY', 'HKD']:
                    inflation_ticker = self._get_inflation_ticker_by_currency(currency)
                    caption += f"Инфляция: {inflation_ticker}\n"
                
                # Describe table will be sent in separate message
                
                # Chart analysis is only available via buttons
                
                # Create keyboard with analysis buttons conditionally
                # Determine composition: portfolios vs assets
                try:
                    has_portfolios_only = all(isinstance(s, (pd.Series, pd.DataFrame)) for s in expanded_symbols)
                    has_assets_only = all(not isinstance(s, (pd.Series, pd.DataFrame)) for s in expanded_symbols)
                    is_mixed_comparison = not (has_portfolios_only or has_assets_only)
                except Exception:
                    # Safe fallback
                    has_portfolios_only = False
                    is_mixed_comparison = False

                keyboard = []

                # Hide these buttons for mixed comparisons (portfolio + asset)
                if not is_mixed_comparison:
                    keyboard.append([
                        InlineKeyboardButton("📉 Drawdowns", callback_data="drawdowns_compare"),
                        InlineKeyboardButton("💰 Dividends", callback_data="dividends_compare")
                    ])
                    keyboard.append([
                        InlineKeyboardButton("🔗 Correlation Matrix", callback_data="correlation_compare")
                    ])

                # Add Risk / Return for all comparisons (portfolios + assets, assets only, portfolios only)
                keyboard.append([
                    InlineKeyboardButton("📊 Risk / Return", callback_data="risk_return_compare")
                ])
                
                # Add chart analysis button if Gemini is available
                if self.gemini_service and self.gemini_service.is_available():
                    keyboard.append([
                        InlineKeyboardButton("AI-анализ графика", callback_data="chart_analysis_compare"),
                        InlineKeyboardButton("AI-анализ данных", callback_data="data_analysis_compare")
                    ])
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send comparison chart with buttons
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=io.BytesIO(img_bytes),
                    caption=self._truncate_caption(caption),
                    reply_markup=reply_markup
                )
                
                # Send describe table in separate message for better markdown formatting
                try:
                    describe_table = self._format_describe_table(comparison)
                    await self._send_message_safe(update, describe_table, parse_mode='Markdown')
                except Exception as e:
                    self.logger.error(f"Error sending describe table: {e}")
                    # Continue without table if there's an error
                
                # AI analysis is now only available via buttons
                
            except Exception as e:
                self.logger.error(f"Error creating comparison: {e}")
                await self._send_message_safe(update, f"❌ Ошибка при создании сравнения: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error in compare command: {e}")
            await self._send_message_safe(update, f"❌ Ошибка в команде сравнения: {str(e)}")

    async def my_portfolios_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /my command for displaying saved portfolios"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Processing /my command for user {user_id}")
            
            # Get user context with detailed logging
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            self.logger.info(f"Full user context: {user_context}")
            
            saved_portfolios = user_context.get('saved_portfolios', {})
            self.logger.info(f"Saved portfolios count: {len(saved_portfolios)}")
            self.logger.info(f"Saved portfolios keys: {list(saved_portfolios.keys())}")
            self.logger.info(f"Saved portfolios content: {saved_portfolios}")
            
            if not saved_portfolios:
                await self._send_message_safe(update, 
                    "💼 У вас пока нет сохраненных портфелей\n\n"
                    "Создайте портфель командой:\n"
                    "`/portfolio символ1:доля1 символ2:доля2 ...`\n\n"
                    "Пример:\n"
                    "`/portfolio SPY.US:0.6 QQQ.US:0.4`"
                )
                return
            
            # Create comprehensive portfolio list
            portfolio_list = "💼 Ваши сохраненные портфели:\n\n"
            
            self.logger.info(f"Processing {len(saved_portfolios)} portfolios for display")
            
            for portfolio_symbol, portfolio_info in saved_portfolios.items():
                self.logger.info(f"Processing portfolio: {portfolio_symbol}")
                self.logger.info(f"Portfolio info keys: {list(portfolio_info.keys())}")
                portfolio_list += f"🏷️ **{portfolio_symbol}**\n"
                
                # Basic info
                symbols = portfolio_info.get('symbols', [])
                weights = portfolio_info.get('weights', [])
                currency = portfolio_info.get('currency', 'N/A')
                created_at = portfolio_info.get('created_at', 'N/A')
                
                portfolio_list += f"📊 Состав: {', '.join(symbols)}\n"
                
                # Weights breakdown
                if symbols and weights and len(symbols) == len(weights):
                    portfolio_list += "💰 Доли:\n"
                    for i, (symbol, weight) in enumerate(zip(symbols, weights)):
                        portfolio_list += f"   • {symbol}: {weight:.1%}\n"
                
                portfolio_list += f"💱 Валюта: {currency}\n"
                
                # Performance metrics if available
                if 'mean_return_annual' in portfolio_info:
                    portfolio_list += f"📈 Годовая доходность: {portfolio_info['mean_return_annual']:.2%}\n"
                if 'volatility_annual' in portfolio_info:
                    portfolio_list += f"📉 Годовая волатильность: {portfolio_info['volatility_annual']:.2%}\n"
                if 'sharpe_ratio' in portfolio_info:
                    portfolio_list += f"⚡ Коэффициент Шарпа: {portfolio_info['sharpe_ratio']:.2f}\n"
                
                # Dates if available
                if 'first_date' in portfolio_info and 'last_date' in portfolio_info:
                    portfolio_list += f"📅 Период: {portfolio_info['first_date']} - {portfolio_info['last_date']}\n"
                
                # Final value if available
                if 'final_value' in portfolio_info and portfolio_info['final_value'] is not None:
                    portfolio_list += f"💵 Финальная стоимость: {portfolio_info['final_value']:.2f} {currency}\n"
                
                portfolio_list += f"🕐 Создан: {created_at}\n"
                portfolio_list += "\n" + "─" * 40 + "\n\n"
            
            # Add usage instructions
                portfolio_list += "💡 **Использование в сравнении:**\n"
                portfolio_list += "• `/compare PF_1 SPY.US` - сравнить портфель с активом\n"
                portfolio_list += "• `/compare PF_1 PF_2` - сравнить два портфеля\n"
                portfolio_list += "• `/compare PF_1 SPY.US QQQ.US` - смешанное сравнение\n"
                portfolio_list += "• `/compare portfolio_123.PF SPY.US` - сравнить портфель с активом\n\n"
                
                portfolio_list += "🔧 **Управление:**\n"
                portfolio_list += "• Портфели автоматически сохраняются при создании\n"
                portfolio_list += "• Портфели с одинаковыми активами и пропорциями не дублируются\n"
                portfolio_list += "• Используйте символы для сравнения и анализа\n"
                portfolio_list += "• Все данные сохраняются в контексте сессии\n\n"
                
                # Create keyboard with clear portfolios button
                keyboard = [
                    [InlineKeyboardButton("🗑️ Очистить все портфели", callback_data="clear_all_portfolios")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send the portfolio list with clear button
                await self._send_message_safe(update, portfolio_list, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            self.logger.error(f"Error in my portfolios command: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_message_safe(update, f"❌ Ошибка при получении списка портфелей: {str(e)}\n\n💡 Попробуйте создать новый портфель командой `/portfolio`")

    async def portfolio_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /portfolio command for creating portfolio with weights"""
        try:
            if not context.args:
                
                await self._send_message_safe(update, 
                    f"📊 Команда /portfolio - Создание портфеля\n\n"
                    f"Введите список активов с указанием долей:\n"
                    f"Примеры:\n"
                    f"• SPY.US:0.5 QQQ.US:0.3 BND.US:0.2\n"
                    f"• SBER.MOEX:0.4 GAZP.MOEX:0.3 LKOH.MOEX:0.3\n"
                    f"• VOO.US:0.6 GC.COMM:0.2 BND.US:0.2\n\n"
                    f"💡Доли должны суммироваться в 1.0 (100%), максимум 10 активов в портфеле\n"
                    f"💡Базовая валюта определяется по первому символу\n"
                )
                
                # Set flag to wait for portfolio input
                user_id = update.effective_user.id
                self.logger.info(f"Setting waiting_for_portfolio=True for user {user_id}")
                self._update_user_context(user_id, waiting_for_portfolio=True)
                
                # Verify the flag was set
                updated_context = self._get_user_context(user_id)
                self.logger.info(f"Updated context waiting_for_portfolio: {updated_context.get('waiting_for_portfolio', False)}")
                return

            # Extract symbols and weights from command arguments
            raw_args = ' '.join(context.args)
            portfolio_data = []
            
            for arg in raw_args.split():
                if ':' in arg:
                    symbol_part, weight_part = arg.split(':', 1)
                    original_symbol = symbol_part.strip()
                    # Преобразуем символ в верхний регистр
                    symbol = original_symbol.upper()
                    
                    try:
                        weight_str = weight_part.strip()
                        self.logger.info(f"DEBUG: Converting weight '{weight_str}' to float for symbol '{symbol}'")
                        weight = float(weight_str)
                    except Exception as e:
                        self.logger.error(f"Error converting weight '{weight_part.strip()}' to float: {e}")
                        await self._send_message_safe(update, f"❌ Некорректная доля для {symbol}: '{weight_part.strip()}'. Доля должна быть числом от 0 до 1")
                        return
                    
                    if weight <= 0 or weight > 1:
                        await self._send_message_safe(update, f"❌ Некорректная доля для {symbol}: {weight}. Доля должна быть от 0 до 1")
                        return
                    
                    portfolio_data.append((symbol, weight))
                    
                else:
                    await self._send_message_safe(update, f"❌ Некорректный формат: {arg}. Используйте формат символ:доля")
                    return
            
            if not portfolio_data:
                await self._send_message_safe(update, "❌ Не указаны активы для портфеля")
                return
            
            # Check if weights sum to approximately 1.0
            total_weight = sum(weight for _, weight in portfolio_data)
            if abs(total_weight - 1.0) > 0.01:
                # Предлагаем исправление, если сумма близка к 1
                if abs(total_weight - 1.0) <= 0.1:
                    corrected_weights = []
                    for symbol, weight in portfolio_data:
                        corrected_weight = weight / total_weight
                        corrected_weights.append((symbol, corrected_weight))
                    
                    await self._send_message_safe(update, 
                        f"⚠️ Сумма долей ({total_weight:.3f}) не равна 1.0\n\n"
                        f"Исправленные доли:\n"
                        f"{chr(10).join([f'• {symbol}: {weight:.3f}' for symbol, weight in corrected_weights])}\n\n"
                        f"Попробуйте команду:\n"
                        f"`/portfolio {' '.join([f'{symbol}:{weight:.3f}' for symbol, weight in corrected_weights])}`"
                    )
                else:
                    await self._send_message_safe(update, 
                        f"❌ Сумма долей должна быть равна 1.0, текущая сумма: {total_weight:.3f}\n\n"
                        f"Пример правильной команды:\n"
                        f"`/portfolio LQDT.MOEX:0.78 OBLG.MOEX:0.16 GOLD.MOEX:0.06`"
                    )
                return
            
            if len(portfolio_data) > 10:
                await self._send_message_safe(update, "❌ Максимум 10 активов в портфеле")
                return
            
            symbols = [symbol for symbol, _ in portfolio_data]
            weights = [weight for _, weight in portfolio_data]
            
            await self._send_message_safe(update, f"Создаю портфель: {', '.join(symbols)}...")
            
            # Create portfolio using okama
            
            self.logger.info(f"DEBUG: About to create portfolio with symbols: {symbols}, weights: {weights}")
            self.logger.info(f"DEBUG: Symbols types: {[type(s) for s in symbols]}")
            self.logger.info(f"DEBUG: Weights types: {[type(w) for w in weights]}")
            
            # Determine base currency from the first asset
            first_symbol = symbols[0]
            currency_info = ""
            try:
                if '.' in first_symbol:
                    namespace = first_symbol.split('.')[1]
                    if namespace == 'MOEX':
                        currency = "RUB"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    elif namespace == 'US':
                        currency = "USD"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    elif namespace == 'LSE':
                        currency = "GBP"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    elif namespace == 'FX':
                        currency = "USD"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    elif namespace == 'COMM':
                        currency = "USD"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    elif namespace == 'INDX':
                        currency = "USD"
                        currency_info = f"автоматически определена по первому активу ({first_symbol})"
                    else:
                        currency = "USD"
                        currency_info = "по умолчанию (USD)"
                else:
                    currency = "USD"
                    currency_info = "по умолчанию (USD)"
                
                self.logger.info(f"Auto-detected currency for portfolio {first_symbol}: {currency}")
                
            except Exception as e:
                self.logger.warning(f"Could not auto-detect currency, using USD: {e}")
                currency = "USD"
                currency_info = "по умолчанию (USD)"
            
            try:
                # Final validation of weights before creating portfolio
                final_total = sum(weights)
                if abs(final_total - 1.0) > 0.001:
                    await self._send_message_safe(update, 
                        f"❌ Ошибка валидации весов: сумма {final_total:.6f} не равна 1.0\n"
                        f"Веса: {', '.join([f'{w:.6f}' for w in weights])}"
                    )
                    return
                
                # Create Portfolio with detected currency
                try:
                    self.logger.info(f"DEBUG: About to create ok.Portfolio with symbols={symbols}, ccy={currency}, weights={weights}")
                    self.logger.info(f"DEBUG: Symbols types: {[type(s) for s in symbols]}")
                    self.logger.info(f"DEBUG: Weights types: {[type(w) for w in weights]}")
                    portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
                    self.logger.info(f"DEBUG: Successfully created portfolio")
                except Exception as e:
                    self.logger.error(f"DEBUG: Error creating portfolio: {e}")
                    self.logger.error(f"DEBUG: Error type: {type(e)}")
                    raise e
                
                self.logger.info(f"Created Portfolio with weights: {weights}, total: {sum(weights):.6f}")
                
                # Get portfolio information (raw object like /info)
                portfolio_text = f"{portfolio}"
                
                # Escape Markdown characters to prevent parsing errors
                portfolio_text = self._escape_markdown(portfolio_text)
                
                # Portfolio information is already set above as raw object
                
                # Generate portfolio symbol using PF namespace and okama's assigned symbol
                user_id = update.effective_user.id
                user_context = self._get_user_context(user_id)
                
                # Count existing portfolios for this user
                portfolio_count = user_context.get('portfolio_count', 0) + 1
                
                # Use PF namespace with okama's assigned symbol
                try:
                    # Get the portfolio symbol that okama assigned
                    if hasattr(portfolio, 'symbol'):
                        portfolio_symbol = portfolio.symbol
                    else:
                        # Fallback to custom symbol if okama doesn't provide one
                        portfolio_symbol = f"PF_{portfolio_count}"
                except Exception as e:
                    self.logger.warning(f"Could not get okama portfolio symbol: {e}")
                    portfolio_symbol = f"PF_{portfolio_count}"
                
                # Create compact portfolio data string for callback (only symbols to avoid Button_data_invalid)
                portfolio_data_str = ','.join(symbols)
                
                # Add portfolio symbol display
                portfolio_text += f"\n\n🏷️ Символ портфеля: `{portfolio_symbol}` (namespace PF)\n"
                portfolio_text += f"💾 Портфель сохранен в контексте для использования в /compare"
                
                # Add buttons with wealth chart as first
                keyboard = [
                    [InlineKeyboardButton("📈 График накопленной доходности", callback_data=f"portfolio_wealth_chart_{portfolio_symbol}")],
                    [InlineKeyboardButton("💰 Доходность", callback_data=f"portfolio_returns_{portfolio_symbol}")],
                    [InlineKeyboardButton("📉 Просадки", callback_data=f"portfolio_drawdowns_{portfolio_symbol}")],
                    [InlineKeyboardButton("📊 Риск метрики", callback_data=f"portfolio_risk_metrics_{portfolio_symbol}")],
                    [InlineKeyboardButton("🎲 Монте Карло", callback_data=f"portfolio_monte_carlo_{portfolio_symbol}")],
                    [InlineKeyboardButton("📈 Процентили 10, 50, 90", callback_data=f"portfolio_forecast_{portfolio_symbol}")],
                    [InlineKeyboardButton("📊 Портфель vs Активы", callback_data=f"portfolio_compare_assets_{portfolio_symbol}")],
                    [InlineKeyboardButton("📈 Rolling CAGR", callback_data=f"portfolio_rolling_cagr_{portfolio_symbol}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Send portfolio information with buttons (no chart)
                await self._send_message_safe(update, portfolio_text, reply_markup=reply_markup)
                
                # Store portfolio data in context
                user_id = update.effective_user.id
                self.logger.info(f"Storing portfolio data in context for user {user_id}")
                self.logger.info(f"Symbols: {symbols}")
                self.logger.info(f"Currency: {currency}")
                self.logger.info(f"Weights: {weights}")
                self.logger.info(f"Portfolio symbol: {portfolio_symbol}")
                
                # Store portfolio information in user context
                self._update_user_context(
                    user_id, 
                    last_assets=symbols,
                    last_analysis_type='portfolio',
                    last_period='MAX',
                    current_symbols=symbols,
                    current_currency=currency,
                    current_currency_info=currency_info,
                    portfolio_weights=weights,
                    portfolio_count=portfolio_count
                )
                
                # Verify what was saved
                saved_context = self._get_user_context(user_id)
                self.logger.info(f"Saved context keys: {list(saved_context.keys())}")
                self.logger.info(f"Saved current_symbols: {saved_context.get('current_symbols')}")
                self.logger.info(f"Saved current_currency: {saved_context.get('current_currency')}")
                self.logger.info(f"Saved portfolio_weights: {saved_context.get('portfolio_weights')}")
                
                # Get current saved portfolios and check for existing portfolio
                saved_portfolios = user_context.get('saved_portfolios', {})
                
                # Check if portfolio with same assets and proportions already exists
                existing_portfolio_symbol = self._check_existing_portfolio(symbols, weights, saved_portfolios)
                
                if existing_portfolio_symbol:
                    # Use existing portfolio symbol and update the message
                    portfolio_symbol = existing_portfolio_symbol
                    portfolio_text += f"\n\n🏷️ Символ портфеля: `{portfolio_symbol}` (namespace PF)\n"
                    portfolio_text += f"✅ Портфель с такими же активами и пропорциями уже существует\n"
                    portfolio_text += f"💾 Используется ранее сохраненный портфель"
                    
                    # Update portfolio count without incrementing
                    portfolio_count = user_context.get('portfolio_count', 0)
                else:
                    # Increment portfolio count for new portfolio
                    portfolio_count = user_context.get('portfolio_count', 0) + 1
                    portfolio_text += f"\n\n🏷️ Символ портфеля: `{portfolio_symbol}` (namespace PF)\n"
                    portfolio_text += f"💾 Портфель сохранен в контексте для использования в /compare"
                
                # Get additional portfolio attributes for comprehensive storage
                portfolio_attributes = {}
                try:
                    # Basic portfolio info
                    portfolio_attributes.update({
                        'symbols': symbols,
                        'weights': weights,
                        'currency': currency,
                        'created_at': datetime.now().isoformat(),
                        'description': f"Портфель: {', '.join(symbols)}",
                        'portfolio_symbol': portfolio_symbol,  # Ensure symbol is preserved
                        'total_weight': sum(weights),
                        'asset_count': len(symbols)
                    })
                    
                    # Portfolio performance metrics
                    if hasattr(portfolio, 'mean_return_annual'):
                        try:
                            value = portfolio.mean_return_annual
                            # Handle Period objects and other non-numeric types
                            if hasattr(value, 'to_timestamp'):
                                try:
                                    value = value.to_timestamp()
                                except Exception:
                                    # If to_timestamp fails, try to convert to string first
                                    if hasattr(value, 'strftime'):
                                        value = str(value)
                                    else:
                                        value = str(value)
                            
                            # Handle Timestamp objects and other datetime-like objects
                            if hasattr(value, 'timestamp'):
                                try:
                                    value = value.timestamp()
                                except Exception:
                                    value = str(value)
                            elif not isinstance(value, (int, float)):
                                # Try to convert non-numeric values
                                value = str(value)
                                import re
                                match = re.search(r'[\d.-]+', value)
                                if match:
                                    value = float(match.group())
                                else:
                                    value = 0.0
                            portfolio_attributes['mean_return_annual'] = float(value)
                        except Exception as e:
                            self.logger.warning(f"Could not convert mean_return_annual to float: {e}")
                            portfolio_attributes['mean_return_annual'] = None
                    
                    if hasattr(portfolio, 'volatility_annual'):
                        try:
                            value = portfolio.volatility_annual
                            # Handle Period objects and other non-numeric types
                            if hasattr(value, 'to_timestamp'):
                                try:
                                    value = value.to_timestamp()
                                except Exception:
                                    # If to_timestamp fails, try to convert to string first
                                    if hasattr(value, 'strftime'):
                                        value = str(value)
                                    else:
                                        value = str(value)
                            
                            # Handle Timestamp objects and other datetime-like objects
                            if hasattr(value, 'timestamp'):
                                try:
                                    value = value.timestamp()
                                except Exception:
                                    value = str(value)
                            elif not isinstance(value, (int, float)):
                                # Try to convert non-numeric values
                                value = str(value)
                                import re
                                match = re.search(r'[\d.-]+', value)
                                if match:
                                    value = float(match.group())
                                else:
                                    value = 0.0
                            portfolio_attributes['volatility_annual'] = float(value)
                        except Exception as e:
                            self.logger.warning(f"Could not convert volatility_annual to float: {e}")
                            portfolio_attributes['volatility_annual'] = None
                    
                    if hasattr(portfolio, 'sharpe_ratio'):
                        try:
                            value = portfolio.sharpe_ratio
                            # Handle Period objects and other non-numeric types
                            if hasattr(value, 'to_timestamp'):
                                try:
                                    value = value.to_timestamp()
                                except Exception:
                                    # If to_timestamp fails, try to convert to string first
                                    if hasattr(value, 'strftime'):
                                        value = str(value)
                                    else:
                                        value = str(value)
                            
                            # Handle Timestamp objects and other datetime-like objects
                            if hasattr(value, 'timestamp'):
                                try:
                                    value = value.timestamp()
                                except Exception:
                                    value = str(value)
                            elif not isinstance(value, (int, float)):
                                # Try to convert non-numeric values
                                value = str(value)
                                import re
                                match = re.search(r'[\d.-]+', value)
                                if match:
                                    value = float(match.group())
                                else:
                                    value = 0.0
                            portfolio_attributes['sharpe_ratio'] = float(value)
                        except Exception as e:
                            self.logger.warning(f"Could not convert sharpe_ratio to float: {e}")
                            portfolio_attributes['sharpe_ratio'] = None
                    
                    # Portfolio dates
                    if hasattr(portfolio, 'first_date'):
                        portfolio_attributes['first_date'] = str(portfolio.first_date)
                    if hasattr(portfolio, 'last_date'):
                        portfolio_attributes['last_date'] = str(portfolio.last_date)
                    if hasattr(portfolio, 'period_length'):
                        portfolio_attributes['period_length'] = str(portfolio.period_length)
                    
                    # Final portfolio value
                    try:
                        final_value = portfolio.wealth_index.iloc[-1]
                        if hasattr(final_value, '__iter__') and not isinstance(final_value, str):
                            if hasattr(final_value, 'iloc'):
                                final_value = final_value.iloc[0]
                            elif hasattr(final_value, '__getitem__'):
                                final_value = final_value[0]
                            else:
                                final_value = list(final_value)[0]
                        
                        # Handle Period objects and other non-numeric types
                        if hasattr(final_value, 'to_timestamp'):
                            try:
                                final_value = final_value.to_timestamp()
                            except Exception:
                                # If to_timestamp fails, try to convert to string first
                                if hasattr(final_value, 'strftime'):
                                    final_value = str(final_value)
                                else:
                                    final_value = str(final_value)
                        
                        # Handle Timestamp objects and other datetime-like objects
                        if hasattr(final_value, 'timestamp'):
                            try:
                                final_value = final_value.timestamp()
                            except Exception:
                                final_value = str(final_value)
                        elif not isinstance(final_value, (int, float)):
                            # Try to convert non-numeric values
                            final_value_str = str(final_value)
                            import re
                            match = re.search(r'[\d.-]+', final_value_str)
                            if match:
                                final_value = float(match.group())
                            else:
                                final_value = 0.0
                        
                        portfolio_attributes['final_value'] = float(final_value)
                    except Exception as e:
                        self.logger.warning(f"Could not get final value for storage: {e}")
                        portfolio_attributes['final_value'] = None
                    
                    # Store as JSON string for better compatibility
                    portfolio_json = json.dumps(portfolio_attributes, ensure_ascii=False, default=str)
                    portfolio_attributes['json_data'] = portfolio_json
                    
                except Exception as e:
                    self.logger.warning(f"Could not get all portfolio attributes: {e}")
                    # Fallback to basic storage
                    portfolio_attributes = {
                        'symbols': symbols,
                        'weights': weights,
                        'currency': currency,
                        'created_at': datetime.now().isoformat(),
                        'description': f"Портфель: {', '.join(symbols)}",
                        'portfolio_symbol': portfolio_symbol,
                        'total_weight': sum(weights),
                        'asset_count': len(symbols),
                        'json_data': json.dumps({
                            'symbols': symbols,
                            'weights': weights,
                            'currency': currency,
                            'portfolio_symbol': portfolio_symbol
                        }, ensure_ascii=False)
                    }
                
                # Add the new portfolio to saved portfolios (always save, even if similar exists)
                saved_portfolios[portfolio_symbol] = portfolio_attributes
                
                # Update saved portfolios in context (single update)
                self.logger.info(f"Updating user context with portfolio: {portfolio_symbol}")
                self.logger.info(f"Portfolio attributes: {portfolio_attributes}")
                self.logger.info(f"Current saved portfolios: {saved_portfolios}")
                
                self._update_user_context(
                    user_id,
                    saved_portfolios=saved_portfolios,
                    portfolio_count=portfolio_count
                )
                
                # Verify context was saved
                saved_context = self._get_user_context(user_id)
                self.logger.info(f"Saved context keys: {list(saved_context.keys())}")
                self.logger.info(f"Saved current_symbols: {saved_context.get('current_symbols')}")
                self.logger.info(f"Saved last_assets: {saved_context.get('last_assets')}")
                self.logger.info(f"Saved portfolio_weights: {saved_context.get('portfolio_weights')}")
                
            except Exception as e:
                self.logger.error(f"Error creating portfolio: {e}")
                await self._send_message_safe(update, 
                    f"❌ Ошибка при создании портфеля: {str(e)}\n\n"
                    "💡 Возможные причины:\n"
                    "• Один из символов недоступен\n"
                    "• Проблемы с данными\n"
                    "• Неверный формат символа\n\n"
                    "Проверьте:\n"
                    "• Правильность написания символов\n"
                    "• Доступность данных для указанных активов"
                )
                
        except Exception as e:
            self.logger.error(f"Error in portfolio command: {e}")
            await self._send_message_safe(update, f"❌ Ошибка при выполнении команды портфеля: {str(e)}")

    async def _handle_portfolio_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle portfolio input from user message"""
        try:
            user_id = update.effective_user.id
            
            # Clear waiting flag
            self._update_user_context(user_id, waiting_for_portfolio=False)
            
            # Extract symbols and weights from input text
            portfolio_data = []
            
            for arg in text.split():
                if ':' in arg:
                    symbol_part, weight_part = arg.split(':', 1)
                    original_symbol = symbol_part.strip()
                    # Преобразуем символ в верхний регистр
                    symbol = original_symbol.upper()
                    
                    try:
                        weight_str = weight_part.strip()
                        self.logger.info(f"DEBUG: Converting weight '{weight_str}' to float for symbol '{symbol}'")
                        weight = float(weight_str)
                    except Exception as e:
                        self.logger.error(f"Error converting weight '{weight_part.strip()}' to float: {e}")
                        await self._send_message_safe(update, f"❌ Некорректная доля для {symbol}: '{weight_part.strip()}'. Доля должна быть числом от 0 до 1")
                        return
                    
                    if weight <= 0 or weight > 1:
                        await self._send_message_safe(update, f"❌ Некорректная доля для {symbol}: {weight}. Доля должна быть от 0 до 1")
                        return
                    
                    portfolio_data.append((symbol, weight))
                    
                else:
                    await self._send_message_safe(update, f"❌ Некорректный формат: {arg}. Используйте формат символ:доля")
                    return
            
            if not portfolio_data:
                await self._send_message_safe(update, "❌ Не указаны активы для портфеля")
                return
            
            # Check if weights sum to approximately 1.0
            total_weight = sum(weight for _, weight in portfolio_data)
            if abs(total_weight - 1.0) > 0.01:
                # Предлагаем исправление, если сумма близка к 1
                if abs(total_weight - 1.0) <= 0.1:
                    corrected_weights = []
                    for symbol, weight in portfolio_data:
                        corrected_weight = weight / total_weight
                        corrected_weights.append((symbol, corrected_weight))
                    
                    await self._send_message_safe(update, 
                        f"⚠️ Сумма долей ({total_weight:.3f}) не равна 1.0\n\n"
                        f"Исправленные доли:\n"
                        f"{chr(10).join([f'• {symbol}: {weight:.3f}' for symbol, weight in corrected_weights])}\n\n"
                        f"Попробуйте команду:\n"
                        f"`/portfolio {' '.join([f'{symbol}:{weight:.3f}' for symbol, weight in corrected_weights])}`"
                    )
                else:
                    await self._send_message_safe(update, 
                        f"❌ Сумма долей должна быть равна 1.0, текущая сумма: {total_weight:.3f}\n\n"
                        f"Пример правильной команды:\n"
                        f"`/portfolio LQDT.MOEX:0.78 OBLG.MOEX:0.16 GOLD.MOEX:0.06`"
                    )
                return
            
            if len(portfolio_data) > 10:
                await self._send_message_safe(update, "❌ Максимум 10 активов в портфеле")
                return
            
            symbols = [symbol for symbol, _ in portfolio_data]
            weights = [weight for _, weight in portfolio_data]
            
            await self._send_message_safe(update, f"Создаю портфель: {', '.join(symbols)}...")
            
            # Create portfolio using okama
            self.logger.info(f"DEBUG: About to create portfolio with symbols: {symbols}, weights: {weights}")
            self.logger.info(f"DEBUG: Symbols types: {[type(s) for s in symbols]}")
            self.logger.info(f"DEBUG: Weights types: {[type(w) for w in weights]}")
            
            # Determine base currency from the first asset using .currency property
            first_symbol = symbols[0]
            currency_info = ""
            try:
                # Create asset to get its currency
                first_asset = ok.Asset(first_symbol)
                currency = first_asset.currency
                currency_info = f"автоматически определена по первому активу ({first_symbol})"
                self.logger.info(f"Currency determined from asset {first_symbol}: {currency}")
            except Exception as e:
                self.logger.warning(f"Could not determine currency from asset {first_symbol}: {e}")
                # Fallback to namespace-based detection using our function
                currency, currency_info = self._get_currency_by_symbol(first_symbol)
            
            # Create portfolio using okama
            try:
                portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
                
                # Get portfolio information (raw object like /info)
                portfolio_text = f"{portfolio}"
                
                # Escape Markdown characters to prevent parsing errors
                portfolio_text = self._escape_markdown(portfolio_text)
                
                # Generate portfolio symbol using PF namespace and okama's assigned symbol
                user_id = update.effective_user.id
                user_context = self._get_user_context(user_id)
                
                # Count existing portfolios for this user
                portfolio_count = user_context.get('portfolio_count', 0) + 1
                
                # Use PF namespace with okama's assigned symbol
                # Get the portfolio symbol that okama assigned
                if hasattr(portfolio, 'symbol'):
                    portfolio_symbol = portfolio.symbol
                else:
                    # Fallback to custom symbol if okama doesn't provide one
                    portfolio_symbol = f"PF_{portfolio_count}"
                
                # Create compact portfolio data string for callback (only symbols to avoid Button_data_invalid)
                portfolio_data_str = ','.join(symbols)
                
                # Add portfolio symbol display
                portfolio_text += f"\n\n🏷️ Символ портфеля: `{portfolio_symbol}`\n"
                portfolio_text += f"💾 Портфель сохранен в контексте для использования в /compare"
                
                # Add buttons with wealth chart as first
                keyboard = [
                    [InlineKeyboardButton("📈 График накопленной доходности", callback_data=f"portfolio_wealth_chart_{portfolio_symbol}")],
                    [InlineKeyboardButton("💰 Доходность", callback_data=f"portfolio_returns_{portfolio_symbol}")],
                    [InlineKeyboardButton("📉 Просадки", callback_data=f"portfolio_drawdowns_{portfolio_symbol}")],
                    [InlineKeyboardButton("📊 Риск метрики", callback_data=f"portfolio_risk_metrics_{portfolio_symbol}")],
                    [InlineKeyboardButton("🎲 Монте Карло", callback_data=f"portfolio_monte_carlo_{portfolio_symbol}")],
                    [InlineKeyboardButton("📈 Процентили 10, 50, 90", callback_data=f"portfolio_forecast_{portfolio_symbol}")],
                    [InlineKeyboardButton("📊 Портфель vs Активы", callback_data=f"portfolio_compare_assets_{portfolio_symbol}")],
                    [InlineKeyboardButton("📈 Rolling CAGR", callback_data=f"portfolio_rolling_cagr_{portfolio_symbol}")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                # Log button creation for debugging
                self.logger.info(f"Created keyboard with {len(keyboard)} buttons for portfolio {portfolio_symbol}")
                for i, button_row in enumerate(keyboard):
                    for j, button in enumerate(button_row):
                        self.logger.info(f"Button [{i}][{j}]: '{button.text}' -> '{button.callback_data}'")
                
                # Send portfolio information with buttons (no chart)
                self.logger.info(f"Sending portfolio message with buttons for portfolio {portfolio_symbol}")
                await self._send_message_safe(update, portfolio_text, reply_markup=reply_markup)
                self.logger.info(f"Portfolio message sent successfully for portfolio {portfolio_symbol}")
                
                # Store portfolio data in context
                user_id = update.effective_user.id
                self.logger.info(f"Storing portfolio data in context for user {user_id}")
                self.logger.info(f"Symbols: {symbols}")
                self.logger.info(f"Currency: {currency}")
                self.logger.info(f"Weights: {weights}")
                self.logger.info(f"Portfolio symbol: {portfolio_symbol}")
                
                # Store portfolio information in user context
                self._update_user_context(
                    user_id, 
                    last_assets=symbols,
                    last_analysis_type='portfolio',
                    last_period='MAX',
                    current_symbols=symbols,
                    current_currency=currency,
                    current_currency_info=currency_info,
                    portfolio_weights=weights,
                    portfolio_count=portfolio_count
                )
                
                # Verify what was saved
                saved_context = self._get_user_context(user_id)
                self.logger.info(f"Saved context keys: {list(saved_context.keys())}")
                self.logger.info(f"Saved current_symbols: {saved_context.get('current_symbols')}")
                self.logger.info(f"Saved current_currency: {saved_context.get('current_currency')}")
                self.logger.info(f"Saved portfolio_weights: {saved_context.get('portfolio_weights')}")
                
                # Get current saved portfolios and add the new portfolio
                saved_portfolios = user_context.get('saved_portfolios', {})
                
                # Create portfolio attributes for storage
                portfolio_attributes = {
                    'symbols': symbols,
                    'weights': weights,
                    'currency': currency,
                    'created_at': datetime.now().isoformat(),
                    'description': f"Портфель: {', '.join(symbols)}",
                    'portfolio_symbol': portfolio_symbol,
                    'total_weight': sum(weights),
                    'asset_count': len(symbols)
                }
                
                # Add portfolio to saved portfolios
                saved_portfolios[portfolio_symbol] = portfolio_attributes
                
                # Update saved portfolios in context
                self._update_user_context(
                    user_id,
                    saved_portfolios=saved_portfolios,
                    portfolio_count=portfolio_count
                )
                
                # Verify what was saved
                final_saved_context = self._get_user_context(user_id)
                self.logger.info(f"Final saved portfolios count: {len(final_saved_context.get('saved_portfolios', {}))}")
                self.logger.info(f"Final saved portfolios keys: {list(final_saved_context.get('saved_portfolios', {}).keys())}")
                
            except Exception as e:
                self.logger.error(f"Error creating portfolio: {e}")
                await self._send_message_safe(update, 
                    f"❌ Ошибка при создании портфеля: {str(e)}\n\n"
                    "💡 Возможные причины:\n"
                    "• Один из символов недоступен\n"
                    "• Проблемы с данными\n"
                    "• Неверный формат символа\n\n"
                    "Проверьте:\n"
                    "• Правильность написания символов\n"
                    "• Доступность данных для указанных активов"
                )
                
        except Exception as e:
            self.logger.error(f"Error in portfolio input handler: {e}")
            await self._send_message_safe(update, f"❌ Ошибка при обработке ввода портфеля: {str(e)}")

    async def _handle_compare_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Handle compare input from user message"""
        try:
            user_id = update.effective_user.id
            
            # Clear waiting flag
            self._update_user_context(user_id, waiting_for_compare=False)
            
            # Parse input text similar to compare_command logic
            raw_args = text.strip()
            
            # Enhanced parsing logic for multiple formats
            if ',' in raw_args:
                # Handle comma-separated symbols (with or without spaces)
                symbols = []
                for symbol_part in raw_args.split(','):
                    symbol_part = symbol_part.strip()
                    if symbol_part:
                        if any(portfolio_indicator in symbol_part.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                            symbols.append(symbol_part)
                        else:
                            symbols.append(symbol_part.upper())
                self.logger.info(f"Parsed comma-separated symbols: {symbols}")
            else:
                # Handle space-separated symbols
                symbols = []
                for symbol in raw_args.split():
                    if any(portfolio_indicator in symbol.upper() for portfolio_indicator in ['PORTFOLIO_', 'PF_', 'PORTFOLIO_', '.PF', '.pf']):
                        symbols.append(symbol)
                    else:
                        symbols.append(symbol.upper())
                self.logger.info(f"Parsed space-separated symbols: {symbols}")
            
            # Clean up symbols
            symbols = [symbol for symbol in symbols if symbol.strip()]
            
            if len(symbols) < 2:
                await self._send_message_safe(update, "❌ Необходимо указать минимум 2 символа для сравнения")
                return
            
            if len(symbols) > 10:
                await self._send_message_safe(update, "❌ Максимум 10 символов для сравнения")
                return
            
            # Process the comparison using the same logic as compare_command
            # We'll reuse the existing comparison logic by calling compare_command with args
            context.args = symbols
            await self.compare_command(update, context)
            
        except Exception as e:
            self.logger.error(f"Error in compare input handler: {e}")
            await self._send_message_safe(update, f"❌ Ошибка при обработке ввода сравнения: {str(e)}")

    async def _send_callback_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, parse_mode: str = None):
        """Отправить сообщение в callback query - исправлено для обработки None и разбивки длинных сообщений"""
        try:
            # Проверяем, что update и context не None
            if update is None or context is None:
                self.logger.error("Cannot send message: update or context is None")
                return
            
            # Разбиваем длинные сообщения на части
            max_length = 4000  # Оставляем запас для безопасности
            if len(text) > max_length:
                self.logger.info(f"Splitting long message ({len(text)} chars) into multiple parts")
                await self._send_long_callback_message(update, context, text, parse_mode)
                return
            
            if hasattr(update, 'callback_query') and update.callback_query is not None:
                # Для callback query используем context.bot.send_message
                try:
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=text,
                        parse_mode=parse_mode
                    )
                except Exception as callback_error:
                    self.logger.error(f"Error sending callback message: {callback_error}")
                    # Fallback: попробуем отправить через _send_message_safe
                    await self._send_message_safe(update, text, parse_mode)
            elif hasattr(update, 'message') and update.message is not None:
                # Для обычных сообщений используем _send_message_safe
                await self._send_message_safe(update, text, parse_mode)
            else:
                # Если ни то, ни другое - логируем ошибку
                self.logger.error("Cannot send message: neither callback_query nor message available")
                self.logger.error(f"Update type: {type(update)}")
                self.logger.error(f"Update attributes: {dir(update) if update else 'None'}")
        except Exception as e:
            self.logger.error(f"Error sending callback message: {e}")
            # Fallback: попробуем отправить через context.bot
            try:
                if hasattr(update, 'callback_query') and update.callback_query is not None:
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=f"❌ Ошибка отправки: {text[:500]}..."
                    )
            except Exception as fallback_error:
                self.logger.error(f"Fallback message sending also failed: {fallback_error}")

    async def _send_long_callback_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, parse_mode: str = None):
        """Отправить длинное сообщение по частям через callback query"""
        try:
            # Разбиваем текст на части
            parts = self._split_text_smart(text)
            
            for i, part in enumerate(parts):
                # Добавляем индикатор части для многочастных сообщений
                if len(parts) > 1:
                    part_text = f"📄 **Часть {i+1} из {len(parts)}:**\n\n{part}"
                else:
                    part_text = part
                
                # Отправляем каждую часть
                if hasattr(update, 'callback_query') and update.callback_query is not None:
                    try:
                        await context.bot.send_message(
                            chat_id=update.callback_query.message.chat_id,
                            text=part_text,
                            parse_mode=parse_mode
                        )
                    except Exception as part_error:
                        self.logger.error(f"Error sending message part {i+1}: {part_error}")
                        # Fallback для этой части
                        await self._send_message_safe(update, part_text, parse_mode)
                elif hasattr(update, 'message') and update.message is not None:
                    await self._send_message_safe(update, part_text, parse_mode)
                
                # Небольшая пауза между частями для избежания rate limiting
                if i < len(parts) - 1:  # Не делаем паузу после последней части
                    import asyncio
                    await asyncio.sleep(0.5)
                    
        except Exception as e:
            self.logger.error(f"Error sending long callback message: {e}")
            # Fallback: отправляем обрезанную версию
            try:
                if hasattr(update, 'callback_query') and update.callback_query is not None:
                    await context.bot.send_message(
                        chat_id=update.callback_query.message.chat_id,
                        text=f"❌ Ошибка разбивки сообщения: {text[:1000]}..."
                    )
            except Exception as fallback_error:
                self.logger.error(f"Fallback long message sending also failed: {fallback_error}")

    def _split_text_smart(self, text: str) -> list:
        """Умное разбиение текста на части с учетом структуры"""
        max_length = 4000
        if len(text) <= max_length:
            return [text]
        
        parts = []
        current_part = ""
        
        # Разбиваем по строкам для лучшего сохранения структуры
        lines = text.split('\n')
        
        for line in lines:
            # Если добавление строки не превышает лимит
            if len(current_part) + len(line) + 1 <= max_length:
                if current_part:
                    current_part += '\n' + line
                else:
                    current_part = line
            else:
                # Если текущая часть не пустая, сохраняем её
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                
                # Если одна строка слишком длинная, разбиваем её
                if len(line) > max_length:
                    # Разбиваем длинную строку по словам
                    words = line.split(' ')
                    temp_line = ""
                    for word in words:
                        if len(temp_line) + len(word) + 1 <= max_length:
                            if temp_line:
                                temp_line += ' ' + word
                            else:
                                temp_line = word
                        else:
                            if temp_line:
                                parts.append(temp_line)
                                temp_line = word
                            else:
                                # Если одно слово слишком длинное, обрезаем его
                                parts.append(word[:max_length])
                                temp_line = word[max_length:]
                    if temp_line:
                        current_part = temp_line
                else:
                    current_part = line
        
        # Добавляем последнюю часть
        if current_part:
            parts.append(current_part)
        
        return parts

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks for additional analysis"""
        query = update.callback_query
        await query.answer()
        
        self.logger.info(f"Button callback received: {query.data}")
        
        try:
            # Parse callback data
            callback_data = query.data
            self.logger.info(f"Processing callback data: {callback_data}")
            
            if callback_data == "drawdowns" or callback_data == "drawdowns_compare" or callback_data == "compare_drawdowns":
                self.logger.info("Drawdowns button clicked")
                
                # Get data from user context
                user_id = update.effective_user.id
                user_context = self._get_user_context(user_id)
                last_analysis_type = user_context.get('last_analysis_type')
                
                self.logger.info(f"Last analysis type: {last_analysis_type}")
                
                if last_analysis_type == 'portfolio':
                    symbols = user_context.get('current_symbols', [])
                    await self._handle_portfolio_drawdowns_button(update, context, symbols)
                else:
                    symbols = user_context.get('current_symbols', [])
                    await self._handle_drawdowns_button(update, context, symbols)
            elif callback_data == "dividends" or callback_data == "dividends_compare" or callback_data == "compare_dividends":
                self.logger.info("Dividends button clicked")
                
                # Get data from user context
                user_id = update.effective_user.id
                user_context = self._get_user_context(user_id)
                symbols = user_context.get('current_symbols', [])
                await self._handle_dividends_button(update, context, symbols)
            elif callback_data == "correlation" or callback_data == "correlation_compare" or callback_data == "compare_correlation":
                self.logger.info("Correlation button clicked")
                
                # Get data from user context
                user_id = update.effective_user.id
                user_context = self._get_user_context(user_id)
                symbols = user_context.get('current_symbols', [])
                await self._handle_correlation_button(update, context, symbols)
            elif callback_data.startswith('info_daily_chart_'):
                symbol = callback_data.replace('info_daily_chart_', '')
                self.logger.info(f"Info daily chart button clicked for symbol: {symbol}")
                await self._handle_daily_chart_button(update, context, symbol)
            elif callback_data.startswith('daily_chart_'):
                symbol = callback_data.replace('daily_chart_', '')
                self.logger.info(f"Daily chart button clicked for symbol: {symbol}")
                await self._handle_daily_chart_button(update, context, symbol)
            elif callback_data.startswith('info_monthly_chart_'):
                symbol = callback_data.replace('info_monthly_chart_', '')
                self.logger.info(f"Info monthly chart button clicked for symbol: {symbol}")
                await self._handle_monthly_chart_button(update, context, symbol)
            elif callback_data.startswith('monthly_chart_'):
                symbol = callback_data.replace('monthly_chart_', '')
                self.logger.info(f"Monthly chart button clicked for symbol: {symbol}")
                await self._handle_monthly_chart_button(update, context, symbol)
            elif callback_data.startswith('all_chart_'):
                symbol = callback_data.replace('all_chart_', '')
                self.logger.info(f"All chart button clicked for symbol: {symbol}")
                await self._handle_all_chart_button(update, context, symbol)
            elif callback_data.startswith('info_dividends_'):
                symbol = callback_data.replace('info_dividends_', '')
                self.logger.info(f"Info dividends button clicked for symbol: {symbol}")
                await self._handle_single_dividends_button(update, context, symbol)
            elif callback_data.startswith('dividends_') and ',' not in callback_data:
                # Для одиночного актива (dividends_AAA)
                symbol = callback_data.replace('dividends_', '')
                self.logger.info(f"Dividends button clicked for symbol: {symbol}")
                await self._handle_single_dividends_button(update, context, symbol)
            elif callback_data.startswith('tushare_daily_chart_'):
                symbol = callback_data.replace('tushare_daily_chart_', '')
                self.logger.info(f"Tushare daily chart button clicked for symbol: {symbol}")
                await self._handle_tushare_daily_chart_button(update, context, symbol)
            elif callback_data.startswith('tushare_monthly_chart_'):
                symbol = callback_data.replace('tushare_monthly_chart_', '')
                self.logger.info(f"Tushare monthly chart button clicked for symbol: {symbol}")
                await self._handle_tushare_monthly_chart_button(update, context, symbol)
            elif callback_data.startswith('tushare_all_chart_'):
                symbol = callback_data.replace('tushare_all_chart_', '')
                self.logger.info(f"Tushare all chart button clicked for symbol: {symbol}")
                await self._handle_tushare_all_chart_button(update, context, symbol)
            elif callback_data.startswith('tushare_dividends_'):
                symbol = callback_data.replace('tushare_dividends_', '')
                self.logger.info(f"Tushare dividends button clicked for symbol: {symbol}")
                await self._handle_tushare_dividends_button(update, context, symbol)
            elif callback_data.startswith('portfolio_risk_metrics_'):
                portfolio_symbol = callback_data.replace('portfolio_risk_metrics_', '')
                self.logger.info(f"Portfolio risk metrics button clicked for portfolio: {portfolio_symbol}")
                await self._handle_portfolio_risk_metrics_by_symbol(update, context, portfolio_symbol)
            elif callback_data.startswith('risk_metrics_'):
                symbols = callback_data.replace('risk_metrics_', '').split(',')
                self.logger.info(f"Risk metrics button clicked for symbols: {symbols}")
                await self._handle_risk_metrics_button(update, context, symbols)
            elif callback_data.startswith('portfolio_monte_carlo_'):
                portfolio_symbol = callback_data.replace('portfolio_monte_carlo_', '')
                self.logger.info(f"Portfolio monte carlo button clicked for portfolio: {portfolio_symbol}")
                await self._handle_portfolio_monte_carlo_by_symbol(update, context, portfolio_symbol)
            elif callback_data.startswith('monte_carlo_'):
                symbols = callback_data.replace('monte_carlo_', '').split(',')
                self.logger.info(f"Monte Carlo button clicked for symbols: {symbols}")
                await self._handle_monte_carlo_button(update, context, symbols)
            elif callback_data.startswith('portfolio_forecast_'):
                portfolio_symbol = callback_data.replace('portfolio_forecast_', '')
                self.logger.info(f"Portfolio forecast button clicked for portfolio: {portfolio_symbol}")
                await self._handle_portfolio_forecast_by_symbol(update, context, portfolio_symbol)
            elif callback_data.startswith('forecast_'):
                symbols = callback_data.replace('forecast_', '').split(',')
                self.logger.info(f"Forecast button clicked for symbols: {symbols}")
                await self._handle_forecast_button(update, context, symbols)

            elif callback_data.startswith('portfolio_wealth_chart_'):
                portfolio_symbol = callback_data.replace('portfolio_wealth_chart_', '')
                self.logger.info(f"Portfolio wealth chart button clicked for portfolio: {portfolio_symbol}")
                await self._handle_portfolio_wealth_chart_by_symbol(update, context, portfolio_symbol)
            elif callback_data.startswith('wealth_chart_'):
                symbols = callback_data.replace('wealth_chart_', '').split(',')
                self.logger.info(f"Wealth chart button clicked for symbols: {symbols}")
                self.logger.info(f"Callback data: '{callback_data}'")
                self.logger.info(f"Parsed symbols: {[f"'{s}'" for s in symbols]}")
                self.logger.info(f"Symbol types: {[type(s) for s in symbols]}")
                self.logger.info(f"Symbol lengths: {[len(str(s)) if s else 'None' for s in symbols]}")
                await self._handle_portfolio_wealth_chart_button(update, context, symbols)
            elif callback_data.startswith('portfolio_returns_'):
                portfolio_symbol = callback_data.replace('portfolio_returns_', '')
                self.logger.info(f"Portfolio returns button clicked for portfolio: {portfolio_symbol}")
                await self._handle_portfolio_returns_by_symbol(update, context, portfolio_symbol)
            elif callback_data.startswith('returns_'):
                symbols = callback_data.replace('returns_', '').split(',')
                self.logger.info(f"Returns button clicked for symbols: {symbols}")
                await self._handle_portfolio_returns_button(update, context, symbols)
            elif callback_data.startswith('portfolio_rolling_cagr_'):
                portfolio_symbol = callback_data.replace('portfolio_rolling_cagr_', '')
                self.logger.info(f"Portfolio rolling CAGR button clicked for portfolio: {portfolio_symbol}")
                await self._handle_portfolio_rolling_cagr_by_symbol(update, context, portfolio_symbol)
            elif callback_data.startswith('rolling_cagr_'):
                symbols = callback_data.replace('rolling_cagr_', '').split(',')
                self.logger.info(f"Rolling CAGR button clicked for symbols: {symbols}")
                await self._handle_portfolio_rolling_cagr_button(update, context, symbols)
            elif callback_data.startswith('portfolio_compare_assets_'):
                portfolio_symbol = callback_data.replace('portfolio_compare_assets_', '')
                self.logger.info(f"Portfolio compare assets button clicked for portfolio: {portfolio_symbol}")
                await self._handle_portfolio_compare_assets_by_symbol(update, context, portfolio_symbol)
            elif callback_data.startswith('portfolio_drawdowns_'):
                portfolio_symbol = callback_data.replace('portfolio_drawdowns_', '')
                self.logger.info(f"Portfolio drawdowns button clicked for portfolio: {portfolio_symbol}")
                await self._handle_portfolio_drawdowns_by_symbol(update, context, portfolio_symbol)
            elif callback_data.startswith('compare_assets_'):
                symbols = callback_data.replace('compare_assets_', '').split(',')
                self.logger.info(f"Compare assets button clicked for symbols: {symbols}")
                await self._handle_portfolio_compare_assets_button(update, context, symbols)
            elif callback_data == 'clear_all_portfolios':
                self.logger.info("Clear all portfolios button clicked")
                await self._handle_clear_all_portfolios_button(update, context)
            elif callback_data == 'compare_risk_return':
                self.logger.info("Compare Risk / Return button clicked")
                await self._handle_risk_return_compare_button(update, context)
            elif callback_data == 'risk_return_compare':
                self.logger.info("Risk / Return button clicked")
                await self._handle_risk_return_compare_button(update, context)
            elif callback_data == 'chart_analysis_compare':
                self.logger.info("Chart analysis button clicked")
                await self._handle_chart_analysis_compare_button(update, context)
            elif callback_data == 'data_analysis_compare':
                self.logger.info("Data analysis button clicked")
                await self._handle_data_analysis_compare_button(update, context)
            elif callback_data.startswith('namespace_'):
                namespace = callback_data.replace('namespace_', '')
                self.logger.info(f"Namespace button clicked for: {namespace}")
                await self._handle_namespace_button(update, context, namespace)
            elif callback_data.startswith('excel_namespace_'):
                namespace = callback_data.replace('excel_namespace_', '')
                self.logger.info(f"Excel namespace button clicked for: {namespace}")
                await self._handle_excel_namespace_button(update, context, namespace)
            elif callback_data == 'utility_clear_portfolios':
                self.logger.info("Utility clear portfolios button clicked")
                await self._handle_clear_all_portfolios_button(update, context)
            elif callback_data == 'clear_all_portfolios':
                self.logger.info("Clear all portfolios button clicked")
                await self._handle_clear_all_portfolios_button(update, context)
            else:
                self.logger.warning(f"Unknown button callback: {callback_data}")
                await self._send_callback_message(update, context, "❌ Неизвестная кнопка")
                
        except Exception as e:
            self.logger.error(f"Error in button callback: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при обработке кнопки: {str(e)}")

    async def _handle_risk_return_compare_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Risk / Return (CAGR) button for all comparison types"""
        try:
            user_id = update.effective_user.id
            user_context = self._get_user_context(user_id)
            symbols = user_context.get('current_symbols', [])
            display_symbols = user_context.get('display_symbols', symbols)  # Use descriptive names for display
            currency = user_context.get('current_currency', 'USD')
            expanded_symbols = user_context.get('expanded_symbols', [])
            portfolio_contexts = user_context.get('portfolio_contexts', [])

            # Validate that we have symbols to compare
            if not expanded_symbols:
                await self._send_callback_message(update, context, "ℹ️ Нет данных для сравнения. Выполните команду /compare заново.")
                return

            await self._send_callback_message(update, context, "📊 Создаю график Risk / Return (CAGR)…")

            # Prepare assets for comparison
            asset_list_items = []
            asset_names = []
            
            # Use display_symbols for proper naming - they already contain descriptive names
            for i, symbol in enumerate(symbols):
                if i < len(expanded_symbols):
                    if isinstance(expanded_symbols[i], (pd.Series, pd.DataFrame)):
                        # This is a portfolio - recreate it
                        if i < len(portfolio_contexts):
                            pctx = portfolio_contexts[i]
                            try:
                                p = ok.Portfolio(
                                    pctx.get('portfolio_symbols', []),
                                    weights=pctx.get('portfolio_weights', []),
                                    ccy=pctx.get('portfolio_currency') or currency,
                                )
                                asset_list_items.append(p)
                                asset_names.append(display_symbols[i])  # Use descriptive name
                            except Exception as pe:
                                self.logger.warning(f"Failed to recreate portfolio for Risk/Return: {pe}")
                    else:
                        # This is a regular asset
                        asset_list_items.append(symbol)
                        asset_names.append(display_symbols[i])  # Use descriptive name

            if not asset_list_items:
                await self._send_callback_message(update, context, "❌ Не удалось подготовить активы для построения графика")
                return

            # Create AssetList with selected assets/portfolios
            img_buffer = None
            try:
                asset_list = ok.AssetList(asset_list_items, ccy=currency)
                
                # okama plotting
                asset_list.plot_assets(kind="cagr")
                current_fig = plt.gcf()
                
                # Apply styling
                if current_fig.axes:
                    ax = current_fig.axes[0]
                    chart_styles.apply_styling(
                        ax,
                        title=f"Risk / Return: CAGR\n{', '.join(asset_names)}",
                        ylabel='CAGR (%)',
                        grid=True,
                        legend=True,
                        copyright=True
                    )
                img_buffer = io.BytesIO()
                chart_styles.save_figure(current_fig, img_buffer)
                img_buffer.seek(0)
                chart_styles.cleanup_figure(current_fig)
            except Exception as plot_error:
                # Fallback: compute CAGR manually and plot as bar chart
                self.logger.warning(f"Risk/Return okama plot failed, falling back to manual bar: {plot_error}")
                try:
                    cagr_values = {}
                    
                    # Calculate CAGR for each asset
                    for i, asset in enumerate(asset_list_items):
                        asset_name = asset_names[i]
                        try:
                            if isinstance(asset, str):
                                # Individual asset
                                asset_obj = ok.Asset(asset)
                                cagr = asset_obj.get_cagr()
                            else:
                                # Portfolio
                                cagr = asset.get_cagr()
                            
                            if hasattr(cagr, 'iloc'):
                                cagr_val = float(cagr.iloc[0])
                            elif hasattr(cagr, '__iter__') and not isinstance(cagr, str):
                                cagr_val = float(list(cagr)[0])
                            else:
                                cagr_val = float(cagr)
                        except Exception:
                            # Manual CAGR calculation
                            try:
                                if isinstance(asset, str):
                                    asset_obj = ok.Asset(asset)
                                    wealth_index = asset_obj.wealth_index
                                else:
                                    wealth_index = asset.wealth_index
                                
                                wi = wealth_index.dropna()
                                periods = len(wi)
                                cagr_val = ((wi.iloc[-1] / wi.iloc[0]) ** (12.0 / max(periods, 1))) - 1 if periods > 1 else 0.0
                            except Exception:
                                cagr_val = 0.0
                        
                        cagr_values[asset_name] = cagr_val

                    cagr_df = pd.DataFrame.from_dict(cagr_values, orient='index')
                    cagr_df.columns = ['CAGR']
                    fig, ax = chart_styles.create_bar_chart(
                        cagr_df['CAGR'],
                        title=f"Risk / Return: CAGR\n{', '.join(asset_names)}",
                        ylabel='CAGR (%)'
                    )
                    img_buffer = io.BytesIO()
                    chart_styles.save_figure(fig, img_buffer)
                    img_buffer.seek(0)
                    chart_styles.cleanup_figure(fig)
                except Exception as fallback_error:
                    self.logger.error(f"Risk/Return manual bar failed: {fallback_error}")
                    await self._send_callback_message(update, context, "❌ Не удалось построить график Risk / Return (CAGR)")
                    return

            # Send image
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(f"📊 Risk / Return (CAGR) для сравнения: {', '.join(asset_names)}")
            )

        except Exception as e:
            self.logger.error(f"Error handling Risk / Return button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при построении Risk / Return: {str(e)}")

    async def _handle_chart_analysis_compare_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle chart analysis button click for comparison charts"""
        try:
            user_id = update.effective_user.id
            user_context = self._get_user_context(user_id)
            symbols = user_context.get('current_symbols', [])
            display_symbols = user_context.get('display_symbols', symbols)  # Use descriptive names for display
            currency = user_context.get('current_currency', 'USD')
            expanded_symbols = user_context.get('expanded_symbols', [])
            portfolio_contexts = user_context.get('portfolio_contexts', [])

            # Validate that we have symbols to compare
            if not expanded_symbols:
                await self._send_callback_message(update, context, "ℹ️ Нет данных для сравнения. Выполните команду /compare заново.")
                return

            # Check if Gemini service is available
            if not self.gemini_service or not self.gemini_service.is_available():
                await self._send_callback_message(update, context, "❌ Сервис анализа графиков недоступен. Проверьте настройки Gemini API.", parse_mode='Markdown')
                return

            await self._send_callback_message(update, context, "Анализ графика с помощью AI...", parse_mode='Markdown')

            # Recreate the comparison chart for analysis
            try:
                # Prepare assets for comparison
                asset_list_items = []
                asset_names = []
                
                # Use display_symbols for proper naming - they already contain descriptive names
                for i, symbol in enumerate(symbols):
                    if i < len(expanded_symbols):
                        if isinstance(expanded_symbols[i], (pd.Series, pd.DataFrame)):
                            # This is a portfolio - recreate it
                            if i < len(portfolio_contexts):
                                pctx = portfolio_contexts[i]
                                try:
                                    p = ok.Portfolio(
                                        pctx.get('portfolio_symbols', []),
                                        weights=pctx.get('portfolio_weights', []),
                                        ccy=pctx.get('portfolio_currency') or currency,
                                    )
                                    asset_list_items.append(p)
                                    asset_names.append(display_symbols[i])  # Use descriptive name
                                except Exception as pe:
                                    self.logger.warning(f"Failed to recreate portfolio for analysis: {pe}")
                        else:
                            # This is a regular asset
                            asset_list_items.append(symbol)
                            asset_names.append(display_symbols[i])  # Use descriptive name

                if not asset_list_items:
                    await self._send_callback_message(update, context, "❌ Не удалось подготовить активы для анализа", parse_mode='Markdown')
                    return

                # Create comparison
                comparison = ok.AssetList(asset_list_items, ccy=currency)
                
                # Create comparison chart
                fig, ax = chart_styles.create_comparison_chart(
                    comparison.wealth_indexes, symbols, currency
                )
                
                # Save chart to bytes
                img_buffer = io.BytesIO()
                chart_styles.save_figure(fig, img_buffer)
                img_buffer.seek(0)
                img_bytes = img_buffer.getvalue()
                
                # Clear matplotlib cache
                chart_styles.cleanup_figure(fig)
                
                # Analyze chart with Gemini API
                chart_analysis = self.gemini_service.analyze_chart(img_bytes)
                
                if chart_analysis and chart_analysis.get('success'):
                    # Format detailed analysis
                    analysis_text = "🤖 **Анализ графика**\n\n"
                    
                    # Add full analysis from Gemini
                    full_analysis = chart_analysis.get('full_analysis', '')
                    if full_analysis:
                        analysis_text += full_analysis
                    
                    # Gemini provides comprehensive analysis, no need for additional sections
                    
                    analysis_text += f"🔍 **Анализируемые активы:** {', '.join(symbols)}\n"
                    analysis_text += f"💰 **Валюта:** {currency}\n"
                    analysis_text += f"📅 **Период:** полный доступный период данных"
                    
                    await self._send_callback_message(update, context, analysis_text, parse_mode='Markdown')
                    
                else:
                    error_msg = chart_analysis.get('error', 'Неизвестная ошибка') if chart_analysis else 'Анализ не выполнен'
                    await self._send_callback_message(update, context, f"❌ Ошибка анализа графика: {error_msg}", parse_mode='Markdown')
                    
            except Exception as chart_error:
                self.logger.error(f"Error creating chart for analysis: {chart_error}")
                await self._send_callback_message(update, context, f"❌ Ошибка при создании графика для анализа: {str(chart_error)}", parse_mode='Markdown')

        except Exception as e:
            self.logger.error(f"Error handling chart analysis button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при анализе графика: {str(e)}", parse_mode='Markdown')

    async def _handle_data_analysis_compare_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle data analysis button click for comparison charts"""
        try:
            user_id = update.effective_user.id
            user_context = self._get_user_context(user_id)
            symbols = user_context.get('current_symbols', [])
            currency = user_context.get('current_currency', 'USD')
            expanded_symbols = user_context.get('expanded_symbols', [])
            portfolio_contexts = user_context.get('portfolio_contexts', [])

            # Validate that we have symbols to compare
            if not expanded_symbols:
                await self._send_callback_message(update, context, "ℹ️ Нет данных для сравнения. Выполните команду /compare заново.")
                return

            # Check if Gemini service is available
            if not self.gemini_service or not self.gemini_service.is_available():
                await self._send_callback_message(update, context, "❌ Сервис анализа данных недоступен. Проверьте настройки Gemini API.", parse_mode='Markdown')
                return

            await self._send_callback_message(update, context, "🤖 Анализирую данные с помощью Gemini AI...", parse_mode='Markdown')

            # Prepare data for analysis
            try:
                data_info = await self._prepare_data_for_analysis(symbols, currency, expanded_symbols, portfolio_contexts, user_id)
                
                # Analyze data with Gemini
                data_analysis = self.gemini_service.analyze_data(data_info)
                
                if data_analysis and data_analysis.get('success'):
                    analysis_text = data_analysis.get('analysis', '')
                    
                    if analysis_text:
                        analysis_text += f"\n\n🔍 **Анализируемые активы:** {', '.join(symbols)}\n"
                        analysis_text += f"💰 **Валюта:** {currency}\n"
                        analysis_text += f"📅 **Период:** полный доступный период данных\n"
                        analysis_text += f"📊 **Тип анализа:** Данные (не изображение)"
                        
                        await self._send_callback_message(update, context, analysis_text, parse_mode='Markdown')
                    else:
                        await self._send_callback_message(update, context, "🤖 Анализ данных выполнен, но результат пуст", parse_mode='Markdown')
                        
                else:
                    error_msg = data_analysis.get('error', 'Неизвестная ошибка') if data_analysis else 'Анализ не выполнен'
                    await self._send_callback_message(update, context, f"❌ Ошибка анализа данных: {error_msg}", parse_mode='Markdown')
                    
            except Exception as data_error:
                self.logger.error(f"Error preparing data for analysis: {data_error}")
                await self._send_callback_message(update, context, f"❌ Ошибка при подготовке данных для анализа: {str(data_error)}", parse_mode='Markdown')

        except Exception as e:
            self.logger.error(f"Error handling data analysis button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при анализе данных: {str(e)}", parse_mode='Markdown')

    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def _prepare_data_for_analysis(self, symbols: list, currency: str, expanded_symbols: list, portfolio_contexts: list, user_id: int) -> Dict[str, Any]:
        """Prepare comprehensive financial data for Gemini analysis"""
        try:
            # Get user context to access describe table
            describe_table = ""
            if user_id:
                user_context = self._get_user_context(user_id)
                describe_table = user_context.get('describe_table', '')
            
            data_info = {
                'symbols': symbols,
                'currency': currency,
                'period': 'полный доступный период данных',
                'performance': {},
                'correlations': [],
                'additional_info': '',
                'describe_table': describe_table,
                'asset_count': len(symbols),
                'analysis_type': 'asset_comparison'
            }
            
            # Calculate detailed performance metrics for each symbol
            for i, symbol in enumerate(symbols):
                try:
                    if i < len(expanded_symbols):
                        asset_data = expanded_symbols[i]
                        
                        # Get comprehensive performance metrics
                        performance_metrics = {}
                        
                        # Calculate metrics from price data
                        try:
                            # Get price data for calculations
                            if hasattr(asset_data, 'close_monthly') and asset_data.close_monthly is not None:
                                prices = asset_data.close_monthly
                            elif hasattr(asset_data, 'close_daily') and asset_data.close_daily is not None:
                                prices = asset_data.close_daily
                            elif hasattr(asset_data, 'adj_close') and asset_data.adj_close is not None:
                                prices = asset_data.adj_close
                            else:
                                prices = None
                            
                            if prices is not None and len(prices) > 1:
                                # Calculate returns from prices
                                returns = prices.pct_change().dropna()
                                
                                # Basic metrics
                                if hasattr(asset_data, 'total_return'):
                                    performance_metrics['total_return'] = asset_data.total_return
                                else:
                                    # Calculate total return from first and last price
                                    total_return = (prices.iloc[-1] / prices.iloc[0]) - 1
                                    performance_metrics['total_return'] = total_return
                                
                                # Annual return (CAGR)
                                if hasattr(asset_data, 'annual_return'):
                                    performance_metrics['annual_return'] = asset_data.annual_return
                                else:
                                    # Calculate CAGR
                                    periods = len(prices)
                                    years = periods / 12.0  # Assuming monthly data
                                    if years > 0:
                                        cagr = ((prices.iloc[-1] / prices.iloc[0]) ** (1.0 / years)) - 1
                                        performance_metrics['annual_return'] = cagr
                                    else:
                                        performance_metrics['annual_return'] = 0.0
                                
                                # Volatility
                                if hasattr(asset_data, 'volatility'):
                                    performance_metrics['volatility'] = asset_data.volatility
                                else:
                                    # Calculate annualized volatility
                                    volatility = returns.std() * (12 ** 0.5)  # Annualized for monthly data
                                    performance_metrics['volatility'] = volatility
                                
                                # Max drawdown
                                if hasattr(asset_data, 'max_drawdown'):
                                    performance_metrics['max_drawdown'] = asset_data.max_drawdown
                                else:
                                    # Calculate max drawdown
                                    cumulative = (1 + returns).cumprod()
                                    running_max = cumulative.expanding().max()
                                    drawdown = (cumulative - running_max) / running_max
                                    max_drawdown = drawdown.min()
                                    performance_metrics['max_drawdown'] = max_drawdown
                                
                                # Store returns for Sortino calculation
                                performance_metrics['_returns'] = returns
                                
                            else:
                                # Fallback values if no price data
                                performance_metrics['total_return'] = 0.0
                                performance_metrics['annual_return'] = 0.0
                                performance_metrics['volatility'] = 0.0
                                performance_metrics['max_drawdown'] = 0.0
                                performance_metrics['_returns'] = None
                        
                        except Exception as e:
                            self.logger.warning(f"Failed to calculate basic metrics for {symbol}: {e}")
                            performance_metrics['total_return'] = 0.0
                            performance_metrics['annual_return'] = 0.0
                            performance_metrics['volatility'] = 0.0
                            performance_metrics['max_drawdown'] = 0.0
                            performance_metrics['_returns'] = None
                        
                        # Sharpe ratio calculation
                        try:
                            if hasattr(asset_data, 'get_sharpe_ratio'):
                                sharpe_ratio = asset_data.get_sharpe_ratio(rf_return=0.02)
                                performance_metrics['sharpe_ratio'] = float(sharpe_ratio)
                            elif hasattr(asset_data, 'sharpe_ratio'):
                                performance_metrics['sharpe_ratio'] = asset_data.sharpe_ratio
                            else:
                                # Manual Sharpe ratio calculation
                                annual_return = performance_metrics.get('annual_return', 0)
                                volatility = performance_metrics.get('volatility', 0)
                                if volatility > 0:
                                    sharpe_ratio = (annual_return - 0.02) / volatility
                                    performance_metrics['sharpe_ratio'] = sharpe_ratio
                                else:
                                    performance_metrics['sharpe_ratio'] = 0.0
                        except Exception as e:
                            self.logger.warning(f"Failed to calculate Sharpe ratio for {symbol}: {e}")
                            performance_metrics['sharpe_ratio'] = 0.0
                        
                        # Sortino ratio calculation
                        try:
                            if hasattr(asset_data, 'sortino_ratio'):
                                performance_metrics['sortino_ratio'] = asset_data.sortino_ratio
                            else:
                                # Manual Sortino ratio calculation
                                annual_return = performance_metrics.get('annual_return', 0)
                                returns = performance_metrics.get('_returns')
                                
                                if returns is not None and len(returns) > 0:
                                    # Calculate downside deviation (only negative returns)
                                    negative_returns = returns[returns < 0]
                                    if len(negative_returns) > 0:
                                        downside_deviation = negative_returns.std() * (12 ** 0.5)  # Annualized
                                        if downside_deviation > 0:
                                            sortino_ratio = (annual_return - 0.02) / downside_deviation
                                            performance_metrics['sortino_ratio'] = sortino_ratio
                                        else:
                                            performance_metrics['sortino_ratio'] = 0.0
                                    else:
                                        # No negative returns, use volatility as fallback
                                        volatility = performance_metrics.get('volatility', 0)
                                        if volatility > 0:
                                            sortino_ratio = (annual_return - 0.02) / volatility
                                            performance_metrics['sortino_ratio'] = sortino_ratio
                                        else:
                                            performance_metrics['sortino_ratio'] = 0.0
                                else:
                                    # Fallback to Sharpe ratio if no returns data
                                    performance_metrics['sortino_ratio'] = performance_metrics.get('sharpe_ratio', 0.0)
                        except Exception as e:
                            self.logger.warning(f"Failed to calculate Sortino ratio for {symbol}: {e}")
                            performance_metrics['sortino_ratio'] = 0.0
                        
                        # Clean up temporary data
                        if '_returns' in performance_metrics:
                            del performance_metrics['_returns']
                        
                        # Additional metrics if available
                        if hasattr(asset_data, 'calmar_ratio'):
                            performance_metrics['calmar_ratio'] = asset_data.calmar_ratio
                        if hasattr(asset_data, 'var_95'):
                            performance_metrics['var_95'] = asset_data.var_95
                        if hasattr(asset_data, 'cvar_95'):
                            performance_metrics['cvar_95'] = asset_data.cvar_95
                        
                        data_info['performance'][symbol] = performance_metrics
                        
                    else:
                        # Fallback for missing data
                        data_info['performance'][symbol] = {
                            'total_return': 0,
                            'annual_return': 0,
                            'volatility': 0,
                            'sharpe_ratio': 0,
                            'sortino_ratio': 0,
                            'max_drawdown': 0
                        }
                        
                except Exception as e:
                    self.logger.warning(f"Failed to get performance metrics for {symbol}: {e}")
                    data_info['performance'][symbol] = {
                        'total_return': 0,
                        'annual_return': 0,
                        'volatility': 0,
                        'sharpe_ratio': 0,
                        'sortino_ratio': 0,
                        'max_drawdown': 0
                    }
            
            # Calculate correlation matrix if we have multiple assets
            if len(expanded_symbols) > 1:
                try:
                    # Try to get actual correlation data from okama
                    correlation_matrix = []
                    
                    # Check if we can get correlation from the first asset
                    if hasattr(expanded_symbols[0], 'correlation_matrix'):
                        correlation_matrix = expanded_symbols[0].correlation_matrix.tolist()
                    else:
                        # Create a simple correlation matrix as fallback
                        for i in range(len(symbols)):
                            row = []
                            for j in range(len(symbols)):
                                if i == j:
                                    row.append(1.0)
                                else:
                                    # Estimate correlation based on asset types
                                    row.append(0.3)  # Conservative estimate
                            correlation_matrix.append(row)
                    
                    data_info['correlations'] = correlation_matrix
                    
                except Exception as e:
                    self.logger.warning(f"Failed to calculate correlations: {e}")
                    # Create identity matrix as fallback
                    correlation_matrix = []
                    for i in range(len(symbols)):
                        row = []
                        for j in range(len(symbols)):
                            row.append(1.0 if i == j else 0.0)
                        correlation_matrix.append(row)
                    data_info['correlations'] = correlation_matrix
            
            # Add portfolio context information
            if portfolio_contexts:
                portfolio_info = []
                for pctx in portfolio_contexts:
                    portfolio_info.append(f"Портфель {pctx.get('symbol', 'Unknown')}: {len(pctx.get('portfolio_symbols', []))} активов")
                data_info['additional_info'] = f"Включает портфели: {'; '.join(portfolio_info)}"
            
            # Add analysis metadata
            data_info['analysis_metadata'] = {
                'timestamp': self._get_current_timestamp(),
                'data_source': 'okama.AssetList.describe()',
                'analysis_depth': 'comprehensive',
                'includes_correlations': len(data_info['correlations']) > 0,
                'includes_describe_table': bool(describe_table)
            }
            
            return data_info
            
        except Exception as e:
            self.logger.error(f"Error preparing data for analysis: {e}")
            return {
                'symbols': symbols,
                'currency': currency,
                'period': 'полный доступный период данных',
                'performance': {},
                'correlations': [],
                'additional_info': f'Ошибка подготовки данных: {str(e)}',
                'describe_table': '',
                'asset_count': len(symbols),
                'analysis_type': 'asset_comparison',
                'analysis_metadata': {
                    'timestamp': self._get_current_timestamp(),
                    'data_source': 'error_fallback',
                    'analysis_depth': 'basic',
                    'includes_correlations': False,
                    'includes_describe_table': False
                }
            }

    async def _handle_drawdowns_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle drawdowns button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling drawdowns button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            
            if 'current_symbols' not in user_context:
                self.logger.warning(f"current_symbols not found in user context for user {user_id}")
                await self._send_callback_message(update, context, "❌ Данные о сравнении не найдены. Выполните команду /compare заново.")
                return
            
            symbols = user_context['current_symbols']
            currency = user_context.get('current_currency', 'USD')
            
            self.logger.info(f"Creating drawdowns chart for symbols: {symbols}, currency: {currency}")
            await self._send_callback_message(update, context, "📉 Создаю график drawdowns...")
            
            # Check if this is a mixed comparison (portfolios + assets)
            user_context = self._get_user_context(user_id)
            last_analysis_type = user_context.get('last_analysis_type', 'comparison')
            expanded_symbols = user_context.get('expanded_symbols', [])
            
            if last_analysis_type == 'comparison' and any(isinstance(s, (pd.Series, pd.DataFrame)) for s in expanded_symbols):
                # This is a mixed comparison, handle differently
                await self._send_callback_message(update, context, "📉 Создаю график drawdowns для смешанного сравнения...")
                await self._create_mixed_comparison_drawdowns_chart(update, context, symbols, currency)
            else:
                # Regular comparison, create AssetList
                asset_list = ok.AssetList(symbols, ccy=currency)
                await self._create_drawdowns_chart(update, context, asset_list, symbols, currency)
        
        except Exception as e:
            self.logger.error(f"Error handling drawdowns button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика drawdowns: {str(e)}")

    async def _create_mixed_comparison_drawdowns_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list, currency: str):
        """Create drawdowns chart for mixed comparison (portfolios + assets)"""
        try:
            self.logger.info(f"Creating mixed comparison drawdowns chart for symbols: {symbols}")
            
            # Get user context to restore portfolio information
            user_id = update.effective_user.id
            user_context = self._get_user_context(user_id)
            portfolio_contexts = user_context.get('portfolio_contexts', [])
            expanded_symbols = user_context.get('expanded_symbols', [])
            
            # Separate portfolios and individual assets using expanded_symbols
            portfolio_data = []
            asset_symbols = []
            
            for i, expanded_symbol in enumerate(expanded_symbols):
                if isinstance(expanded_symbol, (pd.Series, pd.DataFrame)):
                    # This is a portfolio wealth index
                    portfolio_data.append(expanded_symbol)
                else:
                    # This is an individual asset symbol
                    asset_symbols.append(expanded_symbol)
            
            # Calculate drawdowns for all items
            drawdowns_data = {}
            
            # Process portfolios separately to avoid AssetList creation issues
            for i, portfolio_context in enumerate(portfolio_contexts):
                if i < len(portfolio_data):
                    try:
                        self.logger.info(f"Processing portfolio {i} for drawdowns")
                        
                        # Get portfolio details from context
                        assets = portfolio_context.get('portfolio_symbols', [])
                        weights = portfolio_context.get('portfolio_weights', [])
                        symbol = portfolio_context.get('symbol', f'Portfolio_{i+1}')
                        
                        if assets and weights and len(assets) == len(weights):
                            self.logger.info(f"Portfolio {i} assets: {assets}, weights: {weights}")
                            
                            # Create portfolio using ok.Portfolio
                            import okama as ok
                            portfolio = ok.Portfolio(
                                assets=assets,
                                weights=weights,
                                rebalancing_strategy=ok.Rebalance(period="year"),
                                symbol=symbol
                            )
                            
                            # Calculate drawdowns for portfolio
                            wealth_series = portfolio.wealth_index
                            self.logger.info(f"Portfolio {symbol} wealth_series length: {len(wealth_series)}, dtype: {wealth_series.dtype}")
                            
                            returns = wealth_series.pct_change().dropna()
                            if len(returns) > 0:
                                cumulative = (1 + returns).cumprod()
                                running_max = cumulative.expanding().max()
                                drawdowns = (cumulative - running_max) / running_max
                                drawdowns_data[symbol] = drawdowns
                                self.logger.info(f"Successfully created drawdowns for {symbol}: {len(drawdowns)} points")
                            else:
                                self.logger.warning(f"Portfolio {symbol}: No returns data after pct_change")
                        else:
                            self.logger.warning(f"Portfolio {i} missing valid assets/weights data")
                    except Exception as portfolio_error:
                        self.logger.warning(f"Could not process portfolio {i}: {portfolio_error}")
                        continue
            
            # Process individual assets separately
            if asset_symbols:
                try:
                    asset_asset_list = ok.AssetList(asset_symbols, ccy=currency)
                    
                    for symbol in asset_symbols:
                        if symbol in asset_asset_list.wealth_indexes.columns:
                            # Calculate drawdowns for individual asset
                            wealth_series = asset_asset_list.wealth_indexes[symbol]
                            self.logger.info(f"Asset {symbol} wealth_series length: {len(wealth_series)}, dtype: {wealth_series.dtype}")
                            
                            returns = wealth_series.pct_change().dropna()
                            if len(returns) > 0:
                                cumulative = (1 + returns).cumprod()
                                running_max = cumulative.expanding().max()
                                drawdowns = (cumulative - running_max) / running_max
                                drawdowns_data[symbol] = drawdowns
                                self.logger.info(f"Successfully created drawdowns for {symbol}: {len(drawdowns)} points")
                            else:
                                self.logger.warning(f"Asset {symbol}: No returns data after pct_change")
                        else:
                            self.logger.warning(f"Asset {symbol} not found in wealth_indexes columns")
                except Exception as asset_error:
                    self.logger.warning(f"Could not process individual assets: {asset_error}")
            
            if not drawdowns_data:
                await self._send_callback_message(update, context, "❌ Не удалось создать данные для графика просадок")
                return
            
            # Create chart using chart_styles
            try:
                # Combine all drawdowns into a DataFrame
                drawdowns_df = pd.DataFrame(drawdowns_data)
                
                fig, ax = chart_styles.create_drawdowns_chart(
                    drawdowns_df, list(drawdowns_data.keys()), currency
                )
                
                # Save chart to bytes with memory optimization
                img_buffer = io.BytesIO()
                chart_styles.save_figure(fig, img_buffer)
                img_buffer.seek(0)
                img_bytes = img_buffer.getvalue()
                
                # Clear matplotlib cache to free memory
                chart_styles.cleanup_figure(fig)
                
                # Send drawdowns chart
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id, 
                    photo=io.BytesIO(img_bytes),
                    caption=self._truncate_caption(f"📉 График просадок для смешанного сравнения\n\nПоказывает просадки портфелей и активов")
                )
                
            except Exception as chart_error:
                self.logger.error(f"Error creating drawdowns chart: {chart_error}")
                await self._send_callback_message(update, context, f"❌ Ошибка при создании графика просадок: {str(chart_error)}")
                
        except Exception as e:
            self.logger.error(f"Error in mixed comparison drawdowns chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика просадок: {str(e)}")
            
            if not drawdowns_data:
                await self._send_callback_message(update, context, "❌ Не удалось создать данные для графика просадок")
                return
            
            # Clean drawdowns data to handle Period indices
            cleaned_drawdowns_data = {}
            for key, series in drawdowns_data.items():
                if isinstance(series, pd.Series):
                    # Convert Period index to datetime if needed
                    if hasattr(series.index, 'dtype') and str(series.index.dtype).startswith('period'):
                        series.index = series.index.to_timestamp()
                    cleaned_drawdowns_data[key] = series
            
            # Create drawdowns chart
            fig, ax = chart_styles.create_drawdowns_chart(
                data=pd.DataFrame(cleaned_drawdowns_data),
                symbols=list(cleaned_drawdowns_data.keys()),
                ccy=currency
            )
            
            # Save chart
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            img_buffer.seek(0)
            
            # Clear matplotlib cache
            chart_styles.cleanup_figure(fig)
            
            # Create caption
            portfolio_count = len(portfolio_data)
            asset_count = len(asset_symbols)
            
            # Get portfolio names from context
            portfolio_names = []
            for i, portfolio_series in enumerate(portfolio_data):
                if i < len(portfolio_contexts):
                    portfolio_names.append(portfolio_contexts[i]['symbol'])
                else:
                    portfolio_names.append(f'Portfolio_{i+1}')
            
            caption = f"📉 Просадки смешанного сравнения\n\n"
            caption += f"📊 Состав:\n"
            if portfolio_count > 0:
                caption += f"• Портфели: {', '.join(portfolio_names)}\n"
            if asset_count > 0:
                caption += f"• Индивидуальные активы: {', '.join(asset_symbols)}\n"
            caption += f"• Валюта: {currency}\n\n"
            caption += f"💡 График показывает:\n"
            caption += f"• Просадки портфелей и активов\n"
            caption += f"• Сравнение рисков\n"
            caption += f"• Периоды восстановления"
            
            # Send chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(caption)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating mixed comparison drawdowns chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика просадок: {str(e)}")

    async def _handle_dividends_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle dividends button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling dividends button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            
            if 'current_symbols' not in user_context:
                self.logger.warning(f"current_symbols not found in user context for user {user_id}")
                await self._send_callback_message(update, context, "❌ Данные о сравнении не найдены. Выполните команду /compare заново.")
                return
            
            symbols = user_context['current_symbols']
            currency = user_context.get('current_currency', 'USD')
            
            self.logger.info(f"Creating dividends chart for symbols: {symbols}, currency: {currency}")
            await self._send_callback_message(update, context, "💰 Создаю график дивидендной доходности...")
            
            # Check if this is a mixed comparison (portfolios + assets)
            user_context = self._get_user_context(user_id)
            last_analysis_type = user_context.get('last_analysis_type', 'comparison')
            expanded_symbols = user_context.get('expanded_symbols', [])
            
            if last_analysis_type == 'comparison' and any(isinstance(s, (pd.Series, pd.DataFrame)) for s in expanded_symbols):
                # This is a mixed comparison, handle differently
                await self._send_callback_message(update, context, "💰 Создаю график дивидендной доходности для смешанного сравнения...")
                await self._create_mixed_comparison_dividends_chart(update, context, symbols, currency)
            else:
                # Regular comparison, create AssetList
                asset_list = ok.AssetList(symbols, ccy=currency)
                await self._create_dividend_yield_chart(update, context, asset_list, symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling dividends button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика дивидендной доходности: {str(e)}")

    async def _create_mixed_comparison_dividends_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list, currency: str):
        """Create dividends chart for mixed comparison (portfolios + assets)"""
        try:
            self.logger.info(f"Creating mixed comparison dividends chart for symbols: {symbols}")
            
            # Get user context to restore portfolio information
            user_id = update.effective_user.id
            user_context = self._get_user_context(user_id)
            portfolio_contexts = user_context.get('portfolio_contexts', [])
            expanded_symbols = user_context.get('expanded_symbols', [])
            
            # Separate portfolios and individual assets using expanded_symbols
            portfolio_data = []
            asset_symbols = []
            
            for i, expanded_symbol in enumerate(expanded_symbols):
                if isinstance(expanded_symbol, (pd.Series, pd.DataFrame)):
                    # This is a portfolio wealth index
                    portfolio_data.append(expanded_symbol)
                else:
                    # This is an individual asset symbol
                    asset_symbols.append(expanded_symbol)
            
            # Create dividends data for both portfolios and assets
            dividends_data = {}
            
            # Process portfolios separately to avoid AssetList creation issues
            for i, portfolio_context in enumerate(portfolio_contexts):
                if i < len(portfolio_data):
                    try:
                        self.logger.info(f"Processing portfolio {i} for dividends")
                        
                        # Get portfolio details from context
                        assets = portfolio_context.get('portfolio_symbols', [])
                        weights = portfolio_context.get('portfolio_weights', [])
                        symbol = portfolio_context.get('symbol', f'Portfolio_{i+1}')
                        
                        if assets and weights and len(assets) == len(weights):
                            self.logger.info(f"Portfolio {i} assets: {assets}, weights: {weights}")
                            
                            # Create separate AssetList for portfolio assets
                            try:
                                portfolio_asset_list = ok.AssetList(assets, ccy=currency)
                                
                                if hasattr(portfolio_asset_list, 'dividend_yields'):
                                    # Calculate weighted dividend yield
                                    total_dividend_yield = 0
                                    for asset, weight in zip(assets, weights):
                                        if asset in portfolio_asset_list.dividend_yields.columns:
                                            dividend_yield = portfolio_asset_list.dividend_yields[asset].iloc[-1] if not portfolio_asset_list.dividend_yields[asset].empty else 0
                                            total_dividend_yield += dividend_yield * weight
                                            self.logger.info(f"Asset {asset}: dividend_yield={dividend_yield}, weight={weight}")
                                        else:
                                            self.logger.warning(f"Asset {asset} not found in dividend_yields columns")
                                    
                                    dividends_data[symbol] = total_dividend_yield
                                    self.logger.info(f"Successfully calculated weighted dividend yield for {symbol}: {total_dividend_yield}")
                                else:
                                    self.logger.warning(f"Portfolio asset list does not have dividend_yields attribute for {symbol}")
                                    dividends_data[symbol] = 0  # Default value
                            except Exception as asset_list_error:
                                self.logger.warning(f"Could not create AssetList for portfolio {symbol}: {asset_list_error}")
                                dividends_data[symbol] = 0  # Default value
                        else:
                            self.logger.warning(f"Portfolio {symbol} missing valid assets/weights data for dividends")
                            dividends_data[symbol] = 0  # Default value
                    except Exception as portfolio_error:
                        self.logger.warning(f"Could not process portfolio {i} for dividends: {portfolio_error}")
                        dividends_data[symbol] = 0  # Default value
                        continue
            
            # Process individual assets separately
            if asset_symbols:
                try:
                    asset_asset_list = ok.AssetList(asset_symbols, ccy=currency)
                    
                    if hasattr(asset_asset_list, 'dividend_yields'):
                        for symbol in asset_symbols:
                            if symbol in asset_asset_list.dividend_yields.columns:
                                dividend_yield = asset_asset_list.dividend_yields[symbol].iloc[-1] if not asset_asset_list.dividend_yields[symbol].empty else 0
                                dividends_data[symbol] = dividend_yield
                                self.logger.info(f"Successfully got dividend yield for {symbol}: {dividend_yield}")
                            else:
                                self.logger.warning(f"Asset {symbol} not found in dividend_yields columns")
                                dividends_data[symbol] = 0  # Default value
                    else:
                        self.logger.warning("Asset list does not have dividend_yields attribute")
                        for symbol in asset_symbols:
                            dividends_data[symbol] = 0  # Default value
                except Exception as asset_error:
                    self.logger.warning(f"Could not process individual assets: {asset_error}")
                    for symbol in asset_symbols:
                        dividends_data[symbol] = 0  # Default value
            
            if not dividends_data:
                await self._send_callback_message(update, context, "❌ Не удалось создать данные для графика дивидендной доходности")
                return
            
            # Validate dividends data before creating chart
            valid_dividends_data = {}
            for symbol, dividend_yield in dividends_data.items():
                if dividend_yield is not None and not pd.isna(dividend_yield):
                    valid_dividends_data[symbol] = dividend_yield
                else:
                    self.logger.warning(f"Invalid dividend yield for {symbol}: {dividend_yield}")
                    valid_dividends_data[symbol] = 0  # Default to 0
            
            if not valid_dividends_data:
                await self._send_callback_message(update, context, "❌ Не удалось создать валидные данные для графика дивидендной доходности")
                return
            
            # Create chart using chart_styles
            try:
                # Convert Series to DataFrame for chart creation
                dividends_df = pd.DataFrame(valid_dividends_data, index=[0]).T
                fig, ax = chart_styles.create_dividend_yield_chart(
                    dividends_df, list(valid_dividends_data.keys())
                )
                
                # Save chart to bytes with memory optimization
                img_buffer = io.BytesIO()
                chart_styles.save_figure(fig, img_buffer)
                img_buffer.seek(0)
                img_bytes = img_buffer.getvalue()
                
                # Clear matplotlib cache to free memory
                chart_styles.cleanup_figure(fig)
                
                # Send dividend yield chart
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id, 
                    photo=io.BytesIO(img_bytes),
                    caption=self._truncate_caption(f"💰 График дивидендной доходности для смешанного сравнения\n\nПоказывает дивидендную доходность портфелей и активов")
                )
                
            except Exception as chart_error:
                self.logger.error(f"Error creating dividend yield chart: {chart_error}")
                await self._send_callback_message(update, context, f"❌ Ошибка при создании графика дивидендной доходности: {str(chart_error)}")
                
        except Exception as e:
            self.logger.error(f"Error in mixed comparison dividends chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика дивидендной доходности: {str(e)}")

    async def _handle_correlation_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle correlation matrix button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling correlation button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            
            if 'current_symbols' not in user_context:
                self.logger.warning(f"current_symbols not found in user context for user {user_id}")
                await self._send_callback_message(update, context, "❌ Данные о сравнении не найдены. Выполните команду /compare заново.")
                return
            
            symbols = user_context['current_symbols']
            currency = user_context.get('current_currency', 'USD')
            
            self.logger.info(f"Creating correlation matrix for symbols: {symbols}, currency: {currency}")
            await self._send_callback_message(update, context, "🔗 Создаю корреляционную матрицу...")
            
            # Check if this is a mixed comparison (portfolios + assets)
            user_context = self._get_user_context(user_id)
            last_analysis_type = user_context.get('last_analysis_type', 'comparison')
            expanded_symbols = user_context.get('expanded_symbols', [])
            
            if last_analysis_type == 'comparison' and any(isinstance(s, (pd.Series, pd.DataFrame)) for s in expanded_symbols):
                # This is a mixed comparison, handle differently
                await self._send_callback_message(update, context, "🔗 Создаю корреляционную матрицу для смешанного сравнения...")
                await self._create_mixed_comparison_correlation_matrix(update, context, symbols, currency)
            else:
                # Regular comparison, create AssetList
                asset_list = ok.AssetList(symbols, ccy=currency)
                await self._create_correlation_matrix(update, context, asset_list, symbols)
            
        except Exception as e:
            self.logger.error(f"Error handling correlation button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании корреляционной матрицы: {str(e)}")

    async def _create_mixed_comparison_correlation_matrix(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list, currency: str):
        """Create correlation matrix for mixed comparison (portfolios + assets)"""
        try:
            self.logger.info(f"Creating mixed comparison correlation matrix for symbols: {symbols}")
            
            # Get user context to restore portfolio information
            user_id = update.effective_user.id
            user_context = self._get_user_context(user_id)
            portfolio_contexts = user_context.get('portfolio_contexts', [])
            expanded_symbols = user_context.get('expanded_symbols', [])
            
            # Separate portfolios and individual assets using expanded_symbols
            portfolio_data = []
            asset_symbols = []
            
            for i, expanded_symbol in enumerate(expanded_symbols):
                if isinstance(expanded_symbol, (pd.Series, pd.DataFrame)):
                    # This is a portfolio wealth index
                    portfolio_data.append(expanded_symbol)
                else:
                    # This is an individual asset symbol
                    asset_symbols.append(expanded_symbol)
            
            # Calculate correlation data for all items
            correlation_data = {}
            
            # Process portfolios separately to avoid AssetList creation issues
            for i, portfolio_context in enumerate(portfolio_contexts):
                if i < len(portfolio_data):
                    try:
                        self.logger.info(f"Processing portfolio {i} for correlation")
                        
                        # Get portfolio details from context
                        assets = portfolio_context.get('portfolio_symbols', [])
                        weights = portfolio_context.get('portfolio_weights', [])
                        symbol = portfolio_context.get('symbol', f'Portfolio_{i+1}')
                        
                        if assets and weights and len(assets) == len(weights):
                            self.logger.info(f"Portfolio {i} assets: {assets}, weights: {weights}")
                            
                            # Create portfolio using ok.Portfolio
                            import okama as ok
                            portfolio = ok.Portfolio(
                                assets=assets,
                                weights=weights,
                                rebalancing_strategy=ok.Rebalance(period="year"),
                                symbol=symbol
                            )
                            
                            # Calculate returns for portfolio
                            wealth_series = portfolio.wealth_index
                            self.logger.info(f"Portfolio {symbol} wealth_series length: {len(wealth_series)}, dtype: {wealth_series.dtype}")
                            
                            returns = wealth_series.pct_change().dropna()
                            if len(returns) > 0:
                                correlation_data[symbol] = returns
                                self.logger.info(f"Successfully created correlation data for {symbol}: {len(returns)} points")
                            else:
                                self.logger.warning(f"Portfolio {symbol}: No returns data after pct_change")
                        else:
                            self.logger.warning(f"Portfolio {i} missing valid assets/weights data for correlation")
                    except Exception as portfolio_error:
                        self.logger.warning(f"Could not process portfolio {i} for correlation: {portfolio_error}")
                        continue
            
            # Process individual assets separately
            if asset_symbols:
                try:
                    asset_asset_list = ok.AssetList(asset_symbols, ccy=currency)
                    
                    for symbol in asset_symbols:
                        if symbol in asset_asset_list.wealth_indexes.columns:
                            # Calculate returns for individual asset
                            wealth_series = asset_asset_list.wealth_indexes[symbol]
                            self.logger.info(f"Asset {symbol} wealth_series length: {len(wealth_series)}, dtype: {wealth_series.dtype}")
                            
                            returns = wealth_series.pct_change().dropna()
                            if len(returns) > 0:
                                correlation_data[symbol] = returns
                                self.logger.info(f"Successfully created correlation data for {symbol}: {len(returns)} points")
                            else:
                                self.logger.warning(f"Asset {symbol}: No returns data after pct_change")
                        else:
                            self.logger.warning(f"Asset {symbol} not found in wealth_indexes columns")
                except Exception as asset_error:
                    self.logger.warning(f"Could not process individual assets: {asset_error}")
            
            if len(correlation_data) < 2:
                self.logger.warning(f"Not enough correlation data: {len(correlation_data)}")
                await self._send_callback_message(update, context, "❌ Недостаточно данных для создания корреляционной матрицы")
                return
            
            # Create correlation matrix
            try:
                # Combine all returns into a DataFrame
                returns_df = pd.DataFrame(correlation_data)
                
                # Calculate correlation matrix
                correlation_matrix = returns_df.corr()
                
                self.logger.info(f"Correlation matrix created successfully, shape: {correlation_matrix.shape}")
                
                if correlation_matrix.empty:
                    self.logger.warning("Correlation matrix is empty")
                    await self._send_callback_message(update, context, "❌ Не удалось вычислить корреляционную матрицу")
                    return
                
                # Create correlation matrix visualization using chart_styles
                fig, ax = chart_styles.create_correlation_matrix_chart(
                    correlation_matrix
                )
                
                # Save chart to bytes with memory optimization
                img_buffer = io.BytesIO()
                chart_styles.save_figure(fig, img_buffer)
                img_buffer.seek(0)
                img_bytes = img_buffer.getvalue()
                
                # Clear matplotlib cache to free memory
                chart_styles.cleanup_figure(fig)
                
                # Send correlation matrix
                self.logger.info("Sending correlation matrix image...")
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id, 
                    photo=io.BytesIO(img_bytes),
                    caption=self._truncate_caption(f"🔗 Корреляционная матрица для смешанного сравнения\n\nПоказывает корреляцию между доходностями портфелей и активов (от -1 до +1)\n\n• +1: полная положительная корреляция\n• 0: отсутствие корреляции\n• -1: полная отрицательная корреляция")
                )
                self.logger.info("Correlation matrix image sent successfully")
                
                plt.close(fig)
                
            except Exception as chart_error:
                self.logger.error(f"Error creating correlation matrix chart: {chart_error}")
                await self._send_callback_message(update, context, f"❌ Ошибка при создании корреляционной матрицы: {str(chart_error)}")
                
        except Exception as e:
            self.logger.error(f"Error in mixed comparison correlation matrix: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании корреляционной матрицы: {str(e)}")

    async def _handle_daily_chart_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Handle daily chart button click for single asset"""
        try:
            await self._send_callback_message(update, context, "📈 Создаю график за 1 год...")
            
            # Получаем ежедневный график за 1 год
            daily_chart = await self._get_daily_chart(symbol)
            
            if daily_chart:
                caption = f"📈 График за 1 год {symbol}\n\n"
                
                await update.callback_query.message.reply_photo(
                    photo=daily_chart,
                    caption=self._truncate_caption(caption)
                )
            else:
                await self._send_callback_message(update, context, "❌ Не удалось получить график за 1 год")
                
        except Exception as e:
            self.logger.error(f"Error handling daily chart button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика за 1 год: {str(e)}")

    async def _handle_monthly_chart_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Handle monthly chart button click for single asset"""
        try:
            await self._send_callback_message(update, context, "📅 Создаю график за 5 лет...")
            
            # Получаем месячный график за 5 лет
            monthly_chart = await self._get_monthly_chart(symbol)
            
            if monthly_chart:
                caption = f"📅 График за 5 лет {symbol}\n\n"
                
                await update.callback_query.message.reply_photo(
                    photo=monthly_chart,
                    caption=self._truncate_caption(caption)
                )
            else:
                await self._send_callback_message(update, context, "❌ Не удалось получить график за 5 лет")
                
        except Exception as e:
            self.logger.error(f"Error handling monthly chart button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика за 5 лет: {str(e)}")

    async def _handle_all_chart_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Handle all chart button click for single asset"""
        try:
            await self._send_callback_message(update, context, "📊 Создаю график за весь период...")
            
            # Получаем график за весь период
            all_chart = await self._get_all_chart(symbol)
            
            if all_chart:
                caption = f"📊 График за весь период {symbol}\n\n"
                
                await update.callback_query.message.reply_photo(
                    photo=all_chart,
                    caption=self._truncate_caption(caption)
                )
            else:
                await self._send_callback_message(update, context, "❌ Не удалось получить график за весь период")
                
        except Exception as e:
            self.logger.error(f"Error handling all chart button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика за весь период: {str(e)}")

    async def _handle_single_dividends_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Handle dividends button click for single asset"""
        try:
            await self._send_callback_message(update, context, "💵 Получаю информацию о дивидендах...")
            
            # Получаем информацию о дивидендах
            try:
                asset = ok.Asset(symbol)
                if hasattr(asset, 'dividends') and asset.dividends is not None:
                    dividend_info = {'dividends': asset.dividends, 'currency': getattr(asset, 'currency', '')}
                else:
                    dividend_info = {'error': 'No dividends data'}
            except Exception as e:
                dividend_info = {'error': str(e)}
            
            if 'error' not in dividend_info:
                dividends = dividend_info.get('dividends')
                if dividends is not None:
                    currency = dividend_info.get('currency', '')
                
                # Проверяем, что дивиденды не пустые (исправляем проблему с pandas Series)
                if isinstance(dividends, pd.Series):
                    has_dividends = not dividends.empty and dividends.size > 0
                else:
                    has_dividends = bool(dividends) and len(dividends) > 0
                
                if has_dividends:
                    # Формируем краткую информацию о дивидендах + текст последних выплат
                    try:
                        dividend_series = pd.Series(dividends)
                        recent = dividend_series.sort_index(ascending=False).head(10)
                        payouts_lines = []
                        for date, amount in recent.items():
                            if hasattr(date, 'strftime'):
                                formatted_date = date.strftime('%Y-%m-%d')
                            else:
                                formatted_date = str(date)[:10]
                            try:
                                amount_value = float(amount)
                            except Exception:
                                amount_value = amount
                            payouts_lines.append(f"{formatted_date} — {amount_value:.2f} {currency}")
                        payouts_text = "\n".join(payouts_lines)
                    except Exception:
                        # Fallback без pandas
                        items = list(dividends.items())[-10:][::-1]
                        payouts_lines = []
                        for date, amount in items:
                            formatted_date = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)[:10]
                            try:
                                amount_value = float(amount)
                            except Exception:
                                amount_value = amount
                            payouts_lines.append(f"{formatted_date} — {amount_value:.2f} {currency}")
                        payouts_text = "\n".join(payouts_lines)

                    dividend_response = (
                        f"💵 Дивиденды {symbol}\n\n"
                        f"📊 Количество выплат: {len(dividends)}\n"
                        f"💰 Валюта: {currency}\n\n"
                        f"🗓️ Последние выплаты:\n{payouts_text}"
                    )
                    
                    # Получаем график дивидендов (без встроенной таблицы)
                    dividend_chart = await self._get_dividend_chart(symbol)
                    
                    if dividend_chart:
                        await update.callback_query.message.reply_photo(
                            photo=dividend_chart,
                            caption=self._truncate_caption(dividend_response)
                        )
                    else:
                        await self._send_callback_message(update, context, dividend_response)
                else:
                    await self._send_callback_message(update, context, "💵 Дивиденды не выплачивались в указанный период")
            else:
                await self._send_callback_message(update, context, "💵 Информация о дивидендах недоступна")
                
        except Exception as e:
            self.logger.error(f"Error handling dividends button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при получении дивидендов: {str(e)}")

    async def _handle_tushare_daily_chart_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Handle Tushare daily chart button click"""
        try:
            await self._send_callback_message(update, context, "📈 Создаю график за 1 год...")
            
            if not self.tushare_service:
                await self._send_callback_message(update, context, "❌ Сервис Tushare недоступен")
                return
            
            # Get daily chart from Tushare
            chart_bytes = await self._get_tushare_daily_chart(symbol)
            
            if chart_bytes:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=io.BytesIO(chart_bytes),
                    caption=self._truncate_caption(f"📈 График за 1 год {symbol}")
                )
            else:
                await self._send_callback_message(update, context, "❌ Не удалось создать график")
                
        except Exception as e:
            self.logger.error(f"Error handling Tushare daily chart button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика: {str(e)}")

    async def _handle_tushare_monthly_chart_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Handle Tushare monthly chart button click"""
        try:
            await self._send_callback_message(update, context, "📅 Создаю график за 5 лет...")
            
            if not self.tushare_service:
                await self._send_callback_message(update, context, "❌ Сервис Tushare недоступен")
                return
            
            # Get monthly chart from Tushare
            chart_bytes = await self._get_tushare_monthly_chart(symbol)
            
            if chart_bytes:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=io.BytesIO(chart_bytes),
                    caption=self._truncate_caption(f"📅 График за 5 лет {symbol}")
                )
            else:
                await self._send_callback_message(update, context, "❌ Не удалось создать график")
                
        except Exception as e:
            self.logger.error(f"Error handling Tushare monthly chart button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика: {str(e)}")

    async def _handle_tushare_all_chart_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Handle Tushare all chart button click"""
        try:
            await self._send_callback_message(update, context, "📊 Создаю график за весь период...")
            
            if not self.tushare_service:
                await self._send_callback_message(update, context, "❌ Сервис Tushare недоступен")
                return
            
            # Get all chart from Tushare
            chart_bytes = await self._get_tushare_all_chart(symbol)
            
            if chart_bytes:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=io.BytesIO(chart_bytes),
                    caption=self._truncate_caption(f"📊 График за весь период {symbol}")
                )
            else:
                await self._send_callback_message(update, context, "❌ Не удалось создать график")
                
        except Exception as e:
            self.logger.error(f"Error handling Tushare all chart button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика: {str(e)}")

    async def _get_tushare_all_chart(self, symbol: str) -> Optional[bytes]:
        """Get chart from Tushare data for all available period"""
        try:
            import io
            
            def create_tushare_all_chart():
                try:
                    # Set backend for headless mode
                    import matplotlib
                    matplotlib.use('Agg')
                    
                    # Get monthly data from Tushare (for all period)
                    monthly_data = self.tushare_service.get_monthly_data(symbol)
                    
                    if monthly_data.empty:
                        self.logger.warning(f"Monthly data is empty for {symbol}")
                        return None
                    
                    # Prepare data for chart - set trade_date as index
                    chart_data = monthly_data.set_index('trade_date')['close']
                    
                    # Determine currency based on exchange
                    currency = 'HKD' if symbol.endswith('.HK') else 'CNY'
                    
                    # Get asset name from symbol
                    asset_name = symbol.split('.')[0]
                    
                    # Create chart using ChartStyles
                    fig, ax = chart_styles.create_price_chart(
                        data=chart_data,
                        symbol=symbol,
                        currency=currency,
                        period='All'
                    )
                    
                    # Обновляем заголовок с нужным форматом
                    title = f"{symbol} | {asset_name} | {currency} | All"
                    ax.set_title(title, **chart_styles.title)
                    
                    # Убираем подписи осей
                    ax.set_xlabel('')
                    ax.set_ylabel('')
                    
                    # Save to bytes
                    output = io.BytesIO()
                    chart_styles.save_figure(fig, output)
                    output.seek(0)
                    
                    # Cleanup
                    chart_styles.cleanup_figure(fig)
                    
                    return output.getvalue()
                    
                except Exception as e:
                    self.logger.error(f"Error in create_tushare_all_chart for {symbol}: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
                    return None
            
            # Run chart creation in thread to avoid blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(create_tushare_all_chart)
                chart_bytes = future.result(timeout=30)
            
            return chart_bytes
            
        except Exception as e:
            self.logger.error(f"Error getting Tushare all chart for {symbol}: {e}")
            return None

    async def _handle_tushare_dividends_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbol: str):
        """Handle Tushare dividends button click"""
        try:
            await self._send_callback_message(update, context, "💵 Получаю информацию о дивидендах...")
            
            if not self.tushare_service:
                await self._send_callback_message(update, context, "❌ Сервис Tushare недоступен")
                return
            
            # Get dividend data from Tushare
            dividend_data = self.tushare_service.get_dividend_data(symbol)
            
            if dividend_data.empty:
                await self._send_callback_message(update, context, f"💵 Дивиденды для {symbol} не найдены")
                return
            
            # Format dividend information
            info_text = f"💵 Дивиденды {symbol}\n\n"
            
            # Show last 10 dividends
            recent_dividends = dividend_data.tail(10)
            for _, row in recent_dividends.iterrows():
                ann_date = row['ann_date'].strftime('%Y-%m-%d') if pd.notna(row['ann_date']) else 'N/A'
                div_proc_date = row['div_proc_date'].strftime('%Y-%m-%d') if pd.notna(row['div_proc_date']) else 'N/A'
                stk_div_date = row['stk_div_date'].strftime('%Y-%m-%d') if pd.notna(row['stk_div_date']) else 'N/A'
                
                info_text += f"📅 {ann_date}: {row.get('cash_div_tax', 0):.4f}\n"
                info_text += f"   💰 Дата выплаты: {div_proc_date}\n"
                info_text += f"   📊 Дата регистрации: {stk_div_date}\n\n"
            
            await self._send_callback_message(update, context, info_text)
                
        except Exception as e:
            self.logger.error(f"Error handling Tushare dividends button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при получении дивидендов: {str(e)}")

    async def _get_monthly_chart(self, symbol: str) -> Optional[bytes]:
        """Получить месячный график за последние 5 лет используя ChartStyles"""
        try:
            import io
            
            def create_monthly_chart():
                # Устанавливаем backend для headless режима
                import matplotlib
                matplotlib.use('Agg')
                
                asset = ok.Asset(symbol)
                
                # Получаем месячные данные
                monthly_data = asset.close_monthly
                
                # Берем последние 60 месяцев (5 лет)
                filtered_data = monthly_data.tail(60)
                
                # Получаем информацию об активе для заголовка
                asset_name = getattr(asset, 'name', symbol)
                currency = getattr(asset, 'currency', '')
                
                # Используем ChartStyles для создания графика
                fig, ax = chart_styles.create_price_chart(
                    data=filtered_data,
                    symbol=symbol,
                    currency=currency,
                    period='5Y'
                )
                
                # Обновляем заголовок с нужным форматом
                title = f"{symbol} | {asset_name} | {currency} | 5Y"
                ax.set_title(title, **chart_styles.title)
                
                # Убираем подписи осей
                ax.set_xlabel('')
                ax.set_ylabel('')
                
                # Сохраняем в bytes
                output = io.BytesIO()
                chart_styles.save_figure(fig, output)
                output.seek(0)
                
                # Очистка
                chart_styles.cleanup_figure(fig)
                
                return output.getvalue()
            
            # Выполняем с таймаутом
            chart_data = await asyncio.wait_for(
                asyncio.to_thread(create_monthly_chart),
                timeout=30.0
            )
            
            return chart_data
            
        except Exception as e:
            self.logger.error(f"Error getting monthly chart for {symbol}: {e}")
            return None

    async def _get_all_chart(self, symbol: str) -> Optional[bytes]:
        """Получить график за весь доступный период используя ChartStyles"""
        try:
            import io
            
            def create_all_chart():
                # Устанавливаем backend для headless режима
                import matplotlib
                matplotlib.use('Agg')
                
                asset = ok.Asset(symbol)
                
                # Получаем месячные данные за весь период
                monthly_data = asset.close_monthly
                
                # Получаем информацию об активе для заголовка
                asset_name = getattr(asset, 'name', symbol)
                currency = getattr(asset, 'currency', '')
                
                # Используем ChartStyles для создания графика
                fig, ax = chart_styles.create_price_chart(
                    data=monthly_data,
                    symbol=symbol,
                    currency=currency,
                    period='All'
                )
                
                # Обновляем заголовок с нужным форматом
                title = f"{symbol} | {asset_name} | {currency} | All"
                ax.set_title(title, **chart_styles.title)
                
                # Убираем подписи осей
                ax.set_xlabel('')
                ax.set_ylabel('')
                
                # Сохраняем в bytes
                output = io.BytesIO()
                chart_styles.save_figure(fig, output)
                output.seek(0)
                
                # Очистка
                chart_styles.cleanup_figure(fig)
                
                return output.getvalue()
            
            # Выполняем с таймаутом
            chart_data = await asyncio.wait_for(
                asyncio.to_thread(create_all_chart),
                timeout=30.0
            )
            
            return chart_data
            
        except Exception as e:
            self.logger.error(f"Error getting all chart for {symbol}: {e}")
            return None

    async def _get_dividend_chart(self, symbol: str) -> Optional[bytes]:
        """Получить график дивидендов с копирайтом"""
        try:
            # Получаем данные о дивидендах
            try:
                asset = ok.Asset(symbol)
                if hasattr(asset, 'dividends') and asset.dividends is not None:
                    dividend_info = {'dividends': asset.dividends, 'currency': getattr(asset, 'currency', '')}
                else:
                    dividend_info = {'error': 'No dividends data'}
            except Exception as e:
                dividend_info = {'error': str(e)}
            
            if 'error' in dividend_info:
                return None
            
            dividends = dividend_info.get('dividends')
            if dividends is None:
                return None
            
            # Проверяем, что дивиденды не пустые (исправляем проблему с pandas Series)
            if isinstance(dividends, pd.Series):
                if dividends.empty or dividends.size == 0:
                    return None
            else:
                if not dividends or len(dividends) == 0:
                    return None
            
            # Создаем график дивидендов
            dividend_chart = self._create_dividend_chart(symbol, dividend_info['dividends'], dividend_info.get('currency', ''))
            
            if dividend_chart:
                # Копирайт уже добавлен в _create_dividend_chart
                return dividend_chart
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting dividend chart for {symbol}: {e}")
            return None

    async def _get_tushare_daily_chart(self, symbol: str) -> Optional[bytes]:
        """Get daily chart from Tushare data"""
        try:
            import io
            
            def create_tushare_daily_chart():
                try:
                    # Set backend for headless mode
                    import matplotlib
                    matplotlib.use('Agg')
                    
                    # Get daily data from Tushare
                    daily_data = self.tushare_service.get_daily_data(symbol)
                    
                    if daily_data.empty:
                        self.logger.warning(f"Daily data is empty for {symbol}")
                        return None
                    
                    # Prepare data for chart - set trade_date as index
                    chart_data = daily_data.set_index('trade_date')['close']
                    
                    # Take last 252 trading days (approximately 1 year)
                    filtered_data = chart_data.tail(252)
                    
                    # Determine currency based on exchange
                    currency = 'HKD' if symbol.endswith('.HK') else 'CNY'
                    
                    # Get asset name from symbol
                    asset_name = symbol.split('.')[0]
                    
                    # Create chart using ChartStyles
                    fig, ax = chart_styles.create_price_chart(
                        data=filtered_data,
                        symbol=symbol,
                        currency=currency,
                        period='1Y'
                    )
                    
                    # Обновляем заголовок с нужным форматом
                    title = f"{symbol} | {asset_name} | {currency} | 1Y"
                    ax.set_title(title, **chart_styles.title)
                    
                    # Убираем подписи осей
                    ax.set_xlabel('')
                    ax.set_ylabel('')
                    
                    # Save to bytes
                    output = io.BytesIO()
                    chart_styles.save_figure(fig, output)
                    output.seek(0)
                    
                    # Cleanup
                    chart_styles.cleanup_figure(fig)
                    
                    return output.getvalue()
                    
                except Exception as e:
                    self.logger.error(f"Error in create_tushare_daily_chart for {symbol}: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
                    return None
            
            # Run chart creation in thread to avoid blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(create_tushare_daily_chart)
                chart_bytes = future.result(timeout=30)
                
            return chart_bytes
            
        except Exception as e:
            self.logger.error(f"Error getting Tushare daily chart for {symbol}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def _get_tushare_monthly_chart(self, symbol: str) -> Optional[bytes]:
        """Get monthly chart from Tushare data"""
        try:
            import io
            
            def create_tushare_monthly_chart():
                try:
                    # Set backend for headless mode
                    import matplotlib
                    matplotlib.use('Agg')
                    
                    # Get monthly data from Tushare
                    monthly_data = self.tushare_service.get_monthly_data(symbol)
                    
                    if monthly_data.empty:
                        self.logger.warning(f"Monthly data is empty for {symbol}")
                        return None
                    
                    # Prepare data for chart - set trade_date as index
                    chart_data = monthly_data.set_index('trade_date')['close']
                    
                    # Take last 60 months (5 years)
                    filtered_data = chart_data.tail(60)
                    
                    # Determine currency based on exchange
                    currency = 'HKD' if symbol.endswith('.HK') else 'CNY'
                    
                    # Get asset name from symbol
                    asset_name = symbol.split('.')[0]
                    
                    # Create chart using ChartStyles
                    fig, ax = chart_styles.create_price_chart(
                        data=filtered_data,
                        symbol=symbol,
                        currency=currency,
                        period='5Y'
                    )
                    
                    # Обновляем заголовок с нужным форматом
                    title = f"{symbol} | {asset_name} | {currency} | 5Y"
                    ax.set_title(title, **chart_styles.title)
                    
                    # Убираем подписи осей
                    ax.set_xlabel('')
                    ax.set_ylabel('')
                    
                    # Save to bytes
                    output = io.BytesIO()
                    chart_styles.save_figure(fig, output)
                    output.seek(0)
                    
                    # Cleanup
                    chart_styles.cleanup_figure(fig)
                    
                    return output.getvalue()
                    
                except Exception as e:
                    self.logger.error(f"Error in create_tushare_monthly_chart for {symbol}: {e}")
                    import traceback
                    self.logger.error(f"Traceback: {traceback.format_exc()}")
                    return None
            
            # Run chart creation in thread to avoid blocking
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(create_tushare_monthly_chart)
                chart_bytes = future.result(timeout=30)
                
            return chart_bytes
            
        except Exception as e:
            self.logger.error(f"Error getting Tushare monthly chart for {symbol}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    async def _get_dividend_table_image(self, symbol: str) -> Optional[bytes]:
        """Получить изображение таблицы дивидендов с копирайтом"""
        try:
            # Получаем данные о дивидендах
            try:
                asset = ok.Asset(symbol)
                if hasattr(asset, 'dividends') and asset.dividends is not None:
                    dividend_info = {'dividends': asset.dividends, 'currency': getattr(asset, 'currency', '')}
                else:
                    dividend_info = {'error': 'No dividends data'}
            except Exception as e:
                dividend_info = {'error': str(e)}
            
            if 'error' in dividend_info:
                return None
            
            dividends = dividend_info.get('dividends')
            if dividends is None:
                return None
            
            # Проверяем, что дивиденды не пустые (исправляем проблему с pandas Series)
            if isinstance(dividends, pd.Series):
                if dividends.empty or dividends.size == 0:
                    return None
            else:
                if not dividends or len(dividends) == 0:
                    return None
            
            # Создаем изображение таблицы дивидендов
            dividend_table = self._create_dividend_table_image(symbol, dividend_info['dividends'], dividend_info.get('currency', ''))
            
            if dividend_table:
                # Копирайт уже добавлен в _create_dividend_table_image
                return dividend_table
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting dividend table image for {symbol}: {e}")
            return None

    def _create_dividend_chart(self, symbol: str, dividends: dict, currency: str) -> Optional[bytes]:
        """Создать график дивидендов используя ChartStyles"""
        try:
            import io
            
            # Конвертируем дивиденды в pandas Series
            dividend_series = pd.Series(dividends)
            
            # Сортируем по дате
            dividend_series = dividend_series.sort_index()
            
            # Используем ChartStyles для создания графика дивидендов
            fig, ax = chart_styles.create_dividends_chart(
                data=dividend_series,
                symbol=symbol,
                currency=currency
            )
            
            # Сохраняем в bytes
            output = io.BytesIO()
            chart_styles.save_figure(fig, output)
            output.seek(0)
            
            # Очистка
            chart_styles.cleanup_figure(fig)
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error creating dividend chart: {e}")
            return None

    def _create_dividend_table_image(self, symbol: str, dividends: dict, currency: str) -> Optional[bytes]:
        """Создать отдельное изображение с таблицей дивидендов используя ChartStyles"""
        try:
            import io
            
            # Конвертируем дивиденды в pandas Series
            dividend_series = pd.Series(dividends)
            
            # Сортируем по дате (новые сверху)
            dividend_series = dividend_series.sort_index(ascending=False)
            
            # Берем последние 15 выплат для таблицы
            recent_dividends = dividend_series.head(15)
            
            # Создаем таблицу
            table_data = []
            table_headers = ['Дата', f'Сумма ({currency})']
            
            for date, amount in recent_dividends.items():
                # Форматируем дату для лучшей читаемости
                if hasattr(date, 'strftime'):
                    formatted_date = date.strftime('%Y-%m-%d')
                else:
                    formatted_date = str(date)[:10]
                table_data.append([formatted_date, f'{amount:.2f}'])
            
            # Создаем фигуру для таблицы используя chart_styles
            fig, ax, table = chart_styles.create_dividend_table_chart(
                table_data=table_data,
                headers=table_headers,
                title=f'Таблица дивидендов {symbol}\nПоследние {len(table_data)} выплат'
            )
            
            # Стилизуем таблицу
            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 2.0)
            
            # Цвета для заголовков
            for i in range(len(table_headers)):
                table[(0, i)].set_facecolor(chart_styles.colors['success'])
                table[(0, i)].set_text_props(weight='bold', color='white')
                table[(0, i)].set_height(0.12)
            
            # Цвета для строк данных (чередование)
            for i in range(1, len(table_data) + 1):
                for j in range(len(table_headers)):
                    if i % 2 == 0:
                        table[(i, j)].set_facecolor(chart_styles.colors['neutral'])
                    else:
                        table[(i, j)].set_facecolor('white')
                    table[(i, j)].set_text_props(color=chart_styles.colors['text'])
                    table[(i, j)].set_height(0.08)
            
            # Добавляем общую статистику внизу
            total_dividends = dividend_series.sum()
            avg_dividend = dividend_series.mean()
            max_dividend = dividend_series.max()
            
            stats_text = f'Общая сумма: {total_dividends:.2f} {currency} | '
            stats_text += f'Средняя выплата: {avg_dividend:.2f} {currency} | '
            stats_text += f'Максимальная выплата: {max_dividend:.2f} {currency}'
            
            ax.text(0.5, 0.02, stats_text, transform=ax.transAxes, 
                   fontsize=10, ha='center', color=chart_styles.colors['text'],
                   bbox=dict(boxstyle='round,pad=0.5', facecolor=chart_styles.colors['neutral'], alpha=0.8))
            
            # Сохраняем в bytes
            output = io.BytesIO()
            chart_styles.save_figure(fig, output)
            output.seek(0)
            
            # Очистка
            chart_styles.cleanup_figure(fig)
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error creating dividend table image: {e}")
            return None

    async def _handle_risk_metrics_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle risk metrics button click for portfolio"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling risk metrics button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in final_symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            self.logger.info(f"Creating risk metrics for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📊 Анализирую риски портфеля...")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_risk_metrics_report(update, context, portfolio, final_symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling risk metrics button: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при анализе рисков: {str(e)}", parse_mode='Markdown')

    async def _handle_portfolio_risk_metrics_by_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
        """Handle portfolio risk metrics button click by portfolio symbol"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio risk metrics by symbol for user {user_id}, portfolio: {portfolio_symbol}")
            
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if portfolio_symbol not in saved_portfolios:
                await self._send_callback_message(update, context, f"❌ Портфель '{portfolio_symbol}' не найден. Создайте портфель заново.")
                return
            
            portfolio_info = saved_portfolios[portfolio_symbol]
            symbols = portfolio_info.get('symbols', [])
            weights = portfolio_info.get('weights', [])
            currency = portfolio_info.get('currency', 'USD')
            
            self.logger.info(f"Retrieved portfolio data: symbols={symbols}, weights={weights}, currency={currency}")
            
            if not symbols:
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены.")
                return
            
            await self._send_callback_message(update, context, "📊 Анализирую риски портфеля...")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_risk_metrics_report(update, context, portfolio, final_symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio risk metrics by symbol: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при анализе рисков: {str(e)}", parse_mode='Markdown')

    async def _handle_monte_carlo_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle Monte Carlo button click for portfolio"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling Monte Carlo button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in final_symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            self.logger.info(f"Creating Monte Carlo forecast for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "🎲 Создаю прогноз Monte Carlo...")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_monte_carlo_forecast(update, context, portfolio, final_symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling Monte Carlo button: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании прогноза Monte Carlo: {str(e)}")

    async def _handle_portfolio_monte_carlo_by_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
        """Handle portfolio Monte Carlo button click by portfolio symbol"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio Monte Carlo by symbol for user {user_id}, portfolio: {portfolio_symbol}")
            
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if portfolio_symbol not in saved_portfolios:
                await self._send_callback_message(update, context, f"❌ Портфель '{portfolio_symbol}' не найден. Создайте портфель заново.")
                return
            
            portfolio_info = saved_portfolios[portfolio_symbol]
            symbols = portfolio_info.get('symbols', [])
            weights = portfolio_info.get('weights', [])
            currency = portfolio_info.get('currency', 'USD')
            
            self.logger.info(f"Retrieved portfolio data: symbols={symbols}, weights={weights}, currency={currency}")
            
            if not symbols:
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены.")
                return
            
            await self._send_callback_message(update, context, "🎲 Создаю прогноз Monte Carlo...")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_monte_carlo_forecast(update, context, portfolio, final_symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio Monte Carlo by symbol: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании прогноза Monte Carlo: {str(e)}")

    async def _handle_forecast_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle forecast button click for portfolio"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling forecast button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context keys: {list(user_context.keys())}")
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in final_symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            self.logger.info(f"Creating forecast for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📈 Создаю прогноз с процентилями...")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_forecast_chart(update, context, portfolio, final_symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling forecast button: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании прогноза: {str(e)}")

    async def _handle_portfolio_forecast_by_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
        """Handle portfolio forecast button click by portfolio symbol"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio forecast by symbol for user {user_id}, portfolio: {portfolio_symbol}")
            
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if portfolio_symbol not in saved_portfolios:
                await self._send_callback_message(update, context, f"❌ Портфель '{portfolio_symbol}' не найден. Создайте портфель заново.")
                return
            
            portfolio_info = saved_portfolios[portfolio_symbol]
            symbols = portfolio_info.get('symbols', [])
            weights = portfolio_info.get('weights', [])
            currency = portfolio_info.get('currency', 'USD')
            
            self.logger.info(f"Retrieved portfolio data: symbols={symbols}, weights={weights}, currency={currency}")
            
            if not symbols:
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены.")
                return
            
            await self._send_callback_message(update, context, "📈 Создаю прогноз с процентилями...")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_forecast_chart(update, context, portfolio, final_symbols, currency)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio forecast by symbol: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании прогноза: {str(e)}")

    async def _create_risk_metrics_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str):
        """Create and send risk metrics report for portfolio"""
        try:
            # Get portfolio description
            portfolio_description = portfolio.describe()
            
            # Create header
            risk_text = f"📊 **Анализ риск метрик портфеля**\n\n"
            risk_text += f"🎯 **Активы:** {', '.join(symbols)}\n"
            risk_text += f"💰 **Валюта:** {currency}\n\n"
            risk_text += "─" * 50 + "\n\n"
            
            # Parse and explain each metric
            metrics_explained = self._explain_risk_metrics(portfolio_description, portfolio)
            
            # Add metrics with better formatting
            for metric_name, explanation in metrics_explained.items():
                risk_text += f"{metric_name}\n"
                risk_text += f"{explanation}\n\n"
                risk_text += "─" * 30 + "\n\n"
            
            # Add general risk assessment
            risk_text += "🎯 **ОБЩАЯ ОЦЕНКА РИСКА**\n"
            risk_text += "─" * 50 + "\n\n"
            risk_text += self._assess_portfolio_risk(portfolio_description, portfolio)
            
            # Send text report
            await self._send_callback_message(update, context, risk_text)
            
        except Exception as e:
            self.logger.error(f"Error creating risk metrics report: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании отчета о рисках: {str(e)}")

    def _explain_risk_metrics(self, portfolio_description, portfolio) -> dict:
        """Explain each risk metric in detail"""
        explanations = {}
        
        try:
            # 1. Годовая волатильность
            if hasattr(portfolio, 'risk_annual'):
                risk_annual = portfolio.risk_annual
                if hasattr(risk_annual, 'tail'):
                    risk_value = risk_annual.tail(1).iloc[0] if not risk_annual.empty else None
                else:
                    risk_value = risk_annual.iloc[-1] if hasattr(risk_annual, 'iloc') else risk_annual
                
                if risk_value is not None:
                    risk_pct = float(risk_value) * 100
                    # Определяем уровень волатильности
                    if risk_pct <= 5:
                        volatility_level = "Очень низкая"
                        volatility_emoji = "🟢"
                        asset_type = "Типично для облигаций и депозитов"
                    elif risk_pct <= 10:
                        volatility_level = "Низкая"
                        volatility_emoji = "🟢"
                        asset_type = "Типично для консервативных портфелей"
                    elif risk_pct <= 15:
                        volatility_level = "Умеренная"
                        volatility_emoji = "🟡"
                        asset_type = "Типично для сбалансированных портфелей"
                    elif risk_pct <= 25:
                        volatility_level = "Высокая"
                        volatility_emoji = "🟠"
                        asset_type = "Типично для акций"
                    else:
                        volatility_level = "Очень высокая"
                        volatility_emoji = "🔴"
                        asset_type = "Типично для спекулятивных активов"
                    
                    explanations["1. Годовая волатильность"] = (
                        f"{volatility_emoji} **{volatility_level}** ({risk_pct:.1f}% годовых)\n\n"
                        f"💡 **Что это значит:**\n"
                        f"• Портфель может колебаться в пределах ±{risk_pct:.1f}% в год\n"
                        f"• {asset_type}\n\n"
                        f"💡 **Как использовать:**\n"
                        f"• Сравнивайте с другими портфелями\n"
                        f"• При одинаковой доходности выбирайте с меньшей волатильностью\n"
                        f"• Учитывайте свой риск-профиль"
                    )
            
            # 2. Полуотклонение (риск только вниз)
            if hasattr(portfolio, 'semideviation_annual'):
                semidev = portfolio.semideviation_annual
                if hasattr(semidev, 'iloc'):
                    semidev_value = semidev.iloc[-1] if not semidev.empty else None
                else:
                    semidev_value = semidev
                
                if semidev_value is not None:
                    semidev_pct = float(semidev_value) * 100
                    # Сравниваем с общей волатильностью
                    if hasattr(portfolio, 'risk_annual'):
                        risk_annual = portfolio.risk_annual
                        if hasattr(risk_annual, 'tail'):
                            risk_value = risk_annual.tail(1).iloc[0] if not risk_annual.empty else None
                        else:
                            risk_value = risk_annual.iloc[-1] if hasattr(risk_annual, 'iloc') else risk_annual
                        
                        if risk_value is not None:
                            risk_pct = float(risk_value) * 100
                            ratio = semidev_pct / risk_pct if risk_pct > 0 else 1
                            
                            if ratio < 0.7:
                                downside_characteristic = "Портфель 'гладкий' вниз, но может резко расти"
                            elif ratio > 0.9:
                                downside_characteristic = "Портфель одинаково колеблется вверх и вниз"
                            else:
                                downside_characteristic = "Сбалансированное поведение портфеля"
                        else:
                            downside_characteristic = "Стандартное поведение"
                    else:
                        downside_characteristic = "Стандартное поведение"
                    
                    explanations["2. Риск просадок (полуотклонение)"] = (
                        f"📉 **{semidev_pct:.1f}%** годовых\n\n"
                        f"💡 **Что это значит:**\n"
                        f"• Учитывает только отрицательные колебания\n"
                        f"• Более точно отражает страх инвестора\n\n"
                        f"💡 **Характеристика:**\n"
                        f"• {downside_characteristic}\n"
                        f"• Помогает понять, насколько 'комфортно' падать портфелю"
                    )
            
            # 3. VaR (Value at Risk)
            try:
                var_1 = portfolio.get_var_historic(level=1)
                var_5 = portfolio.get_var_historic(level=5)
                
                if var_1 is not None and var_5 is not None:
                    var_1_pct = float(var_1) * 100
                    var_5_pct = float(var_5) * 100
                    
                    # Оценка риска по VaR
                    if abs(var_5_pct) <= 3:
                        var_assessment = "Очень низкий риск потерь"
                        var_emoji = "🟢"
                    elif abs(var_5_pct) <= 8:
                        var_assessment = "Низкий риск потерь"
                        var_emoji = "🟢"
                    elif abs(var_5_pct) <= 15:
                        var_assessment = "Умеренный риск потерь"
                        var_emoji = "🟡"
                    elif abs(var_5_pct) <= 25:
                        var_assessment = "Высокий риск потерь"
                        var_emoji = "🟠"
                    else:
                        var_assessment = "Очень высокий риск потерь"
                        var_emoji = "🔴"
                    
                    explanations["3. VaR (риск потерь)"] = (
                        f"{var_emoji} **{var_assessment}**\n\n"
                        f"📊 **Значения:**\n"
                        f"• 1% VaR: {var_1_pct:.1f}% (99% вероятность, что потери не превысят)\n"
                        f"• 5% VaR: {var_5_pct:.1f}% (95% вероятность, что потери не превысят)\n\n"
                        f"💡 **Как использовать:**\n"
                        f"• Оцените, готовы ли потерять {abs(var_5_pct):.1f}% в месяц\n"
                        f"• Если нет — портфель слишком агрессивный для вас"
                    )
            except Exception as e:
                self.logger.warning(f"Could not get VaR: {e}")
            
            # 4. CVaR (Conditional Value at Risk)
            try:
                cvar_5 = portfolio.get_cvar_historic(level=5)
                
                if cvar_5 is not None:
                    cvar_5_pct = float(cvar_5) * 100
                    
                    # Оценка по CVaR
                    if abs(cvar_5_pct) <= 5:
                        cvar_assessment = "Очень низкие ожидаемые потери в кризис"
                        cvar_emoji = "🟢"
                    elif abs(cvar_5_pct) <= 12:
                        cvar_assessment = "Низкие ожидаемые потери в кризис"
                        cvar_emoji = "🟢"
                    elif abs(cvar_5_pct) <= 20:
                        cvar_assessment = "Умеренные ожидаемые потери в кризис"
                        cvar_emoji = "🟡"
                    elif abs(cvar_5_pct) <= 30:
                        cvar_assessment = "Высокие ожидаемые потери в кризис"
                        cvar_emoji = "🟠"
                    else:
                        cvar_assessment = "Очень высокие ожидаемые потери в кризис"
                        cvar_emoji = "🔴"
                    
                    explanations["4. CVaR (ожидаемые потери в кризис)"] = (
                        f"{cvar_emoji} **{cvar_assessment}**\n\n"
                        f"📊 **Значение:** {cvar_5_pct:.1f}%\n\n"
                        f"💡 **Что это значит:**\n"
                        f"• В худших 5% месяцев ожидайте потери около {abs(cvar_5_pct):.1f}%\n"
                        f"• Более консервативный показатель, чем VaR\n"
                        f"• Помогает понять глубину возможного 'провала'"
                    )
            except Exception as e:
                self.logger.warning(f"Could not get CVaR: {e}")
            
            # 5. Максимальная просадка
            if hasattr(portfolio, 'drawdowns'):
                drawdowns = portfolio.drawdowns
                if hasattr(drawdowns, 'min'):
                    max_dd = drawdowns.min()
                    if max_dd is not None:
                        max_dd_pct = float(max_dd) * 100
                        
                        # Оценка просадки
                        if max_dd_pct <= 5:
                            dd_assessment = "Очень низкая просадка"
                            dd_emoji = "🟢"
                            dd_advice = "Портфель очень стабильный, подходит для консервативных инвесторов"
                        elif max_dd_pct <= 15:
                            dd_assessment = "Низкая просадка"
                            dd_emoji = "🟢"
                            dd_advice = "Портфель стабильный, подходит для большинства инвесторов"
                        elif max_dd_pct <= 30:
                            dd_assessment = "Умеренная просадка"
                            dd_emoji = "🟡"
                            dd_advice = "Требует психологической устойчивости"
                        elif max_dd_pct <= 50:
                            dd_assessment = "Высокая просадка"
                            dd_emoji = "🟠"
                            dd_advice = "Убедитесь, что готовы к таким потерям"
                        else:
                            dd_assessment = "Очень высокая просадка"
                            dd_emoji = "🔴"
                            dd_advice = "Портфель очень агрессивный"
                        
                        explanations["5. Максимальная просадка"] = (
                            f"{dd_emoji} **{dd_assessment}** ({max_dd_pct:.1f}%)\n\n"
                            f"💡 **Что это значит:**\n"
                            f"• Самая большая потеря от пика до дна\n"
                            f"• Критично для психологической устойчивости\n\n"
                            f"💡 **Рекомендация:**\n"
                            f"• {dd_advice}\n"
                            f"• Если не выдержите просадку в {max_dd_pct:.1f}%, пересмотрите состав"
                        )
            
            # 6. Период восстановления
            if hasattr(portfolio, 'recovery_period'):
                recovery = portfolio.recovery_period
                if hasattr(recovery, 'max'):
                    max_recovery = recovery.max()
                    if max_recovery is not None:
                        recovery_years = float(max_recovery) / 12  # в годах
                        
                        # Оценка периода восстановления
                        if recovery_years <= 0.5:
                            recovery_assessment = "Очень быстрое восстановление"
                            recovery_emoji = "🟢"
                        elif recovery_years <= 1:
                            recovery_assessment = "Быстрое восстановление"
                            recovery_emoji = "🟢"
                        elif recovery_years <= 2:
                            recovery_assessment = "Умеренное восстановление"
                            recovery_emoji = "🟡"
                        elif recovery_years <= 4:
                            recovery_assessment = "Медленное восстановление"
                            recovery_emoji = "🟠"
                        else:
                            recovery_assessment = "Очень медленное восстановление"
                            recovery_emoji = "🔴"
                        
                        explanations["6. Период восстановления"] = (
                            f"{recovery_emoji} **{recovery_assessment}** ({recovery_years:.1f} года)\n\n"
                            f"💡 **Что это значит:**\n"
                            f"• Время возврата к предыдущему максимуму\n"
                            f"• Критично при планировании снятия денег\n\n"
                            f"💡 **Как использовать:**\n"
                            f"• Если планируете снимать деньги, убедитесь, что период восстановления приемлем\n"
                            f"• Иначе есть риск 'обнулиться' в неподходящий момент"
                        )
            
        except Exception as e:
            self.logger.error(f"Error explaining risk metrics: {e}")
            explanations["Ошибка анализа"] = f"Не удалось проанализировать метрики риска: {str(e)}"
        
        return explanations

    def _assess_portfolio_risk(self, portfolio_description, portfolio) -> str:
        """Assess overall portfolio risk level with improved logic for conservative assets"""
        try:
            risk_level = "Средний"
            risk_color = "🟡"
            risk_score = 0
            recommendations = []
            
            # Check volatility (weight: 40%)
            if hasattr(portfolio, 'risk_annual'):
                risk_annual = portfolio.risk_annual
                if hasattr(risk_annual, 'tail'):
                    risk_value = risk_annual.tail(1).iloc[0] if not risk_annual.empty else None
                else:
                    risk_value = risk_annual.iloc[-1] if hasattr(risk_annual, 'iloc') else risk_annual
                
                if risk_value is not None:
                    risk_pct = float(risk_value) * 100
                    
                    if risk_pct <= 5:
                        risk_score += 0  # Очень низкий риск
                        volatility_assessment = "Очень низкая"
                        volatility_emoji = "🟢"
                    elif risk_pct <= 10:
                        risk_score += 1  # Низкий риск
                        volatility_assessment = "Низкая"
                        volatility_emoji = "🟢"
                    elif risk_pct <= 15:
                        risk_score += 2  # Умеренный риск
                        volatility_assessment = "Умеренная"
                        volatility_emoji = "🟡"
                    elif risk_pct <= 25:
                        risk_score += 3  # Высокий риск
                        volatility_assessment = "Высокая"
                        volatility_emoji = "🟠"
                    else:
                        risk_score += 4  # Очень высокий риск
                        volatility_assessment = "Очень высокая"
                        volatility_emoji = "🔴"
                    
                    # Добавляем рекомендации по волатильности
                    if risk_pct <= 5:
                        recommendations.append("• Портфель очень консервативный, идеален для сохранения капитала")
                        recommendations.append("• Подходит для инвесторов с низкой толерантностью к риску")
                    elif risk_pct <= 10:
                        recommendations.append("• Портфель консервативный, подходит для большинства инвесторов")
                        recommendations.append("• Рассмотрите добавление акций для роста доходности")
                    elif risk_pct <= 15:
                        recommendations.append("• Портфель сбалансированный, подходит для долгосрочных целей")
                    elif risk_pct <= 25:
                        recommendations.append("• Портфель агрессивный, требует психологической устойчивости")
                        recommendations.append("• Рассмотрите добавление облигаций для снижения волатильности")
                    else:
                        recommendations.append("• Портфель очень агрессивный, подходит только для опытных инвесторов")
                        recommendations.append("• Увеличьте долю защитных активов (облигации, золото)")
            
            # Check max drawdown (weight: 30%)
            if hasattr(portfolio, 'drawdowns'):
                drawdowns = portfolio.drawdowns
                if hasattr(drawdowns, 'min'):
                    max_dd = drawdowns.min()
                    if max_dd is not None:
                        max_dd_pct = abs(float(max_dd) * 100)
                        
                        if max_dd_pct <= 5:
                            risk_score += 0  # Очень низкий риск
                            dd_assessment = "Очень низкая"
                        elif max_dd_pct <= 15:
                            risk_score += 1  # Низкий риск
                            dd_assessment = "Низкая"
                        elif max_dd_pct <= 30:
                            risk_score += 2  # Умеренный риск
                            dd_assessment = "Умеренная"
                        elif max_dd_pct <= 50:
                            risk_score += 3  # Высокий риск
                            dd_assessment = "Высокая"
                        else:
                            risk_score += 4  # Очень высокий риск
                            dd_assessment = "Очень высокая"
                        
                        # Добавляем рекомендации по просадке
                        if max_dd_pct <= 5:
                            recommendations.append("• Просадка очень низкая, портфель очень стабильный")
                        elif max_dd_pct <= 15:
                            recommendations.append("• Просадка низкая, подходит для большинства инвесторов")
                        elif max_dd_pct <= 30:
                            recommendations.append("• Просадка умеренная, требует психологической устойчивости")
                        else:
                            recommendations.append("• Просадка высокая, убедитесь, что готовы к таким потерям")
            
            # Check VaR (weight: 20%)
            try:
                var_5 = portfolio.get_var_historic(level=5)
                if var_5 is not None:
                    var_5_pct = abs(float(var_5) * 100)
                    
                    if var_5_pct <= 3:
                        risk_score += 0  # Очень низкий риск
                    elif var_5_pct <= 8:
                        risk_score += 1  # Низкий риск
                    elif var_5_pct <= 15:
                        risk_score += 2  # Умеренный риск
                    elif var_5_pct <= 25:
                        risk_score += 3  # Высокий риск
                    else:
                        risk_score += 4  # Очень высокий риск
            except Exception:
                pass
            
            # Check CVaR (weight: 10%)
            try:
                cvar_5 = portfolio.get_cvar_historic(level=5)
                if cvar_5 is not None:
                    cvar_5_pct = abs(float(cvar_5) * 100)
                    
                    if cvar_5_pct <= 5:
                        risk_score += 0  # Очень низкий риск
                    elif cvar_5_pct <= 12:
                        risk_score += 1  # Низкий риск
                    elif cvar_5_pct <= 20:
                        risk_score += 2  # Умеренный риск
                    elif cvar_5_pct <= 30:
                        risk_score += 3  # Высокий риск
                    else:
                        risk_score += 4  # Очень высокий риск
            except Exception:
                pass
            
            # Определяем общий уровень риска на основе score
            max_possible_score = 4  # Максимальный score для одного показателя
            normalized_score = risk_score / max_possible_score
            
            if normalized_score <= 0.25:
                risk_level = "Очень низкий"
                risk_color = "🟢"
            elif normalized_score <= 0.5:
                risk_level = "Низкий"
                risk_color = "🟢"
            elif normalized_score <= 0.75:
                risk_level = "Умеренный"
                risk_color = "🟡"
            elif normalized_score <= 1.0:
                risk_level = "Высокий"
                risk_color = "🟠"
            else:
                risk_level = "Очень высокий"
                risk_color = "🔴"
            
            # Формируем итоговую оценку
            assessment = f"{risk_color} **Уровень риска: {risk_level}**\n\n"
            
            if hasattr(portfolio, 'risk_annual'):
                risk_annual = portfolio.risk_annual
                if hasattr(risk_annual, 'tail'):
                    risk_value = risk_annual.tail(1).iloc[0] if not risk_annual.empty else None
                else:
                    risk_value = risk_annual.iloc[-1] if hasattr(risk_annual, 'iloc') else risk_annual
                
                if risk_value is not None:
                    risk_pct = float(risk_value) * 100
                    assessment += f"📊 **Ключевые показатели:**\n"
                    assessment += f"• Волатильность: {volatility_emoji} {volatility_assessment} ({risk_pct:.1f}%)\n"
                    
                    if hasattr(portfolio, 'drawdowns'):
                        drawdowns = portfolio.drawdowns
                        if hasattr(drawdowns, 'min'):
                            max_dd = drawdowns.min()
                            if max_dd is not None:
                                max_dd_pct = abs(float(max_dd) * 100)
                                assessment += f"• Макс. просадка: {dd_assessment} ({max_dd_pct:.1f}%)\n"
            
            assessment += f"\n📋 **Рекомендации:**\n"
            if recommendations:
                for rec in recommendations:
                    assessment += f"{rec}\n"
            else:
                assessment += "• Портфель сбалансированный, специальных рекомендаций не требуется."
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing portfolio risk: {e}")
            return "Не удалось оценить общий уровень риска портфеля."

    async def _create_monte_carlo_forecast(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str):
        """Create and send Monte Carlo forecast chart for portfolio"""
        try:
            self.logger.info(f"Creating Monte Carlo forecast chart for portfolio: {symbols}")
            
            # Generate Monte Carlo forecast (okama creates the figure)
            forecast_data = portfolio.plot_forecast_monte_carlo(distr="norm", years=10, n=20)

            # Get the current figure from matplotlib (created by okama)
            current_fig = plt.gcf()

            # Apply chart styles to the current figure
            if current_fig.axes:
                ax = current_fig.axes[0]
                
                
                # Apply standard chart styling with centralized style
                chart_styles.apply_styling(
                    ax,
                    title=f'Прогноз Monte Carlo\n{", ".join(symbols)}',
                    ylabel='Накопленная доходность',
                    grid=True,
                    legend=False,
                    copyright=True
                )
            
            # Save the figure
            img_buffer = io.BytesIO()
            current_fig.savefig(img_buffer, format='PNG', dpi=96, bbox_inches='tight')
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            plt.close(current_fig)
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(
                    f"🎲 Прогноз Monte Carlo для портфеля: {', '.join(symbols)}\n\n"
                    f"📊 Параметры:\n"
                    f"• Распределение: Нормальное (norm)\n"
                    f"• Период: 10 лет\n"
                    f"• Количество симуляций: 20\n"
                    f"• Валюта: {currency}\n\n"
                    f"💡 График показывает возможные траектории роста портфеля на основе исторической волатильности и доходности."
                )
            )
            
        except Exception as e:
            self.logger.error(f"Error creating Monte Carlo forecast chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика Monte Carlo: {str(e)}")

    async def _create_forecast_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str):
        """Create and send forecast chart with percentiles for portfolio"""
        try:
            self.logger.info(f"Creating forecast chart with percentiles for portfolio: {symbols}")
            
            # Generate forecast chart using okama
            # y.plot_forecast(years=10, today_value=1000, percentiles=[10, 50, 90])
            forecast_data = portfolio.plot_forecast(
                years=10, 
                today_value=1000, 
                percentiles=[10, 50, 90]
            )
            
            # Get the current figure from matplotlib (created by okama)
            current_fig = plt.gcf()
            
            # Apply chart styles to the current figure
            if current_fig.axes:
                ax = current_fig.axes[0]  # Get the first (and usually only) axes
                
                
                # Force legend update to match the new colors
                if ax.get_legend():
                    ax.get_legend().remove()
                ax.legend(**chart_styles.legend)
                
                # Apply standard chart styling with centralized style
                chart_styles.apply_styling(
                    ax,
                    title=f'Прогноз с процентилями\n{", ".join(symbols)}',
                    ylabel='Накопленная доходность',
                    grid=True,
                    legend=True,
                    copyright=True
                )
            
            # Save the figure
            img_buffer = io.BytesIO()
            current_fig.savefig(img_buffer, format='PNG', dpi=96, bbox_inches='tight')
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            plt.close(current_fig)
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(
                    f"📈 Прогноз с процентилями для портфеля: {', '.join(symbols)}\n\n"
                    f"📊 Параметры:\n"
                    f"• Период: 10 лет\n"
                    f"• Начальная стоимость: 1000 {currency}\n"
                    f"• процентили: 10%, 50%, 90%\n\n"
                    f"💡 График показывает:\n"
                    f"• 10% процентиль: пессимистичный сценарий\n"
                    f"• 50% процентиль: средний сценарий\n"
                    f"• 90% процентиль: оптимистичный сценарий"
                )
            )
            
        except Exception as e:
            self.logger.error(f"Error creating forecast chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика прогноза: {str(e)}")

    async def _handle_portfolio_drawdowns_by_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
        """Handle portfolio drawdowns button click by portfolio symbol"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio drawdowns by symbol for user {user_id}, portfolio: {portfolio_symbol}")
            
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if portfolio_symbol not in saved_portfolios:
                await self._send_callback_message(update, context, f"❌ Портфель '{portfolio_symbol}' не найден. Создайте портфель заново.")
                return
            
            portfolio_info = saved_portfolios[portfolio_symbol]
            symbols = portfolio_info.get('symbols', [])
            weights = portfolio_info.get('weights', [])
            currency = portfolio_info.get('currency', 'USD')
            
            self.logger.info(f"Retrieved portfolio data: symbols={symbols}, weights={weights}, currency={currency}")
            
            if not symbols:
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены.")
                return
            
            # Filter out None values and empty strings
            final_symbols = [s for s in symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            await self._send_callback_message(update, context, "📉 Создаю график просадок...")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    if i < len(weights):
                        valid_weights.append(weights[i])
                    else:
                        valid_weights.append(1.0 / len(final_symbols))
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            await self._create_portfolio_drawdowns_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio drawdowns by symbol: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика просадок: {str(e)}")

    async def _handle_portfolio_drawdowns_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle portfolio drawdowns button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio drawdowns button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            self.logger.info(f"Button symbols: {button_symbols}")
            self.logger.info(f"Final symbols: {final_symbols}")
            self.logger.info(f"Current symbols from context: {user_context.get('current_symbols')}")
            self.logger.info(f"Last assets from context: {user_context.get('last_assets')}")
            
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in final_symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            self.logger.info(f"Creating drawdowns chart for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📉 Создаю график просадок...")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_portfolio_drawdowns_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio drawdowns button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика просадок: {str(e)}")

    async def _create_portfolio_drawdowns_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list):
        """Create and send portfolio drawdowns chart"""
        try:
            self.logger.info(f"Creating portfolio drawdowns chart for portfolio: {symbols}")
            
            # Generate drawdowns chart using okama
            # portfolio.drawdowns.plot()
            drawdowns_data = portfolio.drawdowns.plot()
            
            # Get the current figure from matplotlib (created by okama)
            current_fig = plt.gcf()
            
            # Apply chart styles to the current figure
            if current_fig.axes:
                ax = current_fig.axes[0]
                
                # Apply drawdown-specific styling with standard grid colors and date labels above
                chart_styles.apply_drawdown_styling(
                    ax,
                    title=f'Просадки портфеля\n{", ".join(symbols)}',
                    ylabel='Просадка (%)',
                    grid=True,
                    legend=False,
                    copyright=True
                )
            
            # Save the figure
            img_buffer = io.BytesIO()
            chart_styles.save_figure(current_fig, img_buffer)
            img_buffer.seek(0)
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(current_fig)
            
            # Get drawdowns statistics
            try:
                # Get 5 largest drawdowns
                largest_drawdowns = portfolio.drawdowns.nsmallest(5)
                
                # Get longest recovery periods (convert to years)
                longest_recoveries = portfolio.recovery_period.nlargest(5) / 12
                
                # Build enhanced caption
                caption = f"📉 Просадки портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                
                # Add largest drawdowns
                caption += f"📉 5 самых больших просадок:\n"
                for i, (date, drawdown) in enumerate(largest_drawdowns.items(), 1):
                    date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                    drawdown_pct = drawdown * 100
                    caption += f"{i}. {date_str}: {drawdown_pct:.2f}%\n"
                
                caption += f"\n⏱️ Самые долгие периоды восстановления:\n"
                for i, (date, recovery_years) in enumerate(longest_recoveries.items(), 1):
                    date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                    caption += f"{i}. {date_str}: {recovery_years:.1f} лет\n"
                
                caption += f"\n💡 График показывает:\n"
                caption += f"• Максимальную просадку портфеля\n"
                caption += f"• Периоды восстановления\n"
                caption += f"• Волатильность доходности"
                
            except Exception as e:
                self.logger.warning(f"Could not get drawdowns statistics: {e}")
                # Fallback to basic caption
                caption = f"📉 Просадки портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                caption += f"💡 График показывает:\n"
                caption += f"• Максимальную просадку портфеля\n"
                caption += f"• Периоды восстановления\n"
                caption += f"• Волатильность доходности"
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(caption)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio drawdowns chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика просадок: {str(e)}")

    async def _handle_portfolio_returns_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle portfolio returns button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio returns button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in final_symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            self.logger.info(f"Creating returns chart for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "💰 Создаю график доходности...")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_portfolio_returns_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio returns button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика доходности: {str(e)}")

    async def _handle_portfolio_returns_by_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
        """Handle portfolio returns button click by portfolio symbol"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio returns by symbol for user {user_id}, portfolio: {portfolio_symbol}")
            
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if portfolio_symbol not in saved_portfolios:
                await self._send_callback_message(update, context, f"❌ Портфель '{portfolio_symbol}' не найден. Создайте портфель заново.")
                return
            
            portfolio_info = saved_portfolios[portfolio_symbol]
            symbols = portfolio_info.get('symbols', [])
            weights = portfolio_info.get('weights', [])
            currency = portfolio_info.get('currency', 'USD')
            
            self.logger.info(f"Retrieved portfolio data: symbols={symbols}, weights={weights}, currency={currency}")
            
            if not symbols:
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены.")
                return
            
            await self._send_callback_message(update, context, "💰 Создаю график доходности...")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_portfolio_returns_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio returns by symbol: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика доходности: {str(e)}")

    async def _create_portfolio_returns_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list):
        """Create and send portfolio returns chart"""
        try:
            self.logger.info(f"Creating portfolio returns chart for portfolio: {symbols}")
            
            # Generate annual returns chart using okama
            # portfolio.annual_return_ts.plot(kind="bar")
            returns_data = portfolio.annual_return_ts.plot(kind="bar")
            
            # Get the current figure from matplotlib (created by okama)
            current_fig = plt.gcf()
            
            # Apply chart styles to the current figure
            if current_fig.axes:
                ax = current_fig.axes[0]
                
                # Apply standard chart styling with centralized style
                chart_styles.apply_styling(
                    ax,
                    title=f'Годовая доходность портфеля\n{", ".join(symbols)}',
                    ylabel='Доходность (%)',
                    grid=True,
                    legend=False,
                    copyright=True
                )
            
            # Save the figure
            img_buffer = io.BytesIO()
            chart_styles.save_figure(current_fig, img_buffer)
            img_buffer.seek(0)
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(current_fig)
            
            # Get returns statistics
            try:
                # Get returns statistics
                mean_return_monthly = portfolio.mean_return_monthly
                mean_return_annual = portfolio.mean_return_annual
                cagr = portfolio.get_cagr()
                
                # Handle CAGR which might be a Series
                if hasattr(cagr, '__iter__') and not isinstance(cagr, str):
                    # If it's a Series or array-like, get the first value
                    if hasattr(cagr, 'iloc'):
                        cagr_value = cagr.iloc[0]
                    elif hasattr(cagr, '__getitem__'):
                        cagr_value = cagr[0]
                    else:
                        cagr_value = list(cagr)[0]
                else:
                    cagr_value = cagr
                
                # Build enhanced caption
                caption = f"💰 Годовая доходность портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                
                # Add returns statistics
                caption += f"📈 Статистика доходности:\n"
                caption += f"• Средняя месячная доходность: {mean_return_monthly:.2%}\n"
                caption += f"• Средняя годовая доходность: {mean_return_annual:.2%}\n"
                caption += f"• CAGR (Compound Annual Growth Rate): {cagr_value:.2%}\n\n"
                
                caption += f"💡 График показывает:\n"
                caption += f"• Годовую доходность по годам\n"
                caption += f"• Волатильность доходности\n"
                caption += f"• Тренды доходности портфеля"
                
            except Exception as e:
                self.logger.warning(f"Could not get returns statistics: {e}")
                # Fallback to basic caption
                caption = f"💰 Годовая доходность портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                caption += f"💡 График показывает:\n"
                caption += f"• Годовую доходность по годам\n"
                caption += f"• Волатильность доходности\n"
                caption += f"• Тренды доходности портфеля"
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(caption)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio returns chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика доходности: {str(e)}")

    async def _handle_portfolio_wealth_chart_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle portfolio wealth chart button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio wealth chart button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Filter out None values and empty strings
            final_symbols = [s for s in final_symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            self.logger.info(f"Creating wealth chart for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📈 Создаю график накопленной доходности...")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database - be more lenient
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    # Don't check price data length as it might be empty but symbol still valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_portfolio_wealth_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio wealth chart button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика накопленной доходности: {str(e)}")

    async def _create_portfolio_wealth_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list):
        """Create and send portfolio wealth chart"""
        try:
            self.logger.info(f"Creating portfolio wealth chart for portfolio: {symbols}")
            
            # Generate wealth chart using chart_styles
            wealth_index = portfolio.wealth_index
            
            # Create portfolio chart with chart_styles using optimized method
            fig, ax = chart_styles.create_portfolio_wealth_chart(
                data=wealth_index, symbols=symbols, currency=currency
            )
            
            # Save chart to bytes with memory optimization
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            img_buffer.seek(0)
            img_bytes = img_buffer.getvalue()
            
            # Clear matplotlib cache to free memory
            chart_styles.cleanup_figure(fig)
            
            # Build caption
            caption = f"📈 График накопленной доходности портфеля: {', '.join(symbols)}\n\n"
            caption += f"📊 Параметры:\n"
            caption += f"• Валюта: {currency}\n"
            caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n"
            caption += f"• Период: MAX (весь доступный период)\n\n"
            
            # Get final portfolio value safely
            try:
                final_value = portfolio.wealth_index.iloc[-1]
                
                # Handle different types of final_value
                if hasattr(final_value, '__iter__') and not isinstance(final_value, str):
                    if hasattr(final_value, 'iloc'):
                        final_value = final_value.iloc[0]
                    elif hasattr(final_value, '__getitem__'):
                        final_value = final_value[0]
                    else:
                        final_value = list(final_value)[0]
                
                # Convert to float safely
                if isinstance(final_value, (int, float)):
                    final_value = float(final_value)
                else:
                    final_value_str = str(final_value)
                    try:
                        final_value = float(final_value_str)
                    except (ValueError, TypeError):
                        import re
                        numeric_match = re.search(r'[\d.]+', final_value_str)
                        if numeric_match:
                            final_value = float(numeric_match.group())
                        else:
                            raise ValueError(f"Cannot convert {final_value} to float")
                
                caption += f"📈 Накопленная доходность: {final_value:.2f} {currency}"
            except Exception as e:
                self.logger.warning(f"Could not get final portfolio value: {e}")
                caption += f"📈 Накопленная доходность: недоступна"
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(img_bytes),
                caption=self._truncate_caption(caption)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio wealth chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика накопленной доходности: {str(e)}")

    async def _handle_portfolio_wealth_chart_by_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
        """Handle portfolio wealth chart button click by portfolio symbol"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio wealth chart by symbol for user {user_id}, portfolio: {portfolio_symbol}")
            
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if portfolio_symbol not in saved_portfolios:
                await self._send_callback_message(update, context, f"❌ Портфель '{portfolio_symbol}' не найден. Создайте портфель заново.")
                return
            
            portfolio_info = saved_portfolios[portfolio_symbol]
            symbols = portfolio_info.get('symbols', [])
            weights = portfolio_info.get('weights', [])
            currency = portfolio_info.get('currency', 'USD')
            
            self.logger.info(f"Retrieved portfolio data: symbols={symbols}, weights={weights}, currency={currency}")
            
            if not symbols:
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены.")
                return
            
            await self._send_callback_message(update, context, "📈 Создаю график накопленной доходности...")
            
            # Create portfolio and generate wealth chart
            portfolio = ok.Portfolio(symbols, weights=weights, ccy=currency)
            await self._create_portfolio_wealth_chart(update, context, portfolio, symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio wealth chart by symbol: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика накопленной доходности: {str(e)}")

    async def _handle_portfolio_rolling_cagr_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle portfolio rolling CAGR button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio rolling CAGR button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in final_symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            self.logger.info(f"Creating rolling CAGR chart for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📈 Создаю график Rolling CAGR...")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_portfolio_rolling_cagr_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio rolling CAGR button: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика Rolling CAGR: {str(e)}")

    async def _handle_portfolio_rolling_cagr_by_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
        """Handle portfolio rolling CAGR button click by portfolio symbol"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio rolling CAGR by symbol for user {user_id}, portfolio: {portfolio_symbol}")
            
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if portfolio_symbol not in saved_portfolios:
                await self._send_callback_message(update, context, f"❌ Портфель '{portfolio_symbol}' не найден. Создайте портфель заново.")
                return
            
            portfolio_info = saved_portfolios[portfolio_symbol]
            symbols = portfolio_info.get('symbols', [])
            weights = portfolio_info.get('weights', [])
            currency = portfolio_info.get('currency', 'USD')
            
            self.logger.info(f"Retrieved portfolio data: symbols={symbols}, weights={weights}, currency={currency}")
            
            if not symbols:
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены.")
                return
            
            await self._send_callback_message(update, context, "📈 Создаю график Rolling CAGR...")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_portfolio_rolling_cagr_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio rolling CAGR by symbol: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика Rolling CAGR: {str(e)}")

    async def _create_portfolio_rolling_cagr_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list):
        """Create and send portfolio rolling CAGR chart"""
        try:
            self.logger.info(f"Creating portfolio rolling CAGR chart for portfolio: {symbols}")
            
            # Get rolling CAGR data
            rolling_cagr_data = portfolio.get_rolling_cagr()
            
            # Create standardized rolling CAGR chart using chart_styles
            fig, ax = chart_styles.create_portfolio_rolling_cagr_chart(
                data=rolling_cagr_data, symbols=symbols, currency=currency
            )
            
            # Save the figure using standardized method
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            chart_styles.cleanup_figure(fig)
            img_buffer.seek(0)
            
            # Get rolling CAGR statistics
            try:
                # Get rolling CAGR data for statistics
                rolling_cagr_series = portfolio.get_rolling_cagr()
                
                # Calculate statistics
                mean_rolling_cagr = rolling_cagr_series.mean()
                std_rolling_cagr = rolling_cagr_series.std()
                min_rolling_cagr = rolling_cagr_series.min()
                max_rolling_cagr = rolling_cagr_series.max()
                current_rolling_cagr = rolling_cagr_series.iloc[-1] if not rolling_cagr_series.empty else None
                
                # Build enhanced caption
                caption = f"📈 Rolling CAGR (MAX период) портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n"
                caption += f"• Окно: MAX период (весь доступный период)\n\n"
                
                # Add rolling CAGR statistics
                caption += f"📈 Статистика Rolling CAGR:\n"
                if current_rolling_cagr is not None:
                    caption += f"• Текущий Rolling CAGR: {current_rolling_cagr:.2%}\n"
                caption += f"• Средний Rolling CAGR: {mean_rolling_cagr:.2%}\n"
                caption += f"• Стандартное отклонение: {std_rolling_cagr:.2%}\n"
                caption += f"• Минимальный: {min_rolling_cagr:.2%}\n"
                caption += f"• Максимальный: {max_rolling_cagr:.2%}\n\n"
                
                caption += f"💡 График показывает:\n"
                caption += f"• Rolling CAGR за весь доступный период\n"
                caption += f"• Динамику изменения CAGR во времени\n"
                caption += f"• Стабильность доходности портфеля"
                
            except Exception as e:
                self.logger.warning(f"Could not get rolling CAGR statistics: {e}")
                # Fallback to basic caption
                caption = f"📈 Rolling CAGR (MAX период) портфеля: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n"
                caption += f"• Окно: MAX период (весь доступный период)\n\n"
                caption += f"💡 График показывает:\n"
                caption += f"• Rolling CAGR за весь доступный период\n"
                caption += f"• Динамику изменения CAGR во времени\n"
                caption += f"• Стабильность доходности портфеля"
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(caption)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio rolling CAGR chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика Rolling CAGR: {str(e)}")

    async def _handle_portfolio_compare_assets_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, symbols: list):
        """Handle portfolio compare assets button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio compare assets button for user {user_id}")
            
            user_context = self._get_user_context(user_id)
            self.logger.info(f"User context content: {user_context}")
            
            # Prefer symbols passed from the button payload; fallback to context
            button_symbols = symbols
            final_symbols = button_symbols or user_context.get('current_symbols') or user_context.get('last_assets')
            self.logger.info(f"Available keys in user context: {list(user_context.keys())}")
            self.logger.info(f"Button symbols: {button_symbols}")
            self.logger.info(f"Final symbols: {final_symbols}")
            self.logger.info(f"Current symbols from context: {user_context.get('current_symbols')}")
            self.logger.info(f"Last assets from context: {user_context.get('last_assets')}")
            
            if not final_symbols:
                self.logger.warning("No symbols provided by button and none found in context")
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены. Выполните команду /portfolio заново.")
                return
            
            # Check if we have portfolio-specific data
            portfolio_weights = user_context.get('portfolio_weights', [])
            portfolio_currency = user_context.get('current_currency', 'USD')
            
            # If we have portfolio weights, use them; otherwise use equal weights
            if portfolio_weights and len(portfolio_weights) == len(final_symbols):
                weights = portfolio_weights
                currency = portfolio_currency
                self.logger.info(f"Using stored portfolio weights: {weights}")
            else:
                # Fallback to equal weights if no portfolio weights found
                weights = self._normalize_or_equalize_weights(final_symbols, [])
                currency = user_context.get('current_currency', 'USD')
                self.logger.info(f"Using equal weights as fallback: {weights}")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in final_symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            self.logger.info(f"Creating compare assets chart for portfolio: {final_symbols}, currency: {currency}, weights: {weights}")
            await self._send_callback_message(update, context, "📊 Создаю график сравнения с активами...")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_portfolio_compare_assets_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio compare assets button: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика сравнения: {str(e)}")

    async def _handle_portfolio_compare_assets_by_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio_symbol: str):
        """Handle portfolio compare assets button click by portfolio symbol"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling portfolio compare assets by symbol for user {user_id}, portfolio: {portfolio_symbol}")
            
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if portfolio_symbol not in saved_portfolios:
                await self._send_callback_message(update, context, f"❌ Портфель '{portfolio_symbol}' не найден. Создайте портфель заново.")
                return
            
            portfolio_info = saved_portfolios[portfolio_symbol]
            symbols = portfolio_info.get('symbols', [])
            weights = portfolio_info.get('weights', [])
            currency = portfolio_info.get('currency', 'USD')
            
            self.logger.info(f"Retrieved portfolio data: symbols={symbols}, weights={weights}, currency={currency}")
            
            if not symbols:
                await self._send_callback_message(update, context, "❌ Данные о портфеле не найдены.")
                return
            
            await self._send_callback_message(update, context, "📊 Создаю график сравнения с активами...")
            
            # Filter out None values and empty strings
            final_symbols = [s for s in symbols if s is not None and str(s).strip()]
            if not final_symbols:
                self.logger.warning("All symbols were None or empty after filtering")
                await self._send_callback_message(update, context, "❌ Все символы пустые или недействительны.")
                return
            
            self.logger.info(f"Filtered symbols: {final_symbols}")
            
            # Validate symbols before creating portfolio
            valid_symbols = []
            valid_weights = []
            invalid_symbols = []
            
            for i, symbol in enumerate(final_symbols):
                try:
                    # Debug logging
                    self.logger.info(f"Validating symbol {i}: '{symbol}' (type: {type(symbol)})")
                    
                    # Test if symbol exists in database
                    test_asset = ok.Asset(symbol)
                    # If asset was created successfully, consider it valid
                    valid_symbols.append(symbol)
                    valid_weights.append(weights[i])
                    self.logger.info(f"Symbol {symbol} validated successfully")
                except Exception as e:
                    invalid_symbols.append(symbol)
                    self.logger.warning(f"Symbol {symbol} is invalid: {e}")
            
            if not valid_symbols:
                error_msg = f"❌ Все символы недействительны: {', '.join(invalid_symbols)}"
                if any('.FX' in s for s in invalid_symbols):
                    error_msg += "\n\n💡 Валютные пары (.FX) могут быть недоступны в базе данных okama."
                await self._send_callback_message(update, context, error_msg)
                return
            
            if invalid_symbols:
                await self._send_callback_message(update, context, f"⚠️ Некоторые символы недоступны: {', '.join(invalid_symbols)}")
            
            # Normalize weights for valid symbols
            if valid_weights:
                total_weight = sum(valid_weights)
                if total_weight > 0:
                    valid_weights = [w / total_weight for w in valid_weights]
                else:
                    valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            else:
                valid_weights = [1.0 / len(valid_symbols)] * len(valid_symbols)
            
            # Create Portfolio with validated symbols
            portfolio = ok.Portfolio(valid_symbols, weights=valid_weights, ccy=currency)
            
            await self._create_portfolio_compare_assets_chart(update, context, portfolio, final_symbols, currency, weights)
            
        except Exception as e:
            self.logger.error(f"Error handling portfolio compare assets by symbol: {e}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика сравнения: {str(e)}")

    async def _create_portfolio_compare_assets_chart(self, update: Update, context: ContextTypes.DEFAULT_TYPE, portfolio, symbols: list, currency: str, weights: list):
        """Create and send portfolio compare assets chart"""
        try:
            self.logger.info(f"Creating portfolio compare assets chart for portfolio: {symbols}")
            
            # Get wealth index with assets data
            compare_data = portfolio.wealth_index_with_assets
            
            # Create standardized comparison chart using chart_styles
            fig, ax = chart_styles.create_portfolio_compare_assets_chart(
                data=compare_data, symbols=symbols, currency=currency
            )
            
            # Save the figure using standardized method
            img_buffer = io.BytesIO()
            chart_styles.save_figure(fig, img_buffer)
            chart_styles.cleanup_figure(fig)
            img_buffer.seek(0)
            
            # Get portfolio comparison statistics
            try:
                # Build enhanced caption
                caption = f"📊 Портфель vs Активы: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                
                # Add portfolio performance vs individual assets
                portfolio_final = portfolio.wealth_index.iloc[-1]
                caption += f"📈 Итоговые значения (накопленная доходность):\n"
                caption += f"• Портфель: {portfolio_final:.2f}\n"
                
                # Get individual asset final values
                for symbol in symbols:
                    try:
                        # Validate symbol before creating Asset
                        if not symbol or symbol.strip() == '':
                            self.logger.warning(f"Empty symbol: '{symbol}'")
                            caption += f"• {symbol}: недоступно\n"
                            continue
                        
                        # Check for invalid characters
                        invalid_chars = ['(', ')', ',']
                        if any(char in symbol for char in invalid_chars):
                            self.logger.warning(f"Invalid symbol contains brackets: '{symbol}'")
                            caption += f"• {symbol}: недоступно\n"
                            continue
                        
                        # Check for proper format
                        if '.' not in symbol:
                            self.logger.warning(f"Symbol missing namespace separator: '{symbol}'")
                            caption += f"• {symbol}: недоступно\n"
                            continue
                        
                        # Get individual asset
                        asset = ok.Asset(symbol, ccy=currency)
                        
                        # Calculate wealth index from price data
                        price_data = asset.price
                        self.logger.info(f"DEBUG: Price data type for {symbol}: {type(price_data)}")
                        
                        # Handle different types of price data
                        if price_data is None:
                            caption += f"• {symbol}: недоступно\n"
                        elif isinstance(price_data, (int, float)):
                            # Single price value - use it directly
                            self.logger.info(f"DEBUG: Single price value for {symbol}: {price_data}")
                            asset_final = float(price_data)
                            caption += f"• {symbol}: {asset_final:.2f}\n"
                        elif hasattr(price_data, '__len__') and len(price_data) > 0:
                            # Time series data - calculate cumulative returns
                            self.logger.info(f"DEBUG: Time series data for {symbol}, length: {len(price_data)}")
                            returns = price_data.pct_change().dropna()
                            wealth_index = (1 + returns).cumprod()
                            asset_final = wealth_index.iloc[-1]
                            caption += f"• {symbol}: {asset_final:.2f}\n"
                        else:
                            caption += f"• {symbol}: недоступно\n"
                    except Exception as e:
                        self.logger.warning(f"Could not get final value for {symbol}: {e}")
                        caption += f"• {symbol}: недоступно\n"
                
                caption += f"\n💡 График показывает:\n"
                caption += f"• Накопленную доходность портфеля vs отдельных активов\n"
                caption += f"• Эффект диверсификации\n"
                caption += f"• Сравнение рисков и доходности"
                
            except Exception as e:
                self.logger.warning(f"Could not get comparison statistics: {e}")
                # Fallback to basic caption
                caption = f"📊 Портфель vs Активы: {', '.join(symbols)}\n\n"
                caption += f"📊 Параметры:\n"
                caption += f"• Валюта: {currency}\n"
                caption += f"• Веса: {', '.join([f'{w:.1%}' for w in weights])}\n\n"
                caption += f"💡 График показывает:\n"
                caption += f"• Накопленную доходность портфеля vs отдельных активов\n"
                caption += f"• Эффект диверсификации\n"
                caption += f"• Сравнение рисков и доходности"
            
            # Send the chart
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=img_buffer,
                caption=self._truncate_caption(caption)
            )
            
        except Exception as e:
            self.logger.error(f"Error creating portfolio compare assets chart: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании графика сравнения: {str(e)}")

    async def _handle_namespace_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, namespace: str):
        """Handle namespace button click - show symbols in specific namespace"""
        try:
            self.logger.info(f"Handling namespace button for: {namespace}")
            
            # Use the unified method that handles both okama and tushare
            await self._show_namespace_symbols(update, context, namespace, is_callback=True)
                
        except ImportError:
            await self._send_callback_message(update, context, "❌ Библиотека okama не установлена")
        except Exception as e:
            self.logger.error(f"Error in namespace button handler: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка: {str(e)}")

    async def _handle_excel_namespace_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE, namespace: str):
        """Handle Excel export button click for namespace"""
        try:
            self.logger.info(f"Handling Excel export for namespace: {namespace}")
            
            # Check if it's a Chinese exchange
            chinese_exchanges = ['SSE', 'SZSE', 'BSE', 'HKEX']
            if namespace in chinese_exchanges:
                await self._handle_tushare_excel_export(update, context, namespace)
                return
            
            # Get symbols in namespace for non-Chinese exchanges
            try:
                symbols_df = ok.symbols_in_namespace(namespace)
                
                # Check if DataFrame is empty
                if symbols_df.empty:
                    await self._send_callback_message(update, context, f"❌ Пространство имен '{namespace}' не найдено или пусто")
                    return
                
                total_symbols = len(symbols_df)
                
                # Show progress message
                await self._send_callback_message(update, context, f"📊 Создаю Excel файл...")
                
                # Create Excel file in memory
                excel_buffer = io.BytesIO()
                symbols_df.to_excel(excel_buffer, index=False, sheet_name=f'{namespace}_Symbols')
                excel_buffer.seek(0)
                
                # Send Excel file
                await context.bot.send_document(
                    chat_id=update.effective_chat.id,
                    document=excel_buffer,
                    filename=f"{namespace}_symbols.xlsx",
                    caption=self._truncate_caption(f"📊 Полный список символов в пространстве {namespace} ({total_symbols})")
                )
                
                excel_buffer.close()
                
            except Exception as e:
                await self._send_callback_message(update, context, f"❌ Ошибка при получении символов для '{namespace}': {str(e)}")
                
        except ImportError:
            await self._send_callback_message(update, context, "❌ Библиотека okama не установлена")
        except Exception as e:
            self.logger.error(f"Error in Excel namespace button handler: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка: {str(e)}")

    async def _handle_tushare_excel_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE, namespace: str):
        """Handle Excel export for Chinese exchanges using Tushare"""
        try:
            if not self.tushare_service:
                await self._send_callback_message(update, context, "❌ Сервис Tushare недоступен")
                return
            
            # Show progress message
            await self._send_callback_message(update, context, f"📊 Создаю Excel файл для {namespace}...")
            
            # Get ALL symbols data from Tushare (no limit for Excel export)
            symbols_data = self.tushare_service.get_exchange_symbols_full(namespace)
            total_count = len(symbols_data)
            
            if not symbols_data:
                await self._send_callback_message(update, context, f"❌ Символы для биржи '{namespace}' не найдены")
                return
            
            # Create DataFrame from symbols data
            df = pd.DataFrame(symbols_data)
            
            # Add additional columns for better Excel formatting
            df['Exchange'] = namespace
            df['Exchange_Name'] = {
                'SSE': 'Shanghai Stock Exchange',
                'SZSE': 'Shenzhen Stock Exchange',
                'BSE': 'Beijing Stock Exchange',
                'HKEX': 'Hong Kong Stock Exchange'
            }.get(namespace, namespace)
            
            # Reorder columns
            df = df[['symbol', 'name', 'currency', 'list_date', 'Exchange', 'Exchange_Name']]
            
            # Rename columns for better readability
            df.columns = ['Symbol', 'Company Name', 'Currency', 'List Date', 'Exchange Code', 'Exchange Name']
            
            # Create Excel file in memory
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name=f'{namespace}_Symbols')
                
                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets[f'{namespace}_Symbols']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            excel_buffer.seek(0)
            
            # Send Excel file
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=excel_buffer,
                filename=f"{namespace}_symbols.xlsx",
                caption=self._truncate_caption(f"📊 Полный список символов биржи {namespace} ({total_count:,} символов)")
            )
            
            excel_buffer.close()
            
        except Exception as e:
            self.logger.error(f"Error in Tushare Excel export for {namespace}: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при создании Excel файла: {str(e)}")

    async def _handle_clear_all_portfolios_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle clear all portfolios button click"""
        try:
            user_id = update.effective_user.id
            self.logger.info(f"Handling clear all portfolios button for user {user_id}")
            
            # Get user context
            user_context = self._get_user_context(user_id)
            saved_portfolios = user_context.get('saved_portfolios', {})
            
            if not saved_portfolios:
                await self._send_callback_message(update, context, "💼 У вас нет сохраненных портфелей для очистки")
                return
            
            # Count portfolios before clearing
            portfolio_count = len(saved_portfolios)
            
            # Clear all portfolios
            user_context['saved_portfolios'] = {}
            user_context['portfolio_count'] = 0
            
            # Update context
            self._update_user_context(user_id, **user_context)
            
            # Send confirmation message
            await self._send_callback_message(
                update, 
                context, 
                f"🗑️ **Очистка завершена!**\n\n"
                f"✅ Удалено портфелей: {portfolio_count}\n"
                f"✅ Счетчик портфелей сброшен\n\n"
                f"💡 Для создания новых портфелей используйте команду `/portfolio`"
            )
            
            self.logger.info(f"Successfully cleared {portfolio_count} portfolios for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error in clear all portfolios button handler: {e}")
            await self._send_callback_message(update, context, f"❌ Ошибка при очистке портфелей: {str(e)}")

    def run(self):
        """Run the bot"""
        # Create application
        application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("info", self.info_command))
        application.add_handler(CommandHandler("list", self.namespace_command))
        application.add_handler(CommandHandler("gemini_status", self.gemini_status_command))
        application.add_handler(CommandHandler("compare", self.compare_command))
        application.add_handler(CommandHandler("portfolio", self.portfolio_command))
        application.add_handler(CommandHandler("my", self.my_portfolios_command))
        
        # Add callback query handler for buttons
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Add message handler for waiting user input after empty /info
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Start the bot
        logger.info("Starting Okama Finance Bot...")
        application.run_polling()

    def _check_existing_portfolio(self, symbols: List[str], weights: List[float], saved_portfolios: Dict) -> Optional[str]:
        """
        Проверяет, существует ли портфель с такими же активами и пропорциями.
        
        Args:
            symbols: Список символов активов
            weights: Список весов активов
            saved_portfolios: Словарь сохраненных портфелей
            
        Returns:
            Символ существующего портфеля или None, если не найден
        """
        # Нормализуем веса для сравнения (сумма = 1.0)
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        for portfolio_symbol, portfolio_info in saved_portfolios.items():
            existing_symbols = portfolio_info.get('symbols', [])
            existing_weights = portfolio_info.get('weights', [])
            
            # Проверяем количество активов
            if len(symbols) != len(existing_symbols):
                continue
                
            # Проверяем, что все символы совпадают (с учетом регистра)
            if set(symbol.upper() for symbol in symbols) != set(symbol.upper() for symbol in existing_symbols):
                continue
                
            # Нормализуем существующие веса
            existing_total = sum(existing_weights)
            if existing_total == 0:
                continue
            normalized_existing_weights = [w / existing_total for w in existing_weights]
            
            # Проверяем, что веса совпадают с точностью до 0.001
            weight_matches = True
            for i, (new_weight, existing_weight) in enumerate(zip(normalized_weights, normalized_existing_weights)):
                if abs(new_weight - existing_weight) > 0.001:
                    weight_matches = False
                    break
                    
            if weight_matches:
                return portfolio_symbol
                
        return None

if __name__ == "__main__":
    try:
        logger.info(f"Starting Okama Finance Bot with Python {sys.version}")
        logger.info(f"Python version info: {sys.version_info}")
        
        # Perform health check
        health_check()
        
        # Optional HTTP health server for platforms expecting an open PORT
        port_env = os.getenv('PORT')
        if port_env:
            try:
                bind_port = int(port_env)
                class HealthHandler(BaseHTTPRequestHandler):
                    def do_GET(self):
                        payload = {
                            "status": "ok",
                            "service": "okama-finance-bot",
                            "environment": "RENDER" if os.getenv('RENDER') else "LOCAL"
                        }
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(payload).encode('utf-8'))
                    def log_message(self, format, *args):
                        return
                def serve_health():
                    server = HTTPServer(('0.0.0.0', bind_port), HealthHandler)
                    logger.info(f"Health server listening on 0.0.0.0:{bind_port}")
                    server.serve_forever()
                threading.Thread(target=serve_health, daemon=True).start()
            except Exception as e:
                logger.warning(f"Failed to start health server on PORT={port_env}: {e}")
        
        if sys.version_info >= (3, 13):
            logger.info("✅ Running on Python 3.13+ with latest python-telegram-bot")
        elif sys.version_info >= (3, 12):
            logger.info("✅ Running on Python 3.12+ with latest python-telegram-bot")
        
        logger.info("🚀 Initializing bot services...")
        bot = ShansAi()
        logger.info("✅ Bot services initialized successfully")
        logger.info("🤖 Starting Telegram bot...")
        bot.run()
    except Exception as e:
        logger.error(f"❌ Fatal error starting bot: {e}")
        logger.error(f"Python version: {sys.version}")
        logger.error(f"Python executable: {sys.executable}")
        traceback.print_exc()
        sys.exit(1)

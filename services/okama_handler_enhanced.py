"""
Enhanced Okama Handler

Расширенный обработчик для работы с okama API, включающий:
- Конвертацию валют
- Поддержку временных периодов
- Обработку всех типов намерений
- Улучшенную обработку ошибок
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EnhancedOkamaHandler:
    """Улучшенный обработчик okama с расширенной функциональностью"""
    
    def __init__(self):
        self.default_period = "5Y"
        self.max_period = "20Y"
        self.max_assets = 20
        
    def process_request(self, intent: str, assets: List[str], **kwargs) -> Dict[str, Any]:
        """Основной метод обработки запроса"""
        try:
            # Проверяем лимиты
            self._validate_request(assets, kwargs.get('period'))
            
            # Определяем период
            period = self._determine_period(kwargs.get('period'), kwargs.get('since_date'), kwargs.get('to_date'))
            
            # Определяем валюту
            currency = kwargs.get('currency') or self._get_default_currency(assets)
            convert_to = kwargs.get('convert_to')

            # Валидация количества активов в зависимости от намерения
            if intent == 'asset_single' and len(assets) < 1:
                return {
                    'error': 'Не указан актив. Укажите тикер, например AAPL.US, SBER.MOEX, GC.COMM',
                    'intent': intent,
                    'assets': assets,
                    'success': False
                }
            if intent == 'asset_compare' and len(assets) < 2:
                return {
                    'error': 'Для сравнения укажите минимум два актива.',
                    'intent': intent,
                    'assets': assets,
                    'success': False
                }
            if intent == 'portfolio_analysis' and len(assets) < 2:
                return {
                    'error': 'Для анализа портфеля укажите минимум два актива.',
                    'intent': intent,
                    'assets': assets,
                    'success': False
                }
            if intent == 'macro_data' and len(assets) < 1:
                return {
                    'error': 'Укажите актив(ы) для макроанализа, например BRENT.COMM или EURUSD.FX.',
                    'intent': intent,
                    'assets': assets,
                    'success': False
                }
            
            # Обрабатываем запрос в зависимости от намерения
            if intent == 'asset_single':
                return self._handle_single_asset(assets[0], period, currency, convert_to)
            elif intent == 'asset_compare':
                return self._handle_asset_comparison(assets, period, currency, convert_to)
            elif intent == 'portfolio_analysis':
                weights = kwargs.get('weights')
                return self._handle_portfolio_analysis(assets, weights, period, currency, convert_to)
            elif intent == 'inflation_data':
                country = kwargs.get('country', 'US')
                return self._handle_inflation_data(country, period)
            elif intent == 'macro_data':
                return self._handle_macro_data(assets, period, currency, convert_to)
            else:
                raise ValueError(f"Неподдерживаемый тип намерения: {intent}")
                
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                'error': str(e),
                'intent': intent,
                'assets': assets,
                'success': False
            }
    
    def _validate_request(self, assets: List[str], period: Optional[str]) -> None:
        """Проверяет корректность запроса"""
        if len(assets) > self.max_assets:
            raise ValueError(f"Превышен лимит активов: {len(assets)} > {self.max_assets}")
        
        if period:
            # Проверяем период
            period_years = self._parse_period(period)
            if period_years > 20:
                raise ValueError(f"Период слишком большой: {period_years} лет > 20 лет")
    
    def _determine_period(self, period: Optional[str], since_date: Optional[str], to_date: Optional[str]) -> str:
        """Определяет период для анализа"""
        if period:
            return period
        
        if since_date and to_date:
            try:
                since = int(since_date)
                to = int(to_date)
                years = to - since
                return f"{years}Y"
            except ValueError:
                pass
        
        return self.default_period
    
    def _get_default_currency(self, assets: List[str]) -> str:
        """Определяет валюту по умолчанию"""
        if not assets:
            return 'USD'
        
        # Определяем валюту по первому активу
        asset = assets[0]
        if asset.endswith('.MOEX'):
            return 'RUB'
        elif asset.endswith('.US') or asset.endswith('.INDX') or asset.endswith('.COMM'):
            return 'USD'
        elif asset.endswith('.FX'):
            return 'USD'
        else:
            return 'USD'
    
    def _handle_single_asset(self, asset: str, period: str, currency: str, convert_to: Optional[str]) -> Dict[str, Any]:
        """Обрабатывает запрос по одному активу"""
        try:
            import okama as ok
            
            # Создаем актив
            ok_asset = ok.Asset(asset)
            
            # Получаем данные
            prices = ok_asset.price
            info = {
                'ticker': asset,
                'currency': getattr(ok_asset, 'currency', currency),
                'name': getattr(ok_asset, 'name', asset),
                'period': period
            }
            
            # Конвертируем валюту если нужно
            if convert_to and convert_to != currency:
                prices = self._convert_currency(prices, currency, convert_to)
                info['currency'] = convert_to
            
            # Вычисляем метрики
            metrics = self._compute_metrics(prices, period)
            info.update({
                'prices': prices,
                'metrics': metrics,
                'converted_currency': convert_to
            })
            
            return info
            
        except Exception as e:
            logger.error(f"Error handling single asset {asset}: {e}")
            raise
    
    def _handle_asset_comparison(self, assets: List[str], period: str, currency: str, convert_to: Optional[str]) -> Dict[str, Any]:
        """Обрабатывает запрос по сравнению активов"""
        try:
            import okama as ok
            
            # Попытка использовать высокоуровневый список активов okama.AssetList
            assetlist_data: Dict[str, Any] = {}
            base_ccy = convert_to or currency
            try:
                al = ok.AssetList(assets, ccy=base_ccy)
                # Дополнительные возможности из okama.AssetList
                try:
                    assetlist_data['names'] = getattr(al, 'names', {})
                except Exception:
                    assetlist_data['names'] = {}
                try:
                    assetlist_data['wealth_indexes'] = getattr(al, 'wealth_indexes', None)
                except Exception:
                    assetlist_data['wealth_indexes'] = None
                try:
                    assetlist_data['drawdowns'] = getattr(al, 'drawdowns', None)
                except Exception:
                    assetlist_data['drawdowns'] = None
                try:
                    assetlist_data['dividend_yield'] = getattr(al, 'dividend_yield', None)
                except Exception:
                    assetlist_data['dividend_yield'] = None
                try:
                    assetlist_data['assets_ror'] = getattr(al, 'assets_ror', None)
                except Exception:
                    assetlist_data['assets_ror'] = None
                try:
                    # Табличный обзор ключевых метрик за стандартные периоды
                    # Используем 1 и 10 лет по умолчанию, как в примере
                    assetlist_data['describe'] = al.describe(years=[1, 10])
                except Exception:
                    assetlist_data['describe'] = None
                try:
                    ror_df = assetlist_data.get('assets_ror')
                    if ror_df is not None and hasattr(ror_df, 'cov'):
                        assetlist_data['covariance'] = ror_df.cov()
                    else:
                        assetlist_data['covariance'] = None
                except Exception:
                    assetlist_data['covariance'] = None
                try:
                    # Скользящая корреляция с бенчмарком (первый актив) за 5 лет по месяцам
                    if hasattr(al, 'index_corr'):
                        assetlist_data['index_corr'] = al.index_corr(rolling_window=12 * 5)
                    else:
                        assetlist_data['index_corr'] = None
                except Exception:
                    assetlist_data['index_corr'] = None
            except Exception as e:
                # Если не удалось построить AssetList, продолжим с ручной агрегацией ниже
                assetlist_data = {'assetlist_error': str(e)}
            
            # Получаем данные по каждому активу (fallback и для совместимости с существующими графиками)
            asset_data = {}
            for asset in assets:
                try:
                    ok_asset = ok.Asset(asset)
                    prices = ok_asset.price
                    # Конвертируем валюту если нужно (используем исходную валюту оценивания, а не валюту актива)
                    if convert_to and convert_to != currency:
                        prices = self._convert_currency(prices, currency, convert_to)
                    asset_data[asset] = prices
                except Exception as e:
                    logger.warning(f"Could not get data for {asset}: {e}")
                    continue
            
            if not asset_data and not assetlist_data:
                raise ValueError("Не удалось получить данные ни по одному активу")
            
            # Выравниваем индексы и считаем доходности (fallback)
            try:
                import pandas as pd
                aligned_data = pd.concat(asset_data.values(), axis=1, join='inner') if asset_data else pd.DataFrame()
                if not aligned_data.empty:
                    aligned_data.columns = list(asset_data.keys())
                returns_data = aligned_data.pct_change().dropna() if not aligned_data.empty else pd.DataFrame()
                metrics = {}
                for asset in assets:
                    if asset in aligned_data:
                        asset_prices = aligned_data[asset].dropna()
                        metrics[asset] = self._compute_metrics(asset_prices, period)
                # Корреляция из доходностей (или из AssetList если доступно)
                correlation = (
                    returns_data.corr().fillna(0.0) if not returns_data.empty else (
                        assetlist_data.get('assets_ror').corr().fillna(0.0) if isinstance(assetlist_data.get('assets_ror'), pd.DataFrame) and not assetlist_data.get('assets_ror').empty else pd.DataFrame()
                    )
                )
            except Exception as e:
                logger.warning(f"Error processing asset data: {e}")
                aligned_data = pd.DataFrame()
                returns_data = pd.DataFrame()
                metrics = {}
                correlation = pd.DataFrame()
            
            # Собираем итог
            result = {
                'tickers': assets,
                'prices': aligned_data,
                'returns': returns_data,
                'metrics': metrics,
                'correlation': correlation,
                'period': period,
                'currency': base_ccy,
                'converted_currency': convert_to
            }
            # Вкладываем дополнительные поля из AssetList, если есть
            result.update(assetlist_data)
            return result
            
        except Exception as e:
            logger.error(f"Error handling asset comparison: {e}")
            raise
    
    def _handle_portfolio_analysis(self, assets: List[str], weights: Optional[List[float]], 
                                 period: str, currency: str, convert_to: Optional[str]) -> Dict[str, Any]:
        """Обрабатывает запрос по анализу портфеля"""
        try:
            import okama as ok
            
            # Определяем веса
            if not weights or len(weights) != len(assets):
                weights = [1.0 / len(assets)] * len(assets)
            
            # Создаем портфель
            portfolio = ok.Portfolio(assets=assets, weights=weights)
            
            # Получаем данные портфеля
            try:
                portfolio_prices = portfolio.nav
            except AttributeError:
                try:
                    portfolio_prices = portfolio.portfolio_value
                except AttributeError:
                    # Создаем синтетический портфель
                    portfolio_prices = self._create_synthetic_portfolio(assets, weights)
            
            # Конвертируем валюту если нужно
            if convert_to and convert_to != currency:
                portfolio_prices = self._convert_currency(portfolio_prices, currency, convert_to)
            
            # Вычисляем метрики портфеля
            portfolio_returns = portfolio_prices.pct_change().dropna()
            portfolio_metrics = self._compute_metrics(portfolio_prices, period)
            
            # Строим efficient frontier
            frontier = None
            try:
                ef = ok.EfficientFrontier(assets=assets)
                frontier = ef.efficient_frontier()
            except Exception as e:
                logger.warning(f"Could not build efficient frontier: {e}")
            
            return {
                'tickers': assets,
                'weights': weights,
                'portfolio_prices': portfolio_prices,
                'portfolio_returns': portfolio_returns,
                'metrics': portfolio_metrics,
                'frontier': frontier,
                'period': period,
                'currency': convert_to or currency,
                'converted_currency': convert_to
            }
            
        except Exception as e:
            logger.error(f"Error handling portfolio analysis: {e}")
            raise
    
    def _handle_inflation_data(self, country: str, period: str) -> Dict[str, Any]:
        """Обрабатывает запрос по данным инфляции"""
        try:
            import okama as ok
            
            # Определяем тикер инфляции
            inflation_tickers = {
                'US': 'US.INFL',
                'RU': 'RUS.INFL',
                'EU': 'EU.INFL'
            }
            
            ticker = inflation_tickers.get(country.upper(), 'US.INFL')
            
            # Получаем данные
            asset = ok.Asset(ticker)
            cpi_data = asset.price
            
            # Вычисляем метрики
            metrics = self._compute_metrics(cpi_data, period)
            
            return {
                'ticker': ticker,
                'country': country,
                'cpi': cpi_data,
                'metrics': metrics,
                'period': period
            }
            
        except Exception as e:
            logger.error(f"Error handling inflation data: {e}")
            raise
    
    def _handle_macro_data(self, assets: List[str], period: str, currency: str, convert_to: Optional[str]) -> Dict[str, Any]:
        """Обрабатывает запрос по макроэкономическим данным"""
        # Для макро-данных используем сравнение активов
        if len(assets) >= 2:
            return self._handle_asset_comparison(assets, period, currency, convert_to)
        elif len(assets) == 1:
            return self._handle_single_asset(assets[0], period, currency, convert_to)
        else:
            raise ValueError("Для макро-анализа необходимо указать активы")
    
    def _compute_metrics(self, prices: pd.Series, period: str) -> Dict[str, Any]:
        """Вычисляет финансовые метрики"""
        if prices.empty:
            return {
                'cagr': None,
                'volatility': None,
                'sharpe': None,
                'max_drawdown': None,
                'total_return': None
            }
        
        # Конвертируем в доходности
        returns = prices.pct_change().dropna()
        
        # CAGR
        n_years = self._parse_period(period)
        if n_years > 0:
            total_return = (prices.iloc[-1] / prices.iloc[0]) - 1.0
            cagr = (1.0 + total_return) ** (1.0 / n_years) - 1.0 if total_return > -0.9999 else None
        else:
            cagr = None
            total_return = None
        
        # Волатильность
        periods_per_year = 252 if len(returns) > 200 else (12 if len(returns) > 20 else 52)
        volatility = float(np.std(returns, ddof=1)) * np.sqrt(periods_per_year) if len(returns) > 1 else None
        
        # Sharpe ratio
        if volatility and volatility > 0:
            mean_return = float(np.mean(returns)) * periods_per_year
            sharpe = mean_return / volatility
        else:
            sharpe = None
        
        # Максимальная просадка
        if len(prices) > 1:
            cummax = prices.cummax()
            drawdowns = prices / cummax - 1.0
            max_drawdown = float(drawdowns.min())
        else:
            max_drawdown = None
        
        return {
            'cagr': cagr,
            'volatility': volatility,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown,
            'total_return': total_return
        }
    
    def _parse_period(self, period: str) -> float:
        """Парсит период в годах"""
        if not period:
            return 5.0
        
        # Убираем 'Y' и конвертируем в число
        try:
            return float(period.replace('Y', ''))
        except ValueError:
            return 5.0
    
    def _convert_currency(self, prices: pd.Series, from_currency: str, to_currency: str) -> pd.Series:
        """Конвертирует цены в другую валюту"""
        try:
            import okama as ok
            
            # Получаем курс конвертации
            if from_currency == to_currency:
                return prices
            
            # Создаем валютную пару
            if from_currency == 'USD' and to_currency == 'RUB':
                rate_asset = ok.Asset('USDRUB.FX')
            elif from_currency == 'RUB' and to_currency == 'USD':
                rate_asset = ok.Asset('RUBUSD.FX')
            elif from_currency == 'EUR' and to_currency == 'USD':
                rate_asset = ok.Asset('EURUSD.FX')
            elif from_currency == 'USD' and to_currency == 'EUR':
                rate_asset = ok.Asset('USDEUR.FX')
            else:
                # Для других валют используем USD как промежуточную
                if from_currency != 'USD':
                    usd_prices = self._convert_currency(prices, from_currency, 'USD')
                else:
                    usd_prices = prices
                
                if to_currency != 'USD':
                    return self._convert_currency(usd_prices, 'USD', to_currency)
                else:
                    return usd_prices
            
            # Получаем курс
            rate = rate_asset.price
            
            # Выравниваем индексы
            aligned_data = pd.concat([prices, rate], axis=1, join='inner')
            if len(aligned_data.columns) >= 2:
                converted_prices = aligned_data.iloc[:, 0] * aligned_data.iloc[:, 1]
                return converted_prices
            else:
                return prices
                
        except Exception as e:
            logger.warning(f"Currency conversion failed: {e}")
            return prices
    
    def _create_synthetic_portfolio(self, assets: List[str], weights: List[float]) -> pd.Series:
        """Создает синтетический портфель"""
        try:
            import okama as ok
            
            # Получаем данные по каждому активу
            asset_data = {}
            for asset in assets:
                try:
                    ok_asset = ok.Asset(asset)
                    asset_data[asset] = ok_asset.price
                except Exception as e:
                    logger.warning(f"Could not get data for {asset}: {e}")
                    continue
            
            if not asset_data:
                raise ValueError("No valid asset data available")
            
            # Выравниваем индексы
            aligned_data = pd.concat(asset_data.values(), axis=1, join='inner')
            aligned_data.columns = list(asset_data.keys())
            
            # Вычисляем взвешенную сумму
            portfolio_values = (aligned_data * weights[:len(aligned_data.columns)]).sum(axis=1)
            
            return portfolio_values
            
        except Exception as e:
            logger.error(f"Error creating synthetic portfolio: {e}")
            # Fallback - создаем простую временную серию
            dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
            return pd.Series([100.0] * len(dates), index=dates)

    def get_inflation(self, country: str = 'US', period: str = '5Y') -> Dict[str, Any]:
        """Получает данные по инфляции (совместимость с bot.py)"""
        try:
            return self._handle_inflation_data(country, period)
        except Exception as e:
            logger.error(f"Error getting inflation data: {e}")
            return {
                'error': f"Ошибка получения данных по инфляции: {str(e)}",
                'success': False
            }

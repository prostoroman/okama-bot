"""
Enhanced Asset Resolver

Нормализатор активов для финансового анализа с расширенными алиасами и проверкой существования.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

@dataclass
class ResolvedAsset:
    """Результат разрешения актива"""
    original: str
    ticker: str
    asset_class: str
    valid: bool
    error_message: Optional[str] = None

class EnhancedAssetResolver:
    """Улучшенный резолвер активов с проверкой существования"""
    
    def __init__(self):
        # Расширенные алиасы для активов
        self.asset_aliases = {
            # Акции US
            'apple': 'AAPL.US', 'tesla': 'TSLA.US', 'google': 'GOOGL.US',
            'microsoft': 'MSFT.US', 'amazon': 'AMZN.US', 'netflix': 'NFLX.US',
            'facebook': 'META.US', 'meta': 'META.US', 'nvidia': 'NVDA.US',
            'amd': 'AMD.US', 'intel': 'INTC.US', 'coca-cola': 'KO.US',
            'disney': 'DIS.US', 'mcdonalds': 'MCD.US', 'starbucks': 'SBUX.US',
            'nike': 'NKE.US', 'adobe': 'ADBE.US', 'salesforce': 'CRM.US',
            
            # Акции MOEX
            'сбер': 'SBER.MOEX', 'сбербанк': 'SBER.MOEX', 'газпром': 'GAZP.MOEX', 'лукойл': 'LKOH.MOEX',
            'норильский никель': 'GMKN.MOEX', 'яндекс': 'YNDX.MOEX', 'магнит': 'MGNT.MOEX',
            
            # ETF
            'spy': 'SPY.US', 'voo': 'VOO.US', 'qqq': 'QQQ.US', 'agg': 'AGG.US',
            'vti': 'VTI.US', 'vxus': 'VXUS.US', 'bnd': 'BND.US',
            
            # Индексы
            'sp500': 'SPX.INDX', 's&p 500': 'SPX.INDX', 'nasdaq': 'IXIC.INDX',
            'dow': 'DJI.INDX', 'rts': 'RTSI.INDX', 'moex': 'IMOEX.INDX',
            
            # Товары
            'золото': 'GC.COMM', 'gold': 'GC.COMM', 'серебро': 'SI.COMM',
            'silver': 'SI.COMM', 'нефть': 'BRENT.COMM', 'oil': 'BRENT.COMM',
            'медь': 'HG.COMM', 'copper': 'HG.COMM',
            
            # Валюты
            'доллар': 'USD.FX', 'dollar': 'USD.FX', 'евро': 'EUR.FX',
            'euro': 'EUR.FX', 'рубль': 'RUB.FX', 'ruble': 'RUB.FX',
            
            # Валютные пары
            'eurusd': 'EURUSD.FX', 'eur/usd': 'EURUSD.FX', 'gbpusd': 'GBPUSD.FX',
            'usdrub': 'USDRUB.FX', 'usd/rub': 'USDRUB.FX',
            
            # Инфляция
            'cpi': 'US.INFL', 'ипц': 'RUS.INFL'
        }
        
        # Классы активов
        self.asset_classes = {
            'US': 'US', 'MOEX': 'MOEX', 'COMM': 'COMM',
            'INDX': 'INDX', 'FX': 'FX', 'INFL': 'INFL'
        }
    
    def resolve(self, raw_assets: List[str]) -> List[ResolvedAsset]:
        """Разрешает список активов"""
        resolved = []
        
        for asset in raw_assets:
            resolved_asset = self._resolve_single_asset(asset)
            resolved.append(resolved_asset)
        
        return resolved
    
    def _resolve_single_asset(self, raw_asset: str) -> ResolvedAsset:
        """Разрешает один актив"""
        original = raw_asset.strip()
        
        # Проверяем алиасы
        if original.lower() in self.asset_aliases:
            ticker = self.asset_aliases[original.lower()]
            asset_class = self._get_asset_class(ticker)
            return ResolvedAsset(
                original=original,
                ticker=ticker,
                asset_class=asset_class,
                valid=True
            )
        
        # Проверяем, уже ли это тикер okama
        if '.' in original and len(original.split('.')) == 2:
            ticker = original.upper()
            asset_class = self._get_asset_class(ticker)
            return ResolvedAsset(
                original=original,
                ticker=ticker,
                asset_class=asset_class,
                valid=True
            )
        
        # Пытаемся угадать класс актива
        ticker = self._guess_ticker(original)
        if ticker:
            asset_class = self._get_asset_class(ticker)
            return ResolvedAsset(
                original=original,
                ticker=ticker,
                asset_class=asset_class,
                valid=True
            )
        
        # Если ничего не подошло
        return ResolvedAsset(
            original=original,
            ticker=original.upper(),
            asset_class='UNKNOWN',
            valid=False,
            error_message=f"Актив '{original}' не найден в базе okama. Проверьте тикер."
        )
    
    def _guess_ticker(self, raw_asset: str) -> Optional[str]:
        """Угадывает тикер на основе названия"""
        asset_upper = raw_asset.upper()
        
        # Если тикер из 1-4 букв — предполагаем .US
        if len(asset_upper) <= 4 and asset_upper.isalpha():
            return f"{asset_upper}.US"
        
        # Если тикер из 5+ букв — ищем как есть
        if len(asset_upper) > 4 and asset_upper.isalpha():
            return asset_upper
        
        return None
    
    def _get_asset_class(self, ticker: str) -> str:
        """Определяет класс актива по тикеру"""
        if '.' not in ticker:
            return 'UNKNOWN'
        
        suffix = ticker.split('.')[-1]
        return self.asset_classes.get(suffix, 'UNKNOWN')
    
    def validate_asset(self, ticker: str) -> bool:
        """Проверяет существование актива в okama"""
        try:
            import okama as ok
            asset = ok.Asset(ticker)
            # Если актив создался без ошибок, считаем его валидным
            return True
        except Exception as e:
            logger.warning(f"Asset validation failed for {ticker}: {e}")
            return False
    
    def get_suggestions(self, invalid_ticker: str) -> List[str]:
        """Предлагает альтернативы для невалидного тикера"""
        suggestions = []
        
        # Ищем похожие тикеры
        for alias, ticker in self.asset_aliases.items():
            if invalid_ticker.lower() in alias or alias in invalid_ticker.lower():
                suggestions.append(ticker)
        
        # Ограничиваем количество предложений
        return suggestions[:5]

"""
Enhanced Intent Parser

Полнофункциональный парсер намерений для финансового анализа с извлечением всех необходимых параметров.

Поддерживаемые намерения:
- asset_single: Анализ одного актива
- asset_compare: Сравнение нескольких активов  
- portfolio_analysis: Анализ портфеля
- inflation_data: Данные по инфляции
- macro_data: Макроэкономические данные

Извлекаемые параметры:
- Символы активов
- Доли портфеля
- Валюты (currency)
- Временные периоды (period, since, from, to)
- Валюты для конвертации (in, convert to)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

@dataclass
class ParsedIntent:
    """Структурированный результат парсинга намерения"""
    intent: str
    assets: List[str]
    weights: Optional[List[float]] = None
    currency: Optional[str] = None
    period: Optional[str] = None
    since_date: Optional[str] = None
    to_date: Optional[str] = None
    convert_to: Optional[str] = None
    country: Optional[str] = None
    raw_text: str = ""

class EnhancedIntentParser:
    """Улучшенный парсер намерений для финансового анализа"""
    
    def __init__(self):
        # Паттерны для распознавания намерений
        self.intent_patterns = {
            'asset_single': [
                r'\b(анализ|покажи|информация|данные|метрики|доходность|волатильность)\s+(?:про|о|об|актив|акции|облигации|etf|фонд)',
                r'\b(какая|как|что|покажи)\s+(?:доходность|волатильность|метрики|данные)',
                r'\b(проанализируй|анализируй|изучи)\s+',
                r'\b(актив|акция|облигация|etf|фонд)\s+(?:с|с\s+тикером|под\s+названием)',
            ],
            'asset_compare': [
                r'\b(сравни|сравнение|сопоставь|против|vs|versus)\s+',
                r'\b(что\s+лучше|какой\s+лучше)\s+',
                r'\b(сравни\s+доходность|сравни\s+риски)\s+',
                r'\b(анализ\s+сравнительный|сравнительный\s+анализ)',
            ],
            'portfolio_analysis': [
                r'\b(портфель|portfolio)\s*:?\s*',
                r'\b(портфель|portfolio)\s+(?:из|состоящий|включающий)',
                r'\b(веса|доли|распределение)\s*:?\s*',
                r'\b(оптимизируй|оптимизация)\s+портфеля',
                r'\b(анализ\s+рисков|риски\s+портфеля)',
            ],
            'inflation_data': [
                r'\b(инфляция|inflation|cpi|ипц)\s+',
                r'\b(индекс\s+потребительских\s+цен|потребительские\s+цены)',
                r'\b(рост\s+цен|изменение\s+цен)\s+',
            ],
            'macro_data': [
                r'\b(курс|курс\s+валют|валютный\s+курс)\s+',
                r'\b(цена\s+на|стоимость)\s+(?:нефть|золото|серебро|газ)',
                r'\b(макро|макроэкономические|экономические)\s+(?:данные|показатели)',
                r'\b(доллар|евро|рубль|юань)\s+(?:к|против|vs)',
            ]
        }
        
        # Паттерны для извлечения параметров
        self.parameter_patterns = {
            'currency': [
                r'\b(?:в|в\s+валюте|отчет\s+в)\s+(USD|EUR|RUB|доллар|евро|рубль)',
                r'\b(USD|EUR|RUB|доллар|евро|рубль)\s+(?:валюта|валюте)',
            ],
            'convert_to': [
                r'\b(?:конвертируй|переведи|в)\s+(USD|EUR|RUB|доллар|евро|рубль)',
                r'\b(?:convert\s+to|in)\s+(USD|EUR|RUB)',
            ],
            'period': [
                r'\b(?:за|за\s+период|за\s+последние?)\s+(\d+)\s*(год|года|лет|y|yr|year|years)',
                r'\b(?:период|временной\s+период)\s+(\d+)\s*(год|года|лет)',
                r'\b(\d+)\s*(год|года|лет|y|yr|year|years)\s+(?:назад|back)',
            ],
            'since_date': [
                r'\b(?:с|since|от|начиная\s+с)\s+(\d{4})',
                r'\b(?:с\s+\d{4}\s+по|\d{4}\s*-\s*\d{4})',
            ],
            'to_date': [
                r'\b(?:по|to|до|по\s+\d{4})\s+(\d{4})',
                r'\b(?:с\s+\d{4}\s+по|\d{4}\s*-\s*\d{4})',
            ],
            'country': [
                r'\b(?:в|по)\s+(США|US|USA|Россия|RU|RUS|Европа|EU|ЕС)',
                r'\b(США|US|USA|Россия|RU|RUS|Европа|EU|ЕС)\s+(?:инфляция|данные)',
            ]
        }
        
        # Алиасы для активов
        self.asset_aliases = {
            # Акции US
            'apple': 'AAPL.US',
            'tesla': 'TSLA.US',
            'google': 'GOOGL.US',
            'microsoft': 'MSFT.US',
            'amazon': 'AMZN.US',
            'netflix': 'NFLX.US',
            'facebook': 'META.US',
            'meta': 'META.US',
            'alphabet': 'GOOGL.US',
            'nvidia': 'NVDA.US',
            'amd': 'AMD.US',
            'intel': 'INTC.US',
            'coca-cola': 'KO.US',
            'cocacola': 'KO.US',
            'disney': 'DIS.US',
            'mcdonalds': 'MCD.US',
            'starbucks': 'SBUX.US',
            'nike': 'NKE.US',
            'adobe': 'ADBE.US',
            'salesforce': 'CRM.US',
            
            # Акции MOEX
            'сбер': 'SBER.MOEX',
            'сбербанк': 'SBER.MOEX',
            'газпром': 'GAZP.MOEX',
            'лукойл': 'LKOH.MOEX',
            'норильский никель': 'GMKN.MOEX',
            'норильск': 'GMKN.MOEX',
            'яндекс': 'YNDX.MOEX',
            'магнит': 'MGNT.MOEX',
            'россети': 'RSTI.MOEX',
            'ростелеком': 'RTKM.MOEX',
            'аэрофлот': 'AFLT.MOEX',
            
            # ETF
            'spy': 'SPY.US',
            'voo': 'VOO.US',
            'qqq': 'QQQ.US',
            'agg': 'AGG.US',
            'vti': 'VTI.US',
            'vxus': 'VXUS.US',
            'bnd': 'BND.US',
            'vgt': 'VGT.US',
            'vht': 'VHT.US',
            'vde': 'VDE.US',
            
            # Индексы
            'sp500': 'SPX.INDX',
            'sp 500': 'SPX.INDX',
            's&p 500': 'SPX.INDX',
            's&p500': 'SPX.INDX',
            'nasdaq': 'IXIC.INDX',
            'nasdaq 100': 'NDX.INDX',
            'dow': 'DJI.INDX',
            'dow jones': 'DJI.INDX',
            'rts': 'RTSI.INDX',
            'moex': 'IMOEX.INDX',
            'imoex': 'IMOEX.INDX',
            
            # Товары
            'золото': 'GC.COMM',
            'gold': 'GC.COMM',
            'серебро': 'SI.COMM',
            'silver': 'SI.COMM',
            'нефть': 'BRENT.COMM',
            'oil': 'BRENT.COMM',
            'brent': 'BRENT.COMM',
            'wti': 'CL.COMM',
            'медь': 'HG.COMM',
            'copper': 'HG.COMM',
            'платина': 'PL.COMM',
            'platinum': 'PL.COMM',
            'палладий': 'PA.COMM',
            'palladium': 'PA.COMM',
            
            # Валюты
            'доллар': 'USD.FX',
            'dollar': 'USD.FX',
            'евро': 'EUR.FX',
            'euro': 'EUR.FX',
            'рубль': 'RUB.FX',
            'ruble': 'RUB.FX',
            'юань': 'CNY.FX',
            'yuan': 'CNY.FX',
            'фунт': 'GBP.FX',
            'pound': 'GBP.FX',
            'иена': 'JPY.FX',
            'yen': 'JPY.FX',
            
            # Валютные пары
            'eurusd': 'EURUSD.FX',
            'eur/usd': 'EURUSD.FX',
            'gbpusd': 'GBPUSD.FX',
            'gbp/usd': 'GBPUSD.FX',
            'usdrub': 'USDRUB.FX',
            'usd/rub': 'USDRUB.FX',
            'eurrub': 'EURRUB.FX',
            'eur/rub': 'EURRUB.FX',
            
            # Инфляция
            'cpi': 'US.INFL',
            'ипц': 'RUS.INFL',
            'инфляция сша': 'US.INFL',
            'инфляция россии': 'RUS.INFL',
            'инфляция европы': 'EU.INFL',
        }
        
        # Классы активов
        self.asset_classes = {
            'US': 'US',
            'MOEX': 'MOEX',
            'COMM': 'COMM',
            'INDX': 'INDX',
            'FX': 'FX',
            'INFL': 'INFL'
        }
    
    def parse(self, text: str) -> ParsedIntent:
        """
        Основной метод парсинга намерения
        
        Args:
            text: Текстовый запрос пользователя
            
        Returns:
            ParsedIntent: Структурированный результат парсинга
        """
        text = text.strip()
        if not text:
            return ParsedIntent(intent='unknown', assets=[], raw_text=text)
        
        # Предобработка: не разбиваем S&P на отдельные буквы
        normalized_text = text.replace('S&P', 'S&P')
        
        # Определяем намерение
        intent = self._determine_intent(normalized_text)
        
        # Извлекаем активы
        assets = self._extract_assets(normalized_text)
        
        # Извлекаем параметры
        params = self._extract_parameters(normalized_text)
        
        # Извлекаем веса для портфеля
        weights = None
        if intent == 'portfolio_analysis':
            weights = self._extract_weights(normalized_text, len(assets))
        
        # Определяем страну для инфляции
        country = params.get('country')
        
        return ParsedIntent(
            intent=intent,
            assets=assets,
            weights=weights,
            currency=params.get('currency'),
            period=params.get('period'),
            since_date=params.get('since_date'),
            to_date=params.get('to_date'),
            convert_to=params.get('convert_to'),
            country=country,
            raw_text=text
        )
    
    def _determine_intent(self, text: str) -> str:
        """Определяет намерение пользователя"""
        text_lower = text.lower()
        
        # Проверяем каждый тип намерения
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return intent
        
        # Если намерение не определено, пытаемся угадать по контексту
        extracted = self._extract_assets(text)
        if len(extracted) == 1:
            return 'asset_single'
        elif len(extracted) > 1:
            return 'asset_compare'
        else:
            return 'unknown'
    
    def _extract_assets(self, text: str) -> List[str]:
        """Извлекает активы из текста"""
        assets: List[str] = []
        
        # Ищем тикеры в формате okama
        okama_pattern = r'\b([A-Z]{1,6}\.[A-Z]{2,6})\b'
        okama_matches = re.findall(okama_pattern, text, re.IGNORECASE)
        assets.extend(okama_matches)
        
        # Ищем обычные тикеры (без точки), исключая части уже найденных okama-тикеров
        ticker_pattern = r'\b([A-Z]{2,5})\b'  # минимум 2 символа
        ticker_matches = re.findall(ticker_pattern, text, re.IGNORECASE)
        
        # Собираем множество всех частей, входящих в уже найденные okama-тикеры
        okama_parts = set()
        for m in okama_matches:
            parts = m.upper().split('.')
            okama_parts.update(parts)
        
        # Исключаем валютные обозначения и служебные токены
        blacklist = {'USD', 'EUR', 'RUB', 'CNY', 'GBP', 'JPY', 'FX', 'INFL'}
        
        # Фильтруем тикеры, которые не являются словами валют и не являются частями уже найденных okama-тикеров
        for ticker in ticker_matches:
            upper_ticker = ticker.upper()
            if upper_ticker in blacklist:
                continue
            if upper_ticker in okama_parts:
                continue
            assets.append(upper_ticker)
        
        # Ищем названия активов через алиасы
        text_lower = text.lower()
        single_currency_symbols = {'USD.FX','EUR.FX','RUB.FX','CNY.FX','GBP.FX','JPY.FX'}
        for alias, symbol in self.asset_aliases.items():
            if alias in text_lower:
                # Пропускаем одиночные валюты, они должны парситься как currency, а не актив
                if symbol in single_currency_symbols:
                    continue
                if symbol not in assets:
                    assets.append(symbol)
        
        # Убираем слишком длинные plain-токены без точки (например, APPLE)
        assets = [a for a in assets if ('.' in a) or (a.isalpha() and 2 <= len(a) <= 4)]
        
        # Убираем дубликаты, сохраняя порядок
        seen = set()
        unique_assets: List[str] = []
        for asset in assets:
            up = asset.upper()
            if up not in seen:
                seen.add(up)
                unique_assets.append(up)
        
        return unique_assets
    
    def _extract_parameters(self, text: str) -> Dict[str, str]:
        """Извлекает все параметры из текста"""
        params: Dict[str, str] = {}
        text_lower = text.lower()
        
        # Извлечение валюты
        for pattern in self.parameter_patterns['currency']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                currency = self._normalize_currency(match.group(1))
                if currency:
                    params['currency'] = currency
                break
        
        # Извлечение валюты для конвертации
        for pattern in self.parameter_patterns['convert_to']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                currency = self._normalize_currency(match.group(1))
                if currency:
                    params['convert_to'] = currency
                break
        
        # Извлечение периода
        for pattern in self.parameter_patterns['period']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                years = int(match.group(1))
                params['period'] = f"{years}Y"
                break
        
        # Извлечение дат
        for pattern in self.parameter_patterns['since_date']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                params['since_date'] = match.group(1)
                break
        
        for pattern in self.parameter_patterns['to_date']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                params['to_date'] = match.group(1)
                break
        
        # Извлечение страны
        for pattern in self.parameter_patterns['country']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                country = self._normalize_country(match.group(1))
                if country:
                    params['country'] = country
                break
        
        return params
    
    def _extract_weights(self, text: str, num_assets: int) -> Optional[List[float]]:
        """Извлекает веса для портфеля"""
        text_lower = text.lower()
        
        # Паттерны для весов
        weight_patterns = [
            r'(\d+(?:\.\d+)?)\s*%?\s*(?:вес|weight|доля)',
            r'вес[аы]?\s*(\d+(?:\.\d+)?)\s*%?',
            r'доля\s*(\d+(?:\.\d+)?)\s*%?',
            r'weight[s]?\s*(\d+(?:\.\d+)?)\s*%?',
            r'(\d+(?:\.\d+)?)\s*%\s*(?:акции|облигации|золото|серебро|нефть)',
            r'веса[аы]?\s*(\d+(?:\.\d+)?)\s*и\s*(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)\s*%\s*и\s*(\d+(?:\.\d+)?)\s*%',
            r'(\d+(?:\.\d+)?)\s*%\s*,\s*(\d+(?:\.\d+)?)\s*%',
        ]
        
        weights: List[float] = []
        for pattern in weight_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                if isinstance(matches[0], tuple):
                    for match in matches:
                        weights.extend([float(w) / 100.0 for w in match])
                else:
                    weights.extend([float(w) / 100.0 for w in matches])
        
        if len(weights) >= num_assets:
            return weights[:num_assets]
        
        return None
    
    def _normalize_currency(self, currency: str) -> Optional[str]:
        """Нормализует валюту к стандартному формату"""
        currency_lower = currency.lower()
        currency_map = {
            'usd': 'USD', 'доллар': 'USD', 'доллары': 'USD', '$': 'USD',
            'eur': 'EUR', 'евро': 'EUR', '€': 'EUR',
            'rub': 'RUB', 'рубль': 'RUB', 'рубли': 'RUB', '₽': 'RUB', 'р': 'RUB',
            'cny': 'CNY', 'юань': 'CNY', '¥': 'CNY',
            'gbp': 'GBP', 'фунт': 'GBP', '£': 'GBP',
            'jpy': 'JPY', 'иена': 'JPY', '¥': 'JPY'
        }
        return currency_map.get(currency_lower)
    
    def _normalize_country(self, country: str) -> Optional[str]:
        """Нормализует страну к стандартному формату"""
        country_lower = country.lower()
        country_map = {
            'сша': 'US', 'us': 'US', 'usa': 'US', 'америка': 'US',
            'россия': 'RU', 'ru': 'RU', 'rus': 'RU', 'рф': 'RU',
            'европа': 'EU', 'eu': 'EU', 'ес': 'EU', 'europe': 'EU'
        }
        return country_map.get(country_lower)
    
    def get_default_period(self) -> str:
        """Возвращает период по умолчанию"""
        return "5Y"
    
    def get_default_currency(self, asset: str) -> Optional[str]:
        """Возвращает валюту по умолчанию для актива"""
        if asset.endswith('.US'):
            return 'USD'
        elif asset.endswith('.MOEX'):
            return 'RUB'
        elif asset.endswith('.COMM'):
            return 'USD'
        elif asset.endswith('.INDX'):
            return 'USD'
        elif asset.endswith('.FX'):
            return 'USD'
        elif asset.endswith('.INFL'):
            return 'USD'
        else:
            return None

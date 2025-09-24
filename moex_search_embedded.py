# moex_search_embedded.py
# Zero-dependency MOEX search with an embedded, curated list of major tickers.
# - No Excel, no web calls.
# - Russian-friendly search via aliases, transliteration, and fuzzy scoring.
# - Extend EMBEDDED universe below as needed.

import re
import difflib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

# ----------------- Curated universe (symbol, English name) --------------------
# Add/adjust freely. Symbols are in SECID.MOEX format.
EMBEDDED: List[Tuple[str, str]] = [
    ("SBER.MOEX", "Sberbank"),
    ("GAZP.MOEX", "Gazprom"),
    ("SIBN.MOEX", "Gazprom Neft"),
    ("LKOH.MOEX", "NK Lukoil"),
    ("ROSN.MOEX", "NK Rosneft"),
    ("GMKN.MOEX", "GMK Norilskiy Nikel"),
    ("PLZL.MOEX", "Polyus"),
    ("NVTK.MOEX", "Novatek"),
    ("SNGS.MOEX", "Surgutneftegaz"),
    ("SNGSP.MOEX", "Surgutneftegaz Pref"),
    ("TATN.MOEX", "Tatneft"),
    ("TATNP.MOEX", "Tatneft Pref"),
    ("MGNT.MOEX", "Magnit"),
    ("MTSS.MOEX", "MTS"),
    ("ALRS.MOEX", "Alrosa"),
    ("CHMF.MOEX", "Severstal"),
    ("NLMK.MOEX", "NLMK"),
    ("RUAL.MOEX", "RUSAL"),
    ("PHOR.MOEX", "PhosAgro"),
    ("MOEX.MOEX", "Moscow Exchange"),
    ("AFLT.MOEX", "Aeroflot"),
    ("OZON.MOEX", "Ozon"),
    ("YDEX.MOEX", "Yandex"),
    ("SELG.MOEX", "Segezha Group"),
    ("PIKK.MOEX", "PIK Group"),
    ("TRNFP.MOEX", "Transneft Pref"),
    ("VTBR.MOEX", "VTB Bank"),
    ("RNFT.MOEX", "RussNeft"),
    ("POLY.MOEX", "Polymetal"),  # keep for legacy/compat; may not trade on MOEX currently
]

# ----------------- Unified asset mappings with direct tickers -----------------
# Combined dictionary: any variant -> direct ticker on exchange
# Based on examples_service.py tickers to ensure accuracy
ASSET_MAPPINGS: Dict[str, str] = {
    # MOEX Assets (Russian + English variants) - Only tickers that exist in examples_service
    "сбер": "SBER.MOEX",
    "сбербанк": "SBER.MOEX", 
    "пао сбербанк": "SBER.MOEX",
    "sber": "SBER.MOEX",
    "sberbank": "SBER.MOEX",
    
    "газпром": "GAZP.MOEX",
    "gazprom": "GAZP.MOEX",
    
    "газпром нефть": "SIBN.MOEX",
    "газпромнефть": "SIBN.MOEX", 
    "газнефть": "SIBN.MOEX",
    "gazprom neft": "SIBN.MOEX",
    
    "лукойл": "LKOH.MOEX",
    "lukoil": "LKOH.MOEX",
    
    "роснефть": "ROSN.MOEX",
    "нк роснефть": "ROSN.MOEX",
    "rosneft": "ROSN.MOEX",
    
    "норникель": "GMKN.MOEX",
    "гмк норильский никель": "GMKN.MOEX",
    "норильский никель": "GMKN.MOEX",
    
    "полюс": "PLZL.MOEX",
    "полюс золото": "PLZL.MOEX",
    "polyus": "PLZL.MOEX",
    
    "новатэк": "NVTK.MOEX",
    "новатек": "NVTK.MOEX",
    "novatek": "NVTK.MOEX",
    
    "сургутнефтегаз": "SNGS.MOEX",
    "сургут": "SNGS.MOEX",
    "surgutneftegaz": "SNGS.MOEX",
    "surgutneftegas": "SNGS.MOEX",  # Alternative spelling from examples_service
    
    "сургутнефтегаз преф": "SNGSP.MOEX",
    "сургут преф": "SNGSP.MOEX",
    
    "татнефть": "TATN.MOEX",
    "tatneft": "TATN.MOEX",
    
    "татнефть преф": "TATNP.MOEX",
    "tatneft pref": "TATNP.MOEX",
    
    "магнит": "MGNT.MOEX",
    "magnit": "MGNT.MOEX",
    
    "мтс": "MTSS.MOEX",
    "mts": "MTSS.MOEX",
    
    "алроса": "ALRS.MOEX",
    "alrosa": "ALRS.MOEX",
    
    "северсталь": "CHMF.MOEX",
    "severstal": "CHMF.MOEX",
    
    "нлмк": "NLMK.MOEX",
    "nlmk": "NLMK.MOEX",
    
    "русал": "RUAL.MOEX",
    "rusal": "RUAL.MOEX",
    
    "фосагро": "PHOR.MOEX",
    "phosagro": "PHOR.MOEX",
    
    "мосбиржа": "MOEX.MOEX",
    "московская биржа": "MOEX.MOEX",
    "moex": "MOEX.MOEX",
    "биржа": "MOEX.MOEX",
    "moscow exchange": "MOEX.MOEX",
    
    "аэрофлот": "AFLT.MOEX",
    "aeroflot": "AFLT.MOEX",
    
    "озон": "OZON.MOEX",
    "ozon": "OZON.MOEX",
    
    "яндекс": "YDEX.MOEX",
    "yandex": "YDEX.MOEX",
    
    "ростелеком": "RTKM.MOEX",  # исправлено: используем RTKM.MOEX как правильный тикер
    "ростел": "RTKM.MOEX",
    "mts": "MTSS.MOEX",
    
    "сегежа": "SELG.MOEX",
    "сегежа групп": "SELG.MOEX",
    "segezha group": "SELG.MOEX",
    
    "пик": "PIKK.MOEX",
    "пик групп": "PIKK.MOEX",
    "pik group": "PIKK.MOEX",
    
    "транснефть преф": "TRNFP.MOEX",
    "тнф преф": "TRNFP.MOEX",
    "транснефть": "TRNFP.MOEX",
    "transneft pref": "TRNFP.MOEX",
    
    "втб": "VTBR.MOEX",
    "vtb bank": "VTBR.MOEX",
    
    "русснефть": "RNFT.MOEX",
    "руснфть": "RNFT.MOEX",
    "росснефть": "RNFT.MOEX",
    "russneft": "RNFT.MOEX",
    
    "полиметалл": "POLY.MOEX",
    "polymetal": "POLY.MOEX",
    
    # Additional MOEX tickers from examples_service
    "система": "AFKS.MOEX",
    "sistema": "AFKS.MOEX",
    
    "vim lqdt": "LQDT.MOEX",
    "вим лкдт": "LQDT.MOEX",
    
    "т-технологии": "T.MOEX",
    "t-technologies": "T.MOEX",
    
    # US Stocks - Only tickers that exist in examples_service
    "microsoft": "MSFT.US",
    "microsft": "MSFT.US",
    "microsoft corp": "MSFT.US",
    "msft": "MSFT.US",
    
    "apple": "AAPL.US",
    "aplle": "AAPL.US",
    "aple": "AAPL.US",
    "apple inc": "AAPL.US",
    "apple computer": "AAPL.US",
    
    "nvidia": "NVDA.US",
    
    "amazon": "AMZN.US",
    "amazn": "AMZN.US",
    "amazon com": "AMZN.US",
    "amazon.com": "AMZN.US",
    
    "alphabet": "GOOG.US",  # Using GOOG.US from examples_service
    "google": "GOOG.US",
    "googl": "GOOG.US",
    "alphabet inc": "GOOG.US",
    
    "meta": "META.US",
    "facebook": "META.US",
    "facebok": "META.US",
    "meta platforms": "META.US",
    
    "tesla": "TSLA.US",
    "tesa": "TSLA.US",
    "tesla motors": "TSLA.US",
    "tesla inc": "TSLA.US",
    
    "nvidia": "NVDA.US",
    "netflix": "NFLX.US",
    "disney": "DIS.US",
    "coca-cola": "KO.US",
    "coca cola": "KO.US",
    "coke": "KO.US",
    
    "sap": "SAP.XETR",
    "siemens": "SIE.XETR",
    "siemenz": "SIE.XETR",
    "bmw": "BMW.XETR",
    "mercedes": "MBG.XETR",
    "volkswagen": "VOW3.XETR",  # исправлено: используем VOW3.XETR как в examples_service
    "infineon": "IFX.XETR",
    "linde": "LIN.XETR",
    "siemens healthineers": "SHL.XETR",
    "continental": "CON.XETR",
    "hella": "HEI.XETR",
    "fresenius medical care": "FME.XETR",
    "fresenius": "FRE.XETR",
    
    # Дополнительные европейские акции
    "allianz": "ALV.XETR",
    "allianz se": "ALV.XETR",
    "deutsche telekom": "DTE.XETR",
    "telekom": "DTE.XETR",
    "basf": "BAS.XETR",
    "basf se": "BAS.XETR",
    "rwe": "RWE.XETR",
    "rwe ag": "RWE.XETR",
    "munich re": "MUV2.XETR",
    "adidas": "ADS.XETR",
    "adidas ag": "ADS.XETR",
    "henkel": "HEN3.XETR",
    "henkel ag": "HEN3.XETR",
    
    # Commodities - только существующие тикеры
    "copper": "HG.COMM",
    "медь": "HG.COMM",  # русский вариант
    
    # Forex - только существующие тикеры
    "eurusd": "EURUSD.FX",
    "gbpusd": "GBPUSD.FX",
    "usdjpy": "USDJPY.FX",
    "usdchf": "USDCHF.FX",
    "доллар евро": "EURUSD.FX",  # русский вариант
    "фунт доллар": "GBPUSD.FX",  # русский вариант
    "йена доллар": "USDJPY.FX",  # русский вариант
    "франк доллар": "USDCHF.FX",  # русский вариант
    
    # Crypto - Only tickers that exist in examples_service
    "bitcoin": "BTC-USD.CC",
    "ethereum": "ETH-USD.CC",
    "binance coin": "BNB-USD.CC",
    "solana": "SOL-USD.CC",
    "xrp": "XRP-USD.CC",
    "tether": "USDT-USD.CC",
    "usd coin": "USDC-USD.CC",
    "dogecoin": "DOGE-USD.CC",
    "cardano": "ADA-USD.CC",
    "tron": "TRX-USD.CC",
    "toncoin": "TON-USD.CC",
    
    # Indices - только существующие тикеры
    "nasdaq": "NDX.INDX",
    "dow": "DJI.INDX",
    "rts": "RTSI.INDX",  # исправлено: используем RTSI.INDX вместо RTS.INDX
    "moex": "IMOEX.INDX",  # исправлено: используем IMOEX.INDX вместо MOEX.MOEX
    "dax": "GDAXH.INDX",  # исправлено: используем GDAXH.INDX вместо DAX.INDX
    "nikkei": "N225.INDX",  # исправлено: используем N225.INDX вместо NKZ0.US
    "hang seng": "HSXUF.US",  # исправлено: используем HSXUF.US вместо HSI.INDX
    
    # Дополнительные варианты для индексов
    "sp500": "SPX.INDX",       # S&P 500
    "s&p 500": "SPX.INDX",
    "dow jones": "DJI.INDX",   # Dow Jones Industrial Average
    "ftse 100": "UKX.INDX",    # FTSE 100 Index
    "cac 40": "FCHI.INDX",     # CAC 40 Index
}

# ----------------- Normalizers & transliteration (rough, stdlib-only) --------
_RU_EQUIV = str.maketrans({"ё": "е"})
_PUNCT_RE = re.compile(r"[\W_]+", re.UNICODE)

def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    s = s.translate(_RU_EQUIV)
    s = _PUNCT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def tokenize(s: str) -> List[str]:
    return [t for t in normalize_text(s).split() if t]

_LAT2RU = {
    "yo":"ё","zh":"ж","kh":"х","ts":"ц","ch":"ч","sh":"ш","sch":"щ","yu":"ю","ya":"я",
    "a":"а","b":"б","v":"в","g":"г","d":"д","e":"е","z":"з","i":"и","j":"й","k":"к",
    "l":"л","m":"м","n":"н","o":"о","p":"п","r":"р","s":"с","t":"т","u":"у","f":"ф","y":"ы","h":"х","x":"кс","q":"к","w":"в","c":"к"
}
_RU2LAT = {
    "ё":"yo","ж":"zh","х":"kh","ц":"ts","ч":"ch","ш":"sh","щ":"sch","ю":"yu","я":"ya",
    "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","з":"z","и":"i","й":"j","к":"k",
    "л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","ы":"y","ь":"", "ъ":"", "э":"e"
}

def ru_to_lat(s: str) -> str:
    out = []
    for ch in s.lower():
        out.append(_RU2LAT.get(ch, ch))
    return "".join(out)

def lat_to_ru(s: str) -> str:
    s = s.lower()
    for m in ["sch","yo","zh","kh","ts","ch","sh","yu","ya"]:
        s = s.replace(m, _LAT2RU[m])
    return "".join(_LAT2RU.get(ch, ch) for ch in s)

STOPWORDS = {
    "public","pjsc","oao","ao","ooo","plc","corp","corporation","inc","ltd","limited","company",
    "bank","group","holding","investments","investment","retail","mining","metals","oil","gas",
    "power","energy","federal","united","airlines","airline","national","research","plant","factory",
    "joint","stock","gmk","nk","pa","pao","pjsc","company"
}

def strip_stopwords(name: str) -> str:
    tokens = [t for t in tokenize(name) if t not in STOPWORDS]
    return " ".join(tokens)

# ----------------- Core data structures --------------------------------------
@dataclass
class Asset:
    symbol: str
    name_en: str
    aliases: List[str] = field(default_factory=list)

class MoexSearchIndex:
    def __init__(self):
        self.assets: Dict[str, Asset] = {}
        self.alias2symbol: Dict[str, str] = {}

    def add_asset(self, symbol: str, name_en: str):
        sym = symbol.strip()
        nm = (name_en or sym).strip()
        a = Asset(symbol=sym, name_en=nm, aliases=[])
        base_aliases = set()
        base_aliases.add(sym.lower())
        base_aliases.add(strip_stopwords(nm))
        base_aliases.add(nm.lower())
        nm_clean = re.sub(r"\b(pjsc|oao|plc|ltd|ao|pao|public|joint|stock|company)\b\.?","", nm, flags=re.I)
        nm_clean = re.sub(r"\s+"," ", nm_clean).strip()
        base_aliases.add(nm_clean.lower())
        base_aliases.add(strip_stopwords(nm_clean))
        base_aliases.add(lat_to_ru(strip_stopwords(nm_clean)))
        base_aliases.add(ru_to_lat(lat_to_ru(strip_stopwords(nm_clean))))

        # Attach RU synonyms (if exist) - removed RU_SYNONYMS dependency
        # for ru in RU_SYNONYMS.get(nm, []):
        #     base_aliases.add(ru)
        #     base_aliases.add(ru_to_lat(ru))

        # Compact
        a.aliases = sorted({normalize_text(x) for x in base_aliases if x})
        self.assets[sym] = a
        for al in a.aliases:
            self.alias2symbol.setdefault(al, sym)

    def build_from_embedded(self):
        for sym, nm in EMBEDDED:
            self.add_asset(sym, nm)

    @staticmethod
    def _score(q: str, alias: str) -> float:
        qt = set(tokenize(q))
        at = set(tokenize(alias))
        jacc = len(qt & at) / max(1, len(qt | at))
        dif = difflib.SequenceMatcher(a=normalize_text(q), b=normalize_text(alias)).ratio()
        return 0.6 * dif + 0.4 * jacc

    def search(self, query: str, top_k: int = 5, min_score: float = 0.45) -> List[Tuple[str, float, str]]:
        qn = normalize_text(query)
        variants = {qn, ru_to_lat(qn), lat_to_ru(qn)}
        scores: Dict[str, Tuple[float, str]] = {}
        for v in variants:
            for al, sym in self.alias2symbol.items():
                score = self._score(v, al)
                if score >= scores.get(sym, (0.0, ""))[0]:
                    scores[sym] = (score, al)
        ranked = sorted([(sym, sc, al) for sym, (sc, al) in scores.items() if sc >= min_score],
                        key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def dump_aliases(self) -> Dict[str, List[str]]:
        return {sym: asset.aliases for sym, asset in self.assets.items()}

# ----------------- Fuzzy search functionality --------------------------------
# Cache for MOEX index to avoid rebuilding it every time
_moex_index_cache = None

def try_fuzzy_search(query: str) -> List[Dict[str, str]]:
    """
    Unified search function that handles both direct mappings and okama search.
    First checks for exact matches in ASSET_MAPPINGS, then falls back to okama search.
    
    Args:
        query: Original search query
        
    Returns:
        List of search results from direct mappings or okama sources
    """
    query_lower = query.lower().strip()
    
    # First, check for exact match in unified asset mappings
    if query_lower in ASSET_MAPPINGS:
        ticker = ASSET_MAPPINGS[query_lower]
        return [{
            'symbol': ticker,
            'name': f"Direct mapping for {query}",
            'source': 'direct_mapping',
            'score': 1.0
        }]
    
    # If no direct mapping, try MOEX search for Russian queries
    if _is_russian_query(query):
        moex_results = _search_moex(query)
        if moex_results:
            return moex_results
    
    # If still no results, try direct okama search
    direct_results = _search_okama(query, 'okama_direct', 0.8)
    return direct_results

def _search_moex(query: str) -> List[Dict[str, str]]:
    """
    Helper function to search MOEX database with caching.
    
    Args:
        query: Search query
        
    Returns:
        List of MOEX search results
    """
    global _moex_index_cache
    
    try:
        if _moex_index_cache is None:
            _moex_index_cache = load_default_index()
        
        moex_results = _moex_index_cache.search(query, top_k=5, min_score=0.45)
        
        results = []
        for symbol, score, alias in moex_results:
            results.append({
                'symbol': symbol,
                'name': f"MOEX Asset ({alias})",
                'source': 'moex',
                'score': score
            })
        return results
    except Exception as e:
        _log_warning(f"MOEX search failed for '{query}': {e}")
        return []

def _search_okama(query: str, source: str, score: float) -> List[Dict[str, str]]:
    """
    Helper function to search okama database.
    
    Args:
        query: Search query
        source: Source identifier
        score: Score to assign to results
        
    Returns:
        List of search results
    """
    try:
        import okama as ok
        search_result = ok.search(query)
        if len(search_result) > 0:
            results = []
            for _, row in search_result.iterrows():
                results.append({
                    'symbol': row['symbol'],
                    'name': row.get('name', ''),
                    'source': source,
                    'score': score
                })
            return results
    except Exception as e:
        _log_warning(f"Okama search failed for '{query}': {e}")
    
    return []

def _log_warning(message: str) -> None:
    """Helper function to log warnings if logging is available."""
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(message)
    except ImportError:
        pass  # No logging available

def _is_russian_query(query: str) -> bool:
    """
    Check if query contains Russian characters.
    
    Args:
        query: Query string
        
    Returns:
        True if query contains Russian characters
    """
    russian_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
    query_chars = set(query.lower())
    return bool(russian_chars & query_chars)

def get_direct_ticker(query: str) -> Optional[str]:
    """
    Get direct ticker for a query without performing the search.
    
    Args:
        query: Original search query
        
    Returns:
        Direct ticker if found in mappings, None otherwise
    """
    query_lower = query.lower().strip()
    return ASSET_MAPPINGS.get(query_lower)

def add_asset_mapping(variant: str, ticker: str) -> None:
    """
    Add a new asset mapping.
    
    Args:
        variant: The variant name
        ticker: The ticker symbol
    """
    ASSET_MAPPINGS[variant.lower()] = ticker.upper()

def remove_asset_mapping(variant: str) -> None:
    """
    Remove an asset mapping.
    
    Args:
        variant: The variant name to remove
    """
    ASSET_MAPPINGS.pop(variant.lower(), None)

# ----------------- Convenience functions -------------------------------------
def load_default_index() -> MoexSearchIndex:
    idx = MoexSearchIndex()
    idx.build_from_embedded()
    return idx

def search_with_fuzzy(query: str, moex_index: Optional[MoexSearchIndex] = None) -> Dict[str, any]:
    """
    Perform unified search with direct mappings and fallback search.
    This is now a wrapper around the unified try_fuzzy_search function.
    
    Args:
        query: Search query
        moex_index: Optional MOEX search index (kept for compatibility)
        
    Returns:
        Dictionary with search results
    """
    # Use the unified search function
    all_results = try_fuzzy_search(query)
    
    # Separate results by source for compatibility
    results = {
        'moex_results': [],
        'fuzzy_results': [],
        'direct_results': [],
        'all_results': all_results,
        'query': query
    }
    
    for result in all_results:
        if result['source'] == 'moex':
            results['moex_results'].append((result['symbol'], result['score'], result['name']))
        elif result['source'] == 'direct_mapping':
            results['direct_results'].append(result)
        else:
            results['fuzzy_results'].append(result)
    
    return results

#!/usr/bin/env python3
"""
Сервис для генерации случайных примеров для команд бота
"""

import random
from typing import List, Tuple, Optional


class ExamplesService:
    """Сервис для генерации случайных примеров"""
    
    def __init__(self):
        """Инициализация сервиса с данными топ-тикеров"""
        self.top_tickers = {
            'US': [
                ('MSFT.US', 'Microsoft'),
                ('AAPL.US', 'Apple'),
                ('NVDA.US', 'NVIDIA'),
                ('AMZN.US', 'Amazon'),
                ('GOOG.US', 'Alphabet (Class C)'),
                ('META.US', 'Meta Platforms'),
                ('LLY.US', 'Eli Lilly'),
                ('BRK.B.US', 'Berkshire Hathaway (B)'),
                ('AVGO.US', 'Broadcom'),
                ('TSM.US', 'Taiwan Semiconductor (ADR)'),
                ('JPM.US', 'JPMorgan Chase'),
                ('TSLA.US', 'Tesla'),
                ('WMT.US', 'Walmart'),
                ('XOM.US', 'Exxon Mobil'),
                ('UNH.US', 'UnitedHealth Group'),
                ('NVO.US', 'Novo Nordisk (ADR)'),
                ('V.US', 'Visa (Class A)'),
                ('MA.US', 'Mastercard (Class A)'),
                ('PG.US', 'Procter & Gamble'),
                ('ORCL.US', 'Oracle')
            ],
            'LSE': [
                ('SHEL.LSE', 'Shell plc'),
                ('AZN.LSE', 'AstraZeneca'),
                ('HSBA.LSE', 'HSBC Holdings'),
                ('ULVR.LSE', 'Unilever'),
                ('BP.LSE', 'BP'),
                ('RIO.LSE', 'Rio Tinto'),
                ('GSK.LSE', 'GSK'),
                ('DGE.LSE', 'Diageo'),
                ('BATS.LSE', 'British American Tobacco'),
                ('REL.LSE', 'RELX'),
                ('NG.LSE', 'National Grid'),
                ('VOD.LSE', 'Vodafone Group'),
                ('LSEG.LSE', 'London Stock Exchange Group'),
                ('BARC.LSE', 'Barclays'),
                ('LLOY.LSE', 'Lloyds Banking Group'),
                ('TSCO.LSE', 'Tesco'),
                ('PRU.LSE', 'Prudential'),
                ('GLEN.LSE', 'Glencore'),
                ('AV.LSE', 'Aviva'),
                ('BA.LSE', 'BAE Systems')
            ],
            'HKEX': [
                ('00700.HKEX', 'Tencent Holdings'),
                ('00941.HKEX', 'China Mobile'),
                ('00005.HKEX', 'HSBC Holdings'),
                ('00939.HKEX', 'China Construction Bank (H)'),
                ('01299.HKEX', 'AIA Group'),
                ('01398.HKEX', 'ICBC (H)'),
                ('02318.HKEX', 'Ping An Insurance (H)'),
                ('00388.HKEX', 'Hong Kong Exchanges & Clearing'),
                ('00988.HKEX', 'China Telecom (H)'),
                ('00883.HKEX', 'CNOOC'),
                ('02388.HKEX', 'BOC Hong Kong'),
                ('03690.HKEX', 'Meituan‑W'),
                ('09988.HKEX', 'Alibaba Group‑SW'),
                ('09618.HKEX', 'JD.com‑SW'),
                ('01810.HKEX', 'Xiaomi‑W'),
                ('01211.HKEX', 'BYD Company'),
                ('01088.HKEX', 'China Shenhua (H)'),
                ('00386.HKEX', 'Sinopec (H)'),
                ('00857.HKEX', 'PetroChina (H)'),
                ('03988.HKEX', 'Bank of China (H)')
            ],
            'MOEX': [
                ('GAZP.MOEX', 'Gazprom'),
                ('SBER.MOEX', 'Sberbank'),
                ('LKOH.MOEX', 'Lukoil'),
                ('ROSN.MOEX', 'Rosneft'),
                ('NVTK.MOEX', 'Novatek'),
                ('GMKN.MOEX', 'Norilsk Nickel'),
                ('PLZL.MOEX', 'Polyus'),
                ('SIBN.MOEX', 'Gazprom Neft'),
                ('PHOR.MOEX', 'PhosAgro'),
                ('SNGS.MOEX', 'Surgutneftegas'),
                ('TATN.MOEX', 'Tatneft'),
                ('NLMK.MOEX', 'NLMK'),
                ('MTSS.MOEX', 'MTS'),
                ('MGNT.MOEX', 'Magnit'),
                ('ALRS.MOEX', 'ALROSA'),
                ('CHMF.MOEX', 'Severstal'),
                ('MOEX.MOEX', 'Moscow Exchange'),
                ('AFKS.MOEX', 'Sistema'),
                ('IRAO.MOEX', 'Inter RAO')
            ],
            'SSE': [
                ('600519.SSE', 'Kweichow Moutai'),
                ('601318.SSE', 'Ping An Insurance (A)'),
                ('601939.SSE', 'China Construction Bank (A)'),
                ('601398.SSE', 'ICBC (A)'),
                ('601988.SSE', 'Bank of China (A)'),
                ('601857.SSE', 'PetroChina (A)'),
                ('600036.SSE', 'China Merchants Bank (A)'),
                ('600028.SSE', 'Sinopec (A)'),
                ('601628.SSE', 'China Life Insurance (A)'),
                ('600030.SSE', 'CITIC Securities'),
                ('600900.SSE', 'China Yangtze Power'),
                ('601601.SSE', 'China Pacific Insurance'),
                ('601668.SSE', 'China State Construction'),
                ('601088.SSE', 'China Shenhua (A)'),
                ('600104.SSE', 'SAIC Motor'),
                ('600276.SSE', 'Hengrui Medicine'),
                ('601166.SSE', 'Industrial Bank'),
                ('600000.SSE', 'Shanghai Pudong Development Bank'),
                ('600837.SSE', 'Haitong Securities'),
                ('600050.SSE', 'China Unicom (A)')
            ],
            'SZSE': [
                ('300750.SZSE', 'CATL'),
                ('000858.SZSE', 'Wuliangye Yibin'),
                ('002594.SZSE', 'BYD'),
                ('000333.SZSE', 'Midea Group'),
                ('000651.SZSE', 'Gree Electric'),
                ('300760.SZSE', 'Shenzhen Mindray Bio‑Medical'),
                ('002415.SZSE', 'Hikvision'),
                ('000063.SZSE', 'ZTE'),
                ('000002.SZSE', 'China Vanke'),
                ('000001.SZSE', 'Ping An Bank'),
                ('002241.SZSE', 'GoerTek'),
                ('300015.SZSE', 'Aier Eye Hospital'),
                ('300124.SZSE', 'Inovance Technology'),
                ('300059.SZSE', 'East Money Information'),
                ('002475.SZSE', 'Luxshare Precision'),
                ('002027.SZSE', 'Focus Media Information'),
                ('300122.SZSE', 'Zhongke Sanhuan'),
                ('000538.SZSE', 'Yunnan Baiyao'),
                ('000895.SZSE', 'Shuanghui Development'),
                ('002352.SZSE', 'SF Holding')
            ],
            'XETR': [
                ('SAP.XETR', 'SAP'),
                ('SIE.XETR', 'Siemens'),
                ('ALV.XETR', 'Allianz'),
                ('DTE.XETR', 'Deutsche Telekom'),
                ('MBG.XETR', 'Mercedes‑Benz Group'),
                ('BMW.XETR', 'BMW'),
                ('BAS.XETR', 'BASF'),
                ('RWE.XETR', 'RWE'),
                ('MUV2.XETR', 'Munich Re'),
                ('ADS.XETR', 'Adidas'),
                ('HEN3.XETR', 'Henkel'),
                ('P911.XETR', 'Porsche AG'),
                ('VOW3.XETR', 'Volkswagen (Pref)'),
                ('IFX.XETR', 'Infineon Technologies'),
                ('LIN.XETR', 'Linde'),
                ('SHL.XETR', 'Siemens Healthineers'),
                ('CON.XETR', 'Continental'),
                ('HEI.XETR', 'HELLA GmbH'),
                ('FME.XETR', 'Fresenius Medical Care'),
                ('FRE.XETR', 'Fresenius SE')
            ],
            'XFRA': [
                ('SAP.XFRA', 'SAP'),
                ('ALV.XFRA', 'Allianz'),
                ('DTE.XFRA', 'Deutsche Telekom'),
                ('SIE.XFRA', 'Siemens'),
                ('BAS.XFRA', 'BASF'),
                ('BMW.XFRA', 'BMW'),
                ('MBG.XFRA', 'Mercedes‑Benz Group'),
                ('BAYN.XFRA', 'Bayer'),
                ('ADS.XFRA', 'Adidas'),
                ('RWE.XFRA', 'RWE'),
                ('HNR1.XFRA', 'Hannover Rück'),
                ('MUV2.XFRA', 'Munich Re'),
                ('P911.XFRA', 'Porsche AG'),
                ('IFX.XFRA', 'Infineon Technologies'),
                ('VOW3.XFRA', 'Volkswagen (Pref)'),
                ('HEI.XFRA', 'HELLA GmbH'),
                ('FME.XFRA', 'Fresenius Medical Care'),
                ('FRE.XFRA', 'Fresenius SE'),
                ('SY1.XFRA', 'Symrise'),
                ('ZAL.XFRA', 'Zalando')
            ],
            'XSTU': [
                ('SAP.XSTU', 'SAP'),
                ('SIE.XSTU', 'Siemens'),
                ('ALV.XSTU', 'Allianz'),
                ('DTE.XSTU', 'Deutsche Telekom'),
                ('MBG.XSTU', 'Mercedes‑Benz Group'),
                ('BMW.XSTU', 'BMW'),
                ('BAS.XSTU', 'BASF'),
                ('RWE.XSTU', 'RWE'),
                ('MUV2.XSTU', 'Munich Re'),
                ('ADS.XSTU', 'Adidas'),
                ('HEN3.XSTU', 'Henkel'),
                ('P911.XSTU', 'Porsche AG'),
                ('VOW3.XSTU', 'Volkswagen (Pref)'),
                ('IFX.XSTU', 'Infineon Technologies'),
                ('SHL.XSTU', 'Siemens Healthineers'),
                ('LIN.XSTU', 'Linde'),
                ('CON.XSTU', 'Continental'),
                ('HEI.XSTU', 'HELLA GmbH'),
                ('FME.XSTU', 'Fresenius Medical Care'),
                ('FRE.XSTU', 'Fresenius SE')
            ],
            'XAMS': [
                ('ASML.XAMS', 'ASML Holding'),
                ('SHELL.XAMS', 'Shell plc'),
                ('PRX.XAMS', 'Prosus'),
                ('REL.XAMS', 'RELX (Amsterdam line)'),
                ('INGA.XAMS', 'ING Groep'),
                ('ADYEN.XAMS', 'Adyen'),
                ('UMG.XAMS', 'Universal Music Group'),
                ('DSM.XAMS', 'DSM‑Firmenich'),
                ('ASM.XAMS', 'ASM International'),
                ('AKZA.XAMS', 'Akzo Nobel'),
                ('NN.XAMS', 'NN Group'),
                ('RAND.XAMS', 'Randstad'),
                ('HEIA.XAMS', 'Heineken'),
                ('URW.XAMS', 'Unibail‑Rodamco‑Westfield'),
                ('TKWY.XAMS', 'Just Eat Takeaway.com'),
                ('WKL.XAMS', 'Wolters Kluwer'),
                ('PHIA.XAMS', 'Philips'),
                ('MT.AMS', 'ArcelorMittal (AMS line)'),
                ('IMCD.XAMS', 'IMCD'),
                ('BESI.XAMS', 'BE Semiconductor')
            ],
            'XTAE': [
                ('LUMI.XTAE', 'Bank Leumi'),
                ('POLI.XTAE', 'Bank Hapoalim'),
                ('ELBT.XTAE', 'Elbit Systems'),
                ('PHOE.XTAE', 'Phoenix Holdings'),
                ('NVMI.XTAE', 'Nova'),
                ('ICL.XTAE', 'ICL Group'),
                ('TEVA.XTAE', 'Teva'),
                ('TASE.XTAE', 'Tel‑Aviv Stock Exchange'),
                ('ENRG.XTAE', 'Energix'),
                ('DMRI.XTAE', 'Y.H. Dimri'),
                ('OPCO.XTAE', 'OPC Energy'),
                ('BZRI.XTAE', 'Bezeq'),
                ('DELT.XTAE', 'Delek Group'),
                ('STRA.XTAE', 'Strauss Group'),
                ('NICE.XTAE', 'NICE Ltd.'),
                ('MTRX.XTAE', 'Matrix IT'),
                ('FIBI.XTAE', 'First International Bank of Israel'),
                ('ISCD.XTAE', 'Israel Corp.'),
                ('SHLD.XTAE', 'Shikun & Binui'),
                ('TSEM.XTAE', 'Tower Semiconductor')
            ]
        }

    def get_info_examples(self, count: int = 3) -> List[str]:
        """Get random examples for /info command with ticker and company name"""
        # Always start with MOEX ticker
        moex_tickers = self.top_tickers.get('MOEX', [])
        if moex_tickers:
            moex_ticker = random.choice(moex_tickers)
            selected_tickers = [moex_ticker]
        else:
            selected_tickers = []
        
        # Collect remaining tickers from all exchanges (excluding Chinese and Hong Kong)
        excluded_exchanges = {'MOEX', 'SSE', 'SZSE', 'HKEX'}
        remaining_tickers = []
        for exchange, tickers in self.top_tickers.items():
            if exchange not in excluded_exchanges:  # Skip MOEX, Chinese and Hong Kong exchanges
                remaining_tickers.extend(tickers)
        
        # Select remaining random tickers
        remaining_count = min(count - len(selected_tickers), len(remaining_tickers))
        if remaining_count > 0:
            additional_tickers = random.sample(remaining_tickers, remaining_count)
            selected_tickers.extend(additional_tickers)
        
        # Format as "ticker - Company Name, Exchange"
        examples = []
        for ticker, company_name in selected_tickers:
            exchange = ticker.split('.')[-1]
            examples.append(f"`{ticker}` - {company_name}, {exchange}")
        
        return examples

    def get_compare_examples(self, count: int = 3, context_tickers: List[str] = None) -> List[str]:
        """Get random examples for /compare command with ready commands from same exchange"""
        examples = []
        
        # Если есть активы в контексте, используем их для формирования примеров
        if context_tickers:
            exchange = self._get_exchange_from_context_tickers(context_tickers)
            if exchange:
                # Получаем тикеры с той же биржи, исключая уже использованные
                available_tickers = self._get_tickers_from_exchange(exchange, context_tickers)
                
                # Если есть достаточно тикеров для сравнения
                if len(available_tickers) >= 2:
                    # Берем один из контекстных тикеров и один новый
                    context_ticker = random.choice(context_tickers)
                    new_ticker, new_company = random.choice(available_tickers)
                    
                    # Находим название компании для контекстного тикера
                    context_company = None
                    for ticker, company in self.top_tickers.get(exchange, []):
                        if ticker == context_ticker:
                            context_company = company
                            break
                    
                    if context_company:
                        command = f"`{context_ticker} {new_ticker}`"
                        description = f"сравнить {context_company} и {new_company}"
                        examples.append(f"{command} - {description}")
                
                # Добавляем еще примеры с той же биржи если нужно
                if len(examples) < count and len(available_tickers) >= 2:
                    remaining_count = count - len(examples)
                    for _ in range(min(remaining_count, len(available_tickers) // 2)):
                        selected_tickers = random.sample(available_tickers, 2)
                        ticker1, company1 = selected_tickers[0]
                        ticker2, company2 = selected_tickers[1]
                        
                        command = f"`{ticker1} {ticker2}`"
                        description = f"сравнить {company1} и {company2}"
                        examples.append(f"{command} - {description}")
        
        # Если примеров недостаточно, добавляем стандартные примеры
        if len(examples) < count:
            remaining_count = count - len(examples)
            
            # Always start with MOEX example if not already present
            moex_tickers = self.top_tickers.get('MOEX', [])
            if len(moex_tickers) >= 2 and not any('MOEX' in ex for ex in examples):
                selected_tickers = random.sample(moex_tickers, 2)
                ticker1, company1 = selected_tickers[0]
                ticker2, company2 = selected_tickers[1]
                
                command = f"`{ticker1} {ticker2}`"
                description = f"сравнить {company1} и {company2}"
                examples.append(f"{command} - {description}")
                remaining_count -= 1
            
            # Get remaining random exchanges (excluding MOEX, Chinese and Hong Kong exchanges)
            excluded_exchanges = {'MOEX', 'SSE', 'SZSE', 'HKEX'}
            remaining_exchanges = [ex for ex in self.top_tickers.keys() if ex not in excluded_exchanges]
            
            if remaining_count > 0:
                selected_exchanges = random.sample(remaining_exchanges, min(remaining_count, len(remaining_exchanges)))
                
                for exchange in selected_exchanges:
                    exchange_tickers = self.top_tickers[exchange]
                    if len(exchange_tickers) >= 2:
                        selected_tickers = random.sample(exchange_tickers, 2)
                        ticker1, company1 = selected_tickers[0]
                        ticker2, company2 = selected_tickers[1]
                        
                        command = f"`{ticker1} {ticker2}`"
                        description = f"сравнить {company1} и {company2}"
                        examples.append(f"{command} - {description}")
        
        return examples[:count]

    def get_portfolio_examples(self, count: int = 3, context_tickers: List[str] = None) -> List[str]:
        """Get random examples for /portfolio command with weights that sum to 1.0"""
        examples = []
        
        # Если есть активы в контексте, используем их для формирования примеров
        if context_tickers:
            exchange = self._get_exchange_from_context_tickers(context_tickers)
            if exchange:
                # Получаем тикеры с той же биржи, исключая уже использованные
                available_tickers = self._get_tickers_from_exchange(exchange, context_tickers)
                
                # Если есть достаточно тикеров для портфеля (минимум 3)
                if len(available_tickers) >= 2:  # Нужно минимум 2 дополнительных к контекстным
                    # Берем один из контекстных тикеров и добавляем еще 2-3 новых
                    context_ticker = random.choice(context_tickers)
                    
                    # Находим название компании для контекстного тикера
                    context_company = None
                    for ticker, company in self.top_tickers.get(exchange, []):
                        if ticker == context_ticker:
                            context_company = company
                            break
                    
                    if context_company:
                        # Выбираем еще 2 тикера для портфеля
                        additional_tickers = random.sample(available_tickers, min(2, len(available_tickers)))
                        
                        # Создаем список всех тикеров для портфеля
                        portfolio_tickers = [(context_ticker, context_company)] + additional_tickers
                        
                        # Генерируем веса
                        weights = self._generate_portfolio_weights(len(portfolio_tickers))
                        
                        # Создаем команду
                        command_parts = []
                        companies = []
                        for i, (ticker, company) in enumerate(portfolio_tickers):
                            command_parts.append(f"{ticker}:{weights[i]:.1f}")
                            companies.append(company)
                        
                        command = f"`{' '.join(command_parts)}`"
                        description = f"создать портфель {', '.join(companies)}"
                        examples.append(f"{command} - {description}")
                
                # Добавляем еще примеры с той же биржи если нужно
                if len(examples) < count and len(available_tickers) >= 3:
                    remaining_count = count - len(examples)
                    for _ in range(min(remaining_count, len(available_tickers) // 3)):
                        selected_tickers = random.sample(available_tickers, 3)
                        
                        # Generate weights that sum to 1.0
                        weights = self._generate_portfolio_weights(3)
                        
                        # Create command example
                        command_parts = []
                        companies = []
                        for i, (ticker, company) in enumerate(selected_tickers):
                            command_parts.append(f"{ticker}:{weights[i]:.1f}")
                            companies.append(company)
                        
                        command = f"`{' '.join(command_parts)}`"
                        description = f"создать портфель {', '.join(companies)}"
                        examples.append(f"{command} - {description}")
        
        # Если примеров недостаточно, добавляем стандартные примеры
        if len(examples) < count:
            remaining_count = count - len(examples)
            
            # Always start with MOEX example if not already present
            moex_tickers = self.top_tickers.get('MOEX', [])
            if len(moex_tickers) >= 3 and not any('MOEX' in ex for ex in examples):
                selected_tickers = random.sample(moex_tickers, 3)
                
                # Generate weights that sum to 1.0
                weights = self._generate_portfolio_weights(3)
                
                # Create MOEX command example
                command_parts = []
                companies = []
                for i, (ticker, company) in enumerate(selected_tickers):
                    command_parts.append(f"{ticker}:{weights[i]:.1f}")
                    companies.append(company)
                
                command = f"`{' '.join(command_parts)}`"
                description = f"создать портфель {', '.join(companies)}"
                examples.append(f"{command} - {description}")
                remaining_count -= 1
            
            # Get remaining random exchanges (excluding MOEX, Chinese and Hong Kong exchanges)
            excluded_exchanges = {'MOEX', 'SSE', 'SZSE', 'HKEX'}
            remaining_exchanges = [ex for ex in self.top_tickers.keys() if ex not in excluded_exchanges]
            
            if remaining_count > 0:
                selected_exchanges = random.sample(remaining_exchanges, min(remaining_count, len(remaining_exchanges)))
                
                for exchange in selected_exchanges:
                    # Get 3 random tickers from the same exchange
                    exchange_tickers = self.top_tickers[exchange]
                    if len(exchange_tickers) >= 3:
                        selected_tickers = random.sample(exchange_tickers, 3)
                        
                        # Generate weights that sum to 1.0
                        weights = self._generate_portfolio_weights(3)
                        
                        # Create command example
                        command_parts = []
                        companies = []
                        for i, (ticker, company) in enumerate(selected_tickers):
                            command_parts.append(f"{ticker}:{weights[i]:.1f}")
                            companies.append(company)
                        
                        command = f"`{' '.join(command_parts)}`"
                        description = f"создать портфель {', '.join(companies)}"
                        examples.append(f"{command} - {description}")
        
        return examples[:count]

    def _generate_portfolio_weights(self, num_assets: int) -> List[float]:
        """Generate random weights that sum to 1.0"""
        # Generate random numbers
        weights = [random.random() for _ in range(num_assets)]
        
        # Normalize to sum to 1.0
        total = sum(weights)
        normalized_weights = [w / total for w in weights]
        
        # Round to 1 decimal place and ensure sum is exactly 1.0
        rounded_weights = [round(w, 1) for w in normalized_weights]
        
        # Adjust the last weight to ensure sum is exactly 1.0
        current_sum = sum(rounded_weights)
        if current_sum != 1.0:
            rounded_weights[-1] = round(1.0 - sum(rounded_weights[:-1]), 1)
        
        return rounded_weights

    def _get_exchange_from_ticker(self, ticker: str) -> Optional[str]:
        """Определить биржу по тикеру"""
        if '.' not in ticker:
            return None
        
        exchange = ticker.split('.')[-1]
        
        # Маппинг бирж
        exchange_mapping = {
            'US': 'US',
            'LSE': 'LSE', 
            'HKEX': 'HKEX',
            'MOEX': 'MOEX',
            'SSE': 'SSE',
            'SZSE': 'SZSE',
            'XETR': 'XETR',
            'XFRA': 'XFRA',
            'XSTU': 'XSTU',
            'XAMS': 'XAMS',
            'XTAE': 'XTAE'
        }
        
        return exchange_mapping.get(exchange)

    def _get_tickers_from_exchange(self, exchange: str, exclude_tickers: List[str] = None) -> List[Tuple[str, str]]:
        """Получить тикеры с указанной биржи, исключая переданные тикеры"""
        if exclude_tickers is None:
            exclude_tickers = []
            
        exchange_tickers = self.top_tickers.get(exchange, [])
        
        # Исключаем переданные тикеры
        filtered_tickers = [
            (ticker, company) for ticker, company in exchange_tickers 
            if ticker not in exclude_tickers
        ]
        
        return filtered_tickers

    def _get_exchange_from_context_tickers(self, context_tickers: List[str]) -> Optional[str]:
        """Определить биржу из списка тикеров в контексте"""
        if not context_tickers:
            return None
            
        # Берем первый тикер для определения биржи
        first_ticker = context_tickers[0]
        return self._get_exchange_from_ticker(first_ticker)

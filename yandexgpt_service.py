import requests
import json
import re
from typing import Dict, List, Optional
from config import Config

class YandexGPTService:
    """
    Service class for YandexGPT integration with Okama platform support.
    
    This service includes enhanced prompts and methods to properly format financial
    instrument names according to Okama namespace conventions:
    
    - CBR: Central Banks official currency exchange rates
    - CC: Cryptocurrency pairs with USD  
    - COMM: Commodities prices
    - FX: FOREX currency market
    - INDX: Indexes
    - INFL: Inflation
    - LSE: London Stock Exchange
    - MOEX: Moscow Exchange
    - PF: Investment Portfolios
    - PIF: Russian open-end mutual funds
    - RATE: Bank deposit rates
    - RATIO: Financial ratios
    - RE: Real estate prices
    - US: US Stock Exchanges and mutual funds
    - XAMS: Euronext Amsterdam
    - XETR: XETRA Exchange
    - XFRA: Frankfurt Stock Exchange
    - XSTU: Stuttgart Exchange
    - XTAE: Tel Aviv Stock Exchange (TASE)
    
    The service automatically converts common instrument names to proper Okama format.
    """
    
    def __init__(self):
        self.api_key = Config.YANDEX_API_KEY
        self.folder_id = Config.YANDEX_FOLDER_ID
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        # Alternative endpoints to try if the main one fails:
        self.fallback_urls = [
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            "https://llm.api.cloud.yandex.net/foundationModels/v1/chat/completions",
            "https://llm.api.cloud.yandex.net/foundationModels/v1/textGeneration"
        ]
        
        # Model priority order - start with most capable models
        self.model_priority = [
            "yandexgpt",
            "yandexgpt-pro",
            "yandexgpt-lite",
            "yandexgpt-2"
        ]
        
        # Debug configuration
        if not self.api_key or not self.folder_id:
            print("⚠️  WARNING: Missing YandexGPT configuration!")
            print("   Please set YANDEX_API_KEY and YANDEX_FOLDER_ID in your environment variables")
        
        # System prompt for financial analysis (optimized for yandexgpt-pro)
        self.system_prompt = """You are a senior financial analyst and investment advisor with extensive expertise in quantitative finance, portfolio theory, and market analysis. You provide professional-grade financial insights and recommendations.

Your core competencies include:
- Modern Portfolio Theory (MPT) and efficient frontier analysis
- Risk metrics: VaR, CVaR, Sharpe ratio, Sortino ratio, maximum drawdown
- Asset allocation strategies and portfolio optimization
- Factor analysis and risk decomposition
- Alternative investments and derivatives
- Behavioral finance and market psychology
- Regulatory compliance and best practices

IMPORTANT: When processing user commands in free form, you MUST convert instrument names to the format understood by Okama platform using the following namespace mapping:

{'CBR': 'Central Banks official currency exchange rates',
 'CC': 'Cryptocurrency pairs with USD',
 'COMM': 'Commodities prices',
 'FX': 'FOREX currency market',
 'INDX': 'Indexes',
 'INFL': 'Inflation',
 'LSE': 'London Stock Exchange',
 'MOEX': 'Moscow Exchange',
 'PF': 'Investment Portfolios',
 'PIF': 'Russian open-end mutual funds',
 'RATE': 'Bank deposit rates',
 'RATIO': 'Financial ratios',
 'RE': 'Real estate prices',
 'US': 'US Stock Exchanges and mutual funds',
 'XAMS': 'Euronext Amsterdam',
 'XETR': 'XETRA Exchange',
 'XFRA': 'Frankfurt Stock Exchange',
 'XSTU': 'Stuttgart Exchange',
 'XTAE': 'Tel Aviv Stock Exchange (TASE)'}

EXAMPLES of proper formatting:
- "S&P 500" → "SPX.INDX"
- "Apple stock" → "AAPL.US"
- "Bitcoin" → "BTC.US" (Note: Some crypto may not be available in Okama)
- "Gold" → "XAU.COMM"
- "EUR/USD" → "EURUSD.FX"
- "Sberbank" → "SBER.MOEX"
- "Tesla" → "TSLA.US"
- "Oil" → "BRENT.COMM"

When providing financial analysis:
1. Use quantitative methods and data-driven insights
2. Explain complex financial concepts with clear examples
3. Provide specific, actionable recommendations
4. Always emphasize risk management and diversification
5. Include relevant financial ratios and metrics
6. Consider market conditions and economic factors
7. Recommend consulting licensed financial advisors for major decisions
8. ALWAYS format instrument names using the Okama namespace format above

Format responses professionally with clear sections, bullet points, and relevant financial terminology. Be precise, thorough, and educational."""

    def analyze_query(self, user_message: str) -> Dict:
        """Analyze user query to determine intent and extract parameters"""
        try:
            # Create a prompt to analyze the user's intent
            analysis_prompt = f"""
            Analyze this user message and extract the following information:
            1. Intent (portfolio, risk, correlation, efficient_frontier, compare, chat, other)
            2. Symbols mentioned (stock tickers, ETF symbols) - IMPORTANT: Convert to Okama format
            3. Time period mentioned
            4. Specific metrics requested
            
            User message: "{user_message}"
            
            CRITICAL: You MUST convert any mentioned financial instruments to Okama namespace format:
            - Stocks: "AAPL.US", "SBER.MOEX", "TSLA.US"
            - Indexes: "SPX.INDX", "RTSI.INDX", "DAX.INDX"
            - Commodities: "XAU.COMM", "BRENT.COMM", "SILVER.COMM"
            - Forex: "EURUSD.FX", "GBPUSD.FX"
            - Crypto: "BTC.CC", "ETH.CC"
            
            Return the analysis as JSON with these fields:
            - intent: string
            - symbols: list of strings (in Okama format)
            - time_period: string or null
            - metrics: list of strings
            - is_chat: boolean (true if it's a general question)
            """
            
            response = self._call_yandex_api(
                system_prompt="You are a helpful assistant that analyzes user queries and returns JSON responses. You MUST convert financial instrument names to Okama namespace format.",
                user_prompt=analysis_prompt,
                temperature=0.1,
                max_tokens=300
            )
            
            # Extract and parse JSON response
            content = response
            # Clean up the response to extract JSON
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                # Fallback analysis
                analysis = {
                    "intent": "chat",
                    "symbols": [],
                    "time_period": None,
                    "metrics": [],
                    "is_chat": True
                }
            
            return analysis
            
        except Exception as e:
            # Fallback to simple keyword matching
            return self._fallback_analysis(user_message)
    
    def _fallback_analysis(self, user_message: str) -> Dict:
        """Fallback analysis using keyword matching"""
        message_lower = user_message.lower()
        
        # Extract symbols (including namespace like .INDX, .US, .COMM)
        symbols = re.findall(r'\b[A-Z]{1,6}\.[A-Z]{2,4}\b', user_message)
        
        # Try to extract and convert common instrument names to Okama format
        # Common stock patterns
        stock_patterns = {
            r'\bapple\b': 'AAPL.US',
            r'\btesla\b': 'TSLA.US',
            r'\bgoogle\b': 'GOOGL.US',
            r'\bmicrosoft\b': 'MSFT.US',
            r'\bamazon\b': 'AMZN.US',
            r'\bsberbank\b': 'SBER.MOEX',
            r'\bгазпром\b': 'GAZP.MOEX',
            r'\bлукойл\b': 'LKOH.MOEX',
            # Use more realistic crypto tickers that might be available in Okama
            r'\bbitcoin\b': 'BTC.US',  # Try as US stock first
            r'\beth\b': 'ETH.US',      # Try as US stock first
            r'\bgold\b': 'XAU.COMM',
            r'\bsilver\b': 'XAG.COMM',
            r'\boil\b': 'BRENT.COMM',
            r'\bsp\s*500\b': 'SPX.INDX',
            r'\bnasdaq\b': 'IXIC.INDX',
            r'\brts\b': 'RTSI.INDX',
            r'\beur\s*usd\b': 'EURUSD.FX',
            r'\bgbp\s*usd\b': 'GBPUSD.FX'
        }
        
        # Convert common names to Okama format
        for pattern, okama_symbol in stock_patterns.items():
            if re.search(pattern, message_lower):
                if okama_symbol not in symbols:
                    symbols.append(okama_symbol)
        
        # Debug: extracted symbols
        
        # Determine intent
        if any(word in message_lower for word in ['portfolio', 'portfolios']):
            intent = 'portfolio'
        elif any(word in message_lower for word in ['risk', 'volatility', 'var']):
            intent = 'risk'
        elif any(word in message_lower for word in ['correlation', 'correlate']):
            intent = 'correlation'
        elif any(word in message_lower for word in ['efficient', 'frontier', 'optimization']):
            intent = 'efficient_frontier'
        elif any(word in message_lower for word in ['compare', 'comparison', 'vs']):
            intent = 'compare'
        else:
            intent = 'chat'
        
        return {
            "intent": intent,
            "symbols": symbols,
            "time_period": None,
            "metrics": [],
            "is_chat": intent == 'chat'
        }
    
    def get_financial_advice(self, user_message: str, context: Optional[Dict] = None) -> str:
        """Get financial advice or answer from YandexGPT"""
        try:
            # Build the prompt with context if available
            if context and context.get('symbols'):
                symbols_info = f"User is asking about: {', '.join(context['symbols'])}. "
            else:
                symbols_info = ""
            
            prompt = f"{symbols_info}User question: {user_message}"
            
            response = self._call_yandex_api(
                system_prompt=self.system_prompt,
                user_prompt=prompt,
                temperature=0.7,
                max_tokens=500
            )
            
            return response
            
        except Exception as e:
            return "Из-за технических проблем с AI сервисом, вот общие финансовые рекомендации:\n\n" + \
                   "• Диверсифицируйте портфель по различным классам активов\n" + \
                   "• Учитывайте ваш профиль риска и инвестиционный горизонт\n" + \
                   "• Регулярно пересматривайте и ребалансируйте портфель\n" + \
                   "• Рассмотрите консультацию с финансовым советником"
    
    def ask_question(self, question: str) -> str:
        """Simple method to ask a question to YandexGPT (alias for get_financial_advice)"""
        print(f"🔍 YandexGPTService.ask_question called with question: {question[:100]}...")
        print(f"🔑 API Key configured: {'Yes' if self.api_key else 'No'}")
        print(f"📁 Folder ID configured: {'Yes' if self.folder_id else 'No'}")
        
        try:
            result = self.get_financial_advice(question)
            print(f"✅ YandexGPT response received, length: {len(result) if result else 0}")
            return result
        except Exception as e:
            print(f"❌ Error in ask_question: {e}")
            return f"Ошибка при получении AI ответа: {str(e)}"
    
    def ask_question_with_vision(self, question: str, image_bytes: bytes, image_description: str = "") -> str:
        """Ask a question to YandexGPT with image analysis capability"""
        print(f"🔍 YandexGPTService.ask_question_with_vision called with question: {question[:100]}...")
        print(f"🖼️ Image provided: {len(image_bytes)} bytes")
        print(f"🔑 API Key configured: {'Yes' if self.api_key else 'No'}")
        print(f"📁 Folder ID configured: {'Yes' if self.folder_id else 'No'}")
        
        try:
            # Try vision-capable models first
            vision_models = ["yandexgpt-vision", "yandexgpt-pro"]
            regular_models = ["yandexgpt", "yandexgpt-lite", "yandexgpt-2"]
            
            # First try vision models
            for model_name in vision_models:
                try:
                    result = self._call_yandex_api_with_vision(
                        model_name, question, image_bytes, image_description
                    )
                    if result and not result.startswith("Ошибка"):
                        print(f"✅ Vision model {model_name} response received, length: {len(result)}")
                        return result
                except Exception as e:
                    print(f"⚠️ Vision model {model_name} failed: {e}")
                    continue
            
            # Fallback to regular models with image description
            print("🔄 Falling back to regular models with image description")
            enhanced_question = f"{question}\n\nОписание изображения: {image_description}"
            for model_name in regular_models:
                try:
                    result = self._call_yandex_api(
                        system_prompt="Ты - финансовый аналитик. Анализируй предоставленную информацию и изображения.",
                        user_prompt=enhanced_question,
                        temperature=0.7,
                        max_tokens=1000
                    )
                    if result and not result.startswith("Ошибка"):
                        print(f"✅ Regular model {model_name} response received, length: {len(result)}")
                        return result
                except Exception as e:
                    print(f"⚠️ Regular model {model_name} failed: {e}")
                    continue
            
            return "Не удалось получить анализ изображения. Попробуйте позже или используйте текстовый запрос."
            
        except Exception as e:
            print(f"❌ Error in ask_question_with_vision: {e}")
            return f"Ошибка при получении AI анализа изображения: {str(e)}"

    def process_freeform_command(self, user_message: str) -> Dict:
        """Process free-form commands and convert instrument names to Okama format"""
        try:
            # Special prompt for free-form command processing
            freeform_prompt = f"""
            Process this user command and convert it to a structured format for Okama platform.
            
            User command: "{user_message}"
            
            Your task:
            1. Identify what the user wants to do (portfolio analysis, risk assessment, comparison, etc.)
            2. Extract and convert ALL mentioned financial instruments to Okama namespace format
            3. Determine the appropriate command structure
            
            CRITICAL FORMATTING RULES:
            - Stocks: "AAPL.US", "SBER.MOEX", "TSLA.US"
            - Indexes: "SPX.INDX", "RTSI.INDX", "DAX.INDX" 
            - Commodities: "XAU.COMM", "BRENT.COMM", "SILVER.COMM"
            - Forex: "EURUSD.FX", "GBPUSD.FX"
            - Crypto: "BTC.CC", "ETH.CC"
            - Mutual Funds: "SBRF.PIF", "VTSAX.US"
            
            Return JSON with:
            - command_type: string (portfolio, risk, correlation, compare, efficient_frontier, chat)
            - symbols: list of strings (in Okama format)
            - parameters: dict with additional parameters
            - original_query: string (user's original message)
            - suggested_command: string (formatted command for Okama)
            """
            
            response = self._call_yandex_api(
                system_prompt="You are a financial command processor that converts free-form requests to Okama platform format. You MUST use Okama namespace formatting for all financial instruments.",
                user_prompt=freeform_prompt,
                temperature=0.1,
                max_tokens=400
            )
            
            # Extract and parse JSON response
            content = response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                # Ensure required fields exist
                result.setdefault('command_type', 'chat')
                result.setdefault('symbols', [])
                result.setdefault('parameters', {})
                result.setdefault('original_query', user_message)
                result.setdefault('suggested_command', '')
                return result
            else:
                # Fallback parsing
                return {
                    "command_type": "chat",
                    "symbols": [],
                    "parameters": {},
                    "original_query": user_message,
                    "suggested_command": "",
                    "error": "Could not parse AI response"
                }
                
        except Exception as e:
            return {
                "command_type": "chat",
                "symbols": [],
                "parameters": {},
                "original_query": user_message,
                "suggested_command": "",
                "error": f"Processing error: {str(e)}"
            }
    
    def enhance_analysis_results(self, analysis_type: str, results: Dict, user_query: str) -> str:
        """Enhance analysis results with YandexGPT insights"""
        try:
            # Create a prompt to interpret the results
            prompt = f"""
            I have performed a {analysis_type} analysis. Here are the results:
            {json.dumps(results, indent=2)}
            
            User's original query was: "{user_query}"
            
            Please provide a brief, insightful interpretation of these results in 2-3 sentences. 
            Focus on what the user should understand from this analysis.
            """
            
            response = self._call_yandex_api(
                system_prompt="You are a financial analyst who interprets financial data and provides clear insights.",
                user_prompt=prompt,
                temperature=0.5,
                max_tokens=150
            )
            
            return response
            
        except Exception as e:
            return "Анализ завершен успешно. Результаты показывают запрошенные финансовые метрики."
    
    def suggest_improvements(self, portfolio_symbols: List[str], current_metrics: Dict) -> str:
        """Suggest portfolio improvements based on current metrics"""
        try:
            prompt = f"""
            Based on this portfolio analysis:
            Portfolio symbols: {', '.join(portfolio_symbols)}
            Current metrics: {json.dumps(current_metrics, indent=2)}
            
            Provide 2-3 specific, actionable suggestions for portfolio improvement. 
            Focus on diversification, risk management, or performance optimization.
            Keep each suggestion to one sentence.
            """
            
            response = self._call_yandex_api(
                system_prompt="You are a portfolio optimization expert who provides practical investment advice.",
                user_prompt=prompt,
                temperature=0.6,
                max_tokens=200
            )
            
            return response
            
        except Exception as e:
            return "Из-за технических проблем с AI сервисом, вот общие рекомендации по оптимизации портфеля:\n\n" + \
                   "• Диверсифицируйте по различным классам активов (акции, облигации, товары)\n" + \
                   "• Учитывайте ваш профиль риска и инвестиционный горизонт\n" + \
                   "• Регулярно ребалансируйте портфель\n" + \
                   "• Рассмотрите консультацию с финансовым советником"
    
    def _call_yandex_api(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Make a call to YandexGPT API with robust fallback to different models"""
        print(f"🌐 YandexGPT API call initiated")
        print(f"🔑 API Key: {'Yes' if self.api_key else 'No'}")
        print(f"📁 Folder ID: {'Yes' if self.folder_id else 'No'}")
        
        try:
            # Check if API key and folder ID are configured
            if not self.api_key or not self.folder_id:
                print("❌ Missing API configuration")
                return "AI service is not properly configured. Please check your API settings."
            
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Try each model in priority order
            for model_name in self.model_priority:
                # Try both request formats for each model
                for format_name, request_data in [
                    ("Primary format", self._create_primary_request(model_name, system_prompt, user_prompt, temperature, max_tokens)),
                    ("Alternative format", self._create_alternative_request(model_name, system_prompt, user_prompt, temperature, max_tokens))
                ]:
                    try:
                        # Создаем сессию без прокси
                        session = requests.Session()
                        session.trust_env = False  # Игнорируем переменные окружения прокси
                        
                        response = session.post(
                            self.base_url,
                            headers=headers,
                            json=request_data,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            return self._parse_successful_response(response)
                        elif response.status_code == 500:
                            break  # Try next model
                        elif response.status_code == 400:
                            continue  # Try next format with same model
                        else:
                            break  # Try next model
                            
                    except requests.exceptions.Timeout:
                        continue
                    except Exception:
                        continue
                
                # If we get here, this model failed completely, try next one
            
            # If we reach here, all models failed
            return "Из-за технических проблем с AI сервисом, попробуйте позже или используйте базовые команды бота для анализа портфеля."
                
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def _create_primary_request(self, model_name: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> dict:
        """Create primary request format for YandexGPT API"""
        return {
            "modelUri": f"gpt://{self.folder_id}/{model_name}",
            "completionOptions": {
                "temperature": str(temperature),
                "maxTokens": str(max_tokens),
                "stream": False
            },
            "messages": [
                {
                    "role": "system",
                    "text": system_prompt
                },
                {
                    "role": "user",
                    "text": user_prompt
                }
            ]
        }
    
    def _create_alternative_request(self, model_name: str, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> dict:
        """Create alternative request format for YandexGPT API"""
        return {
            "modelUri": f"gpt://{self.folder_id}/{model_name}",
            "completionOptions": {
                "temperature": str(temperature),
                "maxTokens": str(max_tokens),
                "stream": False
            },
            "text": f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
        }
    
    def _parse_successful_response(self, response) -> str:
        """Parse successful API response and extract text content"""
        try:
            result = response.json()
            
            # Extract the response text from the result
            alternatives = result.get("result", {}).get("alternatives", [])
            if alternatives and len(alternatives) > 0:
                message = alternatives[0].get("message", {})
                text = message.get("text", "")
                if text:
                    return text
                else:
                    return "AI response received but no text content found."
            else:
                return "AI response received but no content found."
                
        except Exception as parse_error:
            return f"AI response received but could not parse: {response.text[:200]}"
    
    def _call_yandex_api_with_vision(self, model_name: str, question: str, image_bytes: bytes, image_description: str = "") -> str:
        """Make a call to YandexGPT API with vision support"""
        try:
            if not self.api_key or not self.folder_id:
                return "AI service is not properly configured. Please check your API settings."
            
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Create vision request
            request_data = {
                "modelUri": f"gpt://{self.folder_id}/{model_name}",
                "completionOptions": {
                    "temperature": "0.7",
                    "maxTokens": "1000",
                    "stream": False
                },
                "messages": [
                    {
                        "role": "system",
                        "text": "Ты - опытный финансовый аналитик. Анализируй графики и изображения, предоставляя профессиональные выводы на русском языке."
                    },
                    {
                        "role": "user",
                        "text": question,
                        "image": {
                            "data": image_bytes.hex(),
                            "mimeType": "image/png"
                        }
                    }
                ]
            }
            
            # Try vision endpoint
            vision_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
            
            # Создаем сессию без прокси
            session = requests.Session()
            session.trust_env = False  # Игнорируем переменные окружения прокси
            
            response = session.post(
                vision_url,
                headers=headers,
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                return self._parse_successful_response(response)
            elif response.status_code == 500:
                print(f"⚠️ Vision API internal error (status 500): {response.text}")
                return f"Не удалось проанализировать изображение (внутренняя ошибка сервера). Попробуйте позже или используйте текстовый запрос."
            elif response.status_code == 400:
                print(f"⚠️ Vision API bad request (status 400): {response.text}")
                return f"Не удалось проанализировать изображение (неверный запрос). Попробуйте отправить другое изображение."
            else:
                print(f"⚠️ Vision API returned status {response.status_code}: {response.text}")
                # Try alternative vision format
                return self._try_alternative_vision_format(model_name, question, image_bytes, image_description)
                
        except Exception as e:
            print(f"❌ Error in vision API call: {e}")
            return f"Ошибка при анализе изображения: {str(e)}"

    def _try_alternative_vision_format(self, model_name: str, question: str, image_bytes: bytes, image_description: str = "") -> str:
        """Try alternative vision request format"""
        try:
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Alternative vision format
            request_data = {
                "modelUri": f"gpt://{self.folder_id}/{model_name}",
                "completionOptions": {
                    "temperature": "0.7",
                    "maxTokens": "1000",
                    "stream": False
                },
                "text": f"{question}\n\nАнализируй это изображение: {image_description}",
                "image": {
                    "data": image_bytes.hex(),
                    "mimeType": "image/png"
                }
            }
            
            # Создаем сессию без прокси
            session = requests.Session()
            session.trust_env = False  # Игнорируем переменные окружения прокси
            
            response = session.post(
                "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
                headers=headers,
                json=request_data,
                timeout=60
            )
            
            if response.status_code == 200:
                return self._parse_successful_response(response)
            else:
                return f"Не удалось проанализировать изображение (статус: {response.status_code})"
                
        except Exception as e:
            return f"Ошибка при альтернативном анализе изображения: {str(e)}"
    
    def test_api_connection(self) -> Dict:
        """Test method to debug YandexGPT API connection"""
        try:
            # Check configuration
            config_status = {
                'api_key_set': bool(self.api_key),
                'folder_id_set': bool(self.folder_id),
                'base_url': self.base_url
            }
            
            if not self.api_key or not self.folder_id:
                return {
                    'status': 'error',
                    'message': 'Missing API configuration',
                    'config': config_status
                }
            
            # Test simple API call
            test_response = self._call_yandex_api(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'Hello, API test successful!'",
                temperature=0.1,
                max_tokens=50
            )
            
            if "API test successful" in test_response:
                return {
                    'status': 'success',
                    'message': 'API connection working',
                    'response': test_response,
                    'config': config_status
                }
            else:
                return {
                    'status': 'partial',
                    'message': 'API responded but with unexpected content',
                    'response': test_response,
                    'config': config_status
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Test failed: {str(e)}',
                'config': config_status if 'config_status' in locals() else 'Unknown'
            }

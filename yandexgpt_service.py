import requests
import json
import re
from typing import Dict, List, Optional
from config import Config

class YandexGPTService:
    """Service class for YandexGPT integration"""
    
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
        print(f"YandexGPT Service initialized:")
        print(f"  API Key: {'Set' if self.api_key else 'NOT SET'}")
        print(f"  Folder ID: {'Set' if self.folder_id else 'NOT SET'}")
        print(f"  Base URL: {self.base_url}")
        print(f"  Model Priority: {', '.join(self.model_priority)}")
        
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

When providing financial analysis:
1. Use quantitative methods and data-driven insights
2. Explain complex financial concepts with clear examples
3. Provide specific, actionable recommendations
4. Always emphasize risk management and diversification
5. Include relevant financial ratios and metrics
6. Consider market conditions and economic factors
7. Recommend consulting licensed financial advisors for major decisions

Format responses professionally with clear sections, bullet points, and relevant financial terminology. Be precise, thorough, and educational."""

    def analyze_query(self, user_message: str) -> Dict:
        """Analyze user query to determine intent and extract parameters"""
        try:
            # Create a prompt to analyze the user's intent
            analysis_prompt = f"""
            Analyze this user message and extract the following information:
            1. Intent (portfolio, risk, correlation, efficient_frontier, compare, chat, other)
            2. Symbols mentioned (stock tickers, ETF symbols)
            3. Time period mentioned
            4. Specific metrics requested
            
            User message: "{user_message}"
            
            Return the analysis as JSON with these fields:
            - intent: string
            - symbols: list of strings
            - time_period: string or null
            - metrics: list of strings
            - is_chat: boolean (true if it's a general question)
            """
            
            response = self._call_yandex_api(
                system_prompt="You are a helpful assistant that analyzes user queries and returns JSON responses.",
                user_prompt=analysis_prompt,
                temperature=0.1,
                max_tokens=200
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
            print(f"AI service error in analyze_query: {e}")
            # Fallback to simple keyword matching
            return self._fallback_analysis(user_message)
    
    def _fallback_analysis(self, user_message: str) -> Dict:
        """Fallback analysis using keyword matching"""
        message_lower = user_message.lower()
        
        # Extract symbols (including namespace like .INDX, .US, .COMM)
        symbols = re.findall(r'\b[A-Z]{1,6}\.[A-Z]{2,4}\b', user_message)
        
        # Debug: print extracted symbols
        print(f"DEBUG: Extracted symbols from '{user_message}': {symbols}")
        
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
            print(f"AI service error in get_financial_advice: {e}")
            return "Из-за технических проблем с AI сервисом, вот общие финансовые рекомендации:\n\n" + \
                   "• Диверсифицируйте портфель по различным классам активов\n" + \
                   "• Учитывайте ваш профиль риска и инвестиционный горизонт\n" + \
                   "• Регулярно пересматривайте и ребалансируйте портфель\n" + \
                   "• Рассмотрите консультацию с финансовым советником"
    
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
            print(f"AI service error in enhance_analysis_results: {e}")
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
            print(f"AI service error in suggest_improvements: {e}")
            return "Из-за технических проблем с AI сервисом, вот общие рекомендации по оптимизации портфеля:\n\n" + \
                   "• Диверсифицируйте по различным классам активов (акции, облигации, товары)\n" + \
                   "• Учитывайте ваш профиль риска и инвестиционный горизонт\n" + \
                   "• Регулярно ребалансируйте портфель\n" + \
                   "• Рассмотрите консультацию с финансовым советником"
    
    def _call_yandex_api(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Make a call to YandexGPT API with robust fallback to different models"""
        try:
            # Check if API key and folder ID are configured
            if not self.api_key or not self.folder_id:
                print("Missing YandexGPT API configuration")
                return "AI service is not properly configured. Please check your API settings."
            
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Try each model in priority order
            for model_name in self.model_priority:
                print(f"🔄 Trying model: {model_name}")
                
                # Try both request formats for each model
                for format_name, request_data in [
                    ("Primary format", self._create_primary_request(model_name, system_prompt, user_prompt, temperature, max_tokens)),
                    ("Alternative format", self._create_alternative_request(model_name, system_prompt, user_prompt, temperature, max_tokens))
                ]:
                    try:
                        print(f"  📝 Using {format_name}...")
                        
                        response = requests.post(
                            self.base_url,
                            headers=headers,
                            json=request_data,
                            timeout=30
                        )
                        
                        print(f"  📊 Response status: {response.status_code}")
                        
                        if response.status_code == 200:
                            print(f"✅ Model {model_name} succeeded with {format_name}!")
                            return self._parse_successful_response(response)
                        elif response.status_code == 500:
                            print(f"❌ Model {model_name} failed with 500 (internal server error)")
                            break  # Try next model
                        elif response.status_code == 400:
                            print(f"⚠️  Model {model_name} failed with 400 (bad request) - trying next format")
                            continue  # Try next format with same model
                        else:
                            print(f"❌ Model {model_name} failed with {response.status_code}")
                            print(f"  Response: {response.text[:200]}")
                            break  # Try next model
                            
                    except requests.exceptions.Timeout:
                        print(f"⏰ Timeout with {model_name} using {format_name}")
                        continue
                    except Exception as format_error:
                        print(f"❌ Error with {model_name} using {format_name}: {format_error}")
                        continue
                
                # If we get here, this model failed completely, try next one
                print(f"🔄 Moving to next model...")
            
            # If we reach here, all models failed
            print("❌ All models failed")
            return "Из-за технических проблем с AI сервисом, попробуйте позже или используйте базовые команды бота для анализа портфеля."
                
        except Exception as e:
            print(f"❌ Unexpected error in _call_yandex_api: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"📄 Parsing response: {json.dumps(result, indent=2)}")
            
            # Extract the response text from the result
            alternatives = result.get("result", {}).get("alternatives", [])
            if alternatives and len(alternatives) > 0:
                message = alternatives[0].get("message", {})
                text = message.get("text", "")
                if text:
                    return text
                else:
                    print(f"⚠️  No text found in message: {message}")
                    return "AI response received but no text content found."
            else:
                print(f"⚠️  No alternatives found in result: {result}")
                return "AI response received but no content found."
                
        except Exception as parse_error:
            print(f"❌ Error parsing response: {parse_error}")
            return f"AI response received but could not parse: {response.text[:200]}"
    
    def test_api_connection(self) -> Dict:
        """Test method to debug YandexGPT API connection"""
        try:
            print("🧪 Testing YandexGPT API connection...")
            
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

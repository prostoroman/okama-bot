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
        
        # Debug configuration
        print(f"YandexGPT Service initialized:")
        print(f"  API Key: {'Set' if self.api_key else 'NOT SET'}")
        print(f"  Folder ID: {'Set' if self.folder_id else 'NOT SET'}")
        print(f"  Base URL: {self.base_url}")
        
        if not self.api_key or not self.folder_id:
            print("⚠️  WARNING: Missing YandexGPT configuration!")
            print("   Please set YANDEX_API_KEY and YANDEX_FOLDER_ID in your environment variables")
        
        # System prompt for financial analysis
        self.system_prompt = """You are a financial analysis expert assistant. You help users understand financial concepts, analyze investment strategies, and interpret financial data.

Your expertise includes:
- Portfolio analysis and optimization
- Risk management and assessment
- Investment strategies and asset allocation
- Financial metrics interpretation
- Market analysis and trends

When analyzing financial data or providing investment advice:
1. Always consider risk vs. return trade-offs
2. Explain complex concepts in simple terms
3. Provide actionable insights when possible
4. Mention that past performance doesn't guarantee future results
5. Suggest consulting with financial advisors for major decisions

Keep responses concise but informative. Use bullet points and clear formatting when appropriate."""

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
            return f"I'm having trouble connecting to my AI assistant right now. Please try again later. Error: {str(e)}"
    
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
            return "Analysis completed successfully. The results show the financial metrics you requested."
    
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
            return "Consider consulting with a financial advisor for personalized portfolio optimization advice."
    
    def _call_yandex_api(self, system_prompt: str, user_prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Make a call to YandexGPT API"""
        try:
            # Check if API key and folder ID are configured
            if not self.api_key or not self.folder_id:
                print("Missing YandexGPT API configuration")
                return "AI service is not properly configured. Please check your API settings."
            
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Use the correct YandexGPT API format with configured folder ID
            # Try different request formats based on Yandex documentation
            data = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
                "completionOptions": {
                    "temperature": str(temperature),  # Ensure string format
                    "maxTokens": str(max_tokens),    # Ensure string format
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
            
            # Alternative format if the first one fails
            alt_data = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
                "completionOptions": {
                    "temperature": str(temperature),
                    "maxTokens": str(max_tokens),
                    "stream": False
                },
                "text": f"{system_prompt}\n\nUser: {user_prompt}\n\nAssistant:"
            }
            
            # Alternative model URIs to try with configured folder ID
            alt_model_uris = [
                f"gpt://{self.folder_id}/yandexgpt-lite",
                f"gpt://{self.folder_id}/yandexgpt",
                f"gpt://{self.folder_id}/yandexgpt-pro",
                f"gpt://{self.folder_id}/yandexgpt-2"
            ]
            
            print(f"Calling YandexGPT API with primary format: {json.dumps(data, indent=2)}")
            
            # Try primary format first
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            # If primary format fails with 400, try alternative format
            if response.status_code == 400:
                print(f"Primary format failed with 400, trying alternative format...")
                print(f"Alternative format: {json.dumps(alt_data, indent=2)}")
                
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=alt_data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    print("✓ Alternative format succeeded!")
                else:
                    print(f"Alternative format also failed: {response.status_code}")
            
            print(f"YandexGPT API response status: {response.status_code}")
            print(f"YandexGPT API response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"YandexGPT API success response: {json.dumps(result, indent=2)}")
                
                # Extract the response text from the result
                alternatives = result.get("result", {}).get("alternatives", [])
                if alternatives and len(alternatives) > 0:
                    message = alternatives[0].get("message", {})
                    text = message.get("text", "")
                    if text:
                        return text
                    else:
                        print(f"No text found in message: {message}")
                        return "AI response received but no text content found."
                else:
                    print(f"No alternatives found in result: {result}")
                    return "AI response received but no content found."
            else:
                print(f"YandexGPT API error: {response.status_code}")
                print(f"Response text: {response.text}")
                print(f"Response headers: {dict(response.headers)}")
                
                # Try to parse error response
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", "Unknown error")
                    error_code = error_data.get("code", "No error code")
                    error_details = error_data.get("details", "No details")
                    print(f"Error message: {error_message}")
                    print(f"Error code: {error_code}")
                    print(f"Error details: {error_details}")
                    
                    # Return more detailed error information
                    if error_message != "Unknown error":
                        return f"AI service error ({response.status_code}): {error_message}"
                    elif error_code != "No error code":
                        return f"AI service error ({response.status_code}): Code {error_code}"
                    else:
                        return f"AI service error ({response.status_code}): {response.text[:200]}"
                        
                except Exception as parse_error:
                    print(f"Could not parse error response: {parse_error}")
                    # Return the raw response text for debugging
                    return f"AI service error ({response.status_code}): {response.text[:200]}"
                
        except requests.exceptions.Timeout:
            print("YandexGPT API request timed out")
            return "AI service request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            print(f"YandexGPT API request error: {e}")
            return f"AI service request error: {str(e)}"
        except Exception as e:
            print(f"Unexpected error calling YandexGPT API: {e}")
            import traceback
            traceback.print_exc()
            return f"Unexpected error: {str(e)}"
    
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

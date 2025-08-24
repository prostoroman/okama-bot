import openai
from typing import Dict, List, Optional
import json
import re
from config import Config

class ChatGPTService:
    """Service class for ChatGPT integration"""
    
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
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
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes user queries and returns JSON responses."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            # Extract and parse JSON response
            content = response.choices[0].message.content
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
        
        # Extract symbols (uppercase letter combinations)
        symbols = re.findall(r'\b[A-Z]{1,5}\b', user_message)
        
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
        """Get financial advice or answer from ChatGPT"""
        try:
            # Build the prompt with context if available
            if context and context.get('symbols'):
                symbols_info = f"User is asking about: {', '.join(context['symbols'])}. "
            else:
                symbols_info = ""
            
            prompt = f"{symbols_info}User question: {user_message}"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"I'm having trouble connecting to my AI assistant right now. Please try again later. Error: {str(e)}"
    
    def enhance_analysis_results(self, analysis_type: str, results: Dict, user_query: str) -> str:
        """Enhance analysis results with ChatGPT insights"""
        try:
            # Create a prompt to interpret the results
            prompt = f"""
            I have performed a {analysis_type} analysis. Here are the results:
            {json.dumps(results, indent=2)}
            
            User's original query was: "{user_query}"
            
            Please provide a brief, insightful interpretation of these results in 2-3 sentences. 
            Focus on what the user should understand from this analysis.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a financial analyst who interprets financial data and provides clear insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=150
            )
            
            return response.choices[0].message.content
            
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
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a portfolio optimization expert who provides practical investment advice."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return "Consider consulting with a financial advisor for personalized portfolio optimization advice."

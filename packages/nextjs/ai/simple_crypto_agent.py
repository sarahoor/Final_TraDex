import os
import json
import requests
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini API
import google.generativeai as genai

class SimpleCryptoAgent:
    def __init__(self, gemini_api_key: str | None = None):
        # Load API key from environment or parameter
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required. Set it in .env file or pass as parameter.")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("✅ Gemini AI initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini AI: {e}")
            raise
        
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # Set request timeout and headers
        self.session.timeout = 30
        self.session.headers.update({
            'User-Agent': 'Financial-AI-Assistant/1.0',
            'Accept': 'application/json'
        })
        
        # Add CoinGecko API key if available
        coingecko_key = os.getenv("COINGECKO_API_KEY")
        if coingecko_key:
            self.session.headers.update({'x-cg-demo-api-key': coingecko_key})
            print("✅ CoinGecko API key loaded")
        
        self.graph_base = os.getenv("GRAPH_API_BASE", "http://localhost:3000/api/graph")
        
        # Professional Risk Profiles
        self.risk_profiles = {
            "DIAMOND": {
                "name": "Play it Safe 🛡️",
                "description": "Low-risk investment strategy focused on established, stable cryptocurrencies",
                "style": "conservative, capital preservation focused, seeking steady 10-25% annual returns",
                "recommended_assets": ["Bitcoin", "Ethereum", "Stablecoins"],
                "max_volatility": 30,
                "preferred_market_cap": "large_cap"
            },
            "SIGMA": {
                "name": "Smart Investor 📊", 
                "description": "Calculated risk strategy balancing stability with growth potential",
                "style": "balanced, data-driven decisions, targeting 25-75% annual returns with managed risk",
                "recommended_assets": ["Bitcoin", "Ethereum", "Top 20 Altcoins", "DeFi Blue Chips"],
                "max_volatility": 50,
                "preferred_market_cap": "large_to_mid_cap"
            },
            "DEGEN": {
                "name": "High Risk High Reward 🚀",
                "description": "High-growth potential strategy with tolerance for significant volatility",
                "style": "aggressive growth focused, seeking 100%+ returns, comfortable with high volatility",
                "recommended_assets": ["Growth Altcoins", "DeFi Tokens", "Layer 1s", "Emerging Projects"],
                "max_volatility": 80,
                "preferred_market_cap": "mid_to_small_cap"
            }
        }
        print("✅ SimpleCryptoAgent initialized successfully")
    
    def _make_request(self, url: str, params: dict = None, retries: int = 3) -> Dict[str, Any]:
        """Make HTTP request with retry logic and better error handling"""
        for attempt in range(retries):
            try:
                print(f"🔍 Making request to: {url}")
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    print(f"⚠️ Rate limited, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                    return {"error": f"HTTP {response.status_code}"}
                    
            except requests.exceptions.Timeout:
                print(f"⏰ Request timeout (attempt {attempt + 1}/{retries})")
                if attempt == retries - 1:
                    return {"error": "Request timeout"}
                time.sleep(2)
                
            except requests.exceptions.ConnectionError:
                print(f"🌐 Connection error (attempt {attempt + 1}/{retries})")
                if attempt == retries - 1:
                    return {"error": "Connection error"}
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Request error: {e}")
                return {"error": f"Request failed: {str(e)}"}
        
        return {"error": "Max retries exceeded"}
    
    def get_crypto_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch comprehensive crypto data from CoinGecko with 6-month analysis"""
        try:
            print(f"📊 Fetching data for {symbol.upper()}...")
            
            # Get coin data
            url = f"{self.coingecko_base}/coins/{symbol.lower()}"
            params = {'localization': 'false', 'market_data': 'true'}
            data = self._make_request(url, params)
            
            if data.get('error'):
                # Try alternative endpoint with coin list
                print(f"⚠️ Direct lookup failed, searching coin list...")
                return self._search_coin_by_symbol(symbol)
            
            # Get 6-month historical data for enhanced analysis
            hist_url = f"{self.coingecko_base}/coins/{symbol.lower()}/market_chart"
            hist_params = {'vs_currency': 'usd', 'days': '180'}
            hist_data = self._make_request(hist_url, hist_params)
            
            if hist_data.get('error'):
                print(f"⚠️ Historical data unavailable for {symbol}")
                hist_data = {}
            
            # Calculate 6-month metrics
            prices = [price[1] for price in hist_data.get('prices', [])]
            six_month_high = max(prices) if prices else 0
            six_month_low = min(prices) if prices else 0
            current_price = data.get('market_data', {}).get('current_price', {}).get('usd', 0)
            
            # Calculate position relative to 6-month range
            if six_month_high > six_month_low:
                price_position = ((current_price - six_month_low) / (six_month_high - six_month_low)) * 100
            else:
                price_position = 50
            
            result = {
                "symbol": symbol.upper(),
                "current_price": current_price,
                "price_change_24h": data.get('market_data', {}).get('price_change_percentage_24h', 0),
                "price_change_7d": data.get('market_data', {}).get('price_change_percentage_7d', 0),
                "price_change_30d": data.get('market_data', {}).get('price_change_percentage_30d', 0),
                "market_cap": data.get('market_data', {}).get('market_cap', {}).get('usd', 0),
                "volume_24h": data.get('market_data', {}).get('total_volume', {}).get('usd', 0),
                "market_cap_rank": data.get('market_data', {}).get('market_cap_rank', 0),
                "six_month_high": six_month_high,
                "six_month_low": six_month_low,
                "price_position_6m": price_position,
                "prices": prices,
                "description": data.get('description', {}).get('en', '')[:300] + "..." if data.get('description', {}).get('en', '') else ""
            }
            
            print(f"✅ Successfully fetched data for {symbol.upper()}")
            return result
            
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            return {"error": f"Failed to fetch {symbol}: {str(e)}"}
    
    def _search_coin_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """Search for coin by symbol using coin list endpoint"""
        try:
            # Get coin list
            coins_url = f"{self.coingecko_base}/coins/list"
            coins_data = self._make_request(coins_url)
            
            if coins_data.get('error'):
                return {"error": f"Could not search for {symbol}"}
            
            # Find matching coin
            symbol_lower = symbol.lower()
            for coin in coins_data:
                if coin.get('symbol', '').lower() == symbol_lower:
                    # Try to get data using the coin ID
                    return self.get_crypto_data(coin['id'])
            
            return {"error": f"Coin {symbol} not found"}
            
        except Exception as e:
            return {"error": f"Search failed for {symbol}: {str(e)}"}
    
    def calculate_advanced_risk_metrics(self, crypto_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate comprehensive risk metrics including volatility and position analysis"""
        try:
            if not crypto_data.get('prices') or len(crypto_data['prices']) < 30:
                return {"error": "Insufficient data for risk analysis"}
            
            prices = np.array(crypto_data['prices'])
            if len(prices) < 2:
                return {"error": "Not enough price data"}
            
            returns = np.diff(np.log(prices))
            
            # Calculate various risk metrics
            volatility = np.std(returns) * np.sqrt(365) * 100  # Annualized volatility
            max_drawdown = self._calculate_max_drawdown(prices)
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            
            # Risk score (0-100, higher = riskier)
            risk_score = min(100, (volatility * 0.6) + (max_drawdown * 0.4))
            
            # Position analysis
            position_6m = crypto_data.get('price_position_6m', 50)
            
            # Price momentum
            if len(prices) >= 30:
                recent_momentum = (prices[-7:].mean() / prices[-30:].mean() - 1) * 100
            else:
                recent_momentum = 0
            
            return {
                'volatility': round(volatility, 2),
                'max_drawdown': round(max_drawdown, 2),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'risk_score': round(risk_score, 1),
                'price_position_6m': round(position_6m, 1),
                'recent_momentum': round(recent_momentum, 2),
                'six_month_high': crypto_data.get('six_month_high', 0),
                'six_month_low': crypto_data.get('six_month_low', 0)
            }
            
        except Exception as e:
            print(f"❌ Risk calculation error: {e}")
            return {"error": f"Risk calculation failed: {str(e)}"}
    
    def _calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        try:
            if len(prices) < 2:
                return 0
            returns = np.diff(prices) / prices[:-1]
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            return abs(np.min(drawdown)) * 100
        except:
            return 0
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio (assuming 0% risk-free rate)"""
        try:
            if np.std(returns) == 0 or len(returns) == 0:
                return 0
            return np.mean(returns) / np.std(returns) * np.sqrt(365)
        except:
            return 0
    
    def assess_risk_fit(self, risk_metrics: Dict[str, Any], risk_profile: str) -> Dict[str, Any]:
        """Assess how well an asset fits the user's risk profile"""
        try:
            if risk_profile not in self.risk_profiles:
                return {"error": f"Invalid risk profile: {risk_profile}"}
            
            profile = self.risk_profiles[risk_profile]
            max_vol = profile['max_volatility']
            
            volatility = risk_metrics.get('volatility', 0)
            risk_score = risk_metrics.get('risk_score', 0)
            
            # Calculate fit score (0-100)
            if volatility <= max_vol:
                fit_score = 100 - (volatility / max_vol) * 30
            else:
                fit_score = 70 - ((volatility - max_vol) / max_vol) * 50
            
            fit_score = max(0, min(100, fit_score))
            
            recommendation = "STRONG BUY" if fit_score > 80 else "BUY" if fit_score > 60 else "HOLD" if fit_score > 40 else "CAUTION"
            
            return {
                'fit_score': round(fit_score, 1),
                'recommendation': recommendation,
                'risk_assessment': self._get_risk_assessment(risk_score, risk_profile)
            }
            
        except Exception as e:
            print(f"❌ Risk fit assessment error: {e}")
            return {"error": f"Risk assessment failed: {str(e)}"}
    
    def _get_risk_assessment(self, risk_score: float, risk_profile: str) -> str:
        """Get risk assessment text"""
        if risk_profile not in self.risk_profiles:
            return f"❌ Invalid risk profile: {risk_profile}"
        
        profile_limits = {"DIAMOND": 30, "SIGMA": 50, "DEGEN": 80}
        limit = profile_limits[risk_profile]
        
        if risk_score <= limit * 0.7:
            return "✅ Well within your risk tolerance"
        elif risk_score <= limit:
            return "⚠️ Moderate risk for your profile"
        else:
            return "🚨 Higher risk than recommended for your profile"
    
    def detect_multiple_cryptos(self, message: str) -> List[str]:
        """Detect multiple cryptocurrency symbols in a message"""
        crypto_symbols = {
            'btc': 'bitcoin', 'bitcoin': 'bitcoin',
            'eth': 'ethereum', 'ethereum': 'ethereum',
            'sol': 'solana', 'solana': 'solana',
            'ada': 'cardano', 'cardano': 'cardano',
            'matic': 'polygon', 'polygon': 'polygon',
            'link': 'chainlink', 'chainlink': 'chainlink',
            'avax': 'avalanche-2', 'avalanche': 'avalanche-2',
            'dot': 'polkadot', 'polkadot': 'polkadot',
            'uni': 'uniswap', 'uniswap': 'uniswap',
            'aave': 'aave', 'comp': 'compound-governance-token',
            'bnb': 'binancecoin', 'binance': 'binancecoin',
            'xrp': 'ripple', 'ripple': 'ripple',
            'doge': 'dogecoin', 'dogecoin': 'dogecoin',
            'ltc': 'litecoin', 'litecoin': 'litecoin',
            'atom': 'cosmos', 'cosmos': 'cosmos',
            'near': 'near', 'icp': 'internet-computer',
            'fil': 'filecoin', 'filecoin': 'filecoin',
            'mana': 'decentraland', 'decentraland': 'decentraland',
            'sand': 'the-sandbox', 'sandbox': 'the-sandbox',
            'axs': 'axie-infinity', 'grt': 'the-graph',
            'ftm': 'fantom', 'fantom': 'fantom',
            'algo': 'algorand', 'algorand': 'algorand',
            'kaia': 'kaia'  # Adding kaia since user asked about it
        }
        
        message_lower = message.lower()
        detected_symbols = []
        
        for key, value in crypto_symbols.items():
            if key in message_lower and value not in detected_symbols:
                detected_symbols.append(value)
        
        return detected_symbols
    
    def compare_cryptos(self, symbols: List[str], risk_profile: str = "SIGMA") -> str:
        """Compare multiple cryptocurrencies for investment analysis"""
        try:
            if risk_profile not in self.risk_profiles:
                return f"❌ **Invalid Risk Profile**: '{risk_profile}'. Valid options are: {', '.join(self.risk_profiles.keys())}"
            
            profile = self.risk_profiles[risk_profile]
            comparison_data = []
            
            print(f"🔍 Comparing {len(symbols)} cryptocurrencies...")
            
            # Get data for all symbols
            for symbol in symbols:
                crypto_data = self.get_crypto_data(symbol)
                if not crypto_data.get('error'):
                    risk_metrics = self.calculate_advanced_risk_metrics(crypto_data)
                    if not risk_metrics.get('error'):
                        risk_fit = self.assess_risk_fit(risk_metrics, risk_profile)
                        
                        comparison_data.append({
                            'symbol': symbol.upper(),
                            'price': crypto_data['current_price'],
                            'change_24h': crypto_data['price_change_24h'],
                            'change_7d': crypto_data['price_change_7d'],
                            'change_30d': crypto_data['price_change_30d'],
                            'market_cap': crypto_data['market_cap'],
                            'volume_24h': crypto_data['volume_24h'],
                            'rank': crypto_data['market_cap_rank'],
                            'volatility': risk_metrics['volatility'],
                            'risk_score': risk_metrics['risk_score'],
                            'fit_score': risk_fit['fit_score'],
                            'recommendation': risk_fit['recommendation'],
                            'price_position_6m': risk_metrics['price_position_6m'],
                            'six_month_high': risk_metrics['six_month_high'],
                            'six_month_low': risk_metrics['six_month_low'],
                            'recent_momentum': risk_metrics['recent_momentum']
                        })
                        print(f"✅ Analyzed {symbol.upper()}")
                else:
                    print(f"⚠️ Skipped {symbol}: {crypto_data['error']}")
            
            if not comparison_data:
                return "❌ **Error**: Could not fetch data for any of the requested cryptocurrencies."
            
            # Sort by fit score for ranking
            comparison_data.sort(key=lambda x: x['fit_score'], reverse=True)
            
            # Get market context
            fear_greed = self.get_fear_greed_index()
            
            # Create comparison prompt
            comparison_prompt = f"""
            You are a professional cryptocurrency analyst providing a comparative investment analysis.
            
            **COMPARISON REQUEST**: {', '.join([d['symbol'] for d in comparison_data])}
            **INVESTOR PROFILE**: {profile['name']} - {profile['description']}
            **RISK TOLERANCE**: {profile['style']}
            
            **COMPARATIVE DATA**:
            {json.dumps(comparison_data, indent=2)}
            
            **MARKET CONTEXT**:
            - Fear & Greed Index: {fear_greed.get('value', 'N/A')} ({fear_greed.get('classification', 'N/A')})
            
            **RESPONSE FORMAT** (use markdown formatting):
            
            ## 📊 **COMPARATIVE ANALYSIS SUMMARY**
            [Brief overview comparing all assets]
            
            ## 🏆 **RANKING FOR {profile['name'].upper()}**
            ### 1. [Best Fit Asset]
            - **Fit Score**: X% | **Risk Score**: X/100 | **Recommendation**: BUY/HOLD/SELL
            - **Key Strengths**: [Why this ranks #1 for this risk profile]
            - **Entry Strategy**: $X.XX (X% of portfolio)
            
            ### 2. [Second Best Asset]
            - **Fit Score**: X% | **Risk Score**: X/100 | **Recommendation**: BUY/HOLD/SELL
            - **Key Strengths**: [Why this ranks #2]
            - **Entry Strategy**: $X.XX (X% of portfolio)
            
            ### 3. [Third Asset if applicable]
            [Same format]
            
            ## ⚖️ **SIDE-BY-SIDE COMPARISON**
            | Metric | {comparison_data[0]['symbol'] if comparison_data else 'N/A'} | {comparison_data[1]['symbol'] if len(comparison_data) > 1 else 'N/A'} | {comparison_data[2]['symbol'] if len(comparison_data) > 2 else 'N/A'} |
            |--------|------------|------------|------------|
            | Current Price | [prices] | [prices] | [prices] |
            | 24h Change | [changes] | [changes] | [changes] |
            | Risk Score | [scores] | [scores] | [scores] |
            | Volatility | [vol] | [vol] | [vol] |
            | Profile Fit | [fit] | [fit] | [fit] |
            
            ## 💡 **PORTFOLIO ALLOCATION RECOMMENDATION**
            [Specific allocation percentages for a {profile['name']} portfolio]
            
            ## ⚠️ **RISK CONSIDERATIONS**
            [Compare risks across all assets for this risk profile]
            
            ## 📈 **MARKET TIMING**
            [Compare current market positions and entry timing for each asset]
            
            **INSTRUCTIONS**:
            - Use professional, institutional-grade language
            - Avoid slang or casual expressions
            - Focus on quantitative analysis and specific metrics
            - Provide clear reasoning for rankings based on risk profile
            - Include specific price targets and portfolio allocations
            """
            
            response = self.model.generate_content(comparison_prompt)
            return response.text
            
        except Exception as e:
            print(f"❌ Comparison error: {e}")
            return f"❌ **Comparison Failed**: {str(e)}"
    
    def analyze_crypto(self, symbol: str, risk_profile: str = "SIGMA") -> str:
        """Enhanced crypto analysis with risk-adjusted recommendations"""
        try:
            print(f"🔍 Starting analysis for {symbol.upper()}...")
            
            # Validate risk profile
            if risk_profile not in self.risk_profiles:
                return f"❌ **Invalid Risk Profile**: '{risk_profile}'. Valid options are: {', '.join(self.risk_profiles.keys())}"
            
            # Get crypto data
            crypto_data = self.get_crypto_data(symbol)
            if "error" in crypto_data:
                return f"❌ **Error**: {crypto_data['error']}"
            
            # Calculate risk metrics
            risk_metrics = self.calculate_advanced_risk_metrics(crypto_data)
            if "error" in risk_metrics:
                return f"❌ **Risk Analysis Error**: {risk_metrics['error']}"
            
            # Assess fit with risk profile
            risk_fit = self.assess_risk_fit(risk_metrics, risk_profile)
            
            # Get market context
            fear_greed = self.get_fear_greed_index()
            profile = self.risk_profiles[risk_profile]
            
            # Create enhanced analysis prompt
            analysis_prompt = f"""
            You are a professional cryptocurrency analyst providing institutional-grade investment analysis.
            
            **ANALYSIS REQUEST**: {symbol.upper()} for {profile['name']} investor
            **INVESTMENT STRATEGY**: {profile['description']}
            
            **CURRENT MARKET DATA**:
            - Price: ${crypto_data['current_price']:,.4f}
            - 24h Change: {crypto_data['price_change_24h']:.2f}%
            - 7d Change: {crypto_data['price_change_7d']:.2f}%
            - 30d Change: {crypto_data['price_change_30d']:.2f}%
            - Market Cap Rank: #{crypto_data['market_cap_rank']}
            - 24h Volume: ${crypto_data['volume_24h']:,.0f}
            
            **6-MONTH ANALYSIS**:
            - 6M High: ${risk_metrics['six_month_high']:,.4f}
            - 6M Low: ${risk_metrics['six_month_low']:,.4f}
            - Current Position: {risk_metrics['price_position_6m']:.1f}% of 6M range
            - Recent Momentum: {risk_metrics['recent_momentum']:.2f}%
            
            **RISK METRICS**:
            - Volatility: {risk_metrics['volatility']:.1f}% (annualized)
            - Max Drawdown: {risk_metrics['max_drawdown']:.1f}%
            - Risk Score: {risk_metrics['risk_score']:.1f}/100
            - Profile Fit: {risk_fit['fit_score']:.1f}%
            - Assessment: {risk_fit['risk_assessment']}
            
            **MARKET SENTIMENT**:
            - Fear & Greed: {fear_greed.get('value', 'N/A')} ({fear_greed.get('classification', 'N/A')})
            
            **RESPONSE FORMAT** (use markdown formatting):
            
            ## 🎯 **INVESTMENT SIGNAL**: {risk_fit['recommendation']} (Confidence: {risk_fit['fit_score']:.0f}%)
            
            ## 📊 **TECHNICAL ANALYSIS**
            [Analyze price position, momentum, key levels based on 6-month data using professional analysis]
            
            ## 🎰 **RISK ASSESSMENT** 
            [Detailed risk analysis for this specific risk profile with specific volatility numbers]
            
            ## 💰 **STRATEGIC RECOMMENDATION**
            [Specific entry prices, position sizing recommendations, target levels based on risk profile]
            
            ## ⚠️ **KEY LEVELS TO WATCH**
            [Support/resistance levels and potential catalysts]
            
            ## 💡 **PORTFOLIO ALLOCATION**
            [Recommended portfolio percentage for this risk profile]
            
            **IMPORTANT**: 
            - Use professional, clear language suitable for institutional investors
            - Avoid slang or casual expressions
            - Adjust ALL recommendations specifically for {profile['name']} risk tolerance
            - Use the actual volatility and risk metrics provided
            - Reference the 6-month price position in your analysis
            - Provide specific price targets and stop-loss levels
            - Use professional financial terminology with markdown formatting
            """
            
            response = self.model.generate_content(analysis_prompt)
            print(f"✅ Analysis completed for {symbol.upper()}")
            return response.text
            
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return f"❌ **Analysis Failed**: {str(e)}"
    
    def chat(self, message: str, risk_profile: str = "SIGMA") -> str:
        """Enhanced chat with financial focus and multi-crypto comparison"""
        try:
            print(f"💬 Processing chat message...")
            
            # Validate risk profile
            if risk_profile not in self.risk_profiles:
                return f"❌ **Invalid Risk Profile**: '{risk_profile}'. Valid options are: {', '.join(self.risk_profiles.keys())}"
            
            # Always relate responses back to finance/crypto
            profile = self.risk_profiles[risk_profile]
            
            # Check for multiple crypto mentions
            detected_symbols = self.detect_multiple_cryptos(message)
            
            # If multiple cryptos detected, do comparison
            if len(detected_symbols) > 1:
                return self.compare_cryptos(detected_symbols, risk_profile)
            
            # If single crypto mentioned, do detailed analysis
            elif len(detected_symbols) == 1:
                return self.analyze_crypto(detected_symbols[0], risk_profile)
            
            # Special commands
            if 'scan' in message.lower():
                return self.scan_opportunities(risk_profile)
            
            # Get market context for financial relevance
            fear_greed = self.get_fear_greed_index()
            market_overview = self.get_market_overview()
            
            # Enhanced chat prompt with professional language
            chat_prompt = f"""
            You are a professional cryptocurrency and financial markets AI assistant providing institutional-grade analysis.
            
            **INVESTOR PROFILE**: {profile['name']}
            **INVESTMENT STRATEGY**: {profile['description']}
            **APPROACH**: {profile['style']}
            
            **CURRENT MARKET CONTEXT**:
            - Fear & Greed Index: {fear_greed.get('value', 'N/A')} ({fear_greed.get('classification', 'N/A')})
            - Market Interpretation: {fear_greed.get('interpretation', 'Market analysis unavailable')}
            - Total Crypto Market Cap: ${market_overview.get('total_market_cap', {}).get('usd', 0):,.0f}
            
            **USER MESSAGE**: "{message}"
            
            **RESPONSE GUIDELINES**:
            1. ALWAYS relate your response back to finance, investments, or cryptocurrency markets
            2. Even for non-financial questions, provide a brief answer then pivot to relevant financial insights
            3. Use professional, institutional-grade language - avoid slang or casual expressions
            4. Use markdown formatting with proper headers, bold text, and clear structure
            5. Provide actionable financial advice based on their risk profile
            6. Include current market context when relevant
            7. Be professional and analytical, suitable for institutional investors
            
            **EXAMPLES OF PROFESSIONAL TONE**:
            - Instead of "crypto is mooning" → "experiencing significant upward momentum"
            - Instead of "HODL" → "maintain long-term positions"
            - Instead of "to the moon" → "substantial growth potential"
            - Instead of "diamond hands" → "long-term conviction"
            
            **RESPONSE FORMAT**: Use markdown with ## headers, **bold** text, and clear analytical structure.
            """
            
            response = self.model.generate_content(chat_prompt)
            print(f"✅ Chat response generated")
            return response.text
            
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return f"❌ **Analysis Error**: {str(e)}"
    
    def scan_opportunities(self, risk_profile: str = "SIGMA") -> str:
        """Enhanced opportunity scanning with risk-adjusted recommendations"""
        try:
            print(f"🔍 Starting opportunity scan for {risk_profile}...")
            
            # Validate risk profile
            if risk_profile not in self.risk_profiles:
                return f"❌ **Invalid Risk Profile**: '{risk_profile}'. Valid options are: {', '.join(self.risk_profiles.keys())}"
            
            profile = self.risk_profiles[risk_profile]
            
            # Define coin lists based on risk profile
            if risk_profile == "DIAMOND":
                coins = ['bitcoin', 'ethereum', 'cardano', 'polygon', 'chainlink']
            elif risk_profile == "SIGMA":
                coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polygon', 'chainlink', 'avalanche-2', 'uniswap']
            else:  # DEGEN
                coins = ['solana', 'avalanche-2', 'chainlink', 'uniswap', 'aave', 'compound-governance-token', 'the-graph', 'polygon']
            
            opportunities = []
            print(f"🔍 Scanning {len(coins)} tokens for {profile['name']} opportunities...")
            
            for coin in coins:
                try:
                    data = self.get_crypto_data(coin)
                    if not data.get('error'):
                        risk_metrics = self.calculate_advanced_risk_metrics(data)
                        if not risk_metrics.get('error'):
                            risk_fit = self.assess_risk_fit(risk_metrics, risk_profile)
                            
                            opportunities.append({
                                'symbol': coin.upper(),
                                'price': data['current_price'],
                                'change_24h': data['price_change_24h'],
                                'change_7d': data['price_change_7d'],
                                'volatility': risk_metrics['volatility'],
                                'risk_score': risk_metrics['risk_score'],
                                'fit_score': risk_fit['fit_score'],
                                'recommendation': risk_fit['recommendation'],
                                'price_position_6m': risk_metrics['price_position_6m'],
                                'volume': data['volume_24h'],
                                'rank': data['market_cap_rank']
                            })
                            print(f"✅ Analyzed {coin.upper()}")
                except Exception as e:
                    print(f"⚠️ Skipped {coin}: {e}")
                    continue
            
            if not opportunities:
                return f"❌ **Scan Failed**: Could not analyze any opportunities for {risk_profile}"
            
            # Sort by fit score
            opportunities.sort(key=lambda x: x['fit_score'], reverse=True)
            
            # Create scan prompt
            scan_prompt = f"""
            You are a professional cryptocurrency analyst conducting a market opportunity analysis for {profile['name']} investors.
            
            **INVESTMENT PROFILE**: {profile['description']}
            **TARGET RETURNS**: {profile['style']}
            **MAX VOLATILITY TOLERANCE**: {profile['max_volatility']}%
            
            **ANALYZED OPPORTUNITIES**:
            {json.dumps(opportunities[:8], indent=2)}
            
            **ANALYSIS REPORT FORMAT** (use markdown):
            
            ## 🏆 **TOP INVESTMENT OPPORTUNITIES FOR {profile['name'].upper()}**
            
            ### 1. [Best Fit Token]
            - **Risk-Adjusted Score**: X% | **Volatility**: X% | **Recommendation**: BUY/HOLD/SELL
            - **Technical Analysis**: [Professional analysis based on price position and momentum]
            - **Entry Strategy**: $X.XX (Position size: X% of portfolio)
            - **Target Price**: $X.XX | **Stop Loss**: $X.XX
            - **Investment Thesis**: [Why this fits the risk profile]
            
            ### 2. [Second Best Token]
            [Same professional format]
            
            ### 3. [Third Best Token]
            [Same professional format]
            
            ## ⚠️ **RISK MANAGEMENT FRAMEWORK**
            [Professional risk management advice for this profile]
            
            ## 📊 **MARKET TIMING ANALYSIS**
            [Current market conditions and optimal entry timing]
            
            ## 💼 **PORTFOLIO CONSTRUCTION**
            [Recommended portfolio allocation and diversification strategy]
            
            **REQUIREMENTS**:
            - Use professional, institutional-grade language
            - Avoid slang or casual expressions
            - Focus on quantitative analysis and risk metrics
            - Provide specific entry prices and position sizing recommendations
            - Include stop-loss levels appropriate for the risk profile
            - Use actual fit scores and risk metrics provided in the analysis
            """
            
            response = self.model.generate_content(scan_prompt)
            print(f"✅ Scan completed for {risk_profile}")
            return response.text
            
        except Exception as e:
            print(f"❌ Scan error: {e}")
            return f"❌ **Scan Failed**: {str(e)}"
    
    def get_fear_greed_index(self) -> Dict[str, Any]:
        """Get crypto fear & greed index"""
        try:
            url = "https://api.alternative.me/fng/"
            data = self._make_request(url)
            
            if data.get('error'):
                return {"error": "Could not fetch fear & greed index"}
            
            index_value = int(data['data'][0]['value'])
            classification = data['data'][0]['value_classification']
            
            return {
                "value": index_value,
                "classification": classification,
                "interpretation": self._interpret_fear_greed(index_value)
            }
        except Exception as e:
            print(f"❌ Fear & Greed fetch error: {e}")
            return {"error": "Could not fetch fear & greed index"}
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Get overall market data"""
        try:
            url = f"{self.coingecko_base}/global"
            data = self._make_request(url)
            
            if data.get('error'):
                return {"error": "Could not fetch market overview"}
            
            return {
                "total_market_cap": data.get('data', {}).get('total_market_cap', {}),
                "total_volume": data.get('data', {}).get('total_volume', {}),
                "market_cap_percentage": data.get('data', {}).get('market_cap_percentage', {}),
                "active_cryptocurrencies": data.get('data', {}).get('active_cryptocurrencies', 0)
            }
        except Exception as e:
            print(f"❌ Market overview error: {e}")
            return {"error": "Could not fetch market overview"}
    
    def _interpret_fear_greed(self, value: int) -> str:
        """Enhanced fear & greed interpretation"""
        if value <= 25:
            return "Extreme Fear - Historically excellent buying opportunity for long-term investors"
        elif value <= 45:
            return "Fear - Good accumulation zone, consider dollar-cost averaging"
        elif value <= 55:
            return "Neutral - Balanced market conditions, focus on technical analysis"
        elif value <= 75:import os
import json
import requests
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import numpy as np
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gemini API
import google.generativeai as genai

class SimpleCryptoAgent:
    def __init__(self, gemini_api_key: str | None = None):
        # Load API key from environment or parameter
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required. Set it in .env file or pass as parameter.")
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
            print("✅ Gemini AI initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini AI: {e}")
            raise
        
        self.coingecko_base = "https://api.coingecko.com/api/v3"
        self.session = requests.Session()
        
        # Set request timeout and headers
        self.session.timeout = 30
        self.session.headers.update({
            'User-Agent': 'Financial-AI-Assistant/1.0',
            'Accept': 'application/json'
        })
        
        # Add CoinGecko API key if available
        coingecko_key = os.getenv("COINGECKO_API_KEY")
        if coingecko_key:
            self.session.headers.update({'x-cg-demo-api-key': coingecko_key})
            print("✅ CoinGecko API key loaded")
        
        self.graph_base = os.getenv("GRAPH_API_BASE", "http://localhost:3000/api/graph")
        
        # Professional Risk Profiles
        self.risk_profiles = {
            "DIAMOND": {
                "name": "Play it Safe 🛡️",
                "description": "Low-risk investment strategy focused on established, stable cryptocurrencies",
                "style": "conservative, capital preservation focused, seeking steady 10-25% annual returns",
                "recommended_assets": ["Bitcoin", "Ethereum", "Stablecoins"],
                "max_volatility": 30,
                "preferred_market_cap": "large_cap"
            },
            "SIGMA": {
                "name": "Smart Investor 📊", 
                "description": "Calculated risk strategy balancing stability with growth potential",
                "style": "balanced, data-driven decisions, targeting 25-75% annual returns with managed risk",
                "recommended_assets": ["Bitcoin", "Ethereum", "Top 20 Altcoins", "DeFi Blue Chips"],
                "max_volatility": 50,
                "preferred_market_cap": "large_to_mid_cap"
            },
            "DEGEN": {
                "name": "High Risk High Reward 🚀",
                "description": "High-growth potential strategy with tolerance for significant volatility",
                "style": "aggressive growth focused, seeking 100%+ returns, comfortable with high volatility",
                "recommended_assets": ["Growth Altcoins", "DeFi Tokens", "Layer 1s", "Emerging Projects"],
                "max_volatility": 80,
                "preferred_market_cap": "mid_to_small_cap"
            }
        }
        print("✅ SimpleCryptoAgent initialized successfully")
    
    def _make_request(self, url: str, params: dict = None, retries: int = 3) -> Dict[str, Any]:
        """Make HTTP request with retry logic and better error handling"""
        for attempt in range(retries):
            try:
                print(f"🔍 Making request to: {url}")
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    print(f"⚠️ Rate limited, waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                    return {"error": f"HTTP {response.status_code}"}
                    
            except requests.exceptions.Timeout:
                print(f"⏰ Request timeout (attempt {attempt + 1}/{retries})")
                if attempt == retries - 1:
                    return {"error": "Request timeout"}
                time.sleep(2)
                
            except requests.exceptions.ConnectionError:
                print(f"🌐 Connection error (attempt {attempt + 1}/{retries})")
                if attempt == retries - 1:
                    return {"error": "Connection error"}
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Request error: {e}")
                return {"error": f"Request failed: {str(e)}"}
        
        return {"error": "Max retries exceeded"}
    
    def get_crypto_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch comprehensive crypto data from CoinGecko with 6-month analysis"""
        try:
            print(f"📊 Fetching data for {symbol.upper()}...")
            
            # Get coin data
            url = f"{self.coingecko_base}/coins/{symbol.lower()}"
            params = {'localization': 'false', 'market_data': 'true'}
            data = self._make_request(url, params)
            
            if data.get('error'):
                # Try alternative endpoint with coin list
                print(f"⚠️ Direct lookup failed, searching coin list...")
                return self._search_coin_by_symbol(symbol)
            
            # Get 6-month historical data for enhanced analysis
            hist_url = f"{self.coingecko_base}/coins/{symbol.lower()}/market_chart"
            hist_params = {'vs_currency': 'usd', 'days': '180'}
            hist_data = self._make_request(hist_url, hist_params)
            
            if hist_data.get('error'):
                print(f"⚠️ Historical data unavailable for {symbol}")
                hist_data = {}
            
            # Calculate 6-month metrics
            prices = [price[1] for price in hist_data.get('prices', [])]
            six_month_high = max(prices) if prices else 0
            six_month_low = min(prices) if prices else 0
            current_price = data.get('market_data', {}).get('current_price', {}).get('usd', 0)
            
            # Calculate position relative to 6-month range
            if six_month_high > six_month_low:
                price_position = ((current_price - six_month_low) / (six_month_high - six_month_low)) * 100
            else:
                price_position = 50
            
            result = {
                "symbol": symbol.upper(),
                "current_price": current_price,
                "price_change_24h": data.get('market_data', {}).get('price_change_percentage_24h', 0),
                "price_change_7d": data.get('market_data', {}).get('price_change_percentage_7d', 0),
                "price_change_30d": data.get('market_data', {}).get('price_change_percentage_30d', 0),
                "market_cap": data.get('market_data', {}).get('market_cap', {}).get('usd', 0),
                "volume_24h": data.get('market_data', {}).get('total_volume', {}).get('usd', 0),
                "market_cap_rank": data.get('market_data', {}).get('market_cap_rank', 0),
                "six_month_high": six_month_high,
                "six_month_low": six_month_low,
                "price_position_6m": price_position,
                "prices": prices,
                "description": data.get('description', {}).get('en', '')[:300] + "..." if data.get('description', {}).get('en', '') else ""
            }
            
            print(f"✅ Successfully fetched data for {symbol.upper()}")
            return result
            
        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            return {"error": f"Failed to fetch {symbol}: {str(e)}"}
    
    def _search_coin_by_symbol(self, symbol: str) -> Dict[str, Any]:
        """Search for coin by symbol using coin list endpoint"""
        try:
            # Get coin list
            coins_url = f"{self.coingecko_base}/coins/list"
            coins_data = self._make_request(coins_url)
            
            if coins_data.get('error'):
                return {"error": f"Could not search for {symbol}"}
            
            # Find matching coin
            symbol_lower = symbol.lower()
            for coin in coins_data:
                if coin.get('symbol', '').lower() == symbol_lower:
                    # Try to get data using the coin ID
                    return self.get_crypto_data(coin['id'])
            
            return {"error": f"Coin {symbol} not found"}
            
        except Exception as e:
            return {"error": f"Search failed for {symbol}: {str(e)}"}
    
    def calculate_advanced_risk_metrics(self, crypto_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate comprehensive risk metrics including volatility and position analysis"""
        try:
            if not crypto_data.get('prices') or len(crypto_data['prices']) < 30:
                return {"error": "Insufficient data for risk analysis"}
            
            prices = np.array(crypto_data['prices'])
            if len(prices) < 2:
                return {"error": "Not enough price data"}
            
            returns = np.diff(np.log(prices))
            
            # Calculate various risk metrics
            volatility = np.std(returns) * np.sqrt(365) * 100  # Annualized volatility
            max_drawdown = self._calculate_max_drawdown(prices)
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            
            # Risk score (0-100, higher = riskier)
            risk_score = min(100, (volatility * 0.6) + (max_drawdown * 0.4))
            
            # Position analysis
            position_6m = crypto_data.get('price_position_6m', 50)
            
            # Price momentum
            if len(prices) >= 30:
                recent_momentum = (prices[-7:].mean() / prices[-30:].mean() - 1) * 100
            else:
                recent_momentum = 0
            
            return {
                'volatility': round(volatility, 2),
                'max_drawdown': round(max_drawdown, 2),
                'sharpe_ratio': round(sharpe_ratio, 3),
                'risk_score': round(risk_score, 1),
                'price_position_6m': round(position_6m, 1),
                'recent_momentum': round(recent_momentum, 2),
                'six_month_high': crypto_data.get('six_month_high', 0),
                'six_month_low': crypto_data.get('six_month_low', 0)
            }
            
        except Exception as e:
            print(f"❌ Risk calculation error: {e}")
            return {"error": f"Risk calculation failed: {str(e)}"}
    
    def _calculate_max_drawdown(self, prices: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        try:
            if len(prices) < 2:
                return 0
            returns = np.diff(prices) / prices[:-1]
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            return abs(np.min(drawdown)) * 100
        except:
            return 0
    
    def _calculate_sharpe_ratio(self, returns: np.ndarray) -> float:
        """Calculate Sharpe ratio (assuming 0% risk-free rate)"""
        try:
            if np.std(returns) == 0 or len(returns) == 0:
                return 0
            return np.mean(returns) / np.std(returns) * np.sqrt(365)
        except:
            return 0
    
    def assess_risk_fit(self, risk_metrics: Dict[str, Any], risk_profile: str) -> Dict[str, Any]:
        """Assess how well an asset fits the user's risk profile"""
        try:
            if risk_profile not in self.risk_profiles:
                return {"error": f"Invalid risk profile: {risk_profile}"}
            
            profile = self.risk_profiles[risk_profile]
            max_vol = profile['max_volatility']
            
            volatility = risk_metrics.get('volatility', 0)
            risk_score = risk_metrics.get('risk_score', 0)
            
            # Calculate fit score (0-100)
            if volatility <= max_vol:
                fit_score = 100 - (volatility / max_vol) * 30
            else:
                fit_score = 70 - ((volatility - max_vol) / max_vol) * 50
            
            fit_score = max(0, min(100, fit_score))
            
            recommendation = "STRONG BUY" if fit_score > 80 else "BUY" if fit_score > 60 else "HOLD" if fit_score > 40 else "CAUTION"
            
            return {
                'fit_score': round(fit_score, 1),
                'recommendation': recommendation,
                'risk_assessment': self._get_risk_assessment(risk_score, risk_profile)
            }
            
        except Exception as e:
            print(f"❌ Risk fit assessment error: {e}")
            return {"error": f"Risk assessment failed: {str(e)}"}
    
    def _get_risk_assessment(self, risk_score: float, risk_profile: str) -> str:
        """Get risk assessment text"""
        if risk_profile not in self.risk_profiles:
            return f"❌ Invalid risk profile: {risk_profile}"
        
        profile_limits = {"DIAMOND": 30, "SIGMA": 50, "DEGEN": 80}
        limit = profile_limits[risk_profile]
        
        if risk_score <= limit * 0.7:
            return "✅ Well within your risk tolerance"
        elif risk_score <= limit:
            return "⚠️ Moderate risk for your profile"
        else:
            return "🚨 Higher risk than recommended for your profile"
    
    def detect_multiple_cryptos(self, message: str) -> List[str]:
        """Detect multiple cryptocurrency symbols in a message"""
        crypto_symbols = {
            'btc': 'bitcoin', 'bitcoin': 'bitcoin',
            'eth': 'ethereum', 'ethereum': 'ethereum',
            'sol': 'solana', 'solana': 'solana',
            'ada': 'cardano', 'cardano': 'cardano',
            'matic': 'polygon', 'polygon': 'polygon',
            'link': 'chainlink', 'chainlink': 'chainlink',
            'avax': 'avalanche-2', 'avalanche': 'avalanche-2',
            'dot': 'polkadot', 'polkadot': 'polkadot',
            'uni': 'uniswap', 'uniswap': 'uniswap',
            'aave': 'aave', 'comp': 'compound-governance-token',
            'bnb': 'binancecoin', 'binance': 'binancecoin',
            'xrp': 'ripple', 'ripple': 'ripple',
            'doge': 'dogecoin', 'dogecoin': 'dogecoin',
            'ltc': 'litecoin', 'litecoin': 'litecoin',
            'atom': 'cosmos', 'cosmos': 'cosmos',
            'near': 'near', 'icp': 'internet-computer',
            'fil': 'filecoin', 'filecoin': 'filecoin',
            'mana': 'decentraland', 'decentraland': 'decentraland',
            'sand': 'the-sandbox', 'sandbox': 'the-sandbox',
            'axs': 'axie-infinity', 'grt': 'the-graph',
            'ftm': 'fantom', 'fantom': 'fantom',
            'algo': 'algorand', 'algorand': 'algorand',
            'kaia': 'kaia'  # Adding kaia since user asked about it
        }
        
        message_lower = message.lower()
        detected_symbols = []
        
        for key, value in crypto_symbols.items():
            if key in message_lower and value not in detected_symbols:
                detected_symbols.append(value)
        
        return detected_symbols
    
    def compare_cryptos(self, symbols: List[str], risk_profile: str = "SIGMA") -> str:
        """Compare multiple cryptocurrencies for investment analysis"""
        try:
            if risk_profile not in self.risk_profiles:
                return f"❌ **Invalid Risk Profile**: '{risk_profile}'. Valid options are: {', '.join(self.risk_profiles.keys())}"
            
            profile = self.risk_profiles[risk_profile]
            comparison_data = []
            
            print(f"🔍 Comparing {len(symbols)} cryptocurrencies...")
            
            # Get data for all symbols
            for symbol in symbols:
                crypto_data = self.get_crypto_data(symbol)
                if not crypto_data.get('error'):
                    risk_metrics = self.calculate_advanced_risk_metrics(crypto_data)
                    if not risk_metrics.get('error'):
                        risk_fit = self.assess_risk_fit(risk_metrics, risk_profile)
                        
                        comparison_data.append({
                            'symbol': symbol.upper(),
                            'price': crypto_data['current_price'],
                            'change_24h': crypto_data['price_change_24h'],
                            'change_7d': crypto_data['price_change_7d'],
                            'change_30d': crypto_data['price_change_30d'],
                            'market_cap': crypto_data['market_cap'],
                            'volume_24h': crypto_data['volume_24h'],
                            'rank': crypto_data['market_cap_rank'],
                            'volatility': risk_metrics['volatility'],
                            'risk_score': risk_metrics['risk_score'],
                            'fit_score': risk_fit['fit_score'],
                            'recommendation': risk_fit['recommendation'],
                            'price_position_6m': risk_metrics['price_position_6m'],
                            'six_month_high': risk_metrics['six_month_high'],
                            'six_month_low': risk_metrics['six_month_low'],
                            'recent_momentum': risk_metrics['recent_momentum']
                        })
                        print(f"✅ Analyzed {symbol.upper()}")
                else:
                    print(f"⚠️ Skipped {symbol}: {crypto_data['error']}")
            
            if not comparison_data:
                return "❌ **Error**: Could not fetch data for any of the requested cryptocurrencies."
            
            # Sort by fit score for ranking
            comparison_data.sort(key=lambda x: x['fit_score'], reverse=True)
            
            # Get market context
            fear_greed = self.get_fear_greed_index()
            
            # Create comparison prompt
            comparison_prompt = f"""
            You are a professional cryptocurrency analyst providing a comparative investment analysis.
            
            **COMPARISON REQUEST**: {', '.join([d['symbol'] for d in comparison_data])}
            **INVESTOR PROFILE**: {profile['name']} - {profile['description']}
            **RISK TOLERANCE**: {profile['style']}
            
            **COMPARATIVE DATA**:
            {json.dumps(comparison_data, indent=2)}
            
            **MARKET CONTEXT**:
            - Fear & Greed Index: {fear_greed.get('value', 'N/A')} ({fear_greed.get('classification', 'N/A')})
            
            **RESPONSE FORMAT** (use markdown formatting):
            
            ## 📊 **COMPARATIVE ANALYSIS SUMMARY**
            [Brief overview comparing all assets]
            
            ## 🏆 **RANKING FOR {profile['name'].upper()}**
            ### 1. [Best Fit Asset]
            - **Fit Score**: X% | **Risk Score**: X/100 | **Recommendation**: BUY/HOLD/SELL
            - **Key Strengths**: [Why this ranks #1 for this risk profile]
            - **Entry Strategy**: $X.XX (X% of portfolio)
            
            ### 2. [Second Best Asset]
            - **Fit Score**: X% | **Risk Score**: X/100 | **Recommendation**: BUY/HOLD/SELL
            - **Key Strengths**: [Why this ranks #2]
            - **Entry Strategy**: $X.XX (X% of portfolio)
            
            ### 3. [Third Asset if applicable]
            [Same format]
            
            ## ⚖️ **SIDE-BY-SIDE COMPARISON**
            | Metric | {comparison_data[0]['symbol'] if comparison_data else 'N/A'} | {comparison_data[1]['symbol'] if len(comparison_data) > 1 else 'N/A'} | {comparison_data[2]['symbol'] if len(comparison_data) > 2 else 'N/A'} |
            |--------|------------|------------|------------|
            | Current Price | [prices] | [prices] | [prices] |
            | 24h Change | [changes] | [changes] | [changes] |
            | Risk Score | [scores] | [scores] | [scores] |
            | Volatility | [vol] | [vol] | [vol] |
            | Profile Fit | [fit] | [fit] | [fit] |
            
            ## 💡 **PORTFOLIO ALLOCATION RECOMMENDATION**
            [Specific allocation percentages for a {profile['name']} portfolio]
            
            ## ⚠️ **RISK CONSIDERATIONS**
            [Compare risks across all assets for this risk profile]
            
            ## 📈 **MARKET TIMING**
            [Compare current market positions and entry timing for each asset]
            
            **INSTRUCTIONS**:
            - Use professional, institutional-grade language
            - Avoid slang or casual expressions
            - Focus on quantitative analysis and specific metrics
            - Provide clear reasoning for rankings based on risk profile
            - Include specific price targets and portfolio allocations
            """
            
            response = self.model.generate_content(comparison_prompt)
            return response.text
            
        except Exception as e:
            print(f"❌ Comparison error: {e}")
            return f"❌ **Comparison Failed**: {str(e)}"
    
    def analyze_crypto(self, symbol: str, risk_profile: str = "SIGMA") -> str:
        """Enhanced crypto analysis with risk-adjusted recommendations"""
        try:
            print(f"🔍 Starting analysis for {symbol.upper()}...")
            
            # Validate risk profile
            if risk_profile not in self.risk_profiles:
                return f"❌ **Invalid Risk Profile**: '{risk_profile}'. Valid options are: {', '.join(self.risk_profiles.keys())}"
            
            # Get crypto data
            crypto_data = self.get_crypto_data(symbol)
            if "error" in crypto_data:
                return f"❌ **Error**: {crypto_data['error']}"
            
            # Calculate risk metrics
            risk_metrics = self.calculate_advanced_risk_metrics(crypto_data)
            if "error" in risk_metrics:
                return f"❌ **Risk Analysis Error**: {risk_metrics['error']}"
            
            # Assess fit with risk profile
            risk_fit = self.assess_risk_fit(risk_metrics, risk_profile)
            
            # Get market context
            fear_greed = self.get_fear_greed_index()
            profile = self.risk_profiles[risk_profile]
            
            # Create enhanced analysis prompt
            analysis_prompt = f"""
            You are a professional cryptocurrency analyst providing institutional-grade investment analysis.
            
            **ANALYSIS REQUEST**: {symbol.upper()} for {profile['name']} investor
            **INVESTMENT STRATEGY**: {profile['description']}
            
            **CURRENT MARKET DATA**:
            - Price: ${crypto_data['current_price']:,.4f}
            - 24h Change: {crypto_data['price_change_24h']:.2f}%
            - 7d Change: {crypto_data['price_change_7d']:.2f}%
            - 30d Change: {crypto_data['price_change_30d']:.2f}%
            - Market Cap Rank: #{crypto_data['market_cap_rank']}
            - 24h Volume: ${crypto_data['volume_24h']:,.0f}
            
            **6-MONTH ANALYSIS**:
            - 6M High: ${risk_metrics['six_month_high']:,.4f}
            - 6M Low: ${risk_metrics['six_month_low']:,.4f}
            - Current Position: {risk_metrics['price_position_6m']:.1f}% of 6M range
            - Recent Momentum: {risk_metrics['recent_momentum']:.2f}%
            
            **RISK METRICS**:
            - Volatility: {risk_metrics['volatility']:.1f}% (annualized)
            - Max Drawdown: {risk_metrics['max_drawdown']:.1f}%
            - Risk Score: {risk_metrics['risk_score']:.1f}/100
            - Profile Fit: {risk_fit['fit_score']:.1f}%
            - Assessment: {risk_fit['risk_assessment']}
            
            **MARKET SENTIMENT**:
            - Fear & Greed: {fear_greed.get('value', 'N/A')} ({fear_greed.get('classification', 'N/A')})
            
            **RESPONSE FORMAT** (use markdown formatting):
            
            ## 🎯 **INVESTMENT SIGNAL**: {risk_fit['recommendation']} (Confidence: {risk_fit['fit_score']:.0f}%)
            
            ## 📊 **TECHNICAL ANALYSIS**
            [Analyze price position, momentum, key levels based on 6-month data using professional analysis]
            
            ## 🎰 **RISK ASSESSMENT** 
            [Detailed risk analysis for this specific risk profile with specific volatility numbers]
            
            ## 💰 **STRATEGIC RECOMMENDATION**
            [Specific entry prices, position sizing recommendations, target levels based on risk profile]
            
            ## ⚠️ **KEY LEVELS TO WATCH**
            [Support/resistance levels and potential catalysts]
            
            ## 💡 **PORTFOLIO ALLOCATION**
            [Recommended portfolio percentage for this risk profile]
            
            **IMPORTANT**: 
            - Use professional, clear language suitable for institutional investors
            - Avoid slang or casual expressions
            - Adjust ALL recommendations specifically for {profile['name']} risk tolerance
            - Use the actual volatility and risk metrics provided
            - Reference the 6-month price position in your analysis
            - Provide specific price targets and stop-loss levels
            - Use professional financial terminology with markdown formatting
            """
            
            response = self.model.generate_content(analysis_prompt)
            print(f"✅ Analysis completed for {symbol.upper()}")
            return response.text
            
        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return f"❌ **Analysis Failed**: {str(e)}"
    
    def chat(self, message: str, risk_profile: str = "SIGMA") -> str:
        """Enhanced chat with financial focus and multi-crypto comparison"""
        try:
            print(f"💬 Processing chat message...")
            
            # Validate risk profile
            if risk_profile not in self.risk_profiles:
                return f"❌ **Invalid Risk Profile**: '{risk_profile}'. Valid options are: {', '.join(self.risk_profiles.keys())}"
            
            # Always relate responses back to finance/crypto
            profile = self.risk_profiles[risk_profile]
            
            # Check for multiple crypto mentions
            detected_symbols = self.detect_multiple_cryptos(message)
            
            # If multiple cryptos detected, do comparison
            if len(detected_symbols) > 1:
                return self.compare_cryptos(detected_symbols, risk_profile)
            
            # If single crypto mentioned, do detailed analysis
            elif len(detected_symbols) == 1:
                return self.analyze_crypto(detected_symbols[0], risk_profile)
            
            # Special commands
            if 'scan' in message.lower():
                return self.scan_opportunities(risk_profile)
            
            # Get market context for financial relevance
            fear_greed = self.get_fear_greed_index()
            market_overview = self.get_market_overview()
            
            # Enhanced chat prompt with professional language
            chat_prompt = f"""
            You are a professional cryptocurrency and financial markets AI assistant providing institutional-grade analysis.
            
            **INVESTOR PROFILE**: {profile['name']}
            **INVESTMENT STRATEGY**: {profile['description']}
            **APPROACH**: {profile['style']}
            
            **CURRENT MARKET CONTEXT**:
            - Fear & Greed Index: {fear_greed.get('value', 'N/A')} ({fear_greed.get('classification', 'N/A')})
            - Market Interpretation: {fear_greed.get('interpretation', 'Market analysis unavailable')}
            - Total Crypto Market Cap: ${market_overview.get('total_market_cap', {}).get('usd', 0):,.0f}
            
            **USER MESSAGE**: "{message}"
            
            **RESPONSE GUIDELINES**:
            1. ALWAYS relate your response back to finance, investments, or cryptocurrency markets
            2. Even for non-financial questions, provide a brief answer then pivot to relevant financial insights
            3. Use professional, institutional-grade language - avoid slang or casual expressions
            4. Use markdown formatting with proper headers, bold text, and clear structure
            5. Provide actionable financial advice based on their risk profile
            6. Include current market context when relevant
            7. Be professional and analytical, suitable for institutional investors
            
            **EXAMPLES OF PROFESSIONAL TONE**:
            - Instead of "crypto is mooning" → "experiencing significant upward momentum"
            - Instead of "HODL" → "maintain long-term positions"
            - Instead of "to the moon" → "substantial growth potential"
            - Instead of "diamond hands" → "long-term conviction"
            
            **RESPONSE FORMAT**: Use markdown with ## headers, **bold** text, and clear analytical structure.
            """
            
            response = self.model.generate_content(chat_prompt)
            print(f"✅ Chat response generated")
            return response.text
            
        except Exception as e:
            print(f"❌ Chat error: {e}")
            return f"❌ **Analysis Error**: {str(e)}"
    
    def scan_opportunities(self, risk_profile: str = "SIGMA") -> str:
        """Enhanced opportunity scanning with risk-adjusted recommendations"""
        try:
            print(f"🔍 Starting opportunity scan for {risk_profile}...")
            
            # Validate risk profile
            if risk_profile not in self.risk_profiles:
                return f"❌ **Invalid Risk Profile**: '{risk_profile}'. Valid options are: {', '.join(self.risk_profiles.keys())}"
            
            profile = self.risk_profiles[risk_profile]
            
            # Define coin lists based on risk profile
            if risk_profile == "DIAMOND":
                coins = ['bitcoin', 'ethereum', 'cardano', 'polygon', 'chainlink']
            elif risk_profile == "SIGMA":
                coins = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polygon', 'chainlink', 'avalanche-2', 'uniswap']
            else:  # DEGEN
                coins = ['solana', 'avalanche-2', 'chainlink', 'uniswap', 'aave', 'compound-governance-token', 'the-graph', 'polygon']
            
            opportunities = []
            print(f"🔍 Scanning {len(coins)} tokens for {profile['name']} opportunities...")
            
            for coin in coins:
                try:
                    data = self.get_crypto_data(coin)
                    if not data.get('error'):
                        risk_metrics = self.calculate_advanced_risk_metrics(data)
                        if not risk_metrics.get('error'):
                            risk_fit = self.assess_risk_fit(risk_metrics, risk_profile)
                            
                            opportunities.append({
                                'symbol': coin.upper(),
                                'price': data['current_price'],
                                'change_24h': data['price_change_24h'],
                                'change_7d': data['price_change_7d'],
                                'volatility': risk_metrics['volatility'],
                                'risk_score': risk_metrics['risk_score'],
                                'fit_score': risk_fit['fit_score'],
                                'recommendation': risk_fit['recommendation'],
                                'price_position_6m': risk_metrics['price_position_6m'],
                                'volume': data['volume_24h'],
                                'rank': data['market_cap_rank']
                            })
                            print(f"✅ Analyzed {coin.upper()}")
                except Exception as e:
                    print(f"⚠️ Skipped {coin}: {e}")
                    continue
            
            if not opportunities:
                return f"❌ **Scan Failed**: Could not analyze any opportunities for {risk_profile}"
            
            # Sort by fit score
            opportunities.sort(key=lambda x: x['fit_score'], reverse=True)
            
            # Create scan prompt
            scan_prompt = f"""
            You are a professional cryptocurrency analyst conducting a market opportunity analysis for {profile['name']} investors.
            
            **INVESTMENT PROFILE**: {profile['description']}
            **TARGET RETURNS**: {profile['style']}
            **MAX VOLATILITY TOLERANCE**: {profile['max_volatility']}%
            
            **ANALYZED OPPORTUNITIES**:
            {json.dumps(opportunities[:8], indent=2)}
            
            **ANALYSIS REPORT FORMAT** (use markdown):
            
            ## 🏆 **TOP INVESTMENT OPPORTUNITIES FOR {profile['name'].upper()}**
            
            ### 1. [Best Fit Token]
            - **Risk-Adjusted Score**: X% | **Volatility**: X% | **Recommendation**: BUY/HOLD/SELL
            - **Technical Analysis**: [Professional analysis based on price position and momentum]
            - **Entry Strategy**: $X.XX (Position size: X% of portfolio)
            - **Target Price**: $X.XX | **Stop Loss**: $X.XX
            - **Investment Thesis**: [Why this fits the risk profile]
            
            ### 2. [Second Best Token]
            [Same professional format]
            
            ### 3. [Third Best Token]
            [Same professional format]
            
            ## ⚠️ **RISK MANAGEMENT FRAMEWORK**
            [Professional risk management advice for this profile]
            
            ## 📊 **MARKET TIMING ANALYSIS**
            [Current market conditions and optimal entry timing]
            
            ## 💼 **PORTFOLIO CONSTRUCTION**
            [Recommended portfolio allocation and diversification strategy]
            
            **REQUIREMENTS**:
            - Use professional, institutional-grade language
            - Avoid slang or casual expressions
            - Focus on quantitative analysis and risk metrics
            - Provide specific entry prices and position sizing recommendations
            - Include stop-loss levels appropriate for the risk profile
            - Use actual fit scores and risk metrics provided in the analysis
            """
            
            response = self.model.generate_content(scan_prompt)
            print(f"✅ Scan completed for {risk_profile}")
            return response.text
            
        except Exception as e:
            print(f"❌ Scan error: {e}")
            return f"❌ **Scan Failed**: {str(e)}"
    
    def get_fear_greed_index(self) -> Dict[str, Any]:
        """Get crypto fear & greed index"""
        try:
            url = "https://api.alternative.me/fng/"
            data = self._make_request(url)
            
            if data.get('error'):
                return {"error": "Could not fetch fear & greed index"}
            
            index_value = int(data['data'][0]['value'])
            classification = data['data'][0]['value_classification']
            
            return {
                "value": index_value,
                "classification": classification,
                "interpretation": self._interpret_fear_greed(index_value)
            }
        except Exception as e:
            print(f"❌ Fear & Greed fetch error: {e}")
            return {"error": "Could not fetch fear & greed index"}
    
    def get_market_overview(self) -> Dict[str, Any]:
        """Get overall market data"""
        try:
            url = f"{self.coingecko_base}/global"
            data = self._make_request(url)
            
            if data.get('error'):
                return {"error": "Could not fetch market overview"}
            
            return {
                "total_market_cap": data.get('data', {}).get('total_market_cap', {}),
                "total_volume": data.get('data', {}).get('total_volume', {}),
                "market_cap_percentage": data.get('data', {}).get('market_cap_percentage', {}),
                "active_cryptocurrencies": data.get('data', {}).get('active_cryptocurrencies', 0)
            }
        except Exception as e:
            print(f"❌ Market overview error: {e}")
            return {"error": "Could not fetch market overview"}
    
    def _interpret_fear_greed(self, value: int) -> str:
        """Enhanced fear & greed interpretation"""
        if value <= 25:
            return "Extreme Fear - Historically excellent buying opportunity for long-term investors"
        elif value <= 45:
            return "Fear - Good accumulation zone, consider dollar-cost averaging"
        elif value <= 55:
            return "Neutral - Balanced market conditions, focus on technical analysis"
        elif value <= 75:
            return "Greed - Consider profit-taking and reducing position sizes"
        else:
            return "Extreme Greed - High correction risk, defensive positioning recommended"

    def get_dex_snapshot(self, dex: str, seconds_ago: int = 0, first: int = 300) -> Dict[str, Any]:
        """Get DEX data from graph API"""
        try:
            url = f"{self.graph_base}/{dex}?secondsAgo={seconds_ago}&first={first}"
            data = self._make_request(url)
            return data
        except Exception as e:
            return {"error": f"DEX data fetch failed for {dex}: {e}"}
            return "Greed - Consider profit-taking and reducing position sizes"
        else:
            return "Extreme Greed - High correction risk, defensive positioning recommended"

    def get_dex_snapshot(self, dex: str, seconds_ago: int = 0, first: int = 300) -> Dict[str, Any]:
        """Get DEX data from graph API"""
        try:
            url = f"{self.graph_base}/{dex}?secondsAgo={seconds_ago}&first={first}"
            data = self._make_request(url)
            return data
        except Exception as e:
            return {"error": f"DEX data fetch failed for {dex}: {e}"}
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import your enhanced crypto agent
try:
    from simple_crypto_agent import SimpleCryptoAgent
    print("✅ SimpleCryptoAgent imported successfully")
except ImportError as e:
    print(f"❌ Failed to import SimpleCryptoAgent: {e}")
    exit(1)

# FastAPI app
app = FastAPI(
    title="Financial AI Assistant", 
    description="Professional Cryptocurrency Analysis & Investment Strategies",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the AI agent
def initialize_agent():
    """Initialize the crypto agent with proper error handling"""
    try:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            print("❌ GEMINI_API_KEY not found in environment variables")
            print("Please check your .env file contains: GEMINI_API_KEY=your_api_key_here")
            exit(1)
        
        agent = SimpleCryptoAgent(GEMINI_API_KEY)
        print("✅ SimpleCryptoAgent initialized successfully")
        return agent
    except Exception as e:
        print(f"❌ Failed to initialize SimpleCryptoAgent: {e}")
        exit(1)

# Initialize agent at startup
agent = initialize_agent()

class ChatMessage(BaseModel):
    message: str
    risk_profile: str = "SIGMA"

class AnalysisRequest(BaseModel):
    symbol: str
    risk_profile: str = "SIGMA"

class ComparisonRequest(BaseModel):
    symbols: List[str]
    risk_profile: str = "SIGMA"

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the main dashboard"""
    try:
        with open("index.html", "r", encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Financial AI Assistant</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
                    color: white; 
                    padding: 40px; 
                    text-align: center; 
                    min-height: 100vh;
                    margin: 0;
                }
                .container { max-width: 800px; margin: 0 auto; }
                h1 { 
                    color: #10b981; 
                    margin-bottom: 20px; 
                    font-size: 3rem;
                    font-weight: 700;
                }
                .status { 
                    background: rgba(30, 41, 59, 0.8); 
                    padding: 30px; 
                    border-radius: 16px; 
                    border: 1px solid #334155; 
                    backdrop-filter: blur(10px);
                    margin: 20px 0;
                }
                .feature {
                    background: rgba(15, 23, 42, 0.6);
                    padding: 20px;
                    border-radius: 12px;
                    margin: 15px 0;
                    border-left: 4px solid #10b981;
                }
                .api-endpoint {
                    background: rgba(16, 185, 129, 0.1);
                    padding: 10px 15px;
                    border-radius: 8px;
                    font-family: 'Courier New', monospace;
                    color: #10b981;
                    margin: 5px 0;
                }
                .risk-profiles {
                    display: flex;
                    gap: 20px;
                    margin: 20px 0;
                    flex-wrap: wrap;
                    justify-content: center;
                }
                .risk-profile {
                    background: rgba(30, 41, 59, 0.8);
                    padding: 15px;
                    border-radius: 12px;
                    border: 1px solid #334155;
                    flex: 1;
                    min-width: 200px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Financial AI Assistant</h1>
                
                <div class="status">
                    <h2>✅ Server Running Successfully!</h2>
                    <p>Professional cryptocurrency analysis powered by advanced AI</p>
                </div>

                <div class="feature">
                    <h3>🎯 Risk-Adjusted Investment Strategies</h3>
                    <div class="risk-profiles">
                        <div class="risk-profile">
                            <h4>🛡️ Play it Safe</h4>
                            <p>Conservative, low-risk investments</p>
                        </div>
                        <div class="risk-profile">
                            <h4>📊 Smart Investor</h4>
                            <p>Balanced, calculated risks</p>
                        </div>
                        <div class="risk-profile">
                            <h4>🚀 High Risk High Reward</h4>
                            <p>Aggressive growth strategies</p>
                        </div>
                    </div>
                </div>

                <div class="feature">
                    <h3>📊 Advanced Analysis Features</h3>
                    <ul style="text-align: left; max-width: 600px; margin: 0 auto;">
                        <li>6-month price range analysis</li>
                        <li>Volatility and risk scoring</li>
                        <li>Portfolio fit assessment</li>
                        <li>Technical indicator analysis</li>
                        <li>Market sentiment integration</li>
                        <li>Professional markdown formatting</li>
                    </ul>
                </div>

                <div class="feature">
                    <h3>🔌 API Endpoints</h3>
                    <div class="api-endpoint">POST /api/ai/chat</div>
                    <div class="api-endpoint">GET /api/analyze/{symbol}</div>
                    <div class="api-endpoint">POST /api/compare</div>
                    <div class="api-endpoint">GET /api/scan</div>
                    <div class="api-endpoint">GET /api/market-overview</div>
                    <div class="api-endpoint">GET /health</div>
                </div>

                <div class="status">
                    <p><strong>Next Steps:</strong></p>
                    <p>Connect your React frontend to the API endpoints</p>
                    <p>Or test the API directly using the endpoints above</p>
                </div>
            </div>
        </body>
        </html>
        """)

@app.post("/api/ai/chat")
async def chat_with_agent(chat_request: ChatMessage):
    """Enhanced chat endpoint with risk-adjusted responses"""
    try:
        # Validate risk profile
        valid_profiles = ["DIAMOND", "SIGMA", "DEGEN"]
        if chat_request.risk_profile not in valid_profiles:
            chat_request.risk_profile = "SIGMA"
        
        print(f"💬 Processing chat: '{chat_request.message[:50]}...' with profile: {chat_request.risk_profile}")
        
        response = agent.chat(chat_request.message, chat_request.risk_profile)
        
        return JSONResponse(content={
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "risk_profile": chat_request.risk_profile,
            "profile_name": agent.risk_profiles[chat_request.risk_profile]["name"]
        })
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

@app.post("/api/analyze")
async def analyze_crypto_endpoint(request: AnalysisRequest):
    """Enhanced analysis endpoint with risk assessment"""
    try:
        # Validate risk profile
        valid_profiles = ["DIAMOND", "SIGMA", "DEGEN"]
        if request.risk_profile not in valid_profiles:
            request.risk_profile = "SIGMA"
        
        print(f"📊 Analyzing {request.symbol} with profile: {request.risk_profile}")
        
        analysis = agent.analyze_crypto(request.symbol, request.risk_profile)
        
        # Get additional data for response
        crypto_data = agent.get_crypto_data(request.symbol)
        risk_metrics = {}
        if not crypto_data.get('error'):
            risk_metrics = agent.calculate_advanced_risk_metrics(crypto_data)
        
        return JSONResponse(content={
            "analysis": analysis,
            "symbol": request.symbol.upper(),
            "risk_profile": request.risk_profile,
            "profile_name": agent.risk_profiles[request.risk_profile]["name"],
            "risk_metrics": risk_metrics,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.get("/api/analyze/{symbol}")
async def analyze_crypto_get(symbol: str, risk_profile: str = "SIGMA"):
    """GET endpoint for crypto analysis"""
    request = AnalysisRequest(symbol=symbol, risk_profile=risk_profile)
    return await analyze_crypto_endpoint(request)

@app.post("/api/compare")
async def compare_cryptos_endpoint(request: ComparisonRequest):
    """Compare multiple cryptocurrencies"""
    try:
        # Validate risk profile
        valid_profiles = ["DIAMOND", "SIGMA", "DEGEN"]
        if request.risk_profile not in valid_profiles:
            request.risk_profile = "SIGMA"
        
        if len(request.symbols) < 2:
            raise HTTPException(status_code=400, detail="At least 2 symbols required for comparison")
        
        print(f"⚖️ Comparing {len(request.symbols)} cryptos with profile: {request.risk_profile}")
        
        comparison = agent.compare_cryptos(request.symbols, request.risk_profile)
        
        return JSONResponse(content={
            "comparison": comparison,
            "symbols": [s.upper() for s in request.symbols],
            "risk_profile": request.risk_profile,
            "profile_name": agent.risk_profiles[request.risk_profile]["name"],
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Comparison error: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")

@app.get("/api/scan")
async def scan_opportunities_endpoint(risk_profile: str = "SIGMA"):
    """Enhanced opportunity scanning"""
    try:
        # Validate risk profile
        valid_profiles = ["DIAMOND", "SIGMA", "DEGEN"]
        if risk_profile not in valid_profiles:
            risk_profile = "SIGMA"
        
        print(f"🔍 Scanning opportunities with profile: {risk_profile}")
        
        opportunities = agent.scan_opportunities(risk_profile)
        
        return JSONResponse(content={
            "opportunities": opportunities,
            "risk_profile": risk_profile,
            "profile_name": agent.risk_profiles[risk_profile]["name"],
            "scan_timestamp": datetime.now().isoformat(),
            "profile_description": agent.risk_profiles[risk_profile]["description"]
        })
        
    except Exception as e:
        print(f"❌ Scan error: {e}")
        raise HTTPException(status_code=500, detail=f"Scan error: {str(e)}")

@app.get("/api/market-overview")
async def get_market_overview_endpoint():
    """Enhanced market overview with sentiment analysis"""
    try:
        print("📈 Fetching market overview...")
        
        overview = agent.get_market_overview()
        fear_greed = agent.get_fear_greed_index()
        
        # Calculate market health score
        fg_value = fear_greed.get('value', 50)
        market_health = "Healthy" if 30 <= fg_value <= 70 else "Volatile"
        
        return JSONResponse(content={
            "market_overview": overview,
            "fear_greed": fear_greed,
            "market_health": market_health,
            "trading_recommendation": agent._interpret_fear_greed(fg_value),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Market overview error: {e}")
        raise HTTPException(status_code=500, detail=f"Market overview error: {str(e)}")

@app.get("/api/data/{symbol}")
async def get_crypto_data_endpoint(symbol: str):
    """Get enhanced crypto data with risk metrics"""
    try:
        print(f"📊 Fetching data for {symbol}")
        
        data = agent.get_crypto_data(symbol)
        if data.get('error'):
            return JSONResponse(content=data, status_code=404)
        
        risk_metrics = agent.calculate_advanced_risk_metrics(data)
        
        return JSONResponse(content={
            "basic_data": data,
            "risk_metrics": risk_metrics,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"❌ Data error: {e}")
        raise HTTPException(status_code=500, detail=f"Data error: {str(e)}")

@app.get("/api/risk-profiles")
async def get_risk_profiles():
    """Get available risk profiles"""
    return JSONResponse(content={
        "profiles": agent.risk_profiles,
        "default": "SIGMA"
    })

@app.get("/health")
async def health_check():
    """Enhanced health check"""
    try:
        # Test AI connectivity
        print("🏥 Running health check...")
        test_response = agent.model.generate_content("Test connection")
        ai_status = "Connected" if test_response else "Error"
        print(f"🤖 AI Status: {ai_status}")
    except Exception as e:
        print(f"❌ AI health check failed: {e}")
        ai_status = "Error"
    
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "agent": "SimpleCryptoAgent v2.0",
        "ai_model": "Gemini 2.0 Flash",
        "ai_status": ai_status,
        "risk_profiles": list(agent.risk_profiles.keys()),
        "environment_variables": {
            "GEMINI_API_KEY": "✅ Set" if os.getenv("GEMINI_API_KEY") else "❌ Missing",
            "COINGECKO_API_KEY": "✅ Set" if os.getenv("COINGECKO_API_KEY") else "⚠️ Optional",
            "GRAPH_API_BASE": os.getenv("GRAPH_API_BASE", "Default")
        },
        "features": [
            "Risk-adjusted analysis",
            "6-month price analysis", 
            "Advanced risk metrics",
            "Portfolio fit scoring",
            "Professional formatting"
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Financial AI Assistant Server...")
    print("=" * 60)
    print("📊 Dashboard: http://localhost:8000")
    print("🤖 AI Model: Gemini 2.0 Flash")
    print("🎯 Risk Profiles:")
    print("   - 🛡️  DIAMOND: Play it Safe (Low Risk)")
    print("   - 📊 SIGMA: Smart Investor (Calculated Risk)")  
    print("   - 🚀 DEGEN: High Risk High Reward")
    print("\n💬 API Endpoints:")
    print("   - POST /api/ai/chat")
    print("   - GET/POST /api/analyze/{symbol}")
    print("   - POST /api/compare (multi-crypto comparison)")
    print("   - GET /api/scan?risk_profile=SIGMA")
    print("   - GET /api/market-overview")
    print("   - GET /api/risk-profiles")
    print("   - GET /health")
    print("\n✨ Enhanced Features:")
    print("   - Multi-cryptocurrency comparison analysis")
    print("   - 6-month price range analysis")
    print("   - Advanced risk scoring (0-100)")
    print("   - Portfolio fit assessment")
    print("   - Professional institutional-grade language")
    print("   - Risk-adjusted recommendations")
    print("=" * 60)
    
    # Check environment variables at startup
    print("\n🔧 Environment Check:")
    print(f"   - GEMINI_API_KEY: {'✅ Set' if os.getenv('GEMINI_API_KEY') else '❌ Missing'}")
    print(f"   - COINGECKO_API_KEY: {'✅ Set' if os.getenv('COINGECKO_API_KEY') else '⚠️ Optional'}")
    print(f"   - GRAPH_API_BASE: {os.getenv('GRAPH_API_BASE', 'Default')}")
    
    print("\n🚀 Ready to provide professional financial analysis!\n")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
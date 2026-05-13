"""
Forex AI Analysis API - Deploy on Render.com
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================================
# Initialize FastAPI
# ============================================
app = FastAPI(
    title="Forex AI Analysis API",
    description="Real-time Forex market analysis and trading signals",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# Data Models
# ============================================
class AnalysisResponse(BaseModel):
    success: bool
    timestamp: str
    symbol: str
    current_price: float
    indicators: Dict[str, Any]
    signal: Dict[str, Any]
    risk_management: Dict[str, Any]

class SignalResponse(BaseModel):
    success: bool
    timestamp: str
    symbol: str
    signal: str
    confidence: float
    price: float

# ============================================
# Technical Indicators
# ============================================

def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = data.ewm(span=fast, adjust=False).mean()
    ema_slow = data.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2):
    sma = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower

def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr

def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    return k, d

def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = abs(minus_dm)
    
    tr = calculate_atr(high, low, close, period)
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr)
    dx = 100 * abs((plus_di - minus_di) / (plus_di + minus_di))
    adx = dx.rolling(window=period).mean()
    return adx

def generate_signal(rsi: float, macd_hist: float, price: float, 
                    bb_upper: float, bb_lower: float, stoch_k: float = None,
                    adx: float = None) -> Dict[str, Any]:
    
    buy_signals = []
    sell_signals = []
    signal_strength = 0
    
    # RSI Signal
    if rsi < 30:
        buy_signals.append(f"RSI Oversold ({rsi:.1f})")
        signal_strength += 2
    elif rsi < 40:
        buy_signals.append(f"RSI Near Oversold ({rsi:.1f})")
        signal_strength += 1
    elif rsi > 70:
        sell_signals.append(f"RSI Overbought ({rsi:.1f})")
        signal_strength -= 2
    elif rsi > 60:
        sell_signals.append(f"RSI Near Overbought ({rsi:.1f})")
        signal_strength -= 1
    
    # MACD Signal
    if macd_hist > 0:
        buy_signals.append(f"MACD Bullish ({macd_hist:.5f})")
        signal_strength += 1
    elif macd_hist < 0:
        sell_signals.append(f"MACD Bearish ({macd_hist:.5f})")
        signal_strength -= 1
    
    # Bollinger Bands Signal
    if price <= bb_lower:
        buy_signals.append("Price at Lower Band")
        signal_strength += 2
    elif price >= bb_upper:
        sell_signals.append("Price at Upper Band")
        signal_strength -= 2
    
    # Stochastic Signal
    if stoch_k is not None and not pd.isna(stoch_k):
        if stoch_k < 20:
            buy_signals.append(f"Stochastic Oversold ({stoch_k:.1f})")
            signal_strength += 1
        elif stoch_k > 80:
            sell_signals.append(f"Stochastic Overbought ({stoch_k:.1f})")
            signal_strength -= 1
    
    # ADX Signal
    if adx is not None and not pd.isna(adx):
        if adx > 25:
            if signal_strength > 0:
                buy_signals.append(f"Strong Trend (ADX: {adx:.1f})")
            elif signal_strength < 0:
                sell_signals.append(f"Strong Trend (ADX: {adx:.1f})")
    
    # Final decision
    if signal_strength >= 2:
        action = "STRONG_BUY"
        recommendation = "Strong buy signal - Consider long position"
        color = "🟢"
    elif signal_strength >= 1:
        action = "BUY"
        recommendation = "Buy signal - Wait for confirmation"
        color = "🟢"
    elif signal_strength <= -2:
        action = "STRONG_SELL"
        recommendation = "Strong sell signal - Consider short position"
        color = "🔴"
    elif signal_strength <= -1:
        action = "SELL"
        recommendation = "Sell signal - Wait for confirmation"
        color = "🔴"
    else:
        action = "NEUTRAL"
        recommendation = "No clear signal - Stay aside"
        color = "⚪"
    
    return {
        "action": action,
        "color": color,
        "buy_signals": buy_signals,
        "sell_signals": sell_signals,
        "recommendation": recommendation,
        "confidence": round(min(abs(signal_strength) / 4, 0.95), 3)
    }

# ============================================
# API Endpoints
# ============================================

@app.get("/")
def root():
    return {
        "name": "Forex AI Analysis API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "/": "This info",
            "/health": "Health check",
            "/analyze/{symbol}": "Full analysis for a pair",
            "/signal/{symbol}": "Quick signal only",
            "/pairs": "List available pairs"
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/pairs")
def get_pairs():
    """List of available forex pairs"""
    pairs = {
        "majors": ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X", "USDCAD=X", "NZDUSD=X"],
        "minors": ["EURGBP=X", "EURJPY=X", "GBPJPY=X", "AUDJPY=X", "CADJPY=X", "CHFJPY=X"]
    }
    return pairs

@app.get("/analyze/{symbol}", response_model=AnalysisResponse)
async def analyze_forex(symbol: str, period: str = "7d", interval: str = "1h"):
    """Analyze a forex pair and get trading signal"""
    
    try:
        # Download data
        df = yf.download(symbol, period=period, interval=interval, progress=False)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [col[0] for col in df.columns]
        
        if 'Open' not in df.columns:
            df = df[['Open', 'High', 'Low', 'Close']]
        
        if len(df) < 50:
            raise HTTPException(status_code=400, detail=f"Insufficient data (only {len(df)} points)")
        
        # Calculate indicators
        df['RSI'] = calculate_rsi(df['Close'])
        df['MACD_line'], df['MACD_signal'], df['MACD_hist'] = calculate_macd(df['Close'])
        df['BB_upper'], df['BB_middle'], df['BB_lower'] = calculate_bollinger_bands(df['Close'])
        df['ATR'] = calculate_atr(df['High'], df['Low'], df['Close'])
        df['STOCH_K'], df['STOCH_D'] = calculate_stochastic(df['High'], df['Low'], df['Close'])
        df['ADX'] = calculate_adx(df['High'], df['Low'], df['Close'])
        
        df = df.dropna()
        
        if len(df) == 0:
            raise HTTPException(status_code=400, detail="Not enough data after indicator calculation")
        
        # Latest values
        latest = df.iloc[-1]
        current_price = float(latest['Close'])
        
        # Generate signal
        signal = generate_signal(
            rsi=float(latest['RSI']),
            macd_hist=float(latest['MACD_hist']),
            price=current_price,
            bb_upper=float(latest['BB_upper']),
            bb_lower=float(latest['BB_lower']),
            stoch_k=float(latest['STOCH_K']) if not pd.isna(latest['STOCH_K']) else None,
            adx=float(latest['ADX']) if not pd.isna(latest['ADX']) else None
        )
        
        # Risk management
        atr = float(latest['ATR'])
        
        return AnalysisResponse(
            success=True,
            timestamp=datetime.now().isoformat(),
            symbol=symbol.replace('=X', ''),
            current_price=round(current_price, 5),
            indicators={
                "rsi": round(float(latest['RSI']), 2),
                "macd_histogram": round(float(latest['MACD_hist']), 6),
                "bollinger_upper": round(float(latest['BB_upper']), 5),
                "bollinger_middle": round(float(latest['BB_middle']), 5),
                "bollinger_lower": round(float(latest['BB_lower']), 5),
                "atr": round(atr, 5),
                "adx": round(float(latest['ADX']), 2) if not pd.isna(latest['ADX']) else None
            },
            signal=signal,
            risk_management={
                "stop_loss": round(current_price - (atr * 1.5), 5),
                "take_profit": round(current_price + (atr * 2), 5),
                "risk_reward_ratio": 1.33,
                "position_size_suggestion": "1-2% of capital"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/signal/{symbol}", response_model=SignalResponse)
async def get_signal(symbol: str):
    """Quick trading signal only (lightweight)"""
    
    result = await analyze_forex(symbol, period="3d", interval="1h")
    
    return SignalResponse(
        success=True,
        timestamp=datetime.now().isoformat(),
        symbol=symbol.replace('=X', ''),
        signal=result.signal["action"],
        confidence=result.signal["confidence"],
        price=result.current_price
    )

# ============================================
# For local testing
# ============================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
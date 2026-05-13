"""
Forex AI Client - For integration with other AI systems
This allows any AI (Claude, ChatGPT, Gemini, etc.) to call your Forex API
"""

import requests
import json
from typing import Dict, Any, Optional, List

class ForexAIClient:
    """
    Client for Forex AI Analysis API
    Can be used by any AI system to get real-time forex signals
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize client
        
        Args:
            base_url: API endpoint (e.g., http://192.168.1.100:8000)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check if API is healthy"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        response = self.session.get(f"{self.base_url}/model/info")
        return response.json()
    
    def get_pairs(self) -> Dict[str, List[str]]:
        """Get available forex pairs"""
        response = self.session.get(f"{self.base_url}/pairs")
        return response.json()
    
    def get_signal(self, symbol: str = "EURUSD=X") -> Dict[str, Any]:
        """
        Get quick trading signal for a forex pair
        
        Args:
            symbol: Forex pair (EURUSD=X, GBPUSD=X, etc.)
        
        Returns:
            Signal with action, confidence, price, RSI
        """
        response = self.session.get(f"{self.base_url}/signal/{symbol}")
        return response.json()
    
    def analyze_full(self, symbol: str = "EURUSD=X", 
                     period: str = "7d", 
                     interval: str = "1h") -> Dict[str, Any]:
        """
        Get complete analysis with all indicators
        
        Args:
            symbol: Forex pair
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y)
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 4h, 1d)
        """
        params = {"period": period, "interval": interval}
        response = self.session.get(f"{self.base_url}/analyze/{symbol}", params=params)
        return response.json()
    
    def get_multiple_signals(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get signals for multiple forex pairs
        
        Args:
            symbols: List of forex pairs
        
        Returns:
            Dictionary of signals by symbol
        """
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.get_signal(symbol)
            except Exception as e:
                results[symbol] = {"error": str(e)}
        return results
    
    def get_trading_recommendation(self, symbol: str = "EURUSD=X") -> str:
        """
        Get human-readable trading recommendation
        
        Returns:
            Natural language trading recommendation
        """
        signal = self.get_signal(symbol)
        
        if not signal.get('success'):
            return f"Unable to analyze {symbol}: {signal.get('error', 'Unknown error')}"
        
        recommendation = f"""
        FOREX TRADING RECOMMENDATION - {signal['symbol']}
        
        Current Price: ${signal['price']}
        RSI (14): {signal['rsi']}
        
        SIGNAL: {signal['signal']}
        Confidence: {signal['confidence'] * 100:.1f}%
        Reason: {signal['reason']}
        
        Model Accuracy: {signal['model_accuracy'] * 100:.1f}%
        
        Recommendation: {
            'BUY' if signal['signal'] == 'BUY' else 
            'SELL' if signal['signal'] == 'SELL' else 
            'WAIT'
        }
        """
        
        return recommendation.strip()


# ============================================
# Example usage for different AI systems
# ============================================

def example_for_claude():
    """Example of how Claude can use this API"""
    
    client = ForexAIClient("http://localhost:8000")
    
    # Get EURUSD signal
    signal = client.get_signal("EURUSD=X")
    
    # Claude can now analyze this data
    print(f"EURUSD Signal: {signal['signal']}")
    print(f"Price: ${signal['price']}")
    
    return signal


def example_for_chatgpt():
    """Example of how ChatGPT can use this API"""
    
    client = ForexAIClient("http://localhost:8000")
    
    # Get full analysis
    analysis = client.analyze_full("GBPUSD=X")
    
    # ChatGPT can interpret this analysis
    if analysis['success']:
        print(f"GBPUSD Analysis Complete")
        print(f"Signal: {analysis['signal']['action']}")
        print(f"RSI: {analysis['indicators']['rsi']}")
    
    return analysis


def example_for_gemini():
    """Example for Google Gemini"""
    
    client = ForexAIClient("http://localhost:8000")
    
    # Get multiple pairs at once
    pairs = ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X']
    signals = client.get_multiple_signals(pairs)
    
    for symbol, data in signals.items():
        if 'signal' in data:
            print(f"{symbol}: {data['signal']} @ ${data['price']}")
    
    return signals


# ============================================
# Function to format response for LLM consumption
# ============================================

def format_for_llm(signal_data: Dict[str, Any]) -> str:
    """
    Format API response for Large Language Models
    This makes it easy for any LLM to understand the data
    """
    
    if not signal_data.get('success'):
        return f"Error: {signal_data.get('error', 'Unknown')}"
    
    return f"""
    FOREX ANALYSIS RESULT:
    - Pair: {signal_data['symbol']}
    - Current Price: {signal_data['price']}
    - RSI (14): {signal_data['rsi']}
    - Trading Signal: {signal_data['signal']}
    - Confidence: {signal_data['confidence'] * 100:.1f}%
    - Reason: {signal_data['reason']}
    - Model Accuracy: {signal_data['model_accuracy'] * 100:.1f}%
    """


# ============================================
# Quick test
# ============================================

if __name__ == "__main__":
    print("="*60)
    print("Forex AI Client - Testing Connection")
    print("="*60)
    
    client = ForexAIClient()
    
    # Test health
    health = client.health_check()
    print(f"\n✅ Health: {health['status']}")
    
    # Get signal
    signal = client.get_signal("EURUSD=X")
    print(f"\n📊 Signal Response:")
    print(json.dumps(signal, indent=2))
    
    # Get recommendation
    print(f"\n📝 Recommendation:")
    print(client.get_trading_recommendation("EURUSD=X"))
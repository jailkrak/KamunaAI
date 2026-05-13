#!/usr/bin/env python3
"""
Forex AI Chat CLI - Command Line Interface for chatting with Forex AI
Run this file to have a conversation with your AI
"""

import requests
import json
import sys
import os
from datetime import datetime

# ============================================
# Configuration
# ============================================
API_URL = "http://localhost:8000"  # ប្តូរតាម IP របស់អ្នក

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# ============================================
# API Functions
# ============================================

def get_forex_signal(symbol="EURUSD=X"):
    """Get signal from API"""
    try:
        response = requests.get(f"{API_URL}/signal/{symbol}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection error: {e}"}

def get_full_analysis(symbol="EURUSD=X"):
    """Get full analysis"""
    try:
        response = requests.get(f"{API_URL}/analyze/{symbol}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection error: {e}"}

def get_model_info():
    """Get model information"""
    try:
        response = requests.get(f"{API_URL}/model/info", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Cannot get model info"}
    except Exception as e:
        return {"error": f"Connection error: {e}"}

def get_available_pairs():
    """Get list of available forex pairs"""
    try:
        response = requests.get(f"{API_URL}/pairs", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": "Cannot get pairs"}
    except Exception as e:
        return {"error": f"Connection error: {e}"}

# ============================================
# AI Response Generator (Natural Language)
# ============================================

def generate_ai_response(user_input, signal_data=None, analysis_data=None):
    """
    Generate natural language response based on user input and forex data
    """
    user_input_lower = user_input.lower()
    
    # Check if API is connected
    if signal_data and signal_data.get("error"):
        return f"⚠️ {Colors.RED}Cannot connect to Forex API. Make sure the server is running at {API_URL}{Colors.END}\n\n💡 Run: python app.py"
    
    # ===== COMMANDS =====
    
    # Help command
    if user_input_lower in ["help", "?", "h", "ជំនួយ"]:
        return f"""
{Colors.CYAN}{Colors.BOLD}🤖 FOREX AI CHAT - COMMANDS{Colors.END}

{Colors.GREEN}📊 FOREX ANALYSIS:{Colors.END}
  • {Colors.YELLOW}eurusd{Colors.END} or {Colors.YELLOW}eur{Colors.END}     → Get signal for EUR/USD
  • {Colors.YELLOW}gbpusd{Colors.END} or {Colors.YELLOW}gbp{Colors.END}     → Get signal for GBP/USD
  • {Colors.YELLOW}usdjpy{Colors.END} or {Colors.YELLOW}jpy{Colors.END}     → Get signal for USD/JPY
  • {Colors.YELLOW}analyze {symbol}{Colors.END}   → Full technical analysis
  • {Colors.YELLOW}pairs{Colors.END} or {Colors.YELLOW}list{Colors.END}     → Show all available pairs

{Colors.GREEN}💬 GENERAL:{Colors.END}
  • {Colors.YELLOW}hello{Colors.END} / {Colors.YELLOW}hi{Colors.END}        → Greeting
  • {Colors.YELLOW}about{Colors.END} / {Colors.YELLOW}info{Colors.END}      → About this AI
  • {Colors.YELLOW}model{Colors.END}              → Model information
  • {Colors.YELLOW}help{Colors.END}               → Show this menu
  • {Colors.YELLOW}quit{Colors.END} / {Colors.YELLOW}exit{Colors.END}       → Exit chat

{Colors.CYAN}💡 Example: Type "eurusd" to get trading signal{Colors.END}
"""

    # About command
    if user_input_lower in ["about", "info", "what are you", "who are you"]:
        return f"""
{Colors.CYAN}{Colors.BOLD}🤖 ABOUT FOREX AI{Colors.END}

I am a {Colors.GREEN}Forex Trading Assistant{Colors.END} powered by an RSI-based AI model.

{Colors.YELLOW}📈 Model Information:{Colors.END}
  • Type: Rule-based RSI Strategy
  • Strategy: Mean Reversion
  • RSI Buy Threshold: 30 (Oversold)
  • RSI Sell Threshold: 70 (Overbought)
  • Accuracy: ~52% (better than random)

{Colors.YELLOW}🔧 What I can do:{Colors.END}
  • Provide real-time trading signals for major forex pairs
  • Show technical indicators (RSI, MACD, Bollinger Bands)
  • Suggest stop loss and take profit levels
  • Analyze market conditions

{Colors.YELLOW}⚠️ Disclaimer:{Colors.END}
  This is for analysis purposes only. Not financial advice.
  Always do your own research before trading.

Type {Colors.GREEN}help{Colors.END} to see all commands.
"""

    # Model info command
    if user_input_lower in ["model", "ai model", "how does it work"]:
        info = get_model_info()
        if info and not info.get("error"):
            return f"""
{Colors.CYAN}{Colors.BOLD}🧠 AI MODEL DETAILS{Colors.END}

{Colors.YELLOW}Model Type:{Colors.END} {info.get('model_type', 'N/A')}
{Colors.YELLOW}Strategy:{Colors.END} {info.get('strategy', 'N/A')}
{Colors.YELLOW}RSI Buy Signal:{Colors.END} When RSI < {info.get('rsi_buy_threshold', 30)} (Oversold)
{Colors.YELLOW}RSI Sell Signal:{Colors.END} When RSI > {info.get('rsi_sell_threshold', 70)} (Overbought)
{Colors.YELLOW}Accuracy:{Colors.END} {(info.get('accuracy', 0) * 100):.1f}%

{Colors.CYAN}📖 How it works:{Colors.END}
1. I fetch real-time forex data from Yahoo Finance
2. Calculate RSI (Relative Strength Index)
3. Generate signal based on overbought/oversold levels
4. Provide confidence score and recommendation

The model is {Colors.GREEN}simple but effective{Colors.END} for identifying potential reversals.
"""

    # Pairs command
    if user_input_lower in ["pairs", "list", "symbols", "available"]:
        pairs = get_available_pairs()
        if pairs and not pairs.get("error"):
            majors = pairs.get('majors', [])
            minors = pairs.get('minors', [])
            
            response = f"{Colors.CYAN}{Colors.BOLD}📋 AVAILABLE FOREX PAIRS{Colors.END}\n\n"
            response += f"{Colors.GREEN}★ Major Pairs:{Colors.END}\n"
            for p in majors:
                name = p.replace('=X', '')
                response += f"   • {Colors.YELLOW}{name}{Colors.END}\n"
            
            response += f"\n{Colors.GREEN}☆ Minor Pairs:{Colors.END}\n"
            for p in minors:
                name = p.replace('=X', '')
                response += f"   • {Colors.YELLOW}{name}{Colors.END}\n"
            
            response += f"\n{Colors.CYAN}💡 Type any pair name (e.g., 'eurusd') to get signal{Colors.END}"
            return response
        else:
            return f"{Colors.RED}Cannot fetch pairs. Make sure API is running.{Colors.END}"

    # Greeting
    if user_input_lower in ["hello", "hi", "hey", "greeting", "សួស្តី", "ជំរាបសួរ"]:
        return f"""{Colors.GREEN}👋 Hello! I'm your Forex AI Assistant.{Colors.END}

I can help you analyze forex markets and provide trading signals.
Type {Colors.YELLOW}help{Colors.END} to see what I can do.
Type a currency pair like {Colors.YELLOW}eurusd{Colors.END} to get a trading signal!"""

    # ===== FOREX SIGNAL COMMANDS =====
    
    symbol_map = {
        "eurusd": "EURUSD=X", "eur": "EURUSD=X", "euro": "EURUSD=X",
        "gbpusd": "GBPUSD=X", "gbp": "GBPUSD=X", "pound": "GBPUSD=X",
        "usdjpy": "USDJPY=X", "jpy": "USDJPY=X", "yen": "USDJPY=X",
        "usdchf": "USDCHF=X", "chf": "USDCHF=X", "swiss": "USDCHF=X",
        "audusd": "AUDUSD=X", "aud": "AUDUSD=X", "aussie": "AUDUSD=X",
        "usdcad": "USDCAD=X", "cad": "USDCAD=X", "loonie": "USDCAD=X",
        "nzdusd": "NZDUSD=X", "nzd": "NZDUSD=X", "kiwi": "NZDUSD=X",
        "eurgbp": "EURGBP=X", "eurjpy": "EURJPY=X", "gbpjpy": "GBPJPY=X"
    }
    
    # Check if user asked for analysis of a specific pair
    for key, symbol in symbol_map.items():
        if key in user_input_lower:
            signal = get_forex_signal(symbol)
            
            if signal and not signal.get("error"):
                # Determine emoji and color based on signal
                if signal['signal'] == 'BUY':
                    signal_emoji = "🟢"
                    signal_color = Colors.GREEN
                    advice = "Consider LONG position"
                elif signal['signal'] == 'SELL':
                    signal_emoji = "🔴"
                    signal_color = Colors.RED
                    advice = "Consider SHORT position"
                else:
                    signal_emoji = "⚪"
                    signal_color = Colors.YELLOW
                    advice = "Wait for clearer signal"
                
                response = f"""
{Colors.CYAN}{Colors.BOLD}📊 FOREX ANALYSIS - {signal['symbol']}{Colors.END}

{signal_emoji} {signal_color}{Colors.BOLD}Signal: {signal['signal']}{Colors.END}
{Colors.YELLOW}💰 Current Price:{Colors.END} ${signal['price']}
{Colors.YELLOW}📈 RSI (14):{Colors.END} {signal['rsi']:.1f}

{Colors.CYAN}🔍 Analysis:{Colors.END}
{signal['reason']}

{Colors.CYAN}💪 Confidence:{Colors.END} {signal['confidence'] * 100:.1f}%
{Colors.CYAN}🎯 Model Accuracy:{Colors.END} {signal['model_accuracy'] * 100:.1f}%

{Colors.GREEN}📝 Recommendation:{Colors.END} {advice}

{Colors.CYAN}💡 Tip:{Colors.END} Type 'analyze {key}' for detailed technical indicators
"""
                return response
            else:
                return f"{Colors.RED}⚠️ Cannot get signal for {key}. Make sure API is running.{Colors.END}"
    
    # Full analysis command
    if user_input_lower.startswith("analyze "):
        pair_name = user_input_lower.replace("analyze ", "").strip()
        
        # Find symbol
        symbol = None
        for key, sym in symbol_map.items():
            if key == pair_name:
                symbol = sym
                break
        
        if symbol:
            analysis = get_full_analysis(symbol)
            if analysis and not analysis.get("error"):
                ind = analysis['indicators']
                sig = analysis['signal']
                
                signal_color = Colors.GREEN if sig['action'] == 'BUY' else (Colors.RED if sig['action'] == 'SELL' else Colors.YELLOW)
                
                response = f"""
{Colors.CYAN}{Colors.BOLD}🔬 DETAILED TECHNICAL ANALYSIS - {analysis['symbol']}{Colors.END}

{signal_color}{Colors.BOLD}🎯 SIGNAL: {sig['action']}{Colors.END}
{Colors.YELLOW}📊 Confidence: {sig['confidence'] * 100:.1f}%{Colors.END}

{Colors.CYAN}📈 TECHNICAL INDICATORS:{Colors.END}
  • RSI (14): {ind['rsi']:.1f}
  • MACD Histogram: {ind['macd_histogram']:.6f}
  • ATR (Volatility): {ind['atr']:.5f}

{Colors.CYAN}📊 BOLLINGER BANDS:{Colors.END}
  • Upper Band: ${ind['bollinger_upper']:.5f}
  • Middle Band: ${ind['bollinger_middle']:.5f}
  • Lower Band: ${ind['bollinger_lower']:.5f}

{Colors.CYAN}🛡️ RISK MANAGEMENT:{Colors.END}
  • Stop Loss: ${analysis['risk_management']['stop_loss']:.5f}
  • Take Profit: ${analysis['risk_management']['take_profit']:.5f}
  • Risk/Reward: {analysis['risk_management']['risk_reward_ratio']}

{Colors.GREEN}📝 {sig['recommendation']}{Colors.END}
"""
                return response
            else:
                return f"{Colors.RED}Cannot get analysis for {pair_name}{Colors.END}"
        else:
            return f"{Colors.YELLOW}Unknown pair: {pair_name}. Type 'pairs' to see available pairs.{Colors.END}"
    
    # Unknown command - try to be helpful
    return f"""
{Colors.YELLOW}🤔 I don't understand "{user_input}"{Colors.END}

{Colors.CYAN}Try one of these:{Colors.END}
  • Type {Colors.GREEN}eurusd{Colors.END} → Get trading signal
  • Type {Colors.GREEN}analyze eurusd{Colors.END} → Detailed analysis
  • Type {Colors.GREEN}help{Colors.END} → See all commands
  • Type {Colors.GREEN}pairs{Colors.END} → See available currency pairs
"""

# ============================================
# Chat Interface
# ============================================

def print_banner():
    """Print welcome banner"""
    banner = f"""
{Colors.CYAN}{'='*60}{Colors.END}
{Colors.BOLD}🤖 FOREX AI CHAT - Command Line Interface{Colors.END}
{Colors.CYAN}{'='*60}{Colors.END}

{Colors.GREEN}💡 Type 'help' to see all commands
{Colors.GREEN}💡 Type 'quit' to exit
{Colors.GREEN}💡 Try typing 'eurusd' to get a trading signal!

{Colors.YELLOW}⚠️ Make sure your API server is running at {API_URL}
{Colors.CYAN}{'-'*60}{Colors.END}
"""
    print(banner)

def main():
    """Main chat loop"""
    print_banner()
    
    # Check API connection
    print(f"{Colors.CYAN}🔌 Checking API connection...{Colors.END}")
    test = get_forex_signal()
    if test and not test.get("error"):
        print(f"{Colors.GREEN}✅ Connected to Forex API at {API_URL}{Colors.END}\n")
    else:
        print(f"{Colors.RED}❌ Cannot connect to {API_URL}{Colors.END}")
        print(f"{Colors.YELLOW}💡 Make sure you run: python app.py first{Colors.END}\n")
    
    # Chat loop
    while True:
        try:
            # Get user input
            user_input = input(f"{Colors.BOLD}{Colors.CYAN}You{Colors.END} > ").strip()
            
            # Check for exit commands
            if user_input.lower() in ["quit", "exit", "q", "bye", "goodbye", "លា"]:
                print(f"\n{Colors.GREEN}👋 Goodbye! Happy trading!{Colors.END}\n")
                break
            
            # Skip empty input
            if not user_input:
                continue
            
            # Generate AI response
            response = generate_ai_response(user_input)
            
            # Print AI response
            print(f"\n{Colors.BOLD}{Colors.GREEN}AI{Colors.END} > {response}\n")
            
        except KeyboardInterrupt:
            print(f"\n\n{Colors.GREEN}👋 Goodbye!{Colors.END}\n")
            break
        except EOFError:
            break

# ============================================
# Run the chat
# ============================================
if __name__ == "__main__":
    main()
"""
Technical Indicators Module - Calculate indicators for Forex analysis
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
import warnings
warnings.filterwarnings('ignore')


class TechnicalIndicators:
    """
    Calculate comprehensive technical indicators for Forex market analysis
    """
    
    def __init__(self, df=None):
        self.df = df
        self.indicator_names = []
        
    def set_data(self, df):
        """Set or update DataFrame"""
        self.df = df.copy()
        return self
    
    def add_all_indicators(self):
        """
        Add ALL technical indicators for comprehensive analysis
        """
        if self.df is None:
            raise ValueError("No data loaded. Call set_data() first.")
        
        print("Calculating all technical indicators...")
        
        self.add_trend_indicators()
        self.add_momentum_indicators()
        self.add_volatility_indicators()
        self.add_volume_indicators()
        self.add_price_action_indicators()
        self.add_statistical_indicators()
        
        print(f"Total indicators added: {len(self.indicator_names)}")
        
        return self.df
    
    def add_trend_indicators(self):
        """Add trend following indicators"""
        print("  - Trend indicators...")
        
        # Moving Averages
        for period in [10, 20, 50, 100, 200]:
            self.df[f'SMA_{period}'] = ta.sma(self.df['Close'], length=period)
            self.df[f'EMA_{period}'] = ta.ema(self.df['Close'], length=period)
            self.indicator_names.extend([f'SMA_{period}', f'EMA_{period}'])
        
        # Weighted Moving Average
        self.df['WMA_20'] = ta.wma(self.df['Close'], length=20)
        self.indicator_names.append('WMA_20')
        
        # MACD
        macd = ta.macd(self.df['Close'])
        self.df['MACD'] = macd['MACD_12_26_9']
        self.df['MACD_signal'] = macd['MACDs_12_26_9']
        self.df['MACD_histogram'] = macd['MACDh_12_26_9']
        self.indicator_names.extend(['MACD', 'MACD_signal', 'MACD_histogram'])
        
        # ADX for trend strength
        adx = ta.adx(self.df['High'], self.df['Low'], self.df['Close'])
        self.df['ADX'] = adx['ADX_14']
        self.df['DMP'] = adx['DMP_14']
        self.df['DMN'] = adx['DMN_14']
        self.indicator_names.extend(['ADX', 'DMP', 'DMN'])
        
        # Ichimoku Cloud
        ichimoku = ta.ichimoku(self.df['High'], self.df['Low'])
        if isinstance(ichimoku, tuple):
            self.df['Ichimoku_A'] = ichimoku[0]['ISA_9']
            self.df['Ichimoku_B'] = ichimoku[0]['ISB_26']
            self.indicator_names.extend(['Ichimoku_A', 'Ichimoku_B'])
        
        # Parabolic SAR
        self.df['PSAR'] = ta.psar(self.df['High'], self.df['Low'])
        self.indicator_names.append('PSAR')
    
    def add_momentum_indicators(self):
        """Add momentum oscillators"""
        print("  - Momentum indicators...")
        
        # RSI
        for period in [7, 14, 21]:
            self.df[f'RSI_{period}'] = ta.rsi(self.df['Close'], length=period)
            self.indicator_names.append(f'RSI_{period}')
        
        # Stochastic
        stoch = ta.stoch(self.df['High'], self.df['Low'], self.df['Close'])
        self.df['Stoch_K'] = stoch['STOCHk_14_3_3']
        self.df['Stoch_D'] = stoch['STOCHd_14_3_3']
        self.indicator_names.extend(['Stoch_K', 'Stoch_D'])
        
        # Williams %R
        self.df['Williams_R'] = ta.willr(self.df['High'], self.df['Low'], self.df['Close'])
        self.indicator_names.append('Williams_R')
        
        # CCI
        self.df['CCI'] = ta.cci(self.df['High'], self.df['Low'], self.df['Close'])
        self.indicator_names.append('CCI')
        
        # MFI
        self.df['MFI'] = ta.mfi(self.df['High'], self.df['Low'], self.df['Close'], self.df['Volume'])
        self.indicator_names.append('MFI')
        
        # ROC
        for period in [1, 5, 10]:
            self.df[f'ROC_{period}'] = ta.roc(self.df['Close'], length=period)
            self.indicator_names.append(f'ROC_{period}')
    
    def add_volatility_indicators(self):
        """Add volatility indicators"""
        print("  - Volatility indicators...")
        
        # Bollinger Bands
        bbands = ta.bbands(self.df['Close'], length=20, std=2)
        self.df['BB_upper'] = bbands['BBU_20_2.0']
        self.df['BB_middle'] = bbands['BBM_20_2.0']
        self.df['BB_lower'] = bbands['BBL_20_2.0']
        self.df['BB_width'] = (self.df['BB_upper'] - self.df['BB_lower']) / self.df['BB_middle']
        self.df['BB_position'] = (self.df['Close'] - self.df['BB_lower']) / (self.df['BB_upper'] - self.df['BB_lower'])
        self.indicator_names.extend(['BB_upper', 'BB_middle', 'BB_lower', 'BB_width', 'BB_position'])
        
        # Keltner Channels
        kc = ta.kc(self.df['High'], self.df['Low'], self.df['Close'])
        self.df['KC_upper'] = kc['KCUe_20_2']
        self.df['KC_lower'] = kc['KCLe_20_2']
        self.indicator_names.extend(['KC_upper', 'KC_lower'])
        
        # ATR
        for period in [7, 14, 21]:
            self.df[f'ATR_{period}'] = ta.atr(self.df['High'], self.df['Low'], self.df['Close'], length=period)
            self.indicator_names.append(f'ATR_{period}')
        
        # Donchian Channels
        self.df['DC_upper'] = self.df['High'].rolling(20).max()
        self.df['DC_lower'] = self.df['Low'].rolling(20).min()
        self.df['DC_middle'] = (self.df['DC_upper'] + self.df['DC_lower']) / 2
        self.indicator_names.extend(['DC_upper', 'DC_lower', 'DC_middle'])
    
    def add_volume_indicators(self):
        """Add volume-based indicators"""
        print("  - Volume indicators...")
        
        # On-Balance Volume
        self.df['OBV'] = ta.obv(self.df['Close'], self.df['Volume'])
        self.indicator_names.append('OBV')
        
        # Volume Price Trend
        self.df['VPT'] = ta.vpt(self.df['Close'], self.df['Volume'])
        self.indicator_names.append('VPT')
        
        # Money Flow Index (already added)
        
        # Volume SMA
        self.df['Volume_SMA_20'] = self.df['Volume'].rolling(20).mean()
        self.df['Volume_ratio'] = self.df['Volume'] / self.df['Volume_SMA_20']
        self.indicator_names.extend(['Volume_SMA_20', 'Volume_ratio'])
        
        # Chaikin Money Flow
        self.df['CMF'] = ta.cmf(self.df['High'], self.df['Low'], self.df['Close'], self.df['Volume'])
        self.indicator_names.append('CMF')
    
    def add_price_action_indicators(self):
        """Add price action and pattern indicators"""
        print("  - Price action indicators...")
        
        # Candlestick patterns
        patterns = ['doji', 'hammer', 'engulfing', 'morning_star', 'evening_star',
                    'three_white_soldiers', 'three_black_crows']
        
        for pattern in patterns:
            try:
                result = ta.cdl_pattern(self.df['Open'], self.df['High'], 
                                       self.df['Low'], self.df['Close'], name=pattern)
                if result is not None:
                    self.df[f'Pattern_{pattern}'] = result
                    self.indicator_names.append(f'Pattern_{pattern}')
            except:
                pass
        
        # Support and Resistance levels
        for window in [10, 20, 50]:
            self.df[f'Resistance_{window}'] = self.df['High'].rolling(window).max()
            self.df[f'Support_{window}'] = self.df['Low'].rolling(window).min()
            self.indicator_names.extend([f'Resistance_{window}', f'Support_{window}'])
        
        # Fibonacci levels
        self.add_fibonacci_levels()
        
        # Pivot Points
        self.df['Pivot'] = (self.df['High'] + self.df['Low'] + self.df['Close']) / 3
        self.df['R1'] = 2 * self.df['Pivot'] - self.df['Low']
        self.df['S1'] = 2 * self.df['Pivot'] - self.df['High']
        self.indicator_names.extend(['Pivot', 'R1', 'S1'])
    
    def add_fibonacci_levels(self, window=100):
        """Add Fibonacci retracement levels"""
        recent_high = self.df['High'].rolling(window).max()
        recent_low = self.df['Low'].rolling(window).min()
        diff = recent_high - recent_low
        
        fib_levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
        
        for level in fib_levels:
            if level == 0:
                self.df[f'Fib_{int(level*100)}'] = recent_low
            elif level == 1:
                self.df[f'Fib_{int(level*100)}'] = recent_high
            else:
                self.df[f'Fib_{int(level*1000)}'] = recent_low + diff * level
            self.indicator_names.append(f'Fib_{int(level*100 if level<1 else 100)}')
    
    def add_statistical_indicators(self):
        """Add statistical features"""
        print("  - Statistical indicators...")
        
        # Rolling statistics
        for window in [5, 10, 20, 50]:
            self.df[f'Close_mean_{window}'] = self.df['Close'].rolling(window).mean()
            self.df[f'Close_std_{window}'] = self.df['Close'].rolling(window).std()
            self.df[f'Close_skew_{window}'] = self.df['Close'].rolling(window).skew()
            self.df[f'Close_kurt_{window}'] = self.df['Close'].rolling(window).kurt()
            self.indicator_names.extend([f'Close_mean_{window}', f'Close_std_{window}',
                                         f'Close_skew_{window}', f'Close_kurt_{window}'])
        
        # Returns statistics
        self.df['Returns'] = self.df['Close'].pct_change()
        self.df['Returns_zscore'] = (self.df['Returns'] - self.df['Returns'].rolling(20).mean()) / self.df['Returns'].rolling(20).std()
        self.indicator_names.extend(['Returns', 'Returns_zscore'])
        
        # Rolling correlations
        self.df['Price_Volume_corr'] = self.df['Close'].rolling(50).corr(self.df['Volume'])
        self.indicator_names.append('Price_Volume_corr')
    
    def clean_indicators(self, drop_na=True):
        """Remove NaN values from indicator calculations"""
        if drop_na:
            self.df = self.df.dropna()
        
        # Remove infinite values
        self.df = self.df.replace([np.inf, -np.inf], np.nan).dropna()
        
        print(f"Clean data shape: {self.df.shape}")
        return self.df
    
    def get_indicator_list(self):
        """Return list of all calculated indicators"""
        return self.indicator_names
    
    def get_indicator_summary(self):
        """Get summary of indicators by category"""
        summary = {
            'Total Indicators': len(self.indicator_names),
            'Columns in DataFrame': len(self.df.columns),
            'Trend Indicators': len([i for i in self.indicator_names if any(x in i for x in ['SMA', 'EMA', 'MACD', 'ADX', 'PSAR'])]),
            'Momentum Indicators': len([i for i in self.indicator_names if any(x in i for x in ['RSI', 'Stoch', 'Williams', 'CCI', 'MFI', 'ROC'])]),
            'Volatility Indicators': len([i for i in self.indicator_names if any(x in i for x in ['BB', 'ATR', 'KC', 'DC'])]),
            'Volume Indicators': len([i for i in self.indicator_names if any(x in i for x in ['OBV', 'VPT', 'CMF', 'Volume'])]),
            'Price Action': len([i for i in self.indicator_names if any(x in i for x in ['Pattern', 'Resistance', 'Support', 'Fib', 'Pivot'])])
        }
        return summary


# Example usage
if __name__ == "__main__":
    import yfinance as yf
    df = yf.download('EURUSD=X', period='1mo', interval='1h', progress=False)
    df.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    indicators = TechnicalIndicators(df)
    df_with_indicators = indicators.add_all_indicators()
    df_clean = indicators.clean_indicators()
    
    print(indicators.get_indicator_summary())
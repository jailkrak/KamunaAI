import yfinance as yf
import pandas as pd
from typing import List

class TradingDataLoader:
    def __init__(self, symbol: str, start_date: str, end_date: str):
        self.symbol = symbol
        self.start = start_date
        self.end = end_date
    
    def fetch_data(self) -> pd.DataFrame:
        df = yf.download(self.symbol, start=self.start, end=self.end)
        df.reset_index(inplace=True)
        return df
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df['returns'] = df['Close'].pct_change()
        df['ma10'] = df['Close'].rolling(10).mean()
        df['ma50'] = df['Close'].rolling(50).mean()
        df['rsi'] = self._compute_rsi(df['Close'])
        return df.dropna()
    
    def _compute_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
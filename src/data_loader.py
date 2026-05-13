"""
Data Loader Module - Load Forex data from various sources
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class DataLoader:
    """
    Load Forex data from Yahoo Finance or local files
    """
    
    def __init__(self):
        self.data = None
        self.symbol = None
        self.timeframe = None
        
    def load_from_yahoo(self, symbol='EURUSD=X', start='2020-01-01', end=None, interval='1h'):
        """
        Load Forex data from Yahoo Finance
        
        Parameters:
        -----------
        symbol : str
            Forex pair symbol (default: 'EURUSD=X')
        start : str
            Start date (YYYY-MM-DD)
        end : str
            End date (default: today)
        interval : str
            Timeframe: '1m', '5m', '15m', '30m', '1h', '4h', '1d', '1wk', '1mo'
        """
        if end is None:
            end = datetime.now().strftime('%Y-%m-%d')
            
        print(f"Loading {symbol} data from {start} to {end} ({interval})...")
        
        try:
            df = yf.download(symbol, start=start, end=end, interval=interval, progress=False)
            df.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            df = df.dropna()
            
            self.data = df
            self.symbol = symbol
            self.timeframe = interval
            
            print(f"Successfully loaded {len(df)} rows")
            return df
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def load_from_csv(self, filepath, date_column='Date', parse_dates=True):
        """
        Load Forex data from CSV file
        
        Parameters:
        -----------
        filepath : str
            Path to CSV file
        date_column : str
            Name of date column
        parse_dates : bool
            Whether to parse dates
        """
        try:
            if parse_dates:
                df = pd.read_csv(filepath, parse_dates=[date_column], index_col=date_column)
            else:
                df = pd.read_csv(filepath)
                
            # Standardize column names
            df.columns = [col.capitalize() for col in df.columns]
            
            # Ensure required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in df.columns:
                    # Try lowercase
                    if col.lower() in df.columns:
                        df[col] = df[col.lower()]
                        df = df.drop(columns=[col.lower()])
                    else:
                        raise ValueError(f"Required column '{col}' not found in CSV")
            
            self.data = df
            self.symbol = filepath.split('/')[-1].replace('.csv', '')
            
            print(f"Loaded {len(df)} rows from {filepath}")
            return df
            
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None
    
    def load_multiple_pairs(self, symbols, start='2020-01-01', end=None, interval='1h'):
        """
        Load multiple Forex pairs
        
        Parameters:
        -----------
        symbols : list
            List of Forex pairs (e.g., ['EURUSD=X', 'GBPUSD=X', 'USDJPY=X'])
        start, end, interval : same as load_from_yahoo
        """
        data_dict = {}
        
        for symbol in symbols:
            df = self.load_from_yahoo(symbol, start, end, interval)
            if df is not None:
                data_dict[symbol] = df
                
        print(f"\nLoaded {len(data_dict)} currency pairs")
        return data_dict
    
    def get_latest_data(self, period='60d', interval='1h'):
        """
        Get latest data for live analysis
        
        Parameters:
        -----------
        period : str
            Period: '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
        interval : str
            Timeframe interval
        """
        end = datetime.now()
        start = end - timedelta(days=self._parse_period_to_days(period))
        
        return self.load_from_yahoo(
            symbol=self.symbol if self.symbol else 'EURUSD=X',
            start=start.strftime('%Y-%m-%d'),
            end=end.strftime('%Y-%m-%d'),
            interval=interval
        )
    
    def _parse_period_to_days(self, period):
        """Convert period string to days"""
        period_map = {
            '1d': 1, '5d': 5, '1mo': 30, '3mo': 90,
            '6mo': 180, '1y': 365, '2y': 730, '5y': 1825
        }
        return period_map.get(period, 365)
    
    def get_data_info(self):
        """Get information about loaded data"""
        if self.data is None:
            print("No data loaded. Please load data first.")
            return None
            
        info = {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'rows': len(self.data),
            'columns': list(self.data.columns),
            'start_date': self.data.index[0],
            'end_date': self.data.index[-1],
            'missing_values': self.data.isnull().sum().to_dict(),
            'duplicates': self.data.index.duplicated().sum()
        }
        
        return info
    
    def resample_data(self, target_interval):
        """
        Resample data to different timeframe
        
        Parameters:
        -----------
        target_interval : str
            '5min', '15min', '30min', '1H', '4H', '1D', '1W', '1M'
        """
        if self.data is None:
            print("No data to resample")
            return None
            
        resampled = self.data.resample(target_interval).agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        self.data = resampled
        self.timeframe = target_interval
        
        print(f"Resampled to {target_interval}: {len(resampled)} rows")
        return resampled


# Example usage
if __name__ == "__main__":
    loader = DataLoader()
    df = loader.load_from_yahoo('EURUSD=X', start='2023-01-01', interval='1h')
    print(loader.get_data_info())
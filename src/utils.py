"""
Utility functions for Trading AI Project
Logging, file handling, configuration, etc.
"""

import os
import sys
import json
import yaml
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import pickle
import hashlib

def setup_logger(log_file: str = None, level: str = 'INFO') -> logging.Logger:
    """
    Setup logger with file and console handlers
    
    Args:
        log_file: Path to log file (optional)
        level: Logging level
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger('TradingAI')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)
    
    return logger

def save_checkpoint(model, optimizer, epoch, loss, path: str, **kwargs):
    """Save model checkpoint"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
        'loss': loss,
        'timestamp': datetime.now().isoformat()
    }
    checkpoint.update(kwargs)
    
    torch = __import__('torch')
    torch.save(checkpoint, path)
    
def load_checkpoint(path: str, model, optimizer=None, device='cuda'):
    """Load model checkpoint"""
    torch = __import__('torch')
    checkpoint = torch.load(path, map_location=device)
    
    model.load_state_dict(checkpoint['model_state_dict'])
    
    if optimizer:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    
    return checkpoint

def save_json(data: Any, path: str, indent: int = 2):
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=indent)

def load_json(path: str) -> Any:
    """Load data from JSON file"""
    with open(path, 'r') as f:
        return json.load(f)

def save_pickle(obj: Any, path: str):
    """Save object to pickle file"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        pickle.dump(obj, f)

def load_pickle(path: str) -> Any:
    """Load object from pickle file"""
    with open(path, 'rb') as f:
        return pickle.load(f)

def calculate_sharpe_ratio(returns: np.ndarray, risk_free_rate: float = 0.02) -> float:
    """Calculate Sharpe Ratio"""
    excess_returns = returns - risk_free_rate / 252
    if np.std(excess_returns) == 0:
        return 0
    return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)

def calculate_max_drawdown(pnl: np.ndarray) -> Tuple[float, int, int]:
    """Calculate maximum drawdown and its duration"""
    cumulative = np.cumsum(pnl)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = cumulative - running_max
    
    max_dd = np.min(drawdown)
    max_dd_idx = np.argmin(drawdown)
    
    # Find when drawdown started
    start_idx = np.argmax(running_max[:max_dd_idx])
    
    return max_dd, start_idx, max_dd_idx

def create_time_features(timestamp: pd.Series) -> pd.DataFrame:
    """Create time-based features from timestamp"""
    df = pd.DataFrame()
    df['hour'] = timestamp.dt.hour
    df['day_of_week'] = timestamp.dt.dayofweek
    df['day_of_month'] = timestamp.dt.day
    df['month'] = timestamp.dt.month
    df['quarter'] = timestamp.dt.quarter
    df['is_weekend'] = (timestamp.dt.dayofweek >= 5).astype(int)
    df['is_month_end'] = timestamp.dt.is_month_end.astype(int)
    
    # Cyclical encoding for hour
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
    
    # Cyclical encoding for day of week
    df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
    df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
    
    return df

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate common technical indicators
    
    Args:
        df: DataFrame with 'Open', 'High', 'Low', 'Close', 'Volume'
    
    Returns:
        DataFrame with added indicators
    """
    df = df.copy()
    
    # Moving averages
    df['SMA_10'] = df['Close'].rolling(10).mean()
    df['SMA_20'] = df['Close'].rolling(20).mean()
    df['SMA_50'] = df['Close'].rolling(50).mean()
    df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    # MACD
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['BB_Middle'] = df['Close'].rolling(20).mean()
    bb_std = df['Close'].rolling(20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # ATR
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # Volume indicators
    df['Volume_SMA'] = df['Volume'].rolling(20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
    
    # Price rate of change
    df['ROC'] = df['Close'].pct_change(periods=10) * 100
    
    return df

def calculate_performance_metrics(predictions: np.ndarray, actuals: np.ndarray) -> Dict:
    """Calculate comprehensive performance metrics"""
    
    # Directional accuracy
    pred_sign = np.sign(predictions)
    actual_sign = np.sign(actuals)
    directional_accuracy = np.mean(pred_sign == actual_sign)
    
    # Mean squared error
    mse = np.mean((predictions - actuals) ** 2)
    
    # Mean absolute error
    mae = np.mean(np.abs(predictions - actuals))
    
    # R-squared
    ss_res = np.sum((actuals - predictions) ** 2)
    ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
    r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
    
    # Sharpe ratio (assuming daily returns)
    sharpe = calculate_sharpe_ratio(predictions)
    
    # Profit factor
    gross_profit = np.sum(predictions[predictions > 0])
    gross_loss = abs(np.sum(predictions[predictions < 0]))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf
    
    # Win rate
    win_rate = np.mean(predictions > 0)
    
    return {
        'directional_accuracy': directional_accuracy,
        'mse': mse,
        'mae': mae,
        'r2': r2,
        'sharpe_ratio': sharpe,
        'profit_factor': profit_factor,
        'win_rate': win_rate
    }

def hash_dataframe(df: pd.DataFrame) -> str:
    """Create hash of dataframe for caching"""
    return hashlib.md5(pd.util.hash_pandas_object(df, index=True).values).hexdigest()

def ensure_dir(path: str):
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)

def format_currency(value: float, symbol: str = '$') -> str:
    """Format currency value"""
    return f"{symbol}{value:,.2f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage"""
    return f"{value * 100:.{decimals}f}%"

class Timer:
    """Context manager for timing code execution"""
    
    def __init__(self, name: str = None, logger: logging.Logger = None):
        self.name = name
        self.logger = logger
    
    def __enter__(self):
        self.start = datetime.now()
        return self
    
    def __exit__(self, *args):
        self.end = datetime.now()
        self.elapsed = self.end - self.start
        
        if self.logger:
            msg = f"{self.name} took {self.elapsed.total_seconds():.2f}s" if self.name else f"Took {self.elapsed.total_seconds():.2f}s"
            self.logger.info(msg)
    
    def get_elapsed(self) -> float:
        return (datetime.now() - self.start).total_seconds()

class ConfigManager:
    """Manage configuration files"""
    
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = config_dir
    
    def load_config(self, name: str) -> Dict:
        """Load config from JSON or YAML"""
        json_path = os.path.join(self.config_dir, f"{name}.json")
        yaml_path = os.path.join(self.config_dir, f"{name}.yaml")
        yml_path = os.path.join(self.config_dir, f"{name}.yml")
        
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                return json.load(f)
        elif os.path.exists(yaml_path):
            with open(yaml_path, 'r') as f:
                return yaml.safe_load(f)
        elif os.path.exists(yml_path):
            with open(yml_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            raise FileNotFoundError(f"Config {name} not found in {self.config_dir}")
    
    def save_config(self, config: Dict, name: str, format: str = 'json'):
        """Save config to file"""
        os.makedirs(self.config_dir, exist_ok=True)
        
        if format == 'json':
            path = os.path.join(self.config_dir, f"{name}.json")
            with open(path, 'w') as f:
                json.dump(config, f, indent=2)
        elif format in ['yaml', 'yml']:
            path = os.path.join(self.config_dir, f"{name}.{format}")
            with open(path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
"""
Tokenizer for Trading Data
Convert price patterns into tokens/embeddings
Note: Not traditional NLP tokenizer, but for time series encoding
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from sklearn.preprocessing import KBinsDiscretizer

class TradingTokenizer:
    """
    Convert continuous trading data into discrete tokens
    Useful for Transformer models or pattern recognition
    """
    
    def __init__(self, n_bins: int = 10, strategy: str = 'quantile'):
        """
        Args:
            n_bins: Number of bins for discretization
            strategy: 'uniform', 'quantile', or 'kmeans'
        """
        self.n_bins = n_bins
        self.strategy = strategy
        self.discretizer = None
        self.vocab_size = n_bins
        self.pattern_vocab = {}
    
    def fit(self, data: np.ndarray):
        """Fit discretizer on data"""
        self.discretizer = KBinsDiscretizer(
            n_bins=self.n_bins, 
            encode='ordinal',
            strategy=self.strategy
        )
        self.discretizer.fit(data.reshape(-1, 1))
        self.vocab_size = self.n_bins
    
    def tokenize(self, data: np.ndarray) -> np.ndarray:
        """Convert continuous values to tokens"""
        if self.discretizer is None:
            raise ValueError("Tokenizer not fitted. Call fit() first.")
        
        tokens = self.discretizer.transform(data.reshape(-1, 1))
        return tokens.flatten().astype(int)
    
    def detokenize(self, tokens: np.ndarray) -> np.ndarray:
        """Convert tokens back to continuous values (approximate)"""
        if self.discretizer is None:
            raise ValueError("Tokenizer not fitted")
        
        # Get bin centers
        bin_edges = self.discretizer.bin_edges_[0]
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        return np.array([bin_centers[t] for t in tokens])

class PricePatternTokenizer:
    """
    Encode price patterns (e.g., candlestick patterns) as tokens
    """
    
    def __init__(self):
        self.patterns = {
            'DOJI': 0,
            'HAMMER': 1,
            'SHOOTING_STAR': 2,
            'BULLISH_ENGULFING': 3,
            'BEARISH_ENGULFING': 4,
            'MORNING_STAR': 5,
            'EVENING_STAR': 6,
            'THREE_WHITE_SOLDIERS': 7,
            'THREE_BLACK_CROWS': 8,
            'PIERCING': 9,
            'DARK_CLOUD_COVER': 10,
            'HARAMI': 11,
            'HARAMI_CROSS': 12
        }
    
    def identify_candlestick_pattern(self, open_price, high, low, close, prev_close=None):
        """Identify basic candlestick patterns"""
        body = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        total_range = high - low
        
        if total_range == 0:
            return 'DOJI'
        
        # Doji
        if body / total_range < 0.1:
            return 'DOJI'
        
        # Hammer
        if lower_shadow > 2 * body and upper_shadow < body * 0.3:
            return 'HAMMER'
        
        # Shooting Star
        if upper_shadow > 2 * body and lower_shadow < body * 0.3:
            return 'SHOOTING_STAR'
        
        # Engulfing (requires previous candle)
        if prev_close is not None:
            prev_body = abs(prev_close - open_price)
            if close > open_price and prev_close < open_price:
                if body > prev_body:
                    return 'BULLISH_ENGULFING'
            elif close < open_price and prev_close > open_price:
                if body > prev_body:
                    return 'BEARISH_ENGULFING'
        
        return None
    
    def tokenize_sequence(self, df: pd.DataFrame) -> List[int]:
        """Convert price sequence to pattern tokens"""
        tokens = []
        
        for i in range(1, len(df)):
            pattern = self.identify_candlestick_pattern(
                df.iloc[i]['Open'],
                df.iloc[i]['High'],
                df.iloc[i]['Low'],
                df.iloc[i]['Close'],
                df.iloc[i-1]['Close'] if i > 0 else None
            )
            
            if pattern and pattern in self.patterns:
                tokens.append(self.patterns[pattern])
            else:
                tokens.append(-1)  # No pattern
        
        return tokens

class SequenceTokenizer:
    """
    Convert time series sequences into tokenized format for Transformer
    """
    
    def __init__(self, seq_length: int = 60, n_bins: int = 50):
        self.seq_length = seq_length
        self.n_bins = n_bins
        self.price_tokenizer = TradingTokenizer(n_bins=n_bins)
        self.volume_tokenizer = TradingTokenizer(n_bins=10)
    
    def fit(self, price_data: np.ndarray, volume_data: Optional[np.ndarray] = None):
        """Fit tokenizers"""
        self.price_tokenizer.fit(price_data)
        if volume_data is not None:
            self.volume_tokenizer.fit(volume_data)
    
    def tokenize_sequence(self, prices: np.ndarray, volumes: Optional[np.ndarray] = None) -> Dict:
        """Tokenize a single sequence"""
        price_tokens = self.price_tokenizer.tokenize(prices)
        
        result = {
            'price_tokens': price_tokens.tolist(),
            'price_values': prices.tolist()
        }
        
        if volumes is not None:
            volume_tokens = self.volume_tokenizer.tokenize(volumes)
            result['volume_tokens'] = volume_tokens.tolist()
        
        return result
    
    def create_attention_mask(self, sequence_length: int) -> np.ndarray:
        """Create causal attention mask for decoder"""
        mask = np.triu(np.ones((sequence_length, sequence_length)), k=1)
        return mask == 0

def create_price_embeddings(tokens: np.ndarray, embedding_dim: int = 64) -> np.ndarray:
    """
    Simple embedding lookup for price tokens
    """
    vocab_size = max(tokens) + 1
    # Random embedding matrix
    embedding_matrix = np.random.randn(vocab_size, embedding_dim) * 0.01
    
    embeddings = embedding_matrix[tokens]
    return embeddings
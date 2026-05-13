"""
Preprocessing Module - Clean and prepare data for analysis
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split
import joblib
from scipy import stats


class Preprocessor:
    """
    Preprocess Forex data for AI analysis
    """
    
    def __init__(self, scaler_type='robust'):
        """
        Parameters:
        -----------
        scaler_type : str
            'minmax', 'standard', or 'robust'
        """
        self.scaler_type = scaler_type
        self.price_scaler = None
        self.volume_scaler = None
        self.is_fitted = False
        
    def _get_scaler(self):
        """Return the appropriate scaler"""
        if self.scaler_type == 'minmax':
            return MinMaxScaler()
        elif self.scaler_type == 'standard':
            return StandardScaler()
        else:
            return RobustScaler()
    
    def handle_missing_values(self, df, method='ffill'):
        """
        Handle missing values in DataFrame
        
        Parameters:
        -----------
        df : pd.DataFrame
            Input data
        method : str
            'ffill', 'bfill', 'drop', or 'interpolate'
        """
        df_clean = df.copy()
        
        print(f"Missing values before: {df_clean.isnull().sum().sum()}")
        
        if method == 'ffill':
            df_clean = df_clean.fillna(method='ffill')
        elif method == 'bfill':
            df_clean = df_clean.fillna(method='bfill')
        elif method == 'drop':
            df_clean = df_clean.dropna()
        elif method == 'interpolate':
            df_clean = df_clean.interpolate(method='linear')
        
        # Fill any remaining NaN with median
        df_clean = df_clean.fillna(df_clean.median())
        
        print(f"Missing values after: {df_clean.isnull().sum().sum()}")
        return df_clean
    
    def remove_outliers(self, df, columns=None, method='iqr', multiplier=3):
        """
        Remove outliers from specified columns
        
        Parameters:
        -----------
        df : pd.DataFrame
            Input data
        columns : list
            Columns to check (default: all numeric)
        method : str
            'iqr' or 'zscore'
        multiplier : float
            IQR multiplier or Z-score threshold
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        df_clean = df.copy()
        total_removed = 0
        
        for col in columns:
            if method == 'iqr':
                Q1 = df_clean[col].quantile(0.25)
                Q3 = df_clean[col].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - multiplier * IQR
                upper = Q3 + multiplier * IQR
                
                outliers = df_clean[(df_clean[col] < lower) | (df_clean[col] > upper)]
                df_clean = df_clean[(df_clean[col] >= lower) & (df_clean[col] <= upper)]
                total_removed += len(outliers)
                
            elif method == 'zscore':
                z_scores = np.abs(stats.zscore(df_clean[col].dropna()))
                outliers = len(z_scores[z_scores > multiplier])
                df_clean = df_clean[np.abs(stats.zscore(df_clean[col])) <= multiplier]
                total_removed += outliers
        
        print(f"Removed {total_removed} outliers")
        print(f"Shape: {df.shape} -> {df_clean.shape}")
        
        return df_clean
    
    def normalize_data(self, df, price_cols=['Open', 'High', 'Low', 'Close']):
        """
        Normalize price and volume data
        """
        df_normalized = df.copy()
        
        # Normalize price columns
        self.price_scaler = self._get_scaler()
        df_normalized[price_cols] = self.price_scaler.fit_transform(df[price_cols])
        
        # Normalize volume (log transform first for better distribution)
        if 'Volume' in df.columns:
            df_normalized['Volume_log'] = np.log1p(df['Volume'])
            self.volume_scaler = self._get_scaler()
            df_normalized['Volume_scaled'] = self.volume_scaler.fit_transform(
                df_normalized[['Volume_log']]
            )
            df_normalized = df_normalized.drop(['Volume', 'Volume_log'], axis=1)
        
        self.is_fitted = True
        print(f"Data normalized using {self.scaler_type} scaler")
        
        return df_normalized
    
    def create_sequences(self, data, sequence_length=60, step=1):
        """
        Create sequences for time series analysis
        
        Parameters:
        -----------
        data : pd.DataFrame or np.array
            Input data
        sequence_length : int
            Length of each sequence
        step : int
            Step size between sequences
        """
        if isinstance(data, pd.DataFrame):
            data = data.values
            
        sequences = []
        timestamps = []
        
        for i in range(0, len(data) - sequence_length + 1, step):
            seq = data[i:i+sequence_length]
            sequences.append(seq)
            timestamps.append(i + sequence_length - 1)
        
        print(f"Created {len(sequences)} sequences of length {sequence_length}")
        
        return np.array(sequences), timestamps
    
    def split_data(self, X, y=None, train_ratio=0.7, val_ratio=0.15, test_ratio=0.15):
        """
        Split data into train/validation/test sets
        
        Parameters:
        -----------
        X : array-like
            Features
        y : array-like (optional)
            Targets
        train_ratio, val_ratio, test_ratio : float
            Split ratios (must sum to 1)
        """
        assert train_ratio + val_ratio + test_ratio == 1.0, "Ratios must sum to 1"
        
        n = len(X)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        if y is None:
            X_train, X_val, X_test = X[:train_end], X[train_end:val_end], X[val_end:]
            return X_train, X_val, X_test
        else:
            X_train = X[:train_end]
            X_val = X[train_end:val_end]
            X_test = X[val_end:]
            y_train = y[:train_end]
            y_val = y[train_end:val_end]
            y_test = y[val_end:]
            return X_train, X_val, X_test, y_train, y_val, y_test
    
    def save_scalers(self, path_prefix='models_saved/'):
        """Save fitted scalers"""
        if self.price_scaler:
            joblib.dump(self.price_scaler, f'{path_prefix}price_scaler.pkl')
        if self.volume_scaler:
            joblib.dump(self.volume_scaler, f'{path_prefix}volume_scaler.pkl')
        print(f"Scalers saved to {path_prefix}")
    
    def load_scalers(self, path_prefix='models_saved/'):
        """Load fitted scalers"""
        import os
        if os.path.exists(f'{path_prefix}price_scaler.pkl'):
            self.price_scaler = joblib.load(f'{path_prefix}price_scaler.pkl')
        if os.path.exists(f'{path_prefix}volume_scaler.pkl'):
            self.volume_scaler = joblib.load(f'{path_prefix}volume_scaler.pkl')
        self.is_fitted = True
        print("Scalers loaded successfully")
    
    def inverse_transform_price(self, data):
        """Convert normalized prices back to original scale"""
        if self.price_scaler is None:
            raise ValueError("Price scaler not fitted. Call normalize_data first.")
        return self.price_scaler.inverse_transform(data)


# Example usage
if __name__ == "__main__":
    # Test preprocessor
    import yfinance as yf
    df = yf.download('EURUSD=X', period='1mo', interval='1h', progress=False)
    df.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    
    preprocessor = Preprocessor(scaler_type='robust')
    df_clean = preprocessor.handle_missing_values(df)
    df_clean = preprocessor.remove_outliers(df_clean)
    df_norm = preprocessor.normalize_data(df_clean)
    
    print(f"Original: {df.shape}, Normalized: {df_norm.shape}")
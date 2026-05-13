# src/preprocess.py
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import joblib

class Preprocessor:
    def __init__(self, seq_length=60):
        self.seq_length = seq_length
        self.scaler = None
    
    def prepare_data(self, df, features, valid_split=0.2, target_col='future_return'):
        """Prepare data for training"""
        # Normalize features
        self.scaler = MinMaxScaler()
        scaled_data = self.scaler.fit_transform(df[features].values)
        
        # Get target
        target = df[target_col].values
        
        # Create sequences
        X, y = [], []
        for i in range(len(scaled_data) - self.seq_length):
            X.append(scaled_data[i:i+self.seq_length])
            y.append(target[i+self.seq_length])
        
        X = np.array(X)
        y = np.array(y)
        
        # Split
        split_idx = int(len(X) * (1 - valid_split))
        X_train, X_valid = X[:split_idx], X[split_idx:]
        y_train, y_valid = y[:split_idx], y[split_idx:]
        
        return X_train, y_train, X_valid, y_valid, self.scaler
    
    def save_scaler(self, path):
        joblib.dump(self.scaler, path)
    
    def load_scaler(self, path):
        self.scaler = joblib.load(path)
        return self.scaler
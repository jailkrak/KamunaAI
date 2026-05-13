import numpy as np
from sklearn.preprocessing import MinMaxScaler

def create_sequences(data, seq_length=60):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(data[i+seq_length, -1])  # target = close price or signal
    return np.array(X), np.array(y)

def normalize_data(df, columns=['Close', 'Volume', 'rsi']):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[columns])
    return scaled, scaler
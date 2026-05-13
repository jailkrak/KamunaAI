"""
LSTM Model Module - Long Short-Term Memory for time series analysis
"""

import tensorflow as tf
from tensorflow.keras import layers, Model, Input
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout, BatchNormalization, Bidirectional
import numpy as np


class LSTMModel:
    """
    LSTM model for Forex time series analysis
    """
    
    def __init__(self, input_shape, num_layers=2, units=128, dropout=0.2, bidirectional=False):
        """
        Parameters:
        -----------
        input_shape : tuple
            (sequence_length, n_features)
        num_layers : int
            Number of LSTM layers
        units : int
            Number of units in each LSTM layer
        dropout : float
            Dropout rate
        bidirectional : bool
            Whether to use bidirectional LSTM
        """
        self.input_shape = input_shape
        self.num_layers = num_layers
        self.units = units
        self.dropout = dropout
        self.bidirectional = bidirectional
        self.model = None
        
    def build(self, output_units=1, activation='linear'):
        """
        Build the LSTM model architecture
        """
        model = Sequential()
        
        for i in range(self.num_layers):
            return_sequences = (i < self.num_layers - 1)
            lstm_layer = LSTM(
                self.units,
                return_sequences=return_sequences,
                dropout=self.dropout,
                recurrent_dropout=self.dropout,
                input_shape=self.input_shape if i == 0 else None
            )
            
            if self.bidirectional:
                lstm_layer = Bidirectional(lstm_layer)
            
            model.add(lstm_layer)
            model.add(BatchNormalization())
            model.add(Dropout(self.dropout))
        
        # Dense layers
        model.add(Dense(self.units // 2, activation='relu'))
        model.add(Dropout(self.dropout))
        model.add(Dense(self.units // 4, activation='relu'))
        model.add(Dense(output_units, activation=activation))
        
        self.model = model
        print(f"LSTM model built with {self.model.count_params():,} parameters")
        
        return self.model
    
    def build_multitask(self, num_tasks=4):
        """
        Build multi-task LSTM model
        """
        inputs = Input(shape=self.input_shape)
        
        # Shared LSTM layers
        x = LSTM(self.units, return_sequences=True, dropout=self.dropout)(inputs)
        x = BatchNormalization()(x)
        x = LSTM(self.units // 2, dropout=self.dropout)(x)
        x = BatchNormalization()(x)
        
        # Task-specific heads
        outputs = []
        
        # Task 1: Direction (classification)
        dir_out = Dense(64, activation='relu')(x)
        dir_out = Dropout(self.dropout)(dir_out)
        dir_out = Dense(2, activation='softmax', name='direction')(dir_out)
        outputs.append(dir_out)
        
        # Task 2: Volatility (regression)
        vol_out = Dense(64, activation='relu')(x)
        vol_out = Dense(1, activation='linear', name='volatility')(vol_out)
        outputs.append(vol_out)
        
        # Task 3: Trend strength (regression)
        trend_out = Dense(64, activation='relu')(x)
        trend_out = Dense(1, activation='sigmoid', name='trend')(trend_out)
        outputs.append(trend_out)
        
        self.model = Model(inputs=inputs, outputs=outputs)
        print(f"Multi-task LSTM model built with {self.model.count_params():,} parameters")
        
        return self.model
    
    def compile_model(self, learning_rate=0.001, loss='mse', metrics=['mae']):
        """Compile the model"""
        if self.model is None:
            raise ValueError("Model not built. Call build() first.")
        
        from tensorflow.keras.optimizers import Adam
        optimizer = Adam(learning_rate=learning_rate)
        self.model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        print("Model compiled successfully")
        
    def summary(self):
        """Print model summary"""
        if self.model:
            self.model.summary()
        else:
            print("Model not built yet")


# Example usage
if __name__ == "__main__":
    lstm = LSTMModel(input_shape=(60, 50), num_layers=2, units=128)
    model = lstm.build(output_units=1)
    lstm.summary()
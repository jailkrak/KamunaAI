"""
Training Module - Train AI models for Forex analysis
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model, Input
from tensorflow.keras.callbacks import (EarlyStopping, ModelCheckpoint, 
                                        ReduceLROnPlateau, CSVLogger, TensorBoard)
from tensorflow.keras.optimizers import Adam
import joblib
import os
from datetime import datetime


class Trainer:
    """
    Trainer class for Forex AI models
    """
    
    def __init__(self, model, model_name='forex_model'):
        self.model = model
        self.model_name = model_name
        self.history = None
        self.training_start_time = None
        self.training_end_time = None
        
    def compile_model(self, learning_rate=0.001, loss='mse', metrics=['mae']):
        """
        Compile the model before training
        """
        optimizer = Adam(learning_rate=learning_rate)
        self.model.compile(optimizer=optimizer, loss=loss, metrics=metrics)
        print(f"Model compiled with learning_rate={learning_rate}")
        
    def train(self, X_train, y_train, X_val=None, y_val=None,
              epochs=100, batch_size=32, callbacks=None, verbose=1):
        """
        Train the model
        
        Parameters:
        -----------
        X_train, y_train : Training data
        X_val, y_val : Validation data (optional)
        epochs : Number of epochs
        batch_size : Batch size
        callbacks : List of Keras callbacks
        verbose : Verbosity level
        """
        self.training_start_time = datetime.now()
        
        # Default callbacks
        if callbacks is None:
            callbacks = self._get_default_callbacks()
        
        # Prepare validation data
        validation_data = (X_val, y_val) if X_val is not None else None
        
        print(f"\n{'='*50}")
        print(f"Training {self.model_name}")
        print(f"{'='*50}")
        print(f"Training samples: {len(X_train)}")
        if X_val is not None:
            print(f"Validation samples: {len(X_val)}")
        print(f"Epochs: {epochs}")
        print(f"Batch size: {batch_size}")
        print(f"Start time: {self.training_start_time}")
        print(f"{'='*50}\n")
        
        # Train
        self.history = self.model.fit(
            X_train, y_train,
            validation_data=validation_data,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=verbose
        )
        
        self.training_end_time = datetime.now()
        training_duration = self.training_end_time - self.training_start_time
        
        print(f"\n{'='*50}")
        print(f"Training completed!")
        print(f"End time: {self.training_end_time}")
        print(f"Duration: {training_duration}")
        print(f"{'='*50}")
        
        return self.history
    
    def _get_default_callbacks(self):
        """Create default callbacks for training"""
        callbacks = []
        
        # Create models directory if not exists
        os.makedirs('models_saved', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Model checkpoint
        checkpoint = ModelCheckpoint(
            f'models_saved/{self.model_name}_best.h5',
            monitor='val_loss' if self.model.history and 'val_loss' in self.model.history.history else 'loss',
            save_best_only=True,
            verbose=1
        )
        callbacks.append(checkpoint)
        
        # Early stopping
        early_stop = EarlyStopping(
            monitor='val_loss' if self.model.history and 'val_loss' in self.model.history.history else 'loss',
            patience=15,
            restore_best_weights=True,
            verbose=1
        )
        callbacks.append(early_stop)
        
        # Reduce learning rate
        reduce_lr = ReduceLROnPlateau(
            monitor='val_loss' if self.model.history and 'val_loss' in self.model.history.history else 'loss',
            factor=0.5,
            patience=5,
            min_lr=1e-7,
            verbose=1
        )
        callbacks.append(reduce_lr)
        
        # CSV Logger
        csv_logger = CSVLogger(f'logs/{self.model_name}_training_log.csv', append=True)
        callbacks.append(csv_logger)
        
        # TensorBoard
        tensorboard = TensorBoard(log_dir=f'logs/{self.model_name}_{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        callbacks.append(tensorboard)
        
        return callbacks
    
    def save_model(self, path=None):
        """Save trained model"""
        if path is None:
            path = f'models_saved/{self.model_name}_final.h5'
        
        self.model.save(path)
        print(f"Model saved to {path}")
        
    def load_model(self, path):
        """Load saved model"""
        self.model = keras.models.load_model(path)
        print(f"Model loaded from {path}")
        
    def save_training_history(self, path=None):
        """Save training history to file"""
        if path is None:
            path = f'models_saved/{self.model_name}_history.pkl'
        
        if self.history:
            joblib.dump(self.history.history, path)
            print(f"Training history saved to {path}")
    
    def plot_training_history(self, metrics=None):
        """
        Plot training history
        """
        import matplotlib.pyplot as plt
        
        if self.history is None:
            print("No training history available")
            return
        
        if metrics is None:
            metrics = ['loss']
            if 'mae' in self.history.history:
                metrics.append('mae')
            if 'accuracy' in self.history.history:
                metrics.append('accuracy')
        
        n_metrics = len(metrics)
        fig, axes = plt.subplots(n_metrics, 1, figsize=(12, 4*n_metrics))
        
        if n_metrics == 1:
            axes = [axes]
        
        for i, metric in enumerate(metrics):
            if metric in self.history.history:
                axes[i].plot(self.history.history[metric], label=f'Train {metric}')
                if f'val_{metric}' in self.history.history:
                    axes[i].plot(self.history.history[f'val_{metric}'], label=f'Val {metric}')
                axes[i].set_title(f'{metric.upper()} over epochs')
                axes[i].set_xlabel('Epoch')
                axes[i].set_ylabel(metric.upper())
                axes[i].legend()
                axes[i].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def get_training_summary(self):
        """Get summary of training results"""
        if self.history is None:
            return "No training completed yet"
        
        summary = {
            'model_name': self.model_name,
            'training_start': self.training_start_time,
            'training_end': self.training_end_time,
            'duration': self.training_end_time - self.training_start_time if self.training_end_time else None,
            'final_train_loss': self.history.history['loss'][-1] if 'loss' in self.history.history else None,
            'best_val_loss': min(self.history.history['val_loss']) if 'val_loss' in self.history.history else None,
            'total_params': self.model.count_params()
        }
        
        return summary


class MultiTaskTrainer(Trainer):
    """
    Trainer for multi-task learning models
    """
    
    def __init__(self, model, model_name='multitask_forex_model'):
        super().__init__(model, model_name)
        
    def compile_multitask(self, learning_rate=0.001, loss_weights=None):
        """
        Compile multi-task model with different loss weights
        """
        if loss_weights is None:
            loss_weights = {
                'direction': 0.4,
                'volatility': 0.2,
                'price_level': 0.2,
                'trend_strength': 0.2
            }
        
        optimizer = Adam(learning_rate=learning_rate)
        
        self.model.compile(
            optimizer=optimizer,
            loss={
                'direction': 'sparse_categorical_crossentropy',
                'volatility': 'sparse_categorical_crossentropy',
                'price_level': 'binary_crossentropy',
                'trend_strength': 'mse'
            },
            loss_weights=loss_weights,
            metrics={
                'direction': ['accuracy'],
                'volatility': ['accuracy'],
                'price_level': ['accuracy'],
                'trend_strength': ['mae']
            }
        )
        
        print(f"Multi-task model compiled with loss weights: {loss_weights}")


# Example usage
if __name__ == "__main__":
    # Create a simple model for testing
    model = keras.Sequential([
        layers.LSTM(50, return_sequences=True, input_shape=(60, 10)),
        layers.LSTM(25),
        layers.Dense(1)
    ])
    
    trainer = Trainer(model, model_name='test_model')
    trainer.compile_model(learning_rate=0.001)
    
    # Create dummy data
    X_train = np.random.randn(1000, 60, 10)
    y_train = np.random.randn(1000)
    
    # Train (just for testing structure)
    # trainer.train(X_train, y_train, epochs=2, batch_size=32, verbose=1)
    
    print("Trainer class ready")
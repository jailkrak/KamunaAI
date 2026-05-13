"""
Evaluation module for Trading AI Model
Metrics: MSE, MAE, RMSE, R2, Sharpe Ratio, Max Drawdown, Win Rate
"""

import torch
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class Evaluator:
    def __init__(self, model, device='cuda'):
        self.model = model
        self.device = device
        self.model.eval()
    
    def evaluate(self, X_test, y_test, batch_size=64) -> Dict[str, float]:
        """
        Evaluate model on test data
        Returns dictionary of metrics
        """
        predictions = self.get_predictions(X_test, batch_size)
        targets = y_test.cpu().numpy() if torch.is_tensor(y_test) else y_test
        
        # Basic regression metrics
        mse = mean_squared_error(targets, predictions)
        mae = mean_absolute_error(targets, predictions)
        rmse = np.sqrt(mse)
        r2 = r2_score(targets, predictions)
        
        # Trading-specific metrics
        trading_metrics = self.calculate_trading_metrics(predictions, targets)
        
        # Risk metrics
        risk_metrics = self.calculate_risk_metrics(predictions, targets)
        
        return {
            'mse': mse,
            'mae': mae,
            'rmse': rmse,
            'r2_score': r2,
            **trading_metrics,
            **risk_metrics
        }
    
    def get_predictions(self, X_test, batch_size=64) -> np.ndarray:
        """Get model predictions"""
        self.model.eval()
        predictions = []
        
        if torch.is_tensor(X_test):
            X_test = X_test.to(self.device)
            
            with torch.no_grad():
                for i in range(0, len(X_test), batch_size):
                    batch = X_test[i:i+batch_size]
                    pred = self.model(batch)
                    predictions.append(pred.cpu().numpy())
        else:
            # Handle numpy array input
            with torch.no_grad():
                for i in range(0, len(X_test), batch_size):
                    batch = torch.tensor(X_test[i:i+batch_size], dtype=torch.float32).to(self.device)
                    pred = self.model(batch)
                    predictions.append(pred.cpu().numpy())
        
        return np.concatenate(predictions).flatten()
    
    def calculate_trading_metrics(self, predictions: np.ndarray, targets: np.ndarray) -> Dict[str, float]:
        """Calculate trading-specific performance metrics"""
        
        # Direction accuracy (sign prediction)
        pred_direction = np.sign(predictions)
        true_direction = np.sign(targets)
        direction_accuracy = np.mean(pred_direction == true_direction)
        
        # Profit factor (simplified)
        gross_profit = np.sum(predictions[predictions > 0])
        gross_loss = np.abs(np.sum(predictions[predictions < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe Ratio (annualized)
        returns = predictions.flatten()
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        sharpe_ratio = (mean_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        
        # Win rate
        win_rate = np.mean(predictions > 0) if len(predictions) > 0 else 0
        
        # Average return per trade
        avg_return = np.mean(predictions)
        
        # Hit ratio (for binary classification approach)
        threshold = 0.002  # 0.2% threshold
        correct_buy = np.sum((predictions > threshold) & (targets > threshold))
        correct_sell = np.sum((predictions < -threshold) & (targets < -threshold))
        total_signals = np.sum(np.abs(predictions) > threshold)
        hit_ratio = (correct_buy + correct_sell) / total_signals if total_signals > 0 else 0
        
        return {
            'direction_accuracy': direction_accuracy,
            'profit_factor': profit_factor if profit_factor != float('inf') else 999.999,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'hit_ratio': hit_ratio
        }
    
    def calculate_risk_metrics(self, predictions: np.ndarray, targets: np.ndarray) -> Dict[str, float]:
        """Calculate risk metrics"""
        
        # Maximum Drawdown
        cumulative_returns = np.cumprod(1 + predictions.flatten())
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # Volatility
        volatility = np.std(predictions) * np.sqrt(252)
        
        # Sortino Ratio (downside deviation only)
        downside_returns = predictions[predictions < 0]
        downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0.001
        sortino_ratio = (np.mean(predictions) / downside_std) * np.sqrt(252) if downside_std > 0 else 0
        
        # Calmar Ratio
        calmar_ratio = np.mean(predictions) / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Value at Risk (95% confidence)
        var_95 = np.percentile(predictions, 5)
        
        # Conditional VaR (Expected Shortfall)
        cvar_95 = np.mean(predictions[predictions <= var_95]) if len(predictions[predictions <= var_95]) > 0 else var_95
        
        return {
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'var_95': var_95,
            'cvar_95': cvar_95
        }
    
    def backtest_strategy(self, predictions: np.ndarray, targets: np.ndarray, 
                          initial_capital: float = 10000, 
                          commission: float = 0.001) -> Dict[str, float]:
        """
        Simple backtest simulation
        """
        capital = initial_capital
        position = 0
        trades = []
        
        for i, pred in enumerate(predictions):
            signal = 1 if pred > 0.002 else (-1 if pred < -0.002 else 0)
            
            if signal == 1 and position <= 0:
                # Buy
                if position < 0:
                    # Close short position first
                    capital += position * targets[i]  # Simplified
                position = 1
                trades.append({'type': 'BUY', 'price': targets[i], 'capital': capital})
                
            elif signal == -1 and position >= 0:
                # Sell
                if position > 0:
                    capital += position * targets[i]
                position = -1
                trades.append({'type': 'SELL', 'price': targets[i], 'capital': capital})
        
        # Close any open position
        if position != 0:
            capital += position * targets[-1]
        
        total_return = (capital - initial_capital) / initial_capital
        
        return {
            'final_capital': capital,
            'total_return_pct': total_return * 100,
            'num_trades': len(trades),
            'backtest_completed': True
        }

class CrossValidator:
    """Time series cross validation for trading models"""
    
    def __init__(self, model_factory, n_splits=5):
        self.model_factory = model_factory
        self.n_splits = n_splits
    
    def time_series_split(self, X, y, train_ratio=0.7):
        """Create time-based folds"""
        n_samples = len(X)
        train_size = int(n_samples * train_ratio)
        val_size = (n_samples - train_size) // self.n_splits
        
        folds = []
        for i in range(self.n_splits):
            val_start = train_size + i * val_size
            val_end = val_start + val_size if i < self.n_splits - 1 else n_samples
            
            X_train = X[:val_start]
            y_train = y[:val_start]
            X_val = X[val_start:val_end]
            y_val = y[val_start:val_end]
            
            folds.append((X_train, y_train, X_val, y_val))
        
        return folds
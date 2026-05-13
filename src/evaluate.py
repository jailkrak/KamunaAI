"""
Evaluation Module - Comprehensive evaluation for Forex AI analysis
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             confusion_matrix, classification_report, mean_absolute_error,
                             mean_squared_error, r2_score)
import warnings
warnings.filterwarnings('ignore')


class Evaluator:
    """
    Comprehensive model evaluation for Forex analysis
    """
    
    def __init__(self, model=None):
        self.model = model
        self.predictions = None
        self.true_values = None
        self.metrics = {}
        
    def set_model(self, model):
        """Set model for evaluation"""
        self.model = model
        
    def predict(self, X):
        """Make predictions using the model"""
        if self.model is None:
            raise ValueError("No model set. Call set_model() first.")
        
        self.predictions = self.model.predict(X)
        return self.predictions
    
    def evaluate_classification(self, y_true, y_pred, target_names=None):
        """
        Evaluate classification performance
        """
        if target_names is None:
            target_names = ['Class 0', 'Class 1']
        
        metrics = {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted', zero_division=0),
            'recall': recall_score(y_true, y_pred, average='weighted', zero_division=0),
            'f1_score': f1_score(y_true, y_pred, average='weighted', zero_division=0)
        }
        
        print("="*50)
        print("CLASSIFICATION METRICS")
        print("="*50)
        for metric, value in metrics.items():
            print(f"{metric}: {value:.4f}")
        
        print("\nClassification Report:")
        print(classification_report(y_true, y_pred, target_names=target_names))
        
        return metrics
    
    def evaluate_regression(self, y_true, y_pred):
        """
        Evaluate regression performance
        """
        metrics = {
            'mae': mean_absolute_error(y_true, y_pred),
            'mse': mean_squared_error(y_true, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_true, y_pred)),
            'r2': r2_score(y_true, y_pred),
            'mape': np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        }
        
        print("="*50)
        print("REGRESSION METRICS")
        print("="*50)
        for metric, value in metrics.items():
            if metric == 'mape':
                print(f"{metric}: {value:.2f}%")
            else:
                print(f"{metric}: {value:.4f}")
        
        return metrics
    
    def plot_confusion_matrix(self, y_true, y_pred, title="Confusion Matrix"):
        """Plot confusion matrix"""
        cm = confusion_matrix(y_true, y_pred)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', square=True)
        plt.title(title)
        plt.xlabel('Predicted')
        plt.ylabel('Actual')
        plt.show()
        
        return cm
    
    def plot_predictions_vs_actual(self, y_true, y_pred, title="Predictions vs Actual"):
        """Plot predictions against actual values"""
        plt.figure(figsize=(15, 6))
        plt.plot(y_true[:200], label='Actual', alpha=0.7, linewidth=1.5)
        plt.plot(y_pred[:200], label='Predicted', alpha=0.7, linewidth=1.5)
        plt.title(title)
        plt.xlabel('Time Step')
        plt.ylabel('Value')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()
    
    def plot_residuals(self, y_true, y_pred):
        """Plot residuals analysis"""
        residuals = y_true - y_pred
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # Residuals over time
        axes[0,0].plot(residuals[:200])
        axes[0,0].axhline(y=0, color='r', linestyle='--')
        axes[0,0].set_title('Residuals over Time')
        axes[0,0].set_xlabel('Time Step')
        axes[0,0].set_ylabel('Residual')
        axes[0,0].grid(True, alpha=0.3)
        
        # Residuals histogram
        axes[0,1].hist(residuals, bins=50, edgecolor='black', alpha=0.7)
        axes[0,1].set_title('Residuals Distribution')
        axes[0,1].set_xlabel('Residual')
        axes[0,1].set_ylabel('Frequency')
        
        # Q-Q plot
        from scipy import stats
        stats.probplot(residuals, dist="norm", plot=axes[1,0])
        axes[1,0].set_title('Q-Q Plot')
        
        # Residuals vs Predicted
        axes[1,1].scatter(y_pred, residuals, alpha=0.5)
        axes[1,1].axhline(y=0, color='r', linestyle='--')
        axes[1,1].set_title('Residuals vs Predicted')
        axes[1,1].set_xlabel('Predicted Values')
        axes[1,1].set_ylabel('Residuals')
        axes[1,1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
        
        # Residual statistics
        print("\nResidual Statistics:")
        print(f"Mean: {np.mean(residuals):.6f}")
        print(f"Std: {np.std(residuals):.6f}")
        print(f"Skewness: {stats.skew(residuals):.4f}")
        print(f"Kurtosis: {stats.kurtosis(residuals):.4f}")
        
        return residuals
    
    def backtest_strategy(self, df, predictions_direction, initial_capital=10000, 
                          position_size=0.01):
        """
        Backtest trading strategy based on predictions
        
        Parameters:
        -----------
        df : DataFrame with 'Close' prices
        predictions_direction : array of predictions (0=down, 1=up)
        initial_capital : Initial capital amount
        position_size : Position size as fraction of capital (0.01 = 1%)
        """
        capital = initial_capital
        trades = []
        equity_curve = [initial_capital]
        
        for i, pred in enumerate(predictions_direction):
            if i >= len(df) - 1:
                break
            
            current_price = df['Close'].iloc[i]
            next_price = df['Close'].iloc[i+1]
            
            if pred == 1:  # Predict Up - Buy
                daily_return = (next_price - current_price) / current_price
            else:  # Predict Down - Short
                daily_return = -(next_price - current_price) / current_price
            
            # Apply position size
            position_value = capital * position_size
            profit = position_value * daily_return
            capital += profit
            
            equity_curve.append(capital)
            
            trades.append({
                'date': df.index[i],
                'prediction': pred,
                'actual_return': daily_return,
                'profit': profit,
                'capital': capital
            })
        
        trades_df = pd.DataFrame(trades)
        returns = trades_df['actual_return'].values
        
        # Calculate metrics
        total_return = (capital - initial_capital) / initial_capital
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        win_rate = len(trades_df[trades_df['profit'] > 0]) / len(trades_df)
        
        results = {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown * 100,
            'win_rate': win_rate,
            'total_trades': len(trades_df)
        }
        
        print("="*50)
        print("BACKTESTING RESULTS")
        print("="*50)
        print(f"Initial Capital: ${initial_capital:,.2f}")
        print(f"Final Capital: ${capital:,.2f}")
        print(f"Total Return: {total_return*100:.2f}%")
        print(f"Sharpe Ratio: {sharpe_ratio:.3f}")
        print(f"Max Drawdown: {max_drawdown*100:.2f}%")
        print(f"Win Rate: {win_rate*100:.2f}%")
        print(f"Total Trades: {len(trades_df)}")
        
        return results, trades_df, equity_curve
    
    def _calculate_max_drawdown(self, equity_curve):
        """Calculate maximum drawdown"""
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (peak - equity_curve) / peak
        return np.max(drawdown)
    
    def plot_equity_curve(self, equity_curve, benchmark_returns=None):
        """Plot equity curve"""
        plt.figure(figsize=(14, 6))
        plt.plot(equity_curve, label='Strategy Equity', linewidth=2)
        
        if benchmark_returns is not None:
            benchmark_equity = 10000 * (1 + np.cumsum(benchmark_returns))
            plt.plot(benchmark_equity, label='Buy & Hold', linewidth=2, alpha=0.7)
        
        plt.title('Equity Curve')
        plt.xlabel('Trade Number')
        plt.ylabel('Capital ($)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.show()
    
    def compare_models(self, models_dict, X_test, y_test):
        """
        Compare multiple models
        
        Parameters:
        -----------
        models_dict : dict
            {'model_name': model_object}
        X_test, y_test : Test data
        """
        comparisons = {}
        
        for name, model in models_dict.items():
            print(f"\nEvaluating {name}...")
            predictions = model.predict(X_test)
            
            if len(y_test.shape) > 1 and y_test.shape[1] > 1:
                # Multi-output
                metrics = self.evaluate_regression(y_test[:, 0], predictions[:, 0])
            else:
                metrics = self.evaluate_regression(y_test, predictions)
            
            comparisons[name] = metrics
        
        # Create comparison DataFrame
        comparison_df = pd.DataFrame(comparisons).T
        print("\n" + "="*50)
        print("MODEL COMPARISON")
        print("="*50)
        print(comparison_df)
        
        return comparison_df
    
    def calculate_market_metrics(self, df):
        """
        Calculate market-specific metrics for analysis
        """
        metrics = {
            'total_return': (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0],
            'annualized_volatility': df['Close'].pct_change().std() * np.sqrt(252),
            'max_drawdown': self._calculate_max_drawdown(df['Close'].values),
            'avg_true_range': self._calculate_atr(df).mean(),
            'average_daily_range': (df['High'] - df['Low']).mean()
        }
        
        return metrics
    
    def _calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        
        return atr


# Example usage
if __name__ == "__main__":
    # Test evaluator
    evaluator = Evaluator()
    
    # Dummy data for testing
    y_true = np.random.randint(0, 2, 1000)
    y_pred = np.random.randint(0, 2, 1000)
    
    evaluator.evaluate_classification(y_true, y_pred)
    evaluator.plot_confusion_matrix(y_true, y_pred)
    
    print("Evaluator class ready")
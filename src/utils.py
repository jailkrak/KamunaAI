"""
Utility Functions - Helper functions for Forex AI project
"""

import os
import json
import yaml
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import warnings
warnings.filterwarnings('ignore')


class Utils:
    """
    Utility functions for Forex AI project
    """
    
    @staticmethod
    def save_config(config, filepath='config.yaml'):
        """Save configuration to YAML file"""
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        print(f"Config saved to {filepath}")
    
    @staticmethod
    def load_config(filepath='config.yaml'):
        """Load configuration from YAML file"""
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)
        print(f"Config loaded from {filepath}")
        return config
    
    @staticmethod
    def save_json(data, filepath):
        """Save data to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4, default=str)
        print(f"Data saved to {filepath}")
    
    @staticmethod
    def load_json(filepath):
        """Load data from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f"Data loaded from {filepath}")
        return data
    
    @staticmethod
    def create_directory(path):
        """Create directory if it doesn't exist"""
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"Directory created: {path}")
        return path
    
    @staticmethod
    def get_file_size(filepath):
        """Get file size in MB"""
        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / (1024 * 1024)
        return size_mb
    
    @staticmethod
    def calculate_metrics_breakdown(y_true, y_pred):
        """Calculate detailed metrics breakdown"""
        from sklearn.metrics import confusion_matrix
        
        cm = confusion_matrix(y_true, y_pred)
        
        if cm.shape == (2, 2):
            tn, fp, fn, tp = cm.ravel()
            
            metrics = {
                'true_positive': tp,
                'true_negative': tn,
                'false_positive': fp,
                'false_negative': fn,
                'sensitivity': tp / (tp + fn) if (tp + fn) > 0 else 0,
                'specificity': tn / (tn + fp) if (tn + fp) > 0 else 0,
                'precision': tp / (tp + fp) if (tp + fp) > 0 else 0,
                'accuracy': (tp + tn) / (tp + tn + fp + fn)
            }
        else:
            metrics = {'error': 'Non-binary classification'}
        
        return metrics
    
    @staticmethod
    def calculate_profit_factor(trades_df):
        """Calculate profit factor from trades"""
        gross_profit = trades_df[trades_df['profit'] > 0]['profit'].sum()
        gross_loss = abs(trades_df[trades_df['profit'] < 0]['profit'].sum())
        
        if gross_loss == 0:
            return float('inf')
        
        return gross_profit / gross_loss
    
    @staticmethod
    def calculate_calmar_ratio(returns, max_drawdown):
        """Calculate Calmar ratio"""
        annualized_return = returns.mean() * 252
        if max_drawdown == 0:
            return float('inf')
        return annualized_return / abs(max_drawdown)
    
    @staticmethod
    def get_trading_hours_data(df, hour_start=8, hour_end=17):
        """
        Filter data for specific trading hours (e.g., London/New York session)
        """
        df_hours = df[df.index.hour.between(hour_start, hour_end)]
        print(f"Filtered to trading hours: {len(df_hours)} rows")
        return df_hours
    
    @staticmethod
    def calculate_risk_metrics(returns, risk_free_rate=0.02):
        """Calculate advanced risk metrics"""
        # Sharpe ratio
        excess_returns = returns - risk_free_rate / 252
        sharpe = np.sqrt(252) * excess_returns.mean() / returns.std() if returns.std() > 0 else 0
        
        # Sortino ratio (downside deviation)
        negative_returns = returns[returns < 0]
        downside_std = negative_returns.std()
        sortino = np.sqrt(252) * returns.mean() / downside_std if downside_std > 0 else 0
        
        # Maximum drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # VaR (95% confidence)
        var_95 = np.percentile(returns, 5)
        
        # CVaR (Conditional VaR)
        cvar_95 = returns[returns <= var_95].mean()
        
        metrics = {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'max_drawdown': max_drawdown,
            'var_95': var_95,
            'cvar_95': cvar_95
        }
        
        return metrics
    
    @staticmethod
    def generate_experiment_id():
        """Generate unique experiment ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_hash = hashlib.md5(str(np.random.random()).encode()).hexdigest()[:6]
        return f"exp_{timestamp}_{random_hash}"
    
    @staticmethod
    def log_experiment(experiment_id, params, results):
        """Log experiment parameters and results"""
        log_dir = Utils.create_directory('experiment_logs')
        log_file = os.path.join(log_dir, f'{experiment_id}.json')
        
        log_data = {
            'experiment_id': experiment_id,
            'timestamp': datetime.now().isoformat(),
            'parameters': params,
            'results': results
        }
        
        Utils.save_json(log_data, log_file)
        return log_file
    
    @staticmethod
    def print_section_header(title, char='='):
        """Print formatted section header"""
        print(f"\n{char*60}")
        print(f"{title.center(60)}")
        print(f"{char*60}\n")
    
    @staticmethod
    def memory_usage(obj):
        """Calculate memory usage of an object in MB"""
        if isinstance(obj, pd.DataFrame):
            memory = obj.memory_usage(deep=True).sum() / (1024 * 1024)
        elif isinstance(obj, np.ndarray):
            memory = obj.nbytes / (1024 * 1024)
        else:
            memory = len(str(obj)) / (1024 * 1024)
        
        return memory
    
    @staticmethod
    def reduce_memory_usage(df):
        """Reduce DataFrame memory usage by downcasting numeric columns"""
        start_memory = Utils.memory_usage(df)
        
        for col in df.columns:
            col_type = df[col].dtype
            
            if col_type != 'object':
                c_min = df[col].min()
                c_max = df[col].max()
                
                if str(col_type)[:3] == 'int':
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                else:
                    if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                        df[col] = df[col].astype(np.float16)
                    elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        df[col] = df[col].astype(np.float32)
        
        end_memory = Utils.memory_usage(df)
        saved = start_memory - end_memory
        
        print(f"Memory reduced: {start_memory:.2f}MB -> {end_memory:.2f}MB (Saved {saved:.2f}MB)")
        
        return df
    
    @staticmethod
    def time_decorator(func):
        """Decorator to measure function execution time"""
        def wrapper(*args, **kwargs):
            start = datetime.now()
            result = func(*args, **kwargs)
            end = datetime.now()
            duration = end - start
            print(f"{func.__name__} took {duration.total_seconds():.2f} seconds")
            return result
        return wrapper


# Example usage
if __name__ == "__main__":
    utils = Utils()
    
    # Test config
    config = {
        'project': 'Forex AI',
        'version': '1.0',
        'parameters': {
            'learning_rate': 0.001,
            'batch_size': 32
        }
    }
    
    Utils.save_config(config, 'test_config.yaml')
    loaded_config = Utils.load_config('test_config.yaml')
    print(loaded_config)
    
    # Test experiment logging
    exp_id = Utils.generate_experiment_id()
    print(f"Experiment ID: {exp_id}")
    
    # Test section header
    Utils.print_section_header("FOREX AI ANALYSIS SYSTEM")
    
    print("Utils class ready")
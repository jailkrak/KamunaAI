#!/usr/bin/env python3
"""
Testing script for Trading AI Model
Usage: python scripts/test.py --model outputs/final_model/model.pth --data dataset/test.json
"""

import os
import sys
import json
import argparse
import torch
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model_loader import ModelFactory
from src.evaluate import Evaluator
from src.utils import setup_logger

def parse_args():
    parser = argparse.ArgumentParser(description="Test Trading AI Model")
    parser.add_argument("--model", type=str, default="outputs/final_model/model.pth",
                        help="Path to model checkpoint")
    parser.add_argument("--data", type=str, default="dataset/test.json",
                        help="Path to test data")
    parser.add_argument("--config", type=str, default="configs/model_config.json",
                        help="Model configuration")
    parser.add_argument("--device", type=str, default="cuda")
    return parser.parse_args()

def load_test_data(data_path):
    """Load test data from JSON or CSV"""
    if data_path.endswith('.json'):
        with open(data_path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            X = np.array([sample['features'] for sample in data])
            y = np.array([sample['target'] for sample in data])
        else:
            X = np.array([sample['features'] for sample in data['samples']])
            y = np.array([sample['target'] for sample in data['samples']])
    
    elif data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
        feature_cols = [col for col in df.columns if col not in ['timestamp', 'target']]
        X = df[feature_cols].values
        y = df['target'].values
    
    return torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.float32)

def calculate_trading_metrics(predictions, targets, threshold=0.002):
    """Calculate trading-specific metrics"""
    # Convert to trading signals
    pred_signals = np.where(predictions > threshold, 1, np.where(predictions < -threshold, -1, 0))
    true_signals = np.where(targets > threshold, 1, np.where(targets < -threshold, -1, 0))
    
    # Accuracy of direction
    direction_accuracy = np.mean(pred_signals == true_signals)
    
    # Profit factor (mock calculation)
    gross_profit = np.sum(predictions[predictions > 0])
    gross_loss = np.abs(np.sum(predictions[predictions < 0]))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # Sharpe ratio
    returns = predictions.flatten()
    sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
    
    return {
        'direction_accuracy': direction_accuracy,
        'profit_factor': profit_factor,
        'sharpe_ratio': sharpe,
        'total_return': np.sum(returns),
        'win_rate': np.mean(predictions > 0) if len(predictions) > 0 else 0
    }

def main():
    args = parse_args()
    logger = setup_logger("outputs/logs/test.log")
    
    # Load config
    with open(args.config, 'r') as f:
        model_config = json.load(f)
    
    # Load model
    logger.info(f"Loading model from {args.model}")
    model = ModelFactory.create_model(model_config)
    model.load_state_dict(torch.load(args.model, map_location=args.device))
    model.to(args.device)
    model.eval()
    
    # Load test data
    logger.info(f"Loading test data from {args.data}")
    X_test, y_test = load_test_data(args.data)
    X_test = X_test.to(args.device)
    y_test = y_test.to(args.device)
    
    # Evaluate
    logger.info("Running evaluation...")
    evaluator = Evaluator(model, device=args.device)
    
    # Basic metrics
    basic_metrics = evaluator.evaluate(X_test, y_test, batch_size=64)
    
    # Get predictions
    with torch.no_grad():
        predictions = model(X_test).cpu().numpy()
    targets = y_test.cpu().numpy()
    
    # Trading metrics
    trading_metrics = calculate_trading_metrics(predictions, targets)
    
    # Combine results
    results = {**basic_metrics, **trading_metrics}
    
    # Print results
    logger.info("=" * 50)
    logger.info("TEST RESULTS")
    logger.info("=" * 50)
    for key, value in results.items():
        logger.info(f"{key}: {value:.6f}")
    
    # Save results
    with open("outputs/final_model/test_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info("Testing completed!")

if __name__ == "__main__":
    main()
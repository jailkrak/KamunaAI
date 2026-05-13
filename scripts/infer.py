#!/usr/bin/env python3
"""
Inference script for Trading AI Model
Usage: 
  python scripts/infer.py --input "BTC-USD" --lookback 60
  python scripts/infer.py --input data.csv --output predictions.csv
"""

import os
import sys
import json
import argparse
import torch
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model_loader import ModelFactory
from src.preprocess import Preprocessor
from src.utils import setup_logger

def parse_args():
    parser = argparse.ArgumentParser(description="Inference for Trading AI")
    parser.add_argument("--input", type=str, required=True,
                        help="Symbol (e.g., BTC-USD) or path to CSV file")
    parser.add_argument("--model", type=str, default="outputs/final_model/model.pth",
                        help="Path to model")
    parser.add_argument("--scaler", type=str, default="outputs/final_model/scaler.pkl",
                        help="Path to scaler")
    parser.add_argument("--output", type=str, default="outputs/predictions/predictions.csv",
                        help="Output path for predictions")
    parser.add_argument("--lookback", type=int, default=60,
                        help="Number of past days to use")
    parser.add_argument("--device", type=str, default="cuda")
    return parser.parse_args()

def fetch_live_data(symbol, lookback_days=60):
    """Fetch live data from Yahoo Finance"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days + 30)  # Extra for indicators
    
    df = yf.download(symbol, start=start_date, end=end_date, progress=False)
    df.reset_index(inplace=True)
    return df

def add_technical_indicators_simple(df):
    """Add basic indicators for live inference"""
    df = df.copy()
    df['returns'] = df['Close'].pct_change()
    df['ma10'] = df['Close'].rolling(10).mean()
    df['ma20'] = df['Close'].rolling(20).mean()
    df['volatility'] = df['returns'].rolling(20).std()
    
    # Simple RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    return df.dropna()

def predict_single(model, scaler, sequence, device='cuda'):
    """Predict single sequence"""
    if scaler is not None:
        sequence = scaler.transform(sequence.reshape(-1, sequence.shape[-1])).reshape(sequence.shape)
    
    input_tensor = torch.tensor(sequence, dtype=torch.float32).unsqueeze(0).to(device)
    
    with torch.no_grad():
        prediction = model(input_tensor).item()
    
    return prediction

def generate_signal(prediction, thresholds=[-0.002, 0.002]):
    """Generate trading signal based on prediction"""
    if prediction < thresholds[0]:
        return "STRONG_SELL"
    elif prediction < 0:
        return "SELL"
    elif prediction < thresholds[1]:
        return "HOLD"
    elif prediction < 0.01:
        return "BUY"
    else:
        return "STRONG_BUY"

def main():
    args = parse_args()
    logger = setup_logger("outputs/logs/inference.log")
    
    # Load model
    logger.info(f"Loading model from {args.model}")
    with open("configs/model_config.json", 'r') as f:
        model_config = json.load(f)
    
    model = ModelFactory.create_model(model_config)
    model.load_state_dict(torch.load(args.model, map_location=args.device))
    model.to(args.device)
    model.eval()
    
    # Load scaler
    preprocessor = Preprocessor()
    scaler = preprocessor.load_scaler(args.scaler) if os.path.exists(args.scaler) else None
    
    # Get data
    if args.input.endswith('.csv'):
        logger.info(f"Loading data from {args.input}")
        df = pd.read_csv(args.input)
    else:
        logger.info(f"Fetching live data for {args.input}")
        df = fetch_live_data(args.input, args.lookback)
    
    # Prepare features
    df = add_technical_indicators_simple(df)
    
    # Get feature columns from model config
    feature_cols = model_config['input_config']['feature_columns']
    available_features = [col for col in feature_cols if col in df.columns]
    
    if len(available_features) < len(feature_cols):
        logger.warning(f"Missing features: {set(feature_cols) - set(available_features)}")
    
    # Create sequence
    data = df[available_features].values[-args.lookback:]
    
    if len(data) < args.lookback:
        logger.error(f"Need {args.lookback} data points, but only have {len(data)}")
        sys.exit(1)
    
    # Predict
    prediction = predict_single(model, scaler, data, args.device)
    signal = generate_signal(prediction)
    
    # Display results
    logger.info("=" * 50)
    logger.info(f"PREDICTION RESULT")
    logger.info("=" * 50)
    logger.info(f"Symbol: {args.input}")
    logger.info(f"Predicted Return: {prediction:.4%}")
    logger.info(f"Signal: {signal}")
    logger.info(f"Confidence: {'High' if abs(prediction) > 0.005 else 'Medium' if abs(prediction) > 0.002 else 'Low'}")
    
    # Save prediction
    result_df = pd.DataFrame([{
        'timestamp': datetime.now().isoformat(),
        'symbol': args.input,
        'prediction': prediction,
        'signal': signal,
        'lookback_days': args.lookback
    }])
    
    result_df.to_csv(args.output, index=False)
    logger.info(f"Prediction saved to {args.output}")

if __name__ == "__main__":
    main()
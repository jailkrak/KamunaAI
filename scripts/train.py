#!/usr/bin/env python3
"""
Training script for Trading AI Model
Usage: python scripts/train.py --config configs/train_config.json
"""

import os
import sys
import json
import argparse
import torch
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import TradingDataLoader
from src.preprocess import Preprocessor
from src.model_loader import ModelFactory
from src.trainer import Trainer
from src.evaluate import Evaluator
from src.utils import setup_logger, save_checkpoint

def parse_args():
    parser = argparse.ArgumentParser(description="Train Trading AI Model")
    parser.add_argument("--config", type=str, default="configs/train_config.json",
                        help="Path to training configuration")
    parser.add_argument("--resume", type=str, default=None,
                        help="Resume from checkpoint")
    parser.add_argument("--device", type=str, default="cuda",
                        help="Device to use (cuda/cpu)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Load configs
    with open(args.config, 'r') as f:
        train_config = json.load(f)
    
    with open("configs/model_config.json", 'r') as f:
        model_config = json.load(f)
    
    # Setup logger
    logger = setup_logger("outputs/logs/train.log")
    logger.info(f"Starting training with config: {args.config}")
    
    # 1. Load and prepare data
    logger.info("Loading trading data...")
    data_loader = TradingDataLoader(
        symbol=train_config['symbol'],
        start_date=train_config['start_date'],
        end_date=train_config['end_date'],
        timeframe=train_config.get('timeframe', '1d')
    )
    
    df = data_loader.fetch_data()
    df = data_loader.add_technical_indicators(df)
    
    # 2. Preprocess
    logger.info("Preprocessing data...")
    preprocessor = Preprocessor(seq_length=train_config['seq_length'])
    X_train, y_train, X_valid, y_valid, scaler = preprocessor.prepare_data(
        df, 
        features=model_config['input_config']['feature_columns'],
        valid_split=train_config['valid_split']
    )
    
    logger.info(f"Train samples: {X_train.shape}, Valid samples: {X_valid.shape}")
    
    # 3. Create model
    logger.info(f"Creating model: {model_config['model_type']}")
    model = ModelFactory.create_model(model_config)
    
    # 4. Train
    trainer = Trainer(
        model=model,
        device=args.device,
        lr=train_config['learning_rate'],
        weight_decay=train_config.get('weight_decay', 1e-5)
    )
    
    best_valid_loss = float('inf')
    patience_counter = 0
    
    for epoch in range(train_config['epochs']):
        # Train one epoch
        train_loss = trainer.train_epoch(
            X_train, y_train, 
            batch_size=train_config['batch_size']
        )
        
        # Validate
        valid_loss = trainer.validate(X_valid, y_valid, batch_size=train_config['batch_size'])
        
        logger.info(f"Epoch {epoch+1}/{train_config['epochs']} - "
                   f"Train Loss: {train_loss:.6f}, Valid Loss: {valid_loss:.6f}")
        
        # Early stopping
        if valid_loss < best_valid_loss:
            best_valid_loss = valid_loss
            patience_counter = 0
            # Save best model
            save_checkpoint(model, trainer.optimizer, epoch, valid_loss, 
                          "outputs/checkpoints/best_model.pth")
            logger.info(f"Saved best model with validation loss: {valid_loss:.6f}")
        else:
            patience_counter += 1
            if patience_counter >= train_config.get('early_stopping', 10):
                logger.info(f"Early stopping triggered after {epoch+1} epochs")
                break
    
    # 5. Evaluate final model
    logger.info("Evaluating model...")
    evaluator = Evaluator(model, device=args.device)
    metrics = evaluator.evaluate(X_valid, y_valid)
    
    logger.info(f"Final metrics: {json.dumps(metrics, indent=2)}")
    
    # 6. Save final model and scaler
    torch.save(model.state_dict(), "outputs/final_model/model.pth")
    preprocessor.save_scaler("outputs/final_model/scaler.pkl")
    
    # Save metrics
    with open("outputs/final_model/metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info("Training completed successfully!")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Training script for Trading AI Model
Compatible with Trainer class that uses DataLoader
"""

import os
import sys
import json
import argparse
import torch
import numpy as np
import pandas as pd
from torch.utils.data import DataLoader, TensorDataset
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import TradingDataLoader
from src.preprocess import Preprocessor
from src.model_loader import LSTMTradingModel

def parse_args():
    parser = argparse.ArgumentParser(description="Train Trading AI Model")
    parser.add_argument("--config", type=str, default="configs/train_config.json",
                        help="Path to training configuration")
    parser.add_argument("--device", type=str, default="cuda",
                        help="Device to use (cuda/cpu)")
    return parser.parse_args()

def main():
    args = parse_args()
    
    # Load config
    with open(args.config, 'r') as f:
        config = json.load(f)
    
    # Load model config
    with open("configs/model_config.json", 'r') as f:
        model_config = json.load(f)
    
    print("="*50)
    print("🚀 TRAINING TRADING AI MODEL")
    print("="*50)
    
    # 1. Load and prepare data
    print("\n📥 Loading data...")
    loader = TradingDataLoader(
        symbol=config['symbol'],
        start_date=config['start_date'],
        end_date=config['end_date']
    )
    
    df = loader.fetch_data()
    df = loader.add_technical_indicators(df)
    print(f"   Data shape: {df.shape}")
    
    # 2. Preprocess
    print("\n🔧 Preprocessing data...")
    preprocessor = Preprocessor(seq_length=config['seq_length'])
    
    feature_cols = model_config['input_config']['feature_columns']
    X_train, y_train, X_valid, y_valid, scaler = preprocessor.prepare_data(
        df,
        features=feature_cols,
        valid_split=config['valid_split'],
        target_col='future_return'
    )
    
    print(f"   Train set: {X_train.shape}")
    print(f"   Valid set: {X_valid.shape}")
    
    # 3. Create DataLoaders
    print("\n📦 Creating DataLoaders...")
    train_dataset = TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32)
    )
    valid_dataset = TensorDataset(
        torch.tensor(X_valid, dtype=torch.float32),
        torch.tensor(y_valid, dtype=torch.float32)
    )
    
    train_loader = DataLoader(
        train_dataset, 
        batch_size=config['batch_size'], 
        shuffle=True  # Shuffle only for training
    )
    valid_loader = DataLoader(
        valid_dataset, 
        batch_size=config['batch_size'], 
        shuffle=False
    )
    
    # 4. Create model
    print("\n🏗️ Creating model...")
    model = LSTMTradingModel(
        input_size=len(feature_cols),
        hidden_size=model_config['lstm_config']['hidden_size'],
        num_layers=model_config['lstm_config']['num_layers'],
        dropout=model_config['lstm_config']['dropout'],
        bidirectional=model_config['lstm_config']['bidirectional']
    )
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    print(f"   Model parameters: {total_params:,}")
    
    # 5. Train
    print("\n🎯 Starting training...")
    device = args.device if torch.cuda.is_available() else 'cpu'
    print(f"   Device: {device}")
    
    # Import your Trainer class
    from src.trainer import Trainer
    
    trainer = Trainer(
        model=model,
        device=device,
        lr=config['learning_rate']
    )
    
    best_valid_loss = float('inf')
    
    for epoch in range(config['epochs']):
        # Train
        train_loss = trainer.train_epoch(train_loader)
        
        # Validate
        model.eval()
        valid_loss = 0
        with torch.no_grad():
            for X_batch, y_batch in valid_loader:
                X_batch = X_batch.float().to(device)
                y_batch = y_batch.float().to(device)
                pred = model(X_batch)
                loss = trainer.criterion(pred.squeeze(), y_batch)
                valid_loss += loss.item()
        
        valid_loss /= len(valid_loader)
        
        print(f"Epoch {epoch+1}/{config['epochs']} - "
              f"Train Loss: {train_loss:.6f}, Valid Loss: {valid_loss:.6f}")
        
        # Save best model
        if valid_loss < best_valid_loss:
            best_valid_loss = valid_loss
            os.makedirs('outputs/checkpoints', exist_ok=True)
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': trainer.optimizer.state_dict(),
                'valid_loss': valid_loss,
            }, 'outputs/checkpoints/best_model.pth')
            print(f"   ✅ Saved best model (loss: {valid_loss:.6f})")
    
    # 6. Save final model
    print("\n💾 Saving final model...")
    os.makedirs('outputs/final_model', exist_ok=True)
    torch.save(model.state_dict(), 'outputs/final_model/model.pth')
    preprocessor.save_scaler('outputs/final_model/scaler.pkl')
    
    # Save config used
    with open('outputs/final_model/training_config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n✅ Training completed successfully!")
    print(f"📁 Model saved to: outputs/final_model/model.pth")
    print(f"📊 Best validation loss: {best_valid_loss:.6f}")

if __name__ == "__main__":
    main()
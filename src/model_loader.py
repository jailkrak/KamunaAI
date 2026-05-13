import json
import torch
import torch.nn as nn

def load_model_config(config_path="configs/model_config.json"):
    with open(config_path, 'r') as f:
        return json.load(f)

class TradingModelFactory:
    @staticmethod
    def create_model(config_path="configs/model_config.json"):
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        model_type = config['model_type']
        
        if model_type == 'LSTM':
            return LSTMTradingModel(
                input_size=config['input_config']['num_features'],
                hidden_size=config['lstm_config']['hidden_size'],
                num_layers=config['lstm_config']['num_layers'],
                dropout=config['lstm_config']['dropout'],
                bidirectional=config['lstm_config']['bidirectional']
            )
        elif model_type == 'Transformer':
            return TransformerTradingModel(
                input_dim=config['input_config']['num_features'],
                d_model=config['transformer_config']['d_model'],
                nhead=config['transformer_config']['nhead'],
                num_layers=config['transformer_config']['num_encoder_layers']
            )
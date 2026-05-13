# កែប្រែ model_loader.py ដើម្បីបន្ថែម LSTMTradingModel
model_path = '/content/KamunaAI/KamunaAI/KamunaAI/src/model_loader.py'

model_content = '''
import torch
import torch.nn as nn

class LSTMTradingModel(nn.Module):
    """LSTM Model for Trading Prediction"""
    
    def __init__(self, input_size=10, hidden_size=128, num_layers=2, dropout=0.2, bidirectional=True):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout,
            bidirectional=bidirectional
        )
        
        lstm_output_size = hidden_size * (2 if bidirectional else 1)
        self.fc = nn.Linear(lstm_output_size, 1)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        lstm_out, (hidden, cell) = self.lstm(x)
        last_output = lstm_out[:, -1, :]
        last_output = self.dropout(last_output)
        output = self.fc(last_output)
        return output


class TransformerTradingModel(nn.Module):
    """Transformer Model for Trading Prediction"""
    
    def __init__(self, input_dim=10, d_model=64, nhead=4, num_layers=3, dropout=0.1):
        super().__init__()
        self.embedding = nn.Linear(input_dim, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, 
            nhead=nhead, 
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.fc_out = nn.Linear(d_model, 1)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x):
        x = self.embedding(x)
        x = self.transformer(x)
        x = self.dropout(x[:, -1, :])
        return self.fc_out(x)


class ModelFactory:
    """Factory class to create models"""
    
    @staticmethod
    def create_model(config):
        model_type = config.get('model_type', 'LSTM')
        
        if model_type == 'LSTM':
            lstm_config = config.get('lstm_config', {})
            return LSTMTradingModel(
                input_size=config['input_config']['num_features'],
                hidden_size=lstm_config.get('hidden_size', 128),
                num_layers=lstm_config.get('num_layers', 2),
                dropout=lstm_config.get('dropout', 0.2),
                bidirectional=lstm_config.get('bidirectional', True)
            )
        elif model_type == 'Transformer':
            transformer_config = config.get('transformer_config', {})
            return TransformerTradingModel(
                input_dim=config['input_config']['num_features'],
                d_model=transformer_config.get('d_model', 64),
                nhead=transformer_config.get('nhead', 4),
                num_layers=transformer_config.get('num_encoder_layers', 3)
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
'''

# Write the file
with open(model_path, 'w') as f:
    f.write(model_content)

print("✅ model_loader.py has been updated with LSTMTradingModel class!")
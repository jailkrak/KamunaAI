import torch
import numpy as np
from tqdm import tqdm

class Trainer:
    def __init__(self, model, device, lr=0.001):
        self.model = model.to(device)
        self.device = device
        self.criterion = torch.nn.MSELoss()  # regression
        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    def train_epoch(self, dataloader):
        self.model.train()
        total_loss = 0
        for X, y in tqdm(dataloader):
            X, y = X.float().to(self.device), y.float().to(self.device)
            self.optimizer.zero_grad()
            pred = self.model(X)
            loss = self.criterion(pred.squeeze(), y)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()
        return total_loss / len(dataloader)
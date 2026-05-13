from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
import numpy as np
from src.model_loader import LSTMTradingModel

app = FastAPI()
model = LSTMTradingModel(input_size=5)
model.load_state_dict(torch.load("outputs/final_model/model.pth", map_location='cpu'))
model.eval()

class TradingRequest(BaseModel):
    features: list  # sequence of last 60 time steps

@app.post("/predict")
def predict(request: TradingRequest):
    try:
        input_tensor = torch.tensor(request.features, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            pred = model(input_tensor).item()
        return {"predicted_price_change": pred, "signal": "BUY" if pred > 0 else "SELL"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
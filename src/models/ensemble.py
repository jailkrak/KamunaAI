"""
Ensemble Model Module - Combine multiple models for better analysis
"""

import numpy as np
from sklearn.ensemble import VotingClassifier, VotingRegressor, RandomForestClassifier
from sklearn.ensemble import StackingClassifier, StackingRegressor


class EnsembleModel:
    """
    Ensemble model combining LSTM, XGBoost, and other models
    """
    
    def __init__(self, model_type='classification'):
        """
        Parameters:
        -----------
        model_type : str
            'classification' or 'regression'
        """
        self.model_type = model_type
        self.models = {}
        self.ensemble = None
        
    def add_model(self, name, model, weight=1):
        """Add a model to the ensemble"""
        self.models[name] = (name, model, weight)
        print(f"Added model: {name}")
        
    def build_voting_ensemble(self):
        """
        Build voting ensemble (majority voting for classification,
        average for regression)
        """
        if self.model_type == 'classification':
            estimators = [(name, model) for name, model, _ in self.models.values()]
            self.ensemble = VotingClassifier(
                estimators=estimators,
                voting='soft'
            )
        else:
            estimators = [(name, model) for name, model, _ in self.models.values()]
            self.ensemble = VotingRegressor(
                estimators=estimators
            )
        
        print(f"Voting ensemble built with {len(self.models)} models")
        return self.ensemble
    
    def build_stacking_ensemble(self, final_estimator=None):
        """
        Build stacking ensemble with meta-learner
        """
        estimators = [(name, model) for name, model, _ in self.models.values()]
        
        if final_estimator is None:
            if self.model_type == 'classification':
                from sklearn.linear_model import LogisticRegression
                final_estimator = LogisticRegression()
            else:
                from sklearn.linear_model import LinearRegression
                final_estimator = LinearRegression()
        
        if self.model_type == 'classification':
            self.ensemble = StackingClassifier(
                estimators=estimators,
                final_estimator=final_estimator,
                cv=5
            )
        else:
            self.ensemble = StackingRegressor(
                estimators=estimators,
                final_estimator=final_estimator,
                cv=5
            )
        
        print(f"Stacking ensemble built with {len(self.models)} models")
        return self.ensemble
    
    def train(self, X_train, y_train):
        """Train the ensemble model"""
        if self.ensemble is None:
            raise ValueError("Ensemble not built. Call build_voting_ensemble() or build_stacking_ensemble()")
        
        self.ensemble.fit(X_train, y_train)
        print("Ensemble training completed")
        
    def predict(self, X):
        """Make predictions"""
        if self.ensemble is None:
            raise ValueError("Ensemble not trained")
        return self.ensemble.predict(X)
    
    def predict_proba(self, X):
        """Predict probabilities (classification only)"""
        if self.model_type == 'classification' and hasattr(self.ensemble, 'predict_proba'):
            return self.ensemble.predict_proba(X)
        else:
            raise ValueError("Probability prediction not available for this ensemble")
    
    def weighted_average_predict(self, X):
        """
        Custom weighted average prediction
        """
        predictions = []
        weights = []
        
        for name, model, weight in self.models.values():
            pred = model.predict(X)
            predictions.append(pred)
            weights.append(weight)
        
        weights = np.array(weights) / sum(weights)
        weighted_pred = np.zeros_like(predictions[0], dtype=float)
        
        for pred, weight in zip(predictions, weights):
            weighted_pred += pred * weight
        
        if self.model_type == 'classification':
            return (weighted_pred > 0.5).astype(int)
        
        return weighted_pred


# Example usage
if __name__ == "__main__":
    ensemble = EnsembleModel(model_type='classification')
    print("Ensemble model ready")
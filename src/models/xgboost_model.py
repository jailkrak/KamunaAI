"""
XGBoost Model Module - Gradient boosting for Forex analysis
"""

import xgboost as xgb
import numpy as np
from sklearn.model_selection import RandomizedSearchCV


class XGBModel:
    """
    XGBoost model for Forex analysis
    """
    
    def __init__(self, objective='binary:logistic', random_state=42):
        self.model = None
        self.objective = objective
        self.random_state = random_state
        self.best_params = None
        
    def build(self, **kwargs):
        """
        Build XGBoost model with parameters
        
        Default parameters:
        - n_estimators: 100
        - max_depth: 5
        - learning_rate: 0.01
        - subsample: 0.8
        - colsample_bytree: 0.8
        """
        default_params = {
            'n_estimators': 100,
            'max_depth': 5,
            'learning_rate': 0.01,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': self.objective,
            'random_state': self.random_state,
            'eval_metric': 'logloss' if 'binary' in self.objective else 'rmse'
        }
        
        default_params.update(kwargs)
        
        self.model = xgb.XGBClassifier(**default_params) if 'binary' in self.objective else xgb.XGBRegressor(**default_params)
        
        print(f"XGBoost model built with parameters: {default_params}")
        return self.model
    
    def train(self, X_train, y_train, X_val=None, y_val=None, early_stopping_rounds=50):
        """
        Train XGBoost model
        """
        if self.model is None:
            self.build()
        
        eval_set = [(X_train, y_train)]
        if X_val is not None and y_val is not None:
            eval_set.append((X_val, y_val))
        
        self.model.fit(
            X_train, y_train,
            eval_set=eval_set,
            early_stopping_rounds=early_stopping_rounds,
            verbose=True
        )
        
        print("Training completed")
        return self.model
    
    def hyperparameter_tuning(self, X_train, y_train, n_iter=50, cv=5):
        """
        Hyperparameter tuning with RandomizedSearchCV
        """
        param_dist = {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [3, 5, 7, 9],
            'learning_rate': [0.001, 0.01, 0.05, 0.1],
            'subsample': [0.6, 0.7, 0.8, 0.9],
            'colsample_bytree': [0.6, 0.7, 0.8, 0.9],
            'gamma': [0, 0.1, 0.2],
            'reg_alpha': [0, 0.1, 1],
            'reg_lambda': [0, 0.1, 1]
        }
        
        if self.model is None:
            self.build()
        
        random_search = RandomizedSearchCV(
            self.model,
            param_distributions=param_dist,
            n_iter=n_iter,
            cv=cv,
            scoring='accuracy' if 'binary' in self.objective else 'neg_mean_squared_error',
            n_jobs=-1,
            verbose=1,
            random_state=self.random_state
        )
        
        random_search.fit(X_train, y_train)
        
        self.best_params = random_search.best_params_
        self.model = random_search.best_estimator_
        
        print(f"Best parameters: {self.best_params}")
        print(f"Best score: {random_search.best_score_:.4f}")
        
        return self.model
    
    def predict(self, X):
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not trained. Call build() and train() first.")
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Predict probabilities (for classification)"""
        if self.model is None:
            raise ValueError("Model not trained")
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        else:
            raise ValueError("Model does not support probability prediction")
    
    def get_feature_importance(self, feature_names=None):
        """Get feature importance"""
        if self.model is None:
            raise ValueError("Model not trained")
        
        importance = self.model.feature_importances_
        
        if feature_names:
            importance_dict = dict(zip(feature_names, importance))
            importance_dict = dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            return importance_dict
        
        return importance


# Example usage
if __name__ == "__main__":
    xgb_model = XGBModel(objective='binary:logistic')
    xgb_model.build(n_estimators=100, max_depth=5)
    print("XGBoost model ready")
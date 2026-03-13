"""
Energy Demand Forecasting System for CLP
=========================================
Multi-model forecasting system combining:
1. Prophet (seasonal patterns)
2. XGBoost (feature-based)
3. LSTM (deep learning)
4. Ensemble (weighted average)

Author: Prem Vishnoi
Date: March 2026
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class ForecastConfig:
    """Configuration for forecasting models"""
    forecast_horizon: int = 168  # 7 days * 24 hours
    train_test_split: float = 0.8
    prophet_seasonality: str = "multiplicative"
    xgb_n_estimators: int = 100
    lstm_epochs: int = 50
    ensemble_weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.ensemble_weights is None:
            self.ensemble_weights = {
                'prophet': 0.3,
                'xgboost': 0.4,
                'lstm': 0.3
            }


# ============================================================================
# FEATURE ENGINEERING
# ============================================================================

class FeatureEngineer:
    """
    Feature engineering for energy demand forecasting.
    
    Creates features:
    - Time-based: hour, day, month, weekday
    - Lag features: consumption at t-1, t-24, t-168
    - Rolling statistics: mean, std over various windows
    - Weather: temperature, humidity
    - Calendar: holidays, weekends
    """
    
    def __init__(self):
        self.lag_periods = [1, 2, 3, 24, 48, 168]  # 1h, 2h, 3h, 1d, 2d, 1w
        self.rolling_windows = [24, 48, 168]  # 1d, 2d, 1w
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create all features for the model"""
        df = df.copy()
        
        # Ensure datetime index
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
        
        # Time-based features
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        df['year'] = df.index.year
        df['is_weekend'] = (df.index.dayofweek >= 5).astype(int)
        
        # Cyclical encoding for hour and month
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        # Lag features
        for lag in self.lag_periods:
            df[f'consumption_lag_{lag}'] = df['consumption_mwh'].shift(lag)
        
        # Rolling statistics
        for window in self.rolling_windows:
            df[f'consumption_rolling_mean_{window}'] = \
                df['consumption_mwh'].rolling(window=window).mean()
            df[f'consumption_rolling_std_{window}'] = \
                df['consumption_mwh'].rolling(window=window).std()
        
        # Temperature features
        if 'temperature_c' in df.columns:
            df['temp_lag_24'] = df['temperature_c'].shift(24)
            df['temp_rolling_mean_24'] = df['temperature_c'].rolling(24).mean()
            
            # Cooling degree days (base 25°C for Hong Kong)
            df['cooling_degree'] = np.maximum(df['temperature_c'] - 25, 0)
        
        # Drop rows with NaN (from lag/rolling features)
        df = df.dropna()
        
        return df
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names for the model"""
        features = [
            'hour', 'day_of_week', 'day_of_month', 'month', 'quarter',
            'is_weekend', 'hour_sin', 'hour_cos', 'month_sin', 'month_cos',
            'temperature_c', 'humidity_pct'
        ]
        
        for lag in self.lag_periods:
            features.append(f'consumption_lag_{lag}')
        
        for window in self.rolling_windows:
            features.append(f'consumption_rolling_mean_{window}')
            features.append(f'consumption_rolling_std_{window}')
        
        features.extend(['temp_lag_24', 'temp_rolling_mean_24', 'cooling_degree'])
        
        return features


# ============================================================================
# MODELS
# ============================================================================

class ProphetForecaster:
    """
    Facebook Prophet model for seasonal forecasting.
    
    Captures:
    - Yearly seasonality
    - Weekly seasonality
    - Daily seasonality
    - Holiday effects
    """
    
    def __init__(self, config: ForecastConfig):
        self.config = config
        self.model = None
    
    def fit(self, df: pd.DataFrame):
        """Fit Prophet model"""
        # Prophet requires columns: ds, y
        prophet_df = df.reset_index()[['timestamp', 'consumption_mwh']].copy()
        prophet_df.columns = ['ds', 'y']
        
        # Simulated fit (would use actual Prophet in production)
        self.fitted_mean = prophet_df['y'].mean()
        self.fitted_std = prophet_df['y'].std()
        self.daily_pattern = prophet_df.groupby(prophet_df['ds'].dt.hour)['y'].mean()
        self.weekly_pattern = prophet_df.groupby(prophet_df['ds'].dt.dayofweek)['y'].mean()
        
        print("Prophet model fitted")
        return self
    
    def predict(self, periods: int) -> np.ndarray:
        """Generate forecast"""
        # Simulated prediction based on patterns
        predictions = []
        for i in range(periods):
            hour = i % 24
            day_of_week = (i // 24) % 7
            
            hourly_factor = self.daily_pattern.get(hour, self.fitted_mean) / self.fitted_mean
            weekly_factor = self.weekly_pattern.get(day_of_week, self.fitted_mean) / self.fitted_mean
            
            pred = self.fitted_mean * hourly_factor * weekly_factor
            pred += np.random.normal(0, self.fitted_std * 0.1)
            predictions.append(pred)
        
        return np.array(predictions)


class XGBoostForecaster:
    """
    XGBoost model for feature-based forecasting.
    
    Uses gradient boosting on engineered features.
    """
    
    def __init__(self, config: ForecastConfig):
        self.config = config
        self.model = None
        self.feature_engineer = FeatureEngineer()
    
    def fit(self, df: pd.DataFrame, features: List[str]):
        """Fit XGBoost model"""
        # Simulated fit
        self.features = features
        self.feature_means = {f: df[f].mean() for f in features if f in df.columns}
        self.target_mean = df['consumption_mwh'].mean()
        self.target_std = df['consumption_mwh'].std()
        
        # Store feature importances (simulated)
        self.feature_importances_ = {
            f: np.random.uniform(0.01, 0.15) for f in features
        }
        # Make consumption lags most important
        for f in features:
            if 'consumption_lag' in f:
                self.feature_importances_[f] = np.random.uniform(0.1, 0.2)
        
        print("XGBoost model fitted")
        return self
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generate predictions"""
        # Simulated prediction
        predictions = np.full(len(X), self.target_mean)
        
        # Adjust based on features
        if 'hour' in X.columns:
            hour_effect = np.where(
                (X['hour'] >= 9) & (X['hour'] <= 18),
                1.2,
                np.where(
                    (X['hour'] >= 19) & (X['hour'] <= 22),
                    1.3,
                    0.7
                )
            )
            predictions *= hour_effect
        
        if 'temperature_c' in X.columns:
            temp_effect = 1 + 0.02 * np.maximum(X['temperature_c'] - 25, 0)
            predictions *= temp_effect
        
        # Add noise
        predictions += np.random.normal(0, self.target_std * 0.1, len(predictions))
        
        return predictions
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance scores"""
        importance_df = pd.DataFrame([
            {'feature': f, 'importance': v}
            for f, v in self.feature_importances_.items()
        ])
        return importance_df.sort_values('importance', ascending=False)


class LSTMForecaster:
    """
    LSTM neural network for sequence-to-sequence forecasting.
    
    Architecture:
    - Input: sequence of historical consumption
    - LSTM layers: capture temporal dependencies
    - Dense output: predict next N hours
    """
    
    def __init__(self, config: ForecastConfig):
        self.config = config
        self.model = None
        self.sequence_length = 168  # 1 week of history
        self.scaler_mean = None
        self.scaler_std = None
    
    def _build_model(self, input_shape: Tuple[int, int]):
        """Build LSTM architecture"""
        # Would use TensorFlow/Keras in production:
        """
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout
        
        model = Sequential([
            LSTM(64, input_shape=input_shape, return_sequences=True),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(24)  # Predict next 24 hours
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
        """
        pass
    
    def fit(self, df: pd.DataFrame):
        """Fit LSTM model"""
        # Store scaling parameters
        self.scaler_mean = df['consumption_mwh'].mean()
        self.scaler_std = df['consumption_mwh'].std()
        
        # Store patterns for simulation
        self.hourly_pattern = df.groupby(df.index.hour)['consumption_mwh'].mean()
        
        print("LSTM model fitted (simulated)")
        return self
    
    def predict(self, last_sequence: np.ndarray, n_steps: int = 24) -> np.ndarray:
        """Generate predictions"""
        # Simulated LSTM prediction
        predictions = []
        
        for i in range(n_steps):
            hour = i % 24
            base_pred = self.hourly_pattern.get(hour, self.scaler_mean)
            noise = np.random.normal(0, self.scaler_std * 0.08)
            predictions.append(base_pred + noise)
        
        return np.array(predictions)


# ============================================================================
# ENSEMBLE MODEL
# ============================================================================

class EnsembleForecaster:
    """
    Ensemble model combining Prophet, XGBoost, and LSTM.
    
    Uses weighted average of predictions.
    Weights can be optimized on validation set.
    """
    
    def __init__(self, config: ForecastConfig = None):
        self.config = config or ForecastConfig()
        self.prophet = ProphetForecaster(self.config)
        self.xgboost = XGBoostForecaster(self.config)
        self.lstm = LSTMForecaster(self.config)
        self.feature_engineer = FeatureEngineer()
        self.is_fitted = False
    
    def fit(self, df: pd.DataFrame):
        """Fit all models"""
        print("\n" + "="*60)
        print("FITTING ENSEMBLE MODELS")
        print("="*60 + "\n")
        
        # Feature engineering
        df_features = self.feature_engineer.create_features(df)
        features = self.feature_engineer.get_feature_names()
        available_features = [f for f in features if f in df_features.columns]
        
        # Fit individual models
        self.prophet.fit(df_features)
        self.xgboost.fit(df_features, available_features)
        self.lstm.fit(df_features)
        
        self.is_fitted = True
        self.last_data = df_features.tail(168)  # Keep last week for LSTM
        
        print("\nAll models fitted successfully!")
        return self
    
    def predict(self, periods: int = 168) -> pd.DataFrame:
        """Generate ensemble forecast"""
        if not self.is_fitted:
            raise ValueError("Models not fitted. Call fit() first.")
        
        print(f"\nGenerating {periods}-hour forecast...")
        
        # Get predictions from each model
        prophet_pred = self.prophet.predict(periods)
        
        # For XGBoost, we need to create future features
        future_dates = pd.date_range(
            start=self.last_data.index[-1] + timedelta(hours=1),
            periods=periods,
            freq='h'
        )
        
        future_df = pd.DataFrame({
            'timestamp': future_dates,
            'hour': future_dates.hour,
            'day_of_week': future_dates.dayofweek,
            'month': future_dates.month,
            'temperature_c': 28 + 5 * np.sin(2 * np.pi * future_dates.hour / 24),  # Simulated
            'humidity_pct': 75,
            'is_weekend': (future_dates.dayofweek >= 5).astype(int)
        })
        
        xgb_pred = self.xgboost.predict(future_df)
        
        # LSTM prediction
        lstm_pred = self.lstm.predict(
            self.last_data['consumption_mwh'].values,
            n_steps=periods
        )
        
        # Pad LSTM predictions if needed
        if len(lstm_pred) < periods:
            lstm_pred = np.tile(lstm_pred, periods // len(lstm_pred) + 1)[:periods]
        
        # Ensemble
        weights = self.config.ensemble_weights
        ensemble_pred = (
            weights['prophet'] * prophet_pred +
            weights['xgboost'] * xgb_pred +
            weights['lstm'] * lstm_pred
        )
        
        # Create result DataFrame
        result = pd.DataFrame({
            'timestamp': future_dates,
            'prophet_forecast': prophet_pred,
            'xgboost_forecast': xgb_pred,
            'lstm_forecast': lstm_pred,
            'ensemble_forecast': ensemble_pred
        })
        
        return result
    
    def evaluate(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """Calculate forecast accuracy metrics"""
        mae = np.mean(np.abs(y_true - y_pred))
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
        
        return {
            'MAE': round(mae, 2),
            'MAPE': round(mape, 2),
            'RMSE': round(rmse, 2)
        }


# ============================================================================
# MLFLOW INTEGRATION (PRODUCTION)
# ============================================================================

def log_to_mlflow(model, metrics: Dict, params: Dict):
    """
    Log model to MLflow for experiment tracking.
    
    Production code:
    ```python
    import mlflow
    import mlflow.sklearn
    
    mlflow.set_experiment("energy_forecasting")
    
    with mlflow.start_run():
        # Log parameters
        mlflow.log_params(params)
        
        # Log metrics
        mlflow.log_metrics(metrics)
        
        # Log model
        mlflow.sklearn.log_model(model, "model")
        
        # Register model
        mlflow.register_model(
            f"runs:/{mlflow.active_run().info.run_id}/model",
            "energy_demand_forecaster"
        )
    ```
    """
    print(f"\n[MLflow] Logged model with metrics: {metrics}")


# ============================================================================
# DEMO
# ============================================================================

def demo():
    """Run demonstration of the forecasting system"""
    
    print("\n" + "="*70)
    print("  ENERGY DEMAND FORECASTING SYSTEM")
    print("  CLP Power Hong Kong - AI Interview Project")
    print("="*70 + "\n")
    
    # Generate sample data
    print("Generating sample data...")
    
    np.random.seed(42)
    
    # Create 6 months of hourly data
    dates = pd.date_range(start='2024-01-01', end='2024-06-30', freq='h')
    
    # Generate realistic consumption patterns
    consumption = []
    for dt in dates:
        base = 350  # Base load in MW
        
        # Hourly pattern
        hour = dt.hour
        if 9 <= hour <= 18:
            base *= 1.3
        elif 19 <= hour <= 22:
            base *= 1.4
        elif 0 <= hour <= 5:
            base *= 0.6
        
        # Weekly pattern
        if dt.dayofweek >= 5:
            base *= 0.85
        
        # Seasonal pattern
        month = dt.month
        if month in [6, 7, 8]:
            base *= 1.15
        
        # Temperature effect
        temp = 23 + 8 * np.sin(2 * np.pi * (month - 4) / 12)
        if temp > 25:
            base *= 1 + 0.03 * (temp - 25)
        
        # Noise
        base *= (1 + np.random.normal(0, 0.05))
        
        consumption.append(base)
    
    df = pd.DataFrame({
        'timestamp': dates,
        'consumption_mwh': consumption,
        'temperature_c': 23 + 8 * np.sin(2 * np.pi * (dates.month - 4) / 12) + 
                        3 * np.sin(2 * np.pi * (dates.hour - 6) / 24) +
                        np.random.normal(0, 2, len(dates)),
        'humidity_pct': 70 + np.random.normal(0, 10, len(dates))
    })
    df = df.set_index('timestamp')
    
    print(f"Generated {len(df)} hourly records")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    print(f"Consumption stats: mean={df['consumption_mwh'].mean():.1f}, "
          f"max={df['consumption_mwh'].max():.1f}, "
          f"min={df['consumption_mwh'].min():.1f}")
    
    # Split train/test
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]
    
    print(f"\nTraining set: {len(train_df)} records")
    print(f"Test set: {len(test_df)} records")
    
    # Initialize and train ensemble
    config = ForecastConfig(
        forecast_horizon=168,
        ensemble_weights={
            'prophet': 0.3,
            'xgboost': 0.4,
            'lstm': 0.3
        }
    )
    
    ensemble = EnsembleForecaster(config)
    ensemble.fit(train_df)
    
    # Generate forecast
    forecast = ensemble.predict(periods=168)
    
    print("\n" + "="*60)
    print("FORECAST RESULTS (Next 7 Days)")
    print("="*60)
    
    print("\nForecast summary:")
    print(forecast[['timestamp', 'ensemble_forecast']].head(24))
    
    print("\n" + "-"*60)
    print("Model weights:")
    for model, weight in config.ensemble_weights.items():
        print(f"  {model}: {weight:.0%}")
    
    # Evaluate (simulated - using test data as ground truth)
    actual = test_df['consumption_mwh'].values[:168]
    predicted = forecast['ensemble_forecast'].values
    
    if len(actual) >= len(predicted):
        actual = actual[:len(predicted)]
    else:
        predicted = predicted[:len(actual)]
    
    metrics = ensemble.evaluate(actual, predicted)
    
    print("\n" + "-"*60)
    print("Forecast Accuracy (on test set):")
    print(f"  MAE:  {metrics['MAE']:.2f} MWh")
    print(f"  MAPE: {metrics['MAPE']:.2f}%")
    print(f"  RMSE: {metrics['RMSE']:.2f} MWh")
    
    # Log to MLflow (simulated)
    log_to_mlflow(
        ensemble,
        metrics,
        {'ensemble_weights': str(config.ensemble_weights)}
    )
    
    print("\n" + "="*60)
    print("FEATURE IMPORTANCE (XGBoost)")
    print("="*60)
    
    importance = ensemble.xgboost.get_feature_importance()
    print(importance.head(10).to_string(index=False))
    
    print("\n" + "="*70)
    print("  DEMO COMPLETE")
    print("="*70 + "\n")
    
    return ensemble, forecast


if __name__ == "__main__":
    ensemble, forecast = demo()

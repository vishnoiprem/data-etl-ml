# v1_failed_approach.py
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler


def train_complex_demand_model(train_data: pd.DataFrame):
    """
    Over-engineered model focused purely on predictive accuracy.
    Ignores business rules and integration needs.
    """
    # Complex feature engineering
    train_data['price_velocity'] = train_data['price'].pct_change(periods=7)
    train_data['lagged_demand_7'] = train_data['demand'].shift(7)
    # ... 20+ more abstract features

    # Drop rows with NaNs from shifts (losing context)
    train_data = train_data.dropna()

    X = train_data.drop(['demand', 'sku_id'], axis=1)  # Dropped ID - no per-SKU explainability
    y = train_data['demand']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Black-box, high-complexity model
    model = XGBRegressor(
        n_estimators=200,
        max_depth=8,
        objective='reg:squarederror',
        random_state=42
    )
    model.fit(X_scaled, y)

    # Returns a model that outputs a single, mysterious number
    return model, scaler

# In production, this would be called as:
# prediction = model.predict(scaler.transform(new_data))
# Ops Team Reaction: "What does '847.3' mean? How do I use this to place an order?"
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Sample dataset
data = {
    'pickup_time': [10, 15, 20, 25, 30],  # Time to prepare food
    'point_to_point_time': [20, 25, 30, 35, 40],  # Travel time
    'drop_off_time': [5, 10, 5, 10, 5],  # Time to hand over food
    'traffic_congestion': [1, 3, 2, 5, 4],  # Traffic condition (1 = low, 5 = high)
    'order_subtotal': [200, 300, 150, 400, 250],  # Total order price
    'actual_delivery_time': [35, 50, 40, 60, 55]  # Target variable (minutes)
}

# Convert to a DataFrame
df = pd.DataFrame(data)

# Features and target
X = df[['pickup_time', 'point_to_point_time', 'drop_off_time', 'traffic_congestion', 'order_subtotal']]
y = df['actual_delivery_time']

# Split into training and test datasets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(df.head())


from xgboost import XGBRegressor
from sklearn.metrics import mean_squared_error

# Initialize the XGBoost Regressor
model = XGBRegressor(objective='reg:squarederror', random_state=42, learning_rate=0.1, n_estimators=100)

# Train the model
model.fit(X_train_scaled, y_train)

# Make predictions
y_train_pred = model.predict(X_train_scaled)
y_test_pred = model.predict(X_test_scaled)

# Evaluate the model
train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

print(f"Train RMSE: {train_rmse:.2f}")
print(f"Test RMSE: {test_rmse:.2f}")
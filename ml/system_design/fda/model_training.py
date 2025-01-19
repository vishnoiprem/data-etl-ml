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
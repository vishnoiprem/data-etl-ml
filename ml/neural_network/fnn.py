import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

# Load retail store data (for example, sales, foot traffic, promotions, etc.)
data = pd.read_csv('retail_data.csv')

print(data.head(5))

# One-hot encode the categorical columns (e.g., 'weather' and 'day_of_week')
data = pd.get_dummies(data, columns=['weather', 'day_of_week'], drop_first=True)
print(data.head(5))

corr_matrix = data.corr()
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm')
plt.title("Feature Correlation Heatmap")
plt.show()

data.hist(bins=30, figsize=(10, 8))
plt.suptitle("Feature Distributions")
plt.show()


# Preprocess the data
X = data.drop('sales', axis=1)  # Features (foot_traffic, promotion, etc.)
y = data['sales']  # Target variable (sales)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)



# Scale the features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Build the Feedforward Neural Network model
model = Sequential()

# Input layer with 64 neurons, hidden layers, and output layer
model.add(Dense(units=64, activation='relu', input_dim=X_train_scaled.shape[1]))  # Input layer
model.add(Dense(units=32, activation='relu'))  # Hidden layer
model.add(Dense(units=1, activation='linear'))  # Output layer for regression

# Compile the model
model.compile(optimizer='adam', loss='mean_squared_error')

# Train the model
model.fit(X_train_scaled, y_train, epochs=100, batch_size=32)

history = model.fit(X_train_scaled, y_train, epochs=100, batch_size=32, verbose=0)
plt.plot(history.history['loss'])
plt.title('Model Loss over Epochs')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.show()


# Evaluate the model
loss = model.evaluate(X_test_scaled, y_test)
print(f'Model Loss: {loss}')

# Make predictions
predictions = model.predict(X_test_scaled)


# Predictions vs actual sales
plt.scatter(y_test, predictions)
plt.title('Predicted vs Actual Sales')
plt.xlabel('Actual Sales')
plt.ylabel('Predicted Sales')
plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], color='red')  # Line for perfect predictions
plt.show()


# Residuals
residuals = y_test - predictions.flatten()
plt.scatter(predictions, residuals)
plt.title('Residuals Plot')
plt.xlabel('Predicted Sales')
plt.ylabel('Residuals')
plt.axhline(0, color='red')
plt.show()


from tensorflow.keras.utils import plot_model
plot_model(model, to_file='model_architecture.png', show_shapes=True)


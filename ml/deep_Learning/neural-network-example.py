# Comprehensive Neural Network Implementation for Student Grade Prediction
# This example demonstrates a neural network that predicts college GPA based on SAT scores and high school GPA

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# Part 1: Data Preparation
# ----------------------
# We'll create a synthetic dataset of student performance metrics
# Each student has: SAT score, high school GPA, and first-year college GPA (target)

def create_student_dataset(num_students=100):
    """
    Creates a synthetic dataset of student performance metrics.
    
    The data follows these general patterns:
    - SAT scores range from 400 to 800 per section (800-1600 total)
    - High school GPA ranges from 2.0 to 4.0
    - College GPA tends to correlate with both metrics but includes some randomness
    """
    np.random.seed(42)  # For reproducibility
    
    # Generate SAT scores (roughly normally distributed around 1200)
    sat_scores = np.random.normal(1200, 150, num_students)
    sat_scores = np.clip(sat_scores, 800, 1600)
    
    # Generate high school GPAs (roughly normally distributed around 3.5)
    hs_gpas = np.random.normal(3.5, 0.3, num_students)
    hs_gpas = np.clip(hs_gpas, 2.0, 4.0)
    
    # Generate college GPAs with some correlation to input features
    # We'll use a weighted combination plus some random noise
    college_gpas = (
        0.4 * (sat_scores - 800) / 800 +  # Normalized SAT contribution
        0.4 * hs_gpas +                   # High school GPA contribution
        np.random.normal(0, 0.2, num_students)  # Random variation
    )
    college_gpas = np.clip(college_gpas, 2.0, 4.0)
    
    return pd.DataFrame({
        'sat_score': sat_scores,
        'hs_gpa': hs_gpas,
        'college_gpa': college_gpas
    })

# Part 2: Data Preprocessing
# -------------------------
def prepare_data(df):
    """
    Prepares the data for neural network training by:
    1. Splitting into training and testing sets
    2. Scaling the features to have zero mean and unit variance
    """
    # Split features (X) and target (y)
    X = df[['sat_score', 'hs_gpa']]
    y = df['college_gpa']
    
    # Split into training and testing sets (80-20 split)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Scale the features
    # This is crucial for neural networks as it helps with convergence
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler

# Part 3: Neural Network Model
# ---------------------------
def create_model():
    """
    Creates a neural network model with:
    - Input layer: 2 neurons (SAT score, HS GPA)
    - Hidden layer: 4 neurons with ReLU activation
    - Output layer: 1 neuron (predicted college GPA)
    """
    model = keras.Sequential([
        # First hidden layer with ReLU activation
        keras.layers.Dense(
            units=4,
            activation='relu',
            input_shape=(2,),
            kernel_initializer='he_normal'
        ),
        
        # Output layer (linear activation for regression)
        keras.layers.Dense(
            units=1,
            activation='linear',
            kernel_initializer='glorot_normal'
        )
    ])
    
    # Compile model with mean squared error loss
    # Adam optimizer is a good default choice for most problems
    model.compile(
        optimizer='adam',
        loss='mean_squared_error',
        metrics=['mae']
    )
    
    return model

# Part 4: Training and Visualization
# --------------------------------
def train_and_visualize(model, X_train, X_test, y_train, y_test):
    """
    Trains the model and creates visualizations of the training process
    and predictions.
    """
    # Train the model
    history = model.fit(
        X_train, y_train,
        epochs=100,
        batch_size=32,
        validation_data=(X_test, y_test),
        verbose=0
    )
    
    # Create training history plot
    plt.figure(figsize=(10, 5))
    
    # Plot training & validation loss
    plt.subplot(1, 2, 1)
    plt.plot(history.history['loss'], label='Training Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Model Loss Over Time')
    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.legend()
    
    # Plot predictions vs actual values
    plt.subplot(1, 2, 2)
    y_pred = model.predict(X_test)
    plt.scatter(y_test, y_pred, alpha=0.5)
    plt.plot([2, 4], [2, 4], 'r--')  # Perfect prediction line
    plt.title('Predicted vs Actual GPA')
    plt.xlabel('Actual GPA')
    plt.ylabel('Predicted GPA')
    
    plt.tight_layout()
    plt.show()
    
    return y_pred

# Part 5: Main Execution
# ---------------------
def main():
    # Create dataset
    print("Creating dataset...")
    df = create_student_dataset()
    
    # Prepare data
    print("Preparing data...")
    X_train, X_test, y_train, y_test, scaler = prepare_data(df)
    
    # Create and train model
    print("Creating and training model...")
    model = create_model()
    y_pred = train_and_visualize(model, X_train, X_test, y_train, y_test)
    
    # Print sample predictions
    print("\nSample Predictions:")
    for actual, predicted in zip(y_test[:5], y_pred[:5]):
        print(f"Actual GPA: {actual:.2f}, Predicted GPA: {predicted[0]:.2f}")
    
    # Example of using the model for new predictions
    print("\nExample Prediction for New Student:")
    new_student = np.array([[1400, 3.8]])  # SAT score: 1400, HS GPA: 3.8
    new_student_scaled = scaler.transform(new_student)
    prediction = model.predict(new_student_scaled)
    print(f"Predicted College GPA: {prediction[0][0]:.2f}")

if __name__ == "__main__":
    main()

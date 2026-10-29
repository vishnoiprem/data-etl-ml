import numpy as np
import matplotlib.pyplot as plt
import torch
import torch.nn as nn

class LossFunctions:
    """
    A comprehensive implementation of common loss functions
    with practical examples and visualizations.
    """
    
    @staticmethod
    def binary_cross_entropy(y_true, y_pred, epsilon=1e-15):
        """
        Binary Cross-Entropy Loss
        For binary classification problems (e.g., spam detection)
        
        Args:
            y_true: True labels (0 or 1)
            y_pred: Predicted probabilities
            epsilon: Small number to avoid log(0)
        """
        # Clip predictions to avoid log(0)
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        
        # Calculate BCE loss
        loss = -(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
        return np.mean(loss)

    @staticmethod
    def mean_squared_error(y_true, y_pred):
        """
        Mean Squared Error Loss
        For regression problems (e.g., house price prediction)
        
        Args:
            y_true: True values
            y_pred: Predicted values
        """
        return np.mean((y_true - y_pred) ** 2)

    @staticmethod
    def mean_absolute_error(y_true, y_pred):
        """
        Mean Absolute Error Loss
        For regression problems where outliers should have less impact
        
        Args:
            y_true: True values
            y_pred: Predicted values
        """
        return np.mean(np.abs(y_true - y_pred))

    @staticmethod
    def plot_loss_comparison(y_true, y_pred, title="Loss Comparison"):
        """
        Visualize different loss functions for the same predictions
        """
        plt.figure(figsize=(15, 5))
        
        # Calculate losses
        mse = ((y_true - y_pred) ** 2)
        mae = np.abs(y_true - y_pred)
        
        # Plot MSE
        plt.subplot(131)
        plt.scatter(y_true, mse, c='blue', alpha=0.5)
        plt.title('MSE Loss')
        plt.xlabel('True Values')
        plt.ylabel('Loss')
        
        # Plot MAE
        plt.subplot(132)
        plt.scatter(y_true, mae, c='red', alpha=0.5)
        plt.title('MAE Loss')
        plt.xlabel('True Values')
        plt.ylabel('Loss')
        
        # Plot Comparison
        plt.subplot(133)
        plt.scatter(y_true, mse, c='blue', alpha=0.5, label='MSE')
        plt.scatter(y_true, mae, c='red', alpha=0.5, label='MAE')
        plt.title('MSE vs MAE')
        plt.xlabel('True Values')
        plt.ylabel('Loss')
        plt.legend()
        
        plt.tight_layout()
        plt.show()

# Example 1: Binary Classification (Spam Detection)
def spam_detection_example():
    """Demonstrate Binary Cross-Entropy loss with spam detection"""
    # True labels (1 = spam, 0 = not spam)
    y_true = np.array([1, 0, 1, 0, 1])
    
    # Model predictions (probabilities of being spam)
    y_pred = np.array([0.9, 0.1, 0.8, 0.2, 0.7])
    
    loss = LossFunctions.binary_cross_entropy(y_true, y_pred)
    print(f"Spam Detection BCE Loss: {loss:.4f}")
    
    # Show predictions vs actual
    for true, pred in zip(y_true, y_pred):
        status = "SPAM" if true == 1 else "NOT SPAM"
        print(f"True: {status}, Predicted Probability: {pred:.2f}")

# Example 2: Regression (House Price Prediction)
def house_price_example():
    """Demonstrate MSE and MAE with house price prediction"""
    # True house prices (in thousands)
    y_true = np.array([200, 250, 300, 280, 220])
    
    # Predicted house prices
    y_pred = np.array([190, 260, 290, 275, 210])
    
    mse = LossFunctions.mean_squared_error(y_true, y_pred)
    mae = LossFunctions.mean_absolute_error(y_true, y_pred)
    
    print(f"\nHouse Price Prediction:")
    print(f"MSE Loss: {mse:.2f}")
    print(f"MAE Loss: {mae:.2f}")
    
    # Show predictions vs actual
    print("\nDetailed Predictions:")
    for true, pred in zip(y_true, y_pred):
        error = abs(true - pred)
        print(f"True: ${true}k, Predicted: ${pred}k, Error: ${error}k")

# Example 3: Temperature Prediction Exercise
def temperature_prediction_exercise():
    """Interactive exercise for understanding loss functions"""
    temperatures = np.array([20, 22, 25, 23, 21])  # Actual
    predictions = np.array([21, 23, 24, 22, 20])   # Model predictions
    
    mse = LossFunctions.mean_squared_error(temperatures, predictions)
    mae = LossFunctions.mean_absolute_error(temperatures, predictions)
    
    print(f"\nTemperature Prediction Exercise:")
    print(f"MSE Loss: {mse:.2f}°C")
    print(f"MAE Loss: {mae:.2f}°C")
    
    # Visualize the losses
    LossFunctions.plot_loss_comparison(
        temperatures, predictions, 
        "Temperature Prediction Losses"
    )

def main():
    """Run all examples"""
    print("🎯 Loss Functions in Action 🎯")
    print("=" * 40)
    
    # Run examples
    spam_detection_example()
    house_price_example()
    temperature_prediction_exercise()
    
    print("\n✨ Practice Makes Perfect! Keep Learning! ✨")

if __name__ == "__main__":
    main()

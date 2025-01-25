# run_churn_prediction.py

from churn_prediction_system import ChurnPredictionSystem
from generate_sample_data import generate_customer_data
from sklearn.model_selection import train_test_split
import pandas as pd
import matplotlib.pyplot as plt


def main():
    """
    Main function to run the churn prediction pipeline.
    This function orchestrates the entire process from data generation to model evaluation.
    """
    try:
        # Step 1: Generate sample data
        # We create synthetic customer data to simulate real-world scenarios
        print("\n=== Generating Sample Data ===")
        df = generate_customer_data(n_records=1000)
        df.to_csv('customer_data.csv', index=False)
        print(f"Generated {len(df)} records and saved to customer_data.csv")

        # Step 2: Initialize the system
        # Create an instance of our churn prediction system with default parameters
        print("\n=== Initializing Churn Prediction System ===")
        system = ChurnPredictionSystem()

        # Step 3: Preprocess data
        # Transform raw data into a format suitable for machine learning
        print("\n=== Preprocessing Data ===")
        X, y = system.preprocess_data(df)
        print(f"Preprocessed data shape: {X.shape}")

        # Step 4: Split data
        # Divide data into training and testing sets while maintaining class distribution
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        print(f"\nTraining set size: {X_train.shape[0]}")
        print(f"Test set size: {X_test.shape[0]}")

        # Step 5: Train the model
        # Train the Random Forest model with class imbalance handling
        print("\n=== Training Model ===")
        model = system.train_model(X_train, y_train)
        print("Model training completed")

        # Step 6: Evaluate model performance
        # Generate comprehensive performance metrics and visualizations
        print("\n=== Evaluating Model ===")
        results = system.evaluate_model(X_test, y_test)

        # Print detailed performance metrics
        print("\nModel Performance Summary:")
        print(f"ROC-AUC Score: {results['roc_auc_score']:.4f}")
        print("\nDetailed Classification Report:")
        print(results['classification_report'])

        # Step 7: Save the trained model
        # Persist the model and preprocessor for future use
        print("\n=== Saving Model ===")
        model_path = "churn_model_v1.joblib"
        system.save_model(model_path)
        print(f"Model saved to {model_path}")

        # Step 8: Demonstrate prediction on new data
        # Show how to use the model for making predictions
        print("\n=== Testing Predictions ===")
        new_customers = df.head(5)  # Using first 5 records as example
        predictions = system.predict(new_customers.drop(['Churn', 'CustomerID'], axis=1))

        # Create a readable prediction summary
        results_df = pd.DataFrame({
            'CustomerID': new_customers['CustomerID'],
            'Actual Churn': new_customers['Churn'],
            'Predicted Probability': predictions
        })
        print("\nSample Predictions:")
        print(results_df.to_string(index=False))

        # Step 9: Show feature importance analysis
        print("\n=== Feature Importance Analysis ===")
        print("Check the generated plots for feature importance and confusion matrix.")

        print("\n=== Pipeline Completed Successfully ===")

    except Exception as e:
        print(f"\nError: The pipeline failed with the following error:\n{str(e)}")
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nFatal error occurred: {str(e)}")
        print("Please check the logs for more details.")

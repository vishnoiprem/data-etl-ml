from churn_prediction_system import ChurnPredictionSystem
from generate_sample_data import generate_sample_data
from sklearn.model_selection import train_test_split
import pandas as pd


def main():
    """Runs the end-to-end churn prediction pipeline."""

    # Step 1: Generate sample data
    print("Generating sample data...")
    data = generate_sample_data(n_samples=5000, random_state=42)
    print(f"Generated dataset of shape: {data.shape}")
    data.head()


    # Step 2: Initialize churn prediction system
    print("\nInitializing churn prediction system...")
    churn_system = ChurnPredictionSystem(random_state=42)

    # Step 3: Preprocess data
    print("\nPreprocessing data...")
    X, y = churn_system.preprocess_data(data)
    print(f"Preprocessed data shape: {X.shape}")

    # Step 4: Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Train set size: {len(y_train)}  |  Test set size: {len(y_test)}")

    # Step 5: Train model
    print("\nTraining model...")
    churn_system.train_model(X_train, y_train)
    print("Model training completed")

    # Step 6: Evaluate model
    print("\nEvaluating model on test data...")
    results = churn_system.evaluate_model(X_test, y_test)
    print("Model evaluation completed")

    # Step 7: Save trained model
    print("\nSaving trained model...")
    churn_system.save_model('churn_model.pkl')

    # Step 8: Load saved model
    print("\nLoading saved model...")
    churn_system.load_model('churn_model.pkl')

    # Step 9: Generate predictions
    print("\nGenerating predictions on sample data...")
    sample_data = data[:5].drop(['Churn', 'CustomerID'], axis=1)
    probabilities = churn_system.predict(sample_data)

    print("\nSample predictions:")
    print(pd.DataFrame({
        'churn_probability': probabilities
    }))

    print("\nChurn prediction pipeline completed.")


if __name__ == '__main__':
    main()
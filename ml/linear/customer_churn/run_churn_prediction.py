import pandas as pd
from churn_prediction_system import ChurnPredictionSystem
from generate_sample_data import generate_sample_data
from sklearn.model_selection import train_test_split


def main():
    """Runs the end-to-end churn prediction pipeline."""

    # Step 1: Generate sample data
    print("Generating sample data...")
    data = generate_sample_data(n_samples=15000, random_state=42)
    print(f"Generated dataset of shape: {data.shape}")
    print("\nSample data head:")
    print(data.head())

    print("\nSample data summary statistics:")
    print(data.describe())

    print("\nChurn distribution:")
    print(data['Churn'].value_counts(normalize=True))

    # These additional outputs give us a better understanding of the generated data:
    # - The head() method shows the first few rows, giving a glimpse of the data structure.
    # - describe() provides summary statistics for each numeric column.
    # - value_counts(normalize=True) shows the distribution of the target variable 'Churn'.

    # Step 2: Initialize churn prediction system
    print("\nInitializing churn prediction system...")
    churn_system = ChurnPredictionSystem(random_state=42)



    # Step 3: Preprocess data
    print("\nPreprocessing data...")
    X, y = churn_system.preprocess_data(data)
    print(f"Preprocessed data shape: {X.shape}")

    print("\nPreprocessed feature names:")
    print(churn_system.feature_names)

    # Printing the feature names after preprocessing helps verify that the data was 
    # transformed as expected, with categorical features one-hot encoded.

    # Step 4: Split into train and test sets 
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"\nTrain set size: {len(y_train)}  |  Test set size: {len(y_test)}")

    print(f"Train set churn rate: {y_train.mean():.2%}")
    print(f"Test set churn rate: {y_test.mean():.2%}")

    # Comparing the churn rates in the train and test sets helps check if the split 
    # preserved the original distribution, which is important for an unbiased evaluation.

    # Step 5: Train model
    print("\nTraining model...")
    churn_system.train_model(X_train, y_train)
    print("Model training completed")

    # Step 6: Evaluate model
    print("\nEvaluating model on test data...")
    results = churn_system.evaluate_model(X_test, y_test)
    print("Model evaluation completed")

    print("\nTest set performance:")
    print(f"ROC-AUC Score: {results['roc_auc']:.4f}")
    print(f"\nClassification Report:\n{results['classification_report']}")
    print(f"\nConfusion Matrix:\n{results['confusion_matrix']}")

    # These evaluation metrics give a comprehensive view of the model's performance:
    # - ROC-AUC score is a threshold-invariant measure of classification performance.
    # - Classification report shows precision, recall, f1-score for each class.
    # - Confusion matrix shows the distribution of true positives, true negatives, 
    #   false positives, and false negatives.

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
        'CustomerID': data[:5]['CustomerID'],
        'Actual Churn': data[:5]['Churn'],
        'Churn Probability': probabilities
    }))

    # Showing the actual churn status alongside the predicted probabilities for a 
    # small sample helps interpret the model's outputs and builds trust in its predictions.

    print("\nChurn prediction pipeline completed.")


if __name__ == '__main__':
    main()

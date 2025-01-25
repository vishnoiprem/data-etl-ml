# churn_prediction_system.py

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
import seaborn as sns
import matplotlib.pyplot as plt
from imblearn.over_sampling import SMOTE
import joblib
import logging
from datetime import datetime


class ChurnPredictionSystem:

    def __init__(self, random_state=42):
        self.random_state = random_state
        self.model_version = datetime.now().strftime("%Y%m%d_%H%M%S")  # Add this line
        self.logger = self._setup_logger()
        self.preprocessor = None
        self.model = None

    def _setup_logger(self):
        """Configures a logger for the system."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"churn_model_{self.model_version}.log"),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    def preprocess_data(self, df):
        """Preprocesses the input data."""
        try:
            # Define the feature groups
            numeric_features = ['tenure', 'MonthlyCharges', 'TotalCharges']
            categorical_features = ['gender', 'SeniorCitizen', 'Partner', 'Dependents',
                                    'PhoneService', 'InternetService', 'Contract',
                                    'PaperlessBilling', 'PaymentMethod']

            # Create preprocessing pipelines
            numeric_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ])

            categorical_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
                ('onehot', OneHotEncoder(handle_unknown='ignore'))
            ])

            # Combine preprocessing steps
            preprocessor = ColumnTransformer(
                transformers=[
                    ('num', numeric_transformer, numeric_features),
                    ('cat', categorical_transformer, categorical_features)
                ])

            # Prepare features and target
            if 'CustomerID' in df.columns:
                df = df.drop('CustomerID', axis=1)

            X = df.drop('Churn', axis=1)
            y = df['Churn'].map({'Yes': 1, 'No': 0})

            # Transform the features
            X_transformed = preprocessor.fit_transform(X)

            self.preprocessor = preprocessor
            self.feature_names = (numeric_features +
                                  list(preprocessor.named_transformers_['cat']
                                       .named_steps['onehot'].get_feature_names_out(categorical_features)))

            return X_transformed, y

        except Exception as e:
            self.logger.exception(f"Error in preprocessing: {str(e)}")
            raise

    def train_model(self, X, y):
        """Trains the churn prediction model."""
        try:
            # Handle class imbalance
            smote = SMOTE(random_state=self.random_state)
            X_resampled, y_resampled = smote.fit_resample(X, y)

            # Create and train the model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=self.random_state
            )

            # Perform cross-validation
            cv_scores = cross_val_score(model, X_resampled, y_resampled, cv=5)
            self.logger.info(f"Cross-validation scores: {cv_scores}")
            self.logger.info(f"Mean CV score: {cv_scores.mean():.4f} +/- {cv_scores.std():.4f}")

            # Train final model
            model.fit(X_resampled, y_resampled)
            self.model = model

            return model

        except Exception as e:
            self.logger.exception(f"Error in model training: {str(e)}")
            raise

    def evaluate_model(self, X_test, y_test):
        """Evaluates the trained model on test data."""
        try:
            # Generate predictions
            y_pred = self.model.predict(X_test)
            y_prob = self.model.predict_proba(X_test)[:, 1]

            # Calculate evaluation metrics
            results = {
                'classification_report': classification_report(y_test, y_pred),
                'confusion_matrix': confusion_matrix(y_test, y_pred),
                'roc_auc': roc_auc_score(y_test, y_prob)
            }

            # Log evaluation results
            self.logger.info(f"\nClassification report: \n{results['classification_report']}")
            self.logger.info(f"\nConfusion matrix: \n{results['confusion_matrix']}")
            self.logger.info(f"\nROC-AUC score: {results['roc_auc']:.4f}")

            # Plot feature importances
            feature_importances = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)

            plt.figure(figsize=(10, 8))
            sns.barplot(x='importance', y='feature', data=feature_importances[:20])
            plt.title("Feature Importances")
            plt.show()

            return results

        except Exception as e:
            self.logger.exception(f"Error in model evaluation: {str(e)}")
            raise

    def save_model(self, filepath):
        """Saves the trained model to disk."""
        try:
            model_data = {
                'model': self.model,
                'preprocessor': self.preprocessor,
                'feature_names': self.feature_names
            }
            joblib.dump(model_data, filepath)
            self.logger.info(f"Model saved to {filepath}")
        except Exception as e:
            self.logger.exception(f"Error saving model: {str(e)}")
            raise

    def load_model(self, filepath):
        """Loads a saved model from disk."""
        try:
            model_data = joblib.load(filepath)
            self.model = model_data['model']
            self.preprocessor = model_data['preprocessor']
            self.feature_names = model_data['feature_names']
            self.logger.info(f"Model loaded from {filepath}")
        except Exception as e:
            self.logger.exception(f"Error loading model: {str(e)}")
            raise

    def predict(self, X):
        """Generates churn predictions for input data."""
        try:
            X_transformed = self.preprocessor.transform(X)
            y_prob = self.model.predict_proba(X_transformed)[:, 1]
            return y_prob
        except Exception as e:
            self.logger.exception(f"Error generating predictions: {str(e)}")
            raise

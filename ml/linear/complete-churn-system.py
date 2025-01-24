"""
Customer Churn Prediction System with improved data handling
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
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
        self.logger = self._setup_logger()
        self.model_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.preprocessor = None
        self.model = None
        self.feature_names = None

    def _setup_logger(self):
        """Configure logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def _convert_binary_columns(self, df):
        """Convert Yes/No columns to 1/0"""
        for column in df.columns:
            if df[column].dtype == object:
                # Check if column contains only 'Yes'/'No' values
                unique_values = df[column].unique()
                if set(unique_values) <= {'Yes', 'No', 'No internet service', 'No phone service'}:
                    df[column] = df[column].map({'Yes': 1, 'No': 0,
                                               'No internet service': 0, 'No phone service': 0})
        return df

    def preprocess_data(self, df):
        """Preprocess the data with improved categorical handling"""
        try:
            # Make a copy to avoid modifying original data
            df = df.copy()

            # Convert binary columns
            df = self._convert_binary_columns(df)

            # Convert TotalCharges to numeric, handling any special cases
            if 'TotalCharges' in df.columns and df['TotalCharges'].dtype == object:
                df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
                df['TotalCharges'].fillna(0, inplace=True)

            # Separate features that need different preprocessing
            categorical_features = ['InternetService', 'Contract', 'PaymentMethod']
            categorical_features = [f for f in categorical_features if f in df.columns]

            numeric_features = ['tenure', 'MonthlyCharges', 'TotalCharges']
            numeric_features = [f for f in numeric_features if f in df.columns]

            # Create preprocessing steps
            numeric_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ])

            categorical_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
                ('encoder', LabelEncoder())
            ])

            # Create preprocessor
            preprocessor = ColumnTransformer(
                transformers=[
                    ('num', numeric_transformer, numeric_features),
                    ('cat', categorical_transformer, categorical_features)
                ],
                remainder='passthrough'  # This will keep the binary columns
            )

            # Store feature names for later use
            self.feature_names = numeric_features + categorical_features + \
                               [col for col in df.columns if col not in numeric_features +
                                categorical_features + ['Churn']]

            # Prepare target variable
            y = df['Churn'].map({'Yes': 1, 'No': 0}) if df['Churn'].dtype == object else df['Churn']

            # Remove target from features
            X = df.drop('Churn', axis=1)

            # Fit and transform the data
            X_processed = preprocessor.fit_transform(X)

            # Store preprocessor for later use
            self.preprocessor = preprocessor

            return X_processed, y

        except Exception as e:
            self.logger.error(f"Error in preprocessing: {str(e)}")
            raise

    def train_model(self, X, y):
        """Train the model with improved handling of processed data"""
        try:
            # Handle class imbalance
            smote = SMOTE(random_state=self.random_state)
            X_resampled, y_resampled = smote.fit_resample(X, y)

            # Create and train model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=self.random_state
            )

            # Fit the model
            self.model.fit(X_resampled, y_resampled)

            # Calculate and log cross-validation score
            cv_scores = cross_val_score(self.model, X_resampled, y_resampled, cv=5)
            self.logger.info(f"Cross-validation scores: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

            return self.model

        except Exception as e:
            self.logger.error(f"Error in model training: {str(e)}")
            raise

    def evaluate_model(self, X_test, y_test):
        """Evaluate model with improved visualization"""
        try:
            # Generate predictions
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]

            # Calculate metrics
            results = {
                'classification_report': classification_report(y_test, y_pred),
                'confusion_matrix': confusion_matrix(y_test, y_pred),
                'roc_auc_score': roc_auc_score(y_test, y_pred_proba)
            }

            # Log results
            self.logger.info("\nModel Performance:")
            self.logger.info(f"\nClassification Report:\n{results['classification_report']}")
            self.logger.info(f"\nROC-AUC Score: {results['roc_auc_score']:.4f}")

            # Create feature importance visualization
            importances = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)

            plt.figure(figsize=(10, 6))
            sns.barplot(x='importance', y='feature', data=importances.head(10))
            plt.title('Top 10 Most Important Features')
            plt.tight_layout()
            plt.show()

            return results

        except Exception as e:
            self.logger.error(f"Error in model evaluation: {str(e)}")
            raise

def run_complete_pipeline(data_path, model_save_path=None):
    """Run the complete pipeline with improved error handling"""
    system = ChurnPredictionSystem()

    try:
        # Load data
        df = pd.read_csv(data_path)
        system.logger.info(f"Loaded data with shape: {df.shape}")

        # Display initial data info
        system.logger.info("\nInitial data info:")
        system.logger.info(df.dtypes)

        # Preprocess data
        X, y = system.preprocess_data(df)

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # Train model
        model = system.train_model(X_train, y_train)

        # Evaluate model
        results = system.evaluate_model(X_test, y_test)

        # Save model if path provided
        if model_save_path:
            joblib.dump({
                'model': system.model,
                'preprocessor': system.preprocessor,
                'feature_names': system.feature_names,
                'version': system.model_version
            }, model_save_path)
            system.logger.info(f"Model saved to {model_save_path}")

        return system, results

    except Exception as e:
        system.logger.error(f"Pipeline execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Run the pipeline
        system, results = run_complete_pipeline(
            data_path="customer_data.csv",
            model_save_path="churn_model_v1.joblib"
        )
        
        # Print results summary
        print("\nModel Performance Summary:")
        print(f"ROC-AUC Score: {results['roc_auc_score']:.4f}")
        print("\nDetailed Classification Report:")
        print(results['classification_report'])
        
    except Exception as e:
        print(f"Error running pipeline: {str(e)}")

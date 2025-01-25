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
        self.logger = self._setup_logger()
        self.model_version = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.preprocessor = None
        self.model = None
        self.feature_names = None
        
        # Define feature groups
        self.numeric_features = ['tenure', 'MonthlyCharges', 'TotalCharges']
        self.categorical_features = ['InternetService', 'Contract', 'PaymentMethod']
        self.binary_features = ['gender', 'Partner', 'Dependents', 'PhoneService', 
                              'PaperlessBilling', 'Churn']

    def _setup_logger(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'churn_pipeline_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _validate_data(self, df):
        required_columns = set(self.numeric_features + [col for col in self.categorical_features 
                                                      if col != 'Churn'])
        missing_cols = required_columns - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        if len(df) < 100:
            raise ValueError("Insufficient data for reliable model training (minimum 100 records)")
        
        if 'Churn' in df.columns:
            churn_rate = df['Churn'].map({'Yes': 1, 'No': 0}).mean()
            if churn_rate < 0.05 or churn_rate > 0.95:
                self.logger.warning(f"Severe class imbalance detected: {churn_rate:.2%} churn rate")
        
        return True

    def _create_feature_names(self, df):
        numeric_cols = self.numeric_features
        
        categorical_cols = []
        for feature in self.categorical_features:
            if feature in df.columns:
                unique_vals = df[feature].unique()
                categorical_cols.extend([f"{feature}_{val}" for val in unique_vals[1:]])
        
        binary_cols = [f for f in self.binary_features if f != 'Churn' and f in df.columns]
        
        return numeric_cols + categorical_cols + binary_cols

    def preprocess_data(self, df):
        try:
            self._validate_data(df)
            df = df.copy()
            
            numeric_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ])

            categorical_transformer = Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
                ('onehot', OneHotEncoder(drop='first', sparse=False))
            ])

            self.preprocessor = ColumnTransformer(
                transformers=[
                    ('num', numeric_transformer, self.numeric_features),
                    ('cat', categorical_transformer, 
                     [f for f in self.categorical_features if f != 'Churn'])
                ])

            X = df.drop(['Churn', 'CustomerID'] if 'CustomerID' in df.columns else ['Churn'], axis=1)
            y = df['Churn'].map({'Yes': 1, 'No': 0})

            self.feature_names = self._create_feature_names(df)
            X_transformed = self.preprocessor.fit_transform(X)
            
            return X_transformed, y

        except Exception as e:
            self.logger.error(f"Error in preprocessing: {str(e)}")
            raise

    def train_model(self, X, y):
        try:
            smote = SMOTE(random_state=self.random_state)
            X_resampled, y_resampled = smote.fit_resample(X, y)
            
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=self.random_state
            )
            
            cv_scores = cross_val_score(self.model, X_resampled, y_resampled, cv=5)
            self.logger.info(f"Cross-validation scores: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
            
            self.model.fit(X_resampled, y_resampled)
            return self.model
            
        except Exception as e:
            self.logger.error(f"Error in model training: {str(e)}")
            raise

    def evaluate_model(self, X_test, y_test):
        try:
            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]
            
            results = {
                'classification_report': classification_report(y_test, y_pred),
                'confusion_matrix': confusion_matrix(y_test, y_pred),
                'roc_auc_score': roc_auc_score(y_test, y_pred_proba)
            }
            
            self.logger.info("\nModel Performance:")
            self.logger.info(f"\nClassification Report:\n{results['classification_report']}")
            self.logger.info(f"\nROC-AUC Score: {results['roc_auc_score']:.4f}")
            
            self._plot_feature_importance()
            self._plot_confusion_matrix(results['confusion_matrix'])
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in model evaluation: {str(e)}")
            raise

    def _plot_feature_importance(self):
        importances = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        plt.figure(figsize=(12, 6))
        sns.barplot(x='importance', y='feature', data=importances.head(10))
        plt.title('Top 10 Most Important Features')
        plt.tight_layout()
        plt.show()

    def _plot_confusion_matrix(self, cm):
        plt.figure(figsize=(8, 6))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.show()

    def save_model(self, filepath):
        if self.model is None or self.preprocessor is None:
            raise ValueError("Model and preprocessor must be trained before saving")
        
        model_info = {
            'model': self.model,
            'preprocessor': self.preprocessor,
            'feature_names': self.feature_names,
            'version': self.model_version,
            'timestamp': datetime.now().isoformat()
        }
        joblib.dump(model_info, filepath)
        self.logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath):
        model_info = joblib.load(filepath)
        self.model = model_info['model']
        self.preprocessor = model_info['preprocessor']
        self.feature_names = model_info['feature_names']
        self.logger.info(f"Loaded model version: {model_info['version']}")

    def predict(self, X):
        if self.model is None or self.preprocessor is None:
            raise ValueError("Model must be trained or loaded before predicting")
        
        X_processed = self.preprocessor.transform(X)
        predictions = self.model.predict_proba(X_processed)[:, 1]
        return predictions
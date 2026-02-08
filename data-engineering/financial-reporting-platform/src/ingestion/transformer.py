# src/ingestion/transformer.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from typing import Dict, List, Tuple
import logging
from dataclasses import dataclass

from src.config import config

logger = logging.getLogger(__name__)


@dataclass
class TransformationRules:
    """Business rules for data transformation"""

    @staticmethod
    def standardize_column_names(df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        """Standardize column names across different sources"""
        column_mappings = {
            'erp': {
                'account_code': 'gl_account',
                'posting_date': 'transaction_date',
                'local_amount': 'amount_local',
                'document_number': 'transaction_id'
            },
            'pos': {
                'pos_transaction_id': 'transaction_id',
                'transaction_datetime': 'transaction_date',
                'amount': 'amount_local'
            }
        }

        mapping = column_mappings.get(source_type, {})
        df = df.rename(columns=mapping)
        return df

    @staticmethod
    def validate_account_codes(df: pd.DataFrame) -> pd.DataFrame:
        """Validate GL account codes against chart of accounts"""
        chart_of_accounts = {
            "REVENUE": ["401001", "401002", "401003"],
            "COGS": ["501001", "501002", "501003"],
            "EXPENSE": ["601001", "601002", "601003"],
            "ASSET": ["101001", "101002"],
            "LIABILITY": ["201001", "201002"]
        }

        valid_accounts = []
        for accounts in chart_of_accounts.values():
            valid_accounts.extend(accounts)

        valid_mask = df['gl_account'].isin(valid_accounts)
        invalid_count = (~valid_mask).sum()

        if invalid_count > 0:
            logger.warning(f"Found {invalid_count} invalid account codes")
            df = df[valid_mask].copy()

        return df


class DataTransformer:
    """Transform raw data into cleaned silver layer"""

    def __init__(self):
        self.rules = TransformationRules()

    def transform_to_silver(self, bronze_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Transform bronze data to silver layer"""
        silver_data = {}

        for source_name, df in bronze_data.items():
            logger.info(f"Processing {source_name} with {len(df)} records")

            if 'erp' in source_name:
                source_type = 'erp'
            elif 'pos' in source_name:
                source_type = 'pos'
            else:
                source_type = 'other'

            df_transformed = self._apply_transformations(df, source_type)

            df_transformed['processing_timestamp'] = datetime.now()
            df_transformed['data_quality_score'] = self._calculate_quality_score(df_transformed)

            silver_data[source_name] = df_transformed

            self._save_to_silver(source_name, df_transformed)

        return silver_data

    def _apply_transformations(self, df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        """Apply all transformations"""
        df = self.rules.standardize_column_names(df, source_type)

        if 'transaction_date' in df.columns:
            df['transaction_date'] = pd.to_datetime(df['transaction_date'])

        if 'amount_local' in df.columns:
            df['amount_local'] = pd.to_numeric(df['amount_local'], errors='coerce')

        df['year'] = df['transaction_date'].dt.year
        df['month'] = df['transaction_date'].dt.month
        df['day'] = df['transaction_date'].dt.day

        if 'currency_code' in df.columns:
            df['currency_code'] = df['currency_code'].str.upper()

        if 'gl_account' in df.columns:
            df = self.rules.validate_account_codes(df)

        df = self._detect_anomalies(df)

        return df

    def _detect_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect data anomalies"""
        df = df.copy()

        if 'amount_local' in df.columns:
            df['negative_flag'] = df['amount_local'] < 0
            df['high_value_flag'] = df['amount_local'] > config.high_value_threshold

        critical_fields = ['gl_account', 'transaction_date', 'amount_local']
        critical_in_df = [col for col in critical_fields if col in df.columns]

        if critical_in_df:
            df['missing_data_flag'] = df[critical_in_df].isnull().any(axis=1)

        duplicate_fields = ['transaction_id', 'gl_account', 'amount_local', 'transaction_date']
        duplicate_in_df = [col for col in duplicate_fields if col in df.columns]

        if duplicate_in_df:
            df['duplicate_flag'] = df.duplicated(subset=duplicate_in_df, keep='first')

        return df

    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate data quality score"""
        total_records = len(df)
        if total_records == 0:
            return 0.0

        quality_metrics = []

        critical_fields = ['gl_account', 'transaction_date', 'amount_local']
        for field in critical_fields:
            if field in df.columns:
                null_ratio = df[field].isnull().sum() / total_records
                quality_metrics.append(1.0 - null_ratio)

        anomaly_flags = ['negative_flag', 'high_value_flag', 'missing_data_flag', 'duplicate_flag']
        anomaly_columns = [col for col in anomaly_flags if col in df.columns]

        if anomaly_columns:
            anomaly_ratio = df[anomaly_columns].any(axis=1).sum() / total_records
            quality_metrics.append(1.0 - anomaly_ratio)

        if quality_metrics:
            return sum(quality_metrics) / len(quality_metrics)
        else:
            return 1.0

    def _save_to_silver(self, source_name: str, df: pd.DataFrame):
        """Save transformed data to silver layer"""
        os.makedirs(config.silver_path, exist_ok=True)

        file_path = os.path.join(config.silver_path, f"{source_name}_{datetime.now().strftime('%Y%m%d')}.parquet")
        df.to_parquet(file_path, index=False)
        logger.info(f"Saved silver data for {source_name} to {file_path}")

    def load_from_silver(self, source_pattern: str = None) -> Dict[str, pd.DataFrame]:
        """Load data from silver layer"""
        if not os.path.exists(config.silver_path):
            return {}

        silver_data = {}
        for file in os.listdir(config.silver_path):
            if file.endswith('.parquet'):
                if source_pattern and source_pattern not in file:
                    continue

                file_path = os.path.join(config.silver_path, file)
                df = pd.read_parquet(file_path)
                source_name = file.replace('.parquet', '')
                silver_data[source_name] = df

        return silver_data
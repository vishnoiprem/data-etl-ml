# src/processing/business_logic.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
import duckdb
import os

from src.config import config

logger = logging.getLogger(__name__)


class FinancialMetricsCalculator:
    """Calculate financial metrics and KPIs"""

    def __init__(self):
        self.conn = duckdb.connect(database=':memory:')

    def create_gold_layer(self, silver_data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Create gold layer data marts"""

        combined_df = self._combine_silver_data(silver_data)

        if combined_df.empty:
            logger.warning("No data to process for gold layer")
            return {}

        star_schema = self._create_star_schema(combined_df)

        metrics = self._calculate_metrics(star_schema['fact_transactions'])

        variance = self._calculate_variance_analysis(metrics)

        summary = self._create_executive_summary(metrics, variance)

        gold_data = {
            'fact_transactions': star_schema['fact_transactions'],
            'dim_accounts': star_schema['dim_accounts'],
            'dim_dates': star_schema['dim_dates'],
            'dim_countries': star_schema['dim_countries'],
            'monthly_metrics': metrics,
            'variance_analysis': variance,
            'executive_summary': summary
        }

        self._save_gold_layer(gold_data)

        return gold_data

    def _combine_silver_data(self, silver_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Combine data from all silver sources"""
        all_data = []

        for source_name, df in silver_data.items():
            if df.empty:
                continue

            df = df.copy()
            df['source_name'] = source_name

            df['account_category'] = self._map_account_to_category(df['gl_account'])

            df['amount_usd'] = self._convert_to_usd(df['amount_local'], df['currency_code'])

            all_data.append(df)

        if not all_data:
            return pd.DataFrame()

        return pd.concat(all_data, ignore_index=True)

    def _map_account_to_category(self, gl_accounts: pd.Series) -> pd.Series:
        """Map GL accounts to categories"""

        def get_category(account):
            account_str = str(account)
            if account_str.startswith('401'):
                return 'REVENUE'
            elif account_str.startswith('501'):
                return 'COGS'
            elif account_str.startswith('601'):
                return 'EXPENSE'
            elif account_str.startswith('101'):
                return 'ASSET'
            elif account_str.startswith('201'):
                return 'LIABILITY'
            else:
                return 'OTHER'

        return gl_accounts.apply(get_category)

    def _convert_to_usd(self, amounts: pd.Series, currencies: pd.Series) -> pd.Series:
        """Convert local currency to USD"""
        conversion_rates = {
            'THB': 0.028,
            'VND': 0.000041,
            'IDR': 0.000064,
            'USD': 1.0
        }

        def convert(amount, currency):
            rate = conversion_rates.get(currency, 1.0)
            return amount * rate

        return amounts.combine(currencies, convert)

    def _create_star_schema(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Create star schema dimension and fact tables"""

        unique_accounts = df[['gl_account', 'account_category']].drop_duplicates()
        dim_accounts = unique_accounts.copy()
        dim_accounts['account_key'] = range(1, len(dim_accounts) + 1)
        dim_accounts['account_name'] = dim_accounts['gl_account'].apply(
            lambda x: f"Account {x}"
        )

        unique_dates = df['transaction_date'].dropna().unique()
        dim_dates = pd.DataFrame({'date': unique_dates})
        dim_dates['date_key'] = dim_dates['date'].dt.strftime('%Y%m%d').astype(int)
        dim_dates['year'] = dim_dates['date'].dt.year
        dim_dates['month'] = dim_dates['date'].dt.month
        dim_dates['day'] = dim_dates['date'].dt.day
        dim_dates['quarter'] = dim_dates['date'].dt.quarter
        dim_dates['week_number'] = dim_dates['date'].dt.isocalendar().week

        unique_countries = df[['country', 'currency_code']].drop_duplicates()
        dim_countries = unique_countries.copy()
        dim_countries['country_key'] = range(1, len(dim_countries) + 1)
        dim_countries['country_name'] = dim_countries['country'].map({
            'TH': 'Thailand',
            'VN': 'Vietnam',
            'ID': 'Indonesia'
        })

        fact_transactions = df.copy()

        fact_transactions = pd.merge(
            fact_transactions,
            dim_accounts[['gl_account', 'account_key']],
            on='gl_account',
            how='left'
        )

        fact_transactions = pd.merge(
            fact_transactions,
            dim_dates[['date', 'date_key']],
            left_on='transaction_date',
            right_on='date',
            how='left'
        ).drop(columns=['date'])

        fact_transactions = pd.merge(
            fact_transactions,
            dim_countries[['country', 'country_key']],
            on='country',
            how='left'
        )

        fact_columns = [
            'transaction_id', 'date_key', 'account_key', 'country_key',
            'amount_local', 'currency_code', 'amount_usd',
            'source_name', 'processing_timestamp',
            'negative_flag', 'high_value_flag', 'missing_data_flag', 'duplicate_flag'
        ]

        available_columns = [col for col in fact_columns if col in fact_transactions.columns]
        fact_transactions = fact_transactions[available_columns]

        return {
            'fact_transactions': fact_transactions,
            'dim_accounts': dim_accounts,
            'dim_dates': dim_dates,
            'dim_countries': dim_countries
        }

    def _calculate_metrics(self, fact_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate monthly financial metrics"""
        if fact_df.empty:
            return pd.DataFrame()

        # Ensure required columns exist
        if 'amount_usd' not in fact_df.columns:
            fact_df['amount_usd'] = 0

        # Create account category mapping
        if 'account_key' in fact_df.columns and 'dim_accounts' not in self.conn:
            # Create temporary dimension table
            account_map = pd.DataFrame({
                'account_key': range(1, 100),
                'account_category': ['REVENUE', 'COGS', 'EXPENSE', 'ASSET', 'LIABILITY'] * 20
            })
            self.conn.register('dim_accounts', account_map)

        self.conn.register('fact_transactions', fact_df)

        query = """
                WITH monthly_agg \
                         AS (SELECT EXTRACT(YEAR FROM processing_timestamp) as year, EXTRACT (MONTH FROM processing_timestamp) as month, country_key, account_category, SUM (amount_usd) as total_amount_usd, COUNT (*) as transaction_count, AVG (amount_usd) as avg_transaction_amount, MIN (amount_usd) as min_transaction_amount, MAX (amount_usd) as max_transaction_amount
                FROM fact_transactions
                    JOIN dim_accounts USING (account_key)
                GROUP BY 1, 2, 3, 4
                    )
                SELECT
                    year, month, country_key, account_category, total_amount_usd, transaction_count, avg_transaction_amount, min_transaction_amount, max_transaction_amount
                FROM monthly_agg
                ORDER BY year, month, country_key, account_category \
                """

        try:
            metrics_df = self.conn.execute(query).fetchdf()
            return metrics_df
        except:
            logger.warning("Could not calculate metrics, returning empty DataFrame")
            return pd.DataFrame()

    def _calculate_variance_analysis(self, metrics_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate variance from historical averages"""
        if metrics_df.empty:
            return pd.DataFrame()

        self.conn.register('monthly_metrics', metrics_df)

        variance_query = """
                         WITH historical_avg AS (SELECT country_key, \
                                                        account_category, \
                                                        AVG(total_amount_usd) as historical_avg_amount \
                                                 FROM monthly_metrics \
                                                 GROUP BY country_key, account_category),
                              current_month AS (SELECT * \
                                                FROM monthly_metrics \
                                                WHERE (year, month) = (SELECT MAX(year), MAX(month) \
                                                                       FROM monthly_metrics))
                         SELECT c.*, \
                                h.historical_avg_amount, \
                                c.total_amount_usd - h.historical_avg_amount as absolute_variance, \
                                (c.total_amount_usd - h.historical_avg_amount) / NULLIF(h.historical_avg_amount, 0) * \
                                100                                          as percentage_variance
                         FROM current_month c
                                  LEFT JOIN historical_avg h
                                            ON c.country_key = h.country_key
                                                AND c.account_category = h.account_category \
                         """

        try:
            variance_df = self.conn.execute(variance_query).fetchdf()
            return variance_df
        except:
            logger.warning("Could not calculate variance, returning empty DataFrame")
            return pd.DataFrame()

    def _create_executive_summary(self, metrics_df: pd.DataFrame, variance_df: pd.DataFrame) -> pd.DataFrame:
        """Create executive summary dashboard data"""
        if metrics_df.empty:
            return pd.DataFrame()

        current_month = metrics_df[
            (metrics_df['year'] == metrics_df['year'].max()) &
            (metrics_df['month'] == metrics_df['month'].max())
            ]

        if current_month.empty:
            return pd.DataFrame()

        summary_pivot = current_month.pivot_table(
            index='country_key',
            columns='account_category',
            values='total_amount_usd',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        if 'REVENUE' in summary_pivot.columns and 'COGS' in summary_pivot.columns:
            summary_pivot['gross_profit'] = summary_pivot['REVENUE'] - summary_pivot['COGS']
            if (summary_pivot['REVENUE'] > 0).any():
                summary_pivot['gross_margin_pct'] = (summary_pivot['gross_profit'] / summary_pivot['REVENUE']) * 100

        if 'EXPENSE' in summary_pivot.columns and 'gross_profit' in summary_pivot.columns:
            summary_pivot['net_profit'] = summary_pivot['gross_profit'] - summary_pivot['EXPENSE']
            if (summary_pivot['REVENUE'] > 0).any():
                summary_pivot['net_margin_pct'] = (summary_pivot['net_profit'] / summary_pivot['REVENUE']) * 100

        return summary_pivot

    def _save_gold_layer(self, gold_data: Dict[str, pd.DataFrame]):
        """Save gold layer data"""
        os.makedirs(config.gold_path, exist_ok=True)

        for table_name, df in gold_data.items():
            if df.empty:
                continue

            file_path = os.path.join(config.gold_path, f"{table_name}.parquet")
            df.to_parquet(file_path, index=False)
            logger.info(f"Saved {table_name} with {len(df)} records to {file_path}")
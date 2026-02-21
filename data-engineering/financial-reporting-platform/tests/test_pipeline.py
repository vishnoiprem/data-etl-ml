# tests/test_pipeline.py
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingestion.extractor import DataGenerator, DataExtractor
from ingestion.transformer import DataTransformer
from processing.business_logic import FinancialMetricsCalculator
from monitoring.quality_checks import DataQualityChecker


class TestDataGenerator:
    """Test data generation"""

    def test_generate_erp_data(self):
        """Test ERP data generation"""
        generator = DataGenerator(seed=42)
        data = generator.generate_erp_data("TH", num_records=100)

        assert isinstance(data, pd.DataFrame)
        assert len(data) == 100
        assert 'transaction_id' in data.columns
        assert 'gl_account' in data.columns
        assert 'amount_local' in data.columns
        assert 'country' in data.columns
        assert all(data['country'] == 'TH')

    def test_generate_pos_data(self):
        """Test POS data generation"""
        generator = DataGenerator(seed=42)
        data = generator.generate_pos_data("VN", num_records=50)

        assert isinstance(data, pd.DataFrame)
        assert len(data) == 50
        assert 'pos_transaction_id' in data.columns
        assert 'store_id' in data.columns
        assert 'amount' in data.columns
        assert all(data['country'] == 'VN')


class TestDataExtractor:
    """Test data extraction"""

    def test_extract_all_sources(self):
        """Test extraction of all sources"""
        extractor = DataExtractor()
        data = extractor.extract_all_sources()

        assert isinstance(data, dict)
        assert len(data) > 0

        for source_name, df in data.items():
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0

    def test_save_and_load_bronze(self, tmp_path):
        """Test saving and loading from bronze layer"""
        extractor = DataExtractor()

        # Create temporary directory
        test_dir = tmp_path / "test_bronze"
        test_dir.mkdir()

        # Generate test data
        test_data = {"test_source": pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c']
        })}

        # Save to bronze
        extractor.save_to_bronze(test_data)

        # Load from bronze
        loaded_data = extractor.load_from_bronze()

        assert len(loaded_data) > 0


class TestDataTransformer:
    """Test data transformation"""

    def test_transform_to_silver(self):
        """Test transformation to silver layer"""
        transformer = DataTransformer()

        # Create test data
        test_data = {
            "erp_test": pd.DataFrame({
                'transaction_id': ['TRX001', 'TRX002'],
                'gl_account': ['401001', '501001'],
                'posting_date': ['2024-01-01', '2024-01-02'],
                'local_amount': [1000.50, 500.25],
                'currency_code': ['THB', 'THB'],
                'country': ['TH', 'TH']
            })
        }

        silver_data = transformer.transform_to_silver(test_data)

        assert isinstance(silver_data, dict)
        assert 'erp_test' in silver_data

        df = silver_data['erp_test']
        assert 'transaction_date' in df.columns  # Renamed from posting_date
        assert 'amount_local' in df.columns  # Renamed from local_amount
        assert 'year' in df.columns
        assert 'month' in df.columns

    def test_data_quality_score(self):
        """Test data quality score calculation"""
        transformer = DataTransformer()

        # Create perfect data
        perfect_df = pd.DataFrame({
            'gl_account': ['401001', '401002'],
            'transaction_date': [datetime.now(), datetime.now()],
            'amount_local': [1000, 2000]
        })

        perfect_score = transformer._calculate_quality_score(perfect_df)
        assert 0.9 <= perfect_score <= 1.0

        # Create bad data
        bad_df = pd.DataFrame({
            'gl_account': [None, None],
            'transaction_date': [None, None],
            'amount_local': [None, None]
        })

        bad_score = transformer._calculate_quality_score(bad_df)
        assert 0.0 <= bad_score <= 0.3


class TestFinancialMetricsCalculator:
    """Test financial metrics calculation"""

    def test_currency_conversion(self):
        """Test currency conversion to USD"""
        calculator = FinancialMetricsCalculator()

        amounts = pd.Series([1000, 2000, 3000])
        currencies = pd.Series(['THB', 'VND', 'IDR'])

        usd_amounts = calculator._convert_to_usd(amounts, currencies)

        assert len(usd_amounts) == 3
        assert all(usd_amounts > 0)

    def test_account_category_mapping(self):
        """Test GL account to category mapping"""
        calculator = FinancialMetricsCalculator()

        accounts = pd.Series(['401001', '501001', '601001', '101001', '201001'])
        categories = calculator._map_account_to_category(accounts)

        expected = ['REVENUE', 'COGS', 'EXPENSE', 'ASSET', 'LIABILITY']
        assert list(categories) == expected


class TestDataQualityChecker:
    """Test data quality checks"""

    def test_completeness_check(self):
        """Test completeness check"""
        checker = DataQualityChecker()

        test_df = pd.DataFrame({
            'col1': [1, 2, None],
            'col2': ['a', None, 'c'],
            'col3': [1.0, 2.0, 3.0]
        })

        result = checker.check_completeness(test_df)

        assert 'completeness_rate' in result
        assert 0 <= result['completeness_rate'] <= 1

    def test_uniqueness_check(self):
        """Test uniqueness check"""
        checker = DataQualityChecker()

        test_df = pd.DataFrame({
            'transaction_id': ['T001', 'T001', 'T002'],
            'amount': [100, 100, 200]
        })

        result = checker.check_uniqueness(test_df)

        assert 'duplicate_records' in result
        assert result['duplicate_records'] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
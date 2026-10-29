# src/ingestion/extractor.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional
from faker import Faker
import duckdb

from src.config import data_sources, config


class DataGenerator:
    """Generate simulated financial data for local testing"""

    def __init__(self, seed: int = 42):
        self.fake = Faker()
        Faker.seed(seed)
        np.random.seed(seed)

        # Define account structure
        self.account_categories = {
            "REVENUE": ["401001", "401002", "401003"],
            "COGS": ["501001", "501002", "501003"],
            "EXPENSE": ["601001", "601002", "601003"],
            "ASSET": ["101001", "101002"],
            "LIABILITY": ["201001", "201002"],
        }

        # Country-specific settings
        self.country_settings = {
            "TH": {"currency": "THB", "locale": "th_TH"},
            "VN": {"currency": "VND", "locale": "vi_VN"},
            "ID": {"currency": "IDR", "locale": "id_ID"}
        }

    def generate_erp_data(self, country: str, num_records: int = 1000) -> pd.DataFrame:
        """Generate simulated ERP transaction data"""
        settings = self.country_settings.get(country, {"currency": "USD", "locale": "en_US"})
        self.fake = Faker(settings["locale"])

        data = []
        start_date = datetime.now() - timedelta(days=90)

        for _ in range(num_records):
            category = np.random.choice(list(self.account_categories.keys()))
            gl_account = np.random.choice(self.account_categories[category])

            transaction_date = self.fake.date_between(start_date=start_date)

            if category == "REVENUE":
                amount = np.random.lognormal(mean=8, sigma=1.5)
            elif category == "COGS":
                amount = np.random.lognormal(mean=7, sigma=1.2)
            else:
                amount = np.random.lognormal(mean=6, sigma=1.0)

            if np.random.random() < 0.02:
                amount *= np.random.uniform(10, 100)

            data.append({
                "transaction_id": f"TRX{self.fake.unique.random_int(min=100000, max=999999)}",
                "gl_account": gl_account,
                "transaction_date": transaction_date,
                "amount_local": round(amount, 2),
                "currency_code": settings["currency"],
                "document_number": f"DOC{self.fake.random_int(min=1000, max=9999)}",
                "vendor_customer_id": f"CUST{self.fake.random_int(min=1000, max=5000)}",
                "description": self.fake.catch_phrase(),
                "country": country,
                "source_system": "SAP_ERP" if country in ["TH", "VN"] else "Oracle_ERP",
                "created_at": datetime.now(),
                "batch_id": f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            })

        return pd.DataFrame(data)

    def generate_pos_data(self, country: str, num_records: int = 500) -> pd.DataFrame:
        """Generate simulated POS data"""
        settings = self.country_settings.get(country, {"currency": "USD", "locale": "en_US"})

        data = []
        start_date = datetime.now() - timedelta(days=30)

        for _ in range(num_records):
            transaction_date = self.fake.date_between(start_date=start_date)
            store_id = f"STORE{self.fake.random_int(min=1, max=50)}"

            data.append({
                "pos_transaction_id": f"POS{self.fake.unique.random_int(min=1000000, max=9999999)}",
                "store_id": store_id,
                "transaction_datetime": self.fake.date_time_between(
                    start_date=transaction_date,
                    end_date=transaction_date + timedelta(hours=23, minutes=59)
                ),
                "amount": round(np.random.lognormal(mean=5, sigma=1.0), 2),
                "currency": settings["currency"],
                "items_count": np.random.poisson(lam=8),
                "payment_method": np.random.choice(["CASH", "CARD", "E-WALLET", "CREDIT"]),
                "country": country,
                "source_system": "POS_System",
                "created_at": datetime.now(),
                "batch_id": f"BATCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            })

        return pd.DataFrame(data)


class DataExtractor:
    """Extract and load data from various sources"""

    def __init__(self):
        self.generator = DataGenerator()
        self.conn = duckdb.connect(database=':memory:')

    def extract_all_sources(self) -> Dict[str, pd.DataFrame]:
        """Extract data from all simulated sources"""
        extracted_data = {}

        for country in config.supported_countries:
            num_records = config.records_per_country.get(country, 1000)

            erp_data = self.generator.generate_erp_data(country, num_records)
            extracted_data[f"erp_{country}"] = erp_data

            pos_data = self.generator.generate_pos_data(country, num_records // 2)
            extracted_data[f"pos_{country}"] = pos_data

        return extracted_data

    def save_to_bronze(self, data: Dict[str, pd.DataFrame]):
        """Save extracted data to bronze layer"""
        os.makedirs(config.bronze_path, exist_ok=True)

        for source_name, df in data.items():
            file_path = os.path.join(config.bronze_path, f"{source_name}_{datetime.now().strftime('%Y%m%d')}.parquet")
            df.to_parquet(file_path, index=False)
            print(f"Saved {len(df)} records to {file_path}")

    def load_from_bronze(self, source_pattern: str = None) -> Dict[str, pd.DataFrame]:
        """Load data from bronze layer"""
        if not os.path.exists(config.bronze_path):
            return {}

        loaded_data = {}
        for file in os.listdir(config.bronze_path):
            if file.endswith('.parquet'):
                if source_pattern and source_pattern not in file:
                    continue

                file_path = os.path.join(config.bronze_path, file)
                df = pd.read_parquet(file_path)
                source_name = file.replace('.parquet', '')
                loaded_data[source_name] = df

        return loaded_data
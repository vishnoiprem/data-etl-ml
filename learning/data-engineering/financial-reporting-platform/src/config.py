# src/config.py
import os
from dataclasses import dataclass, field
from typing import Dict, List
import yaml


@dataclass
class DataSourceConfig:
    """Configuration for data sources"""
    name: str
    type: str
    country_codes: List[str]
    currency_mapping: Dict[str, str]
    schema_path: str


@dataclass
class PipelineConfig:
    """Main pipeline configuration"""
    bronze_path: str = "data/bronze"
    silver_path: str = "data/silver"
    gold_path: str = "data/gold"
    checkpoint_path: str = "data/checkpoints"
    output_path: str = "output"

    # Processing settings
    batch_size: int = 10000
    partitions: List[str] = field(default_factory=lambda: ["country", "year", "month"])

    # Monitoring
    anomaly_threshold: float = 3.0
    quality_threshold: float = 0.95

    # Countries
    supported_countries: List[str] = field(default_factory=lambda: ["TH", "VN", "ID"])

    # Business rules
    high_value_threshold: float = 1000000
    variance_tolerance: float = 0.1

    # Data generation
    records_per_country: Dict[str, int] = field(default_factory=lambda: {
        "TH": 2000,
        "VN": 2000,
        "ID": 2000
    })


class ConfigLoader:
    """Load configuration from YAML files"""

    @staticmethod
    def load_config(config_path: str = "config.yaml") -> PipelineConfig:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
        else:
            config_dict = {}

        return PipelineConfig(**config_dict)

    @staticmethod
    def load_data_sources() -> Dict[str, DataSourceConfig]:
        """Load data source configurations"""
        return {
            "sap_erp": DataSourceConfig(
                name="SAP_ERP",
                type="erp",
                country_codes=["TH", "VN"],
                currency_mapping={"TH": "THB", "VN": "VND"},
                schema_path="schemas/sap_schema.json"
            ),
            "oracle_erp": DataSourceConfig(
                name="Oracle_ERP",
                type="erp",
                country_codes=["ID"],
                currency_mapping={"ID": "IDR"},
                schema_path="schemas/oracle_schema.json"
            ),
            "pos_system": DataSourceConfig(
                name="POS_System",
                type="pos",
                country_codes=["TH", "VN", "ID"],
                currency_mapping={"TH": "THB", "VN": "VND", "ID": "IDR"},
                schema_path="schemas/pos_schema.json"
            )
        }


# Global configuration
config = ConfigLoader.load_config()
data_sources = ConfigLoader.load_data_sources()
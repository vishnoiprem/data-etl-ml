"""
SCB AML Platform — Global Configuration
All environment-level settings in one place.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────
# BASE PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
DUMMY_DIR = DATA_DIR / "dummy"
OUTPUT_DIR = BASE_DIR / "output"

# ─────────────────────────────────────────────
# 15 COUNTRY CODES
# ─────────────────────────────────────────────
COUNTRIES = ["SG", "HK", "MY", "TH", "IN", "KR", "TW",
             "UK", "US", "AE", "KE", "NG", "PK", "BD", "CN"]

COUNTRY_CURRENCIES = {
    "SG": "SGD", "HK": "HKD", "MY": "MYR", "TH": "THB",
    "IN": "INR", "KR": "KRW", "TW": "TWD", "UK": "GBP",
    "US": "USD", "AE": "AED", "KE": "KES", "NG": "NGN",
    "PK": "PKR", "BD": "BDT", "CN": "CNY"
}

# Approximate USD FX rates (illustrative)
FX_TO_USD = {
    "SGD": 0.74, "HKD": 0.13, "MYR": 0.22, "THB": 0.028,
    "INR": 0.012, "KRW": 0.00075, "TWD": 0.031, "GBP": 1.27,
    "USD": 1.00, "AED": 0.27, "KES": 0.0069, "NGN": 0.0013,
    "PKR": 0.0035, "BDT": 0.0091, "CNY": 0.14
}

# ─────────────────────────────────────────────
# HADOOP / HIVE (local simulation paths)
# ─────────────────────────────────────────────
HDFS_ROOT = str(DATA_DIR / "hdfs_sim")
HIVE_METASTORE_DB = str(DATA_DIR / "hive_metastore.db")

# HDFS partitioning template: /raw/{country_code}/{source}/{YYYY}/{MM}/{DD}/
HDFS_PARTITION_TEMPLATE = "/raw/{country_code}/{source}/{year}/{month}/{day}/"

# ─────────────────────────────────────────────
# SPARK
# ─────────────────────────────────────────────
SPARK_APP_NAME = "SCB_AML_Platform"
SPARK_MASTER = "local[*]"
SPARK_EXECUTOR_MEMORY = "2g"
SPARK_DRIVER_MEMORY = "2g"

# Entity resolution thresholds
JARO_WINKLER_THRESHOLD = 0.85
ID_EXACT_MATCH_WEIGHT = 1.0
NAME_FUZZY_WEIGHT = 0.6
PHONETIC_WEIGHT = 0.4

# ─────────────────────────────────────────────
# ELASTICSEARCH (Lucid Search)
# ─────────────────────────────────────────────
ES_HOST = os.getenv("ES_HOST", "localhost")
ES_PORT = int(os.getenv("ES_PORT", "9200"))
ES_SCHEME = os.getenv("ES_SCHEME", "http")
ES_INDEX_ENTITY = "entity_master"
ES_INDEX_TXN = "transaction_summary"
ES_INDEX_SCREENING = "screening_results"
ES_INDEX_GRAPH = "relationship_graph"
ES_SHARDS = 5
ES_REPLICAS = 1  # 2 in prod; 1 for local dev

# ─────────────────────────────────────────────
# AML DETECTION ENGINE
# ─────────────────────────────────────────────
# Threshold monitoring (USD equivalent)
CTR_THRESHOLD_USD = 10_000       # Currency Transaction Report
STR_HIGH_VALUE_USD = 50_000      # Auto-escalate to STR review
STRUCTURING_WINDOW_DAYS = 3      # Days to detect structuring pattern
STRUCTURING_COUNT_THRESHOLD = 3  # Min txns in window to flag

# Risk score bands
RISK_LOW_MAX = 30
RISK_MEDIUM_MAX = 60
RISK_HIGH_MIN = 61

# ─────────────────────────────────────────────
# KAFKA (ingestion simulation)
# ─────────────────────────────────────────────
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC_TXN = "scb.transactions.raw"
KAFKA_TOPIC_WIRE = "scb.wire_transfers.raw"

# ─────────────────────────────────────────────
# REGULATORY
# ─────────────────────────────────────────────
DATA_RETENTION_YEARS = 7
PROCESSING_SLA_HOURS = 24   # T+1

REGULATORS = {
    "SG": "MAS", "UK": "FCA", "US": "FinCEN",
    "HK": "HKMA", "IN": "RBI", "MY": "BNM",
    "AE": "CBUAE", "KR": "FSC", "TH": "BOT",
    "TW": "FSC_TW", "KE": "CBK", "NG": "CBN",
    "PK": "SBP", "BD": "BB", "CN": "PBOC"
}

# ─────────────────────────────────────────────
# LUCID SEARCH API
# ─────────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8000
API_TITLE = "Lucid Search — SCB AML Entity Search"
API_VERSION = "1.0.0"

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

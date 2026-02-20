"""
SCB AML Platform — Hive Simulator (SQLite backend)
Since we run locally without a Hadoop cluster, this module:
  - Creates SQLite tables mirroring the Hive ODS/CDM/ADS schema
  - Loads dummy Parquet data into these tables
  - Provides a query interface used by Spark jobs in local mode
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from scb_aml_platform.config.settings import DUMMY_DIR, HIVE_METASTORE_DB, COUNTRIES

DUMMY_DIR = Path(DUMMY_DIR)
DB_PATH = Path(HIVE_METASTORE_DB)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def load_ods_tables():
    """Load dummy parquet files into SQLite ODS tables."""
    conn = get_connection()
    files = {
        "ods_customers": "customers.parquet",
        "ods_accounts": "accounts.parquet",
        "ods_transactions": "transactions.parquet",
        "ods_wire_transfers": "wire_transfers.parquet",
        "ods_kyc_records": "kyc_records.parquet",
        "ods_relationships": "relationships.parquet",
        "ref_sanctions_list": "sanctions_list.parquet",
    }

    for table_name, parquet_file in files.items():
        path = DUMMY_DIR / parquet_file
        if not path.exists():
            logger.warning(f"Parquet file not found: {path} — skipping {table_name}")
            continue

        df = pd.read_parquet(path)

        # Flatten list columns (SQLite doesn't support arrays)
        for col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str)

        df.to_sql(table_name, conn, if_exists="replace", index=False)
        logger.info(f"Loaded {len(df):,} rows into {table_name}")

    conn.close()
    logger.success("ODS tables loaded into local Hive simulator (SQLite)")


def query(sql: str) -> pd.DataFrame:
    """Execute SQL and return a DataFrame."""
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn)
        return df
    finally:
        conn.close()


def get_table_info():
    """List all tables and row counts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]

    results = {}
    for t in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        results[t] = cursor.fetchone()[0]

    conn.close()
    return results


if __name__ == "__main__":
    load_ods_tables()
    info = get_table_info()
    print("\nHive Simulator — Table Summary:")
    print("-" * 40)
    for table, count in info.items():
        print(f"  {table:<35} {count:>8,} rows")

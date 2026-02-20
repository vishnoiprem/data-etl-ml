"""
SCB AML Platform — Elasticsearch Index Manager
Creates / updates the 4 Lucid Search indices and loads data.

Indices:
  entity_master       — golden entity profiles
  transaction_summary — aggregated txn metrics
  screening_results   — sanctions/PEP match results
  relationship_graph  — entity relationship edges

Requires: Elasticsearch 8.x running on localhost:9200
If ES is not available, data is saved to JSON files for inspection.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scb_aml_platform.config.settings import (
    ES_HOST, ES_PORT, ES_SCHEME,
    ES_INDEX_ENTITY, ES_INDEX_TXN, ES_INDEX_SCREENING, ES_INDEX_GRAPH,
    BASE_DIR
)

PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"
DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"
MAPPINGS_DIR = Path(__file__).parent.parent / "mappings"
ES_DATA_DIR = Path(BASE_DIR) / "data" / "es_simulation"
ES_DATA_DIR.mkdir(parents=True, exist_ok=True)


def get_es_client():
    """Return ES client or None if unavailable."""
    try:
        from elasticsearch import Elasticsearch
        client = Elasticsearch(
            hosts=[{"host": ES_HOST, "port": ES_PORT, "scheme": ES_SCHEME}],
            request_timeout=30,
        )
        if client.ping():
            logger.info(f"Connected to Elasticsearch: {ES_HOST}:{ES_PORT}")
            return client
        logger.warning("Elasticsearch ping failed. Using file simulation.")
        return None
    except Exception as e:
        logger.warning(f"Elasticsearch not available ({e}). Using file simulation.")
        return None


def load_mapping(index_name: str) -> dict:
    """Load index mapping from JSON file."""
    mapping_file = MAPPINGS_DIR / f"{index_name}_mapping.json"
    if mapping_file.exists():
        with open(mapping_file) as f:
            return json.load(f)
    return {}


def create_index(client, index_name: str):
    """Create ES index with mapping if it doesn't exist."""
    if client.indices.exists(index=index_name):
        logger.info(f"Index {index_name} already exists")
        return
    mapping = load_mapping(index_name)
    client.indices.create(index=index_name, body=mapping)
    logger.info(f"Created index: {index_name}")


def bulk_index(client, index_name: str, docs: list[dict]):
    """Bulk index documents into Elasticsearch."""
    from elasticsearch.helpers import bulk

    actions = [
        {"_index": index_name, "_id": doc.get("entity_id") or doc.get("screening_id") or str(i),
         "_source": doc}
        for i, doc in enumerate(docs)
    ]
    success, errors = bulk(client, actions, raise_on_error=False)
    logger.info(f"  Indexed {success} docs into {index_name} (errors: {len(errors)})")


def save_to_file(index_name: str, docs: list[dict]):
    """Save documents to JSON file (fallback when ES is unavailable)."""
    out = ES_DATA_DIR / f"{index_name}.json"
    with open(out, "w") as f:
        json.dump(docs, f, indent=2, default=str)
    logger.info(f"  Saved {len(docs)} docs to {out}")


def _df_to_docs(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts, handling non-serializable types."""
    docs = []
    for record in df.to_dict("records"):
        clean = {}
        for k, v in record.items():
            if isinstance(v, list):
                clean[k] = [str(x) for x in v]
            elif pd.isna(v) if not isinstance(v, (list, dict)) else False:
                clean[k] = None
            else:
                clean[k] = v
        docs.append(clean)
    return docs


# ─────────────────────────────────────────────
# INDEX 1: entity_master
# ─────────────────────────────────────────────
def index_entity_master(client):
    """Index golden entity profiles."""
    path = PROCESSED_DIR / "entity_master.parquet"
    if not path.exists():
        path = DUMMY_DIR / "customers.parquet"

    df = pd.read_parquet(path)

    # Merge with risk profiles if available
    risk_path = PROCESSED_DIR / "customer_risk_profiles.parquet"
    if risk_path.exists():
        risk = pd.read_parquet(risk_path)[
            ["customer_id", "composite_aml_score", "risk_band", "crs", "trs", "nrs"]
        ]
        merge_key = "entity_id" if "entity_id" in df.columns else "customer_id"
        df = df.merge(risk, left_on=merge_key, right_on="customer_id", how="left")

    df["updated_at"] = datetime.utcnow().isoformat()

    # Rename for ES schema
    if "customer_id" in df.columns and "entity_id" not in df.columns:
        df = df.rename(columns={"customer_id": "entity_id"})
    if "risk_rating" in df.columns and "risk_score" not in df.columns:
        df["risk_score"] = df["risk_rating"].map(
            {"low": 20, "medium": 50, "high": 80}
        ).fillna(20).astype(int)

    docs = _df_to_docs(df)
    logger.info(f"Indexing {len(docs):,} entity profiles → {ES_INDEX_ENTITY}")

    if client:
        create_index(client, ES_INDEX_ENTITY)
        bulk_index(client, ES_INDEX_ENTITY, docs)
    else:
        save_to_file(ES_INDEX_ENTITY, docs)


# ─────────────────────────────────────────────
# INDEX 2: transaction_summary
# ─────────────────────────────────────────────
def index_transaction_summary(client):
    """Index aggregated transaction metrics."""
    path = PROCESSED_DIR / "agg_customer_txn_summary.parquet"
    if not path.exists():
        logger.warning("Transaction summary not found, skipping.")
        return

    df = pd.read_parquet(path)
    if "customer_id" in df.columns and "entity_id" not in df.columns:
        df = df.rename(columns={"customer_id": "entity_id"})

    docs = _df_to_docs(df)
    logger.info(f"Indexing {len(docs):,} txn summaries → {ES_INDEX_TXN}")

    if client:
        create_index(client, ES_INDEX_TXN)
        bulk_index(client, ES_INDEX_TXN, docs)
    else:
        save_to_file(ES_INDEX_TXN, docs)


# ─────────────────────────────────────────────
# INDEX 3: screening_results
# ─────────────────────────────────────────────
def index_screening_results(client):
    """Index sanctions/PEP screening results."""
    path = PROCESSED_DIR / "screening_alerts.parquet"
    if not path.exists():
        logger.warning("Screening alerts not found, skipping.")
        return

    df = pd.read_parquet(path)
    docs = _df_to_docs(df)
    logger.info(f"Indexing {len(docs)} screening results → {ES_INDEX_SCREENING}")

    if client:
        create_index(client, ES_INDEX_SCREENING)
        bulk_index(client, ES_INDEX_SCREENING, docs)
    else:
        save_to_file(ES_INDEX_SCREENING, docs)


# ─────────────────────────────────────────────
# INDEX 4: relationship_graph
# ─────────────────────────────────────────────
def index_relationship_graph(client):
    """Index entity relationship edges."""
    path = DUMMY_DIR / "relationships.parquet"
    df = pd.read_parquet(path)
    docs = _df_to_docs(df)
    logger.info(f"Indexing {len(docs)} relationship edges → {ES_INDEX_GRAPH}")

    if client:
        create_index(client, ES_INDEX_GRAPH)
        bulk_index(client, ES_INDEX_GRAPH, docs)
    else:
        save_to_file(ES_INDEX_GRAPH, docs)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def run():
    logger.info("=" * 60)
    logger.info("Elasticsearch Index Manager — Lucid Search")
    logger.info("=" * 60)

    client = get_es_client()

    index_entity_master(client)
    index_transaction_summary(client)
    index_screening_results(client)
    index_relationship_graph(client)

    if client is None:
        logger.info(f"\nES simulation data saved to: {ES_DATA_DIR}")
        logger.info("To use real ES: start Elasticsearch 8.x on localhost:9200")


if __name__ == "__main__":
    run()

"""
SCB AML Platform — Lucid Search Engine (Core)
High-risk entity identification across 15 countries.

Search modes:
  1. Fuzzy name        — Jaro-Winkler + edit distance
  2. Phonetic          — Double Metaphone encoding
  3. Cross-script      — Arabic ↔ Latin, Chinese ↔ Pinyin
  4. Wildcard          — n-gram partial matching
  5. Multi-country     — federated across all 15 country indices
  6. Filtered          — combine name + risk level + country + PEP flag

When Elasticsearch is available → ES queries
When not available              → Pandas in-memory search (same interface)
"""

import sys
import json
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import jellyfish
from loguru import logger

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from scb_aml_platform.config.settings import (
    BASE_DIR, JARO_WINKLER_THRESHOLD,
    ES_HOST, ES_PORT, ES_SCHEME,
    ES_INDEX_ENTITY, ES_INDEX_TXN, ES_INDEX_SCREENING, ES_INDEX_GRAPH
)

PROCESSED_DIR = Path(BASE_DIR) / "data" / "processed"
DUMMY_DIR = Path(BASE_DIR) / "data" / "dummy"
ES_DATA_DIR = Path(BASE_DIR) / "data" / "es_simulation"


class LucidSearchEngine:
    """
    Core search engine. Uses ES when available, falls back to Pandas.
    Same external interface in both modes.
    """

    def __init__(self):
        self._es = self._connect_es()
        self._load_in_memory()

    def _connect_es(self):
        try:
            from elasticsearch import Elasticsearch
            client = Elasticsearch(
                hosts=[{"host": ES_HOST, "port": ES_PORT, "scheme": ES_SCHEME}],
                request_timeout=10,
            )
            if client.ping():
                logger.info("LucidSearch: connected to Elasticsearch")
                return client
        except Exception:
            pass
        logger.info("LucidSearch: Elasticsearch unavailable, using in-memory mode")
        return None

    def _load_in_memory(self):
        """Load entity data into memory for Pandas-based search."""
        # Try processed entity master first, fall back to raw customers
        entity_path = PROCESSED_DIR / "entity_master.parquet"
        if not entity_path.exists():
            entity_path = DUMMY_DIR / "customers.parquet"

        self.entities = pd.read_parquet(entity_path) if entity_path.exists() else pd.DataFrame()

        # Normalise column names
        if "customer_id" in self.entities.columns and "entity_id" not in self.entities.columns:
            self.entities = self.entities.rename(columns={"customer_id": "entity_id"})

        risk_path = PROCESSED_DIR / "customer_risk_profiles.parquet"
        if risk_path.exists():
            risk = pd.read_parquet(risk_path)[
                ["customer_id", "composite_aml_score", "risk_band", "crs", "trs", "nrs"]
            ].rename(columns={"customer_id": "entity_id"})
            self.entities = self.entities.merge(risk, on="entity_id", how="left")

        txn_path = PROCESSED_DIR / "agg_customer_txn_summary.parquet"
        if txn_path.exists():
            txn = pd.read_parquet(txn_path).rename(columns={"customer_id": "entity_id"})
            self.entities = self.entities.merge(
                txn[["entity_id", "volume_usd_30d", "count_30d",
                     "cross_border_vol_usd", "unique_counterparties"]],
                on="entity_id", how="left"
            )

        self.screening = pd.DataFrame()
        scr_path = PROCESSED_DIR / "screening_alerts.parquet"
        if scr_path.exists():
            self.screening = pd.read_parquet(scr_path)

        self.relationships = pd.DataFrame()
        rel_path = DUMMY_DIR / "relationships.parquet"
        if rel_path.exists():
            self.relationships = pd.read_parquet(rel_path)

        logger.info(f"LucidSearch: loaded {len(self.entities):,} entities in memory")

    # ─────────────────────────────────────────
    # PUBLIC SEARCH API
    # ─────────────────────────────────────────
    def search(
        self,
        query: str,
        countries: Optional[list] = None,
        risk_band: Optional[str] = None,
        pep_only: bool = False,
        max_results: int = 20,
        search_mode: str = "all",    # fuzzy | phonetic | exact | all
    ) -> dict:
        """
        Main search entry point.
        Returns: {results: [...], total: int, search_time_ms: float, query: str}
        """
        import time
        t0 = time.time()

        if self._es:
            results = self._es_search(query, countries, risk_band, pep_only, max_results)
        else:
            results = self._pandas_search(query, countries, risk_band, pep_only,
                                          max_results, search_mode)

        elapsed_ms = round((time.time() - t0) * 1000, 1)
        return {
            "query": query,
            "results": results,
            "total": len(results),
            "search_time_ms": elapsed_ms,
            "backend": "elasticsearch" if self._es else "in_memory",
        }

    def get_entity_profile(self, entity_id: str) -> dict:
        """Full entity profile: entity + txn summary + screening + relationships."""
        entity = self._get_entity(entity_id)
        txn_summary = self._get_txn_summary(entity_id)
        screening = self._get_screening(entity_id)
        relationships = self._get_relationships(entity_id)

        return {
            "entity": entity,
            "transaction_summary": txn_summary,
            "screening_results": screening,
            "related_entities": relationships,
        }

    # ─────────────────────────────────────────
    # ELASTICSEARCH SEARCH
    # ─────────────────────────────────────────
    def _es_search(self, query: str, countries, risk_band, pep_only, max_results) -> list:
        must = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["customer_name^3", "name_variants^2", "name_local_script"],
                    "fuzziness": "AUTO",
                    "operator": "or",
                }
            }
        ]
        filters = []
        if countries:
            filters.append({"terms": {"country_codes": countries}})
        if risk_band:
            filters.append({"term": {"risk_band": risk_band.upper()}})
        if pep_only:
            filters.append({"term": {"pep_flag": "Y"}})

        body = {
            "query": {"bool": {"must": must, "filter": filters}},
            "size": max_results,
            "sort": [{"risk_score": "desc"}, "_score"],
        }

        response = self._es.search(index=ES_INDEX_ENTITY, body=body)
        return [hit["_source"] for hit in response["hits"]["hits"]]

    # ─────────────────────────────────────────
    # PANDAS IN-MEMORY SEARCH
    # ─────────────────────────────────────────
    def _pandas_search(self, query: str, countries, risk_band, pep_only,
                       max_results, mode) -> list:
        if self.entities.empty:
            return []

        df = self.entities.copy()

        # ── Country filter
        if countries:
            country_col = "country_code" if "country_code" in df.columns else "country_codes"
            df = df[df[country_col].isin(countries)]

        # ── Risk band filter
        if risk_band and "risk_band" in df.columns:
            df = df[df["risk_band"].str.upper() == risk_band.upper()]

        # ── PEP filter
        if pep_only and "pep_flag" in df.columns:
            df = df[df["pep_flag"] == "Y"]

        if df.empty:
            return []

        # ── Name matching
        query_norm = query.upper().strip()

        def name_score(name: str) -> float:
            if not isinstance(name, str):
                return 0.0
            name_norm = name.upper().strip()
            # Exact
            if query_norm == name_norm:
                return 1.0
            # Contains
            if query_norm in name_norm or name_norm in query_norm:
                return 0.90
            # Fuzzy
            jw = jellyfish.jaro_winkler_similarity(query_norm, name_norm)
            # Phonetic
            ph = 0.82 if (jellyfish.metaphone(query_norm) ==
                          jellyfish.metaphone(name_norm) and
                          jellyfish.metaphone(query_norm)) else 0.0
            return max(jw, ph)

        name_col = "customer_name" if "customer_name" in df.columns else "entity_name"
        df["_score"] = df[name_col].apply(name_score)

        # Filter minimum score
        df = df[df["_score"] >= 0.70].copy()

        # Sort: score desc, then risk desc
        sort_cols = ["_score"]
        if "composite_aml_score" in df.columns:
            sort_cols.append("composite_aml_score")
        elif "risk_score" in df.columns:
            sort_cols.append("risk_score")

        df = df.sort_values(sort_cols, ascending=False).head(max_results)

        results = []
        for _, row in df.iterrows():
            r = {k: v for k, v in row.items() if not k.startswith("_")}
            r["match_score"] = round(row["_score"] * 100, 1)
            # Sanitise non-serialisable types
            for k, v in list(r.items()):
                if isinstance(v, list):
                    pass
                elif isinstance(v, float) and pd.isna(v):
                    r[k] = None
            results.append(r)

        return results

    # ─────────────────────────────────────────
    # ENTITY DETAIL HELPERS
    # ─────────────────────────────────────────
    def _get_entity(self, entity_id: str) -> dict:
        col = "entity_id" if "entity_id" in self.entities.columns else "customer_id"
        matches = self.entities[self.entities[col] == entity_id]
        if matches.empty:
            return {}
        row = matches.iloc[0].to_dict()
        return {k: (None if (isinstance(v, float) and pd.isna(v)) else v)
                for k, v in row.items()}

    def _get_txn_summary(self, entity_id: str) -> dict:
        txn_path = PROCESSED_DIR / "agg_customer_txn_summary.parquet"
        if not txn_path.exists():
            return {}
        txn = pd.read_parquet(txn_path)
        col = "customer_id"
        matches = txn[txn[col] == entity_id]
        return matches.iloc[0].to_dict() if not matches.empty else {}

    def _get_screening(self, entity_id: str) -> list:
        if self.screening.empty:
            return []
        col = "customer_id"
        matches = self.screening[self.screening[col] == entity_id]
        return matches.to_dict("records") if not matches.empty else []

    def _get_relationships(self, entity_id: str) -> list:
        if self.relationships.empty:
            return []
        rel = self.relationships[
            (self.relationships["entity_id"] == entity_id) |
            (self.relationships["related_entity_id"] == entity_id)
        ]
        return rel.head(20).to_dict("records") if not rel.empty else []

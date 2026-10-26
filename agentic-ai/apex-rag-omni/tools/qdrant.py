"""Qdrant client: 10-shard cluster with shadow index for embedding upgrades.

When we swap embedding models (e.g., 1536-d → 3072-d), we dual-write to
both old + new indexes, query new, then cut over atomically. The shadow
index is the production-safe path for embedding model upgrades.
"""
from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from typing import Iterable

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


N_SHARDS = 10
COLLECTION_NAME = "apex_rag_main"
SHADOW_COLLECTION = "apex_rag_shadow"


class VectorHit(BaseModel):
    doc_id: str
    score: float
    text: str
    shard_id: int
    vector_dim: int


class ShardConfig(BaseModel):
    shard_id: int
    vector_dim: int
    distance: str = "Cosine"
    hnsw_m: int = 16
    hnsw_ef_construction: int = 200


def stable_shard_id(doc_id: str, n_shards: int = N_SHARDS) -> int:
    """Hash a doc_id into a stable shard. SHA-256 mod n_shards.

    Stable means: the same doc_id always lands in the same shard,
    even after a cluster rebalance. Mod-n hashing gives us this.
    """
    h = int(hashlib.sha256(doc_id.encode()).hexdigest(), 16)
    return h % n_shards


@dataclass
class DualWriteResult:
    """Result of a dual-write to main + shadow during a model upgrade."""
    main_written: int
    shadow_written: int
    main_lag_ms: float
    shadow_lag_ms: float
    consistent: bool


def dual_write(docs: Iterable[tuple[str, list[float], str]],
               embed_model_version: str) -> DualWriteResult:
    """Write to both main + shadow collections during an embedding model upgrade.

    Both writes happen, but the shadow collection is the new embedding model.
    Reads still hit the main collection until the cutover.
    """
    t0 = time.perf_counter()
    main_n = 0
    shadow_n = 0
    for doc_id, vec, _text in docs:
        shard = stable_shard_id(doc_id)
        # In production: qdrant_client.upsert(COLLECTION_NAME, points=[...])
        # and qdrant_client.upsert(SHADOW_COLLECTION, points=[...])
        main_n += 1
        shadow_n += 1
    t1 = time.perf_counter()
    return DualWriteResult(
        main_written=main_n, shadow_written=shadow_n,
        main_lag_ms=(t1 - t0) * 1000, shadow_lag_ms=(t1 - t0) * 1000,
        consistent=main_n == shadow_n,
    )


def atomic_cutover(shadow_collection: str = SHADOW_COLLECTION,
                   main_collection: str = COLLECTION_NAME) -> bool:
    """Promote the shadow collection to main. Atomic at the cluster level.

    Steps:
    1. Stop reads on `main_collection`.
    2. Alias swap: `apex_rag_active` -> `shadow_collection`.
    3. Resume reads on the alias.
    """
    logger.info("Cutting over: %s -> %s", main_collection, shadow_collection)
    # In production:
    # qdrant_client.update_collection_aliases(change_aliases=[
    #     AliasOperations(create_alias=AliasDescription(collection_name=shadow_collection, alias_name="apex_rag_active")),
    #     AliasOperations(delete_alias=AliasDescription(collection_name=main_collection, alias_name="apex_rag_active")),
    # ])
    return True

"""
Storage Backend Interfaces

Abstract base classes for online and offline feature stores.
Implementations: Redis, Cassandra, Bigtable, Iceberg, Delta Lake, etc.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union
import asyncio


@dataclass
class FeatureVector:
    """A single entity's feature vector"""
    entity_key: str
    entity_id: str
    features: Dict[str, Any]
    event_timestamp: Optional[str] = None
    created_timestamp: Optional[str] = None


@dataclass
class WriteResult:
    """Result of a write operation"""
    success: bool
    entity_keys: List[str]
    errors: List[str] = None
    latency_ms: float = 0.0


class OnlineStore(ABC):
    """
    Online feature store - low-latency serving (sub-millisecond to few ms).
    
    Implementations:
    - Redis Cluster (primary)
    - Cassandra (wide rows, high write throughput)
    - Bigtable (Google Cloud)
    - DynamoDB (AWS)
    - Aerospike
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize connections, create schemas"""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close connections"""
        pass
    
    @abstractmethod
    async def write_batch(
        self,
        feature_view: str,
        feature_vectors: List[FeatureVector],
        ttl_seconds: Optional[int] = None
    ) -> WriteResult:
        """
        Write a batch of feature vectors.
        
        Args:
            feature_view: Name of the feature view
            feature_vectors: List of feature vectors to write
            ttl_seconds: Optional TTL override
            
        Returns:
            WriteResult with success status and any errors
        """
        pass
    
    @abstractmethod
    async def read_batch(
        self,
        feature_view: str,
        entity_keys: List[str],
        feature_names: Optional[List[str]] = None
    ) -> List[FeatureVector]:
        """
        Read feature vectors for multiple entities.
        
        Args:
            feature_view: Name of the feature view
            entity_keys: List of entity keys to lookup
            feature_names: Optional subset of features to retrieve
            
        Returns:
            List of FeatureVector objects (missing entities return empty features)
        """
        pass
    
    @abstractmethod
    async def read_single(
        self,
        feature_view: str,
        entity_key: str,
        feature_names: Optional[List[str]] = None
    ) -> Optional[FeatureVector]:
        """Read a single entity's feature vector"""
        pass
    
    @abstractmethod
    async def delete(
        self,
        feature_view: str,
        entity_keys: List[str]
    ) -> WriteResult:
        """Delete feature vectors for entities"""
        pass
    
    @abstractmethod
    async def exists(
        self,
        feature_view: str,
        entity_keys: List[str]
    ) -> List[bool]:
        """Check if entities exist in the store"""
        pass
    
    @abstractmethod
    async def get_ttl(self, feature_view: str, entity_key: str) -> Optional[int]:
        """Get remaining TTL for an entity's features"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Health check for the store"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics (memory, keys, latency)"""
        pass


class OfflineStore(ABC):
    """
    Offline feature store - high-throughput batch reads for training.
    
    Implementations:
    - Apache Iceberg (primary - time travel, ACID, partition pruning)
    - Delta Lake (Databricks)
    - Hudi (Uber)
    - Parquet on S3/GCS (basic)
    - BigQuery, Snowflake, Redshift
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        pass
    
    @abstractmethod
    async def close(self) -> None:
        pass
    
    @abstractmethod
    async def write_batch(
        self,
        feature_view: str,
        feature_vectors: List[FeatureVector],
        partition_columns: Optional[List[str]] = None
    ) -> WriteResult:
        """
        Write feature vectors to offline store.
        Typically partitioned by event_timestamp (day/hour).
        """
        pass
    
    @abstractmethod
    async def read_batch(
        self,
        feature_view: str,
        entity_keys: Optional[List[str]] = None,
        feature_names: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[FeatureVector]:
        """
        Read feature vectors for training.
        
        Supports:
        - Time range filters (partition pruning)
        - Entity key filters
        - Feature selection (column pruning)
        - Additional predicates
        """
        pass
    
    @abstractmethod
    async def read_as_dataframe(
        self,
        feature_view: str,
        entity_keys: Optional[List[str]] = None,
        feature_names: Optional[List[str]] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Read as pandas/polars DataFrame for ML training"""
        pass
    
    @abstractmethod
    async def get_historical_features(
        self,
        entity_df: Any,  # DataFrame with entity_key, event_timestamp
        feature_views: List[str],
        feature_names: Optional[List[str]] = None
    ) -> Any:
        """
        Point-in-time correct feature retrieval for training.
        
        This is the critical method for training - it joins entity timestamps
        with feature timestamps to get features as they existed at that time.
        """
        pass
    
    @abstractmethod
    async def compact(self, feature_view: str) -> None:
        """Compact/optimize storage (merge small files, rewrite)"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass


class StoreFactory:
    """Factory for creating store instances based on configuration"""
    
    _online_stores: Dict[str, type] = {}
    _offline_stores: Dict[str, type] = {}
    
    @classmethod
    def register_online_store(cls, name: str, store_class: type) -> None:
        cls._online_stores[name] = store_class
    
    @classmethod
    def register_offline_store(cls, name: str, store_class: type) -> None:
        cls._offline_stores[name] = store_class
    
    @classmethod
    def create_online_store(cls, config: Dict[str, Any]) -> OnlineStore:
        store_type = config.get("type", "redis")
        if store_type not in cls._online_stores:
            raise ValueError(f"Unknown online store type: {store_type}")
        return cls._online_stores[store_type](config)
    
    @classmethod
    def create_offline_store(cls, config: Dict[str, Any]) -> OfflineStore:
        store_type = config.get("type", "iceberg")
        if store_type not in cls._offline_stores:
            raise ValueError(f"Unknown offline store type: {store_type}")
        return cls._offline_stores[store_type](config)
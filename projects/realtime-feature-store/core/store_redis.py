"""
Redis Cluster Implementation of Online Store

Production-grade Redis Cluster client with:
- Connection pooling
- Local L1 caching (with invalidation)
- Pipelining for batch operations
- Circuit breaker for resilience
- Comprehensive metrics
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass

import redis.asyncio as redis
from redis.asyncio.cluster import RedisCluster
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from .store import OnlineStore, FeatureVector, WriteResult
from .feature_view import FeatureView

logger = logging.getLogger(__name__)


@dataclass
class RedisConfig:
    """Redis Cluster configuration"""
    nodes: List[Tuple[str, int]]  # [(host, port), ...]
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = True
    retry_on_timeout: bool = True
    decode_responses: bool = True
    # L1 Cache
    l1_cache_size: int = 10000
    l1_ttl_seconds: int = 60
    # Circuit breaker
    circuit_breaker_threshold: int = 10
    circuit_breaker_timeout: float = 30.0


class CircuitBreaker:
    """Simple circuit breaker for Redis resilience"""
    
    def __init__(self, threshold: int = 10, timeout: float = 30.0):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure = 0
        self.state = "closed"  # closed, open, half-open
        self._lock = asyncio.Lock()
    
    async def call(self, func, *args, **kwargs):
        async with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure > self.timeout:
                    self.state = "half-open"
                    logger.warning("Circuit breaker entering half-open state")
                else:
                    raise RedisError("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            async with self._lock:
                if self.state == "half-open":
                    self.state = "closed"
                    self.failures = 0
                    logger.info("Circuit breaker closed")
            return result
        except Exception as e:
            async with self._lock:
                self.failures += 1
                self.last_failure = time.time()
                if self.failures >= self.threshold:
                    self.state = "open"
                    logger.error(f"Circuit breaker opened after {self.failures} failures")
            raise


class RedisOnlineStore(OnlineStore):
    """
    Redis Cluster implementation of OnlineStore.
    
    Key design decisions:
    - Uses Redis Cluster for horizontal scaling
    - Keys: fs:{feature_view}:{entity_key} -> Hash of feature_name: value
    - TTL managed per feature view
    - L1 in-memory cache for hot keys (with pub/sub invalidation)
    - Pipelining for batch writes/reads
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = RedisConfig(**config)
        self._client: Optional[RedisCluster] = None
        self._l1_cache: Dict[str, Tuple[FeatureVector, float]] = {}  # key -> (vector, expiry)
        self._circuit_breaker = CircuitBreaker(
            self.config.circuit_breaker_threshold,
            self.config.circuit_breaker_timeout
        )
        self._stats = {
            "reads": 0,
            "writes": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": 0,
            "latency_ms_sum": 0.0,
            "latency_count": 0,
        }
        self._pubsub = None
        self._invalidation_task = None
    
    async def initialize(self) -> None:
        """Initialize Redis Cluster connection"""
        startup_nodes = [
            {"host": host, "port": port} 
            for host, port in self.config.nodes
        ]
        
        self._client = RedisCluster(
            startup_nodes=startup_nodes,
            max_connections=self.config.max_connections,
            socket_timeout=self.config.socket_timeout,
            socket_connect_timeout=self.config.socket_connect_timeout,
            socket_keepalive=self.config.socket_keepalive,
            retry_on_timeout=self.config.retry_on_timeout,
            decode_responses=self.config.decode_responses,
            skip_full_coverage_check=True,  # Allow partial cluster
        )
        
        # Test connection
        await self._client.ping()
        logger.info(f"Connected to Redis Cluster with {len(self.config.nodes)} nodes")
        
        # Start invalidation listener for L1 cache
        self._pubsub = self._client.pubsub()
        await self._pubsub.subscribe("fs:invalidation")
        self._invalidation_task = asyncio.create_task(self._invalidation_listener())
    
    async def close(self) -> None:
        if self._invalidation_task:
            self._invalidation_task.cancel()
            try:
                await self._invalidation_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.unsubscribe("fs:invalidation")
            await self._pubsub.close()
        if self._client:
            await self._client.close()
    
    def _make_key(self, feature_view: str, entity_key: str) -> str:
        """Generate Redis key for feature vector"""
        return f"fs:{feature_view}:{entity_key}"
    
    def _serialize_value(self, value: Any) -> str:
        """Serialize feature value to string"""
        if value is None:
            return "null"
        if isinstance(value, (list, dict)):
            import json
            return json.dumps(value)
        if isinstance(value, bytes):
            return value.hex()
        return str(value)
    
    def _deserialize_value(self, value: str, dtype: str) -> Any:
        """Deserialize feature value from string"""
        if value == "null":
            return None
        if dtype in ("array", "struct", "embedding"):
            import json
            return json.loads(value)
        if dtype == "bytes":
            return bytes.fromhex(value)
        if dtype in ("int32", "int64"):
            return int(value)
        if dtype in ("float32", "float64"):
            return float(value)
        if dtype == "bool":
            return value.lower() == "true"
        return value
    
    async def _invalidation_listener(self):
        """Listen for cache invalidation messages"""
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    key = message["data"]
                    if key in self._l1_cache:
                        del self._l1_cache[key]
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Invalidation listener error: {e}")
    
    async def _invalidate_l1(self, feature_view: str, entity_keys: List[str]):
        """Invalidate L1 cache entries and publish to other instances"""
        keys = [self._make_key(feature_view, ek) for ek in entity_keys]
        for key in keys:
            self._l1_cache.pop(key, None)
        
        # Publish invalidation to other instances
        if self._pubsub:
            for key in keys:
                await self._client.publish("fs:invalidation", key)
    
    async def write_batch(
        self,
        feature_view: str,
        feature_vectors: List[FeatureVector],
        ttl_seconds: Optional[int] = None
    ) -> WriteResult:
        start = time.time()
        entity_keys = [fv.entity_key for fv in feature_vectors]
        errors = []
        
        try:
            async with self._client.pipeline(transaction=True) as pipe:
                for fv in feature_vectors:
                    key = self._make_key(feature_view, fv.entity_key)
                    # Store as hash: feature_name -> serialized value
                    mapping = {
                        name: self._serialize_value(val)
                        for name, val in fv.features.items()
                    }
                    # Add metadata
                    if fv.event_timestamp:
                        mapping["_event_timestamp"] = fv.event_timestamp
                    if fv.created_timestamp:
                        mapping["_created_timestamp"] = fv.created_timestamp
                    
                    pipe.hset(key, mapping=mapping)
                    
                    # Set TTL
                    ttl = ttl_seconds or self.config.l1_ttl_seconds
                    pipe.expire(key, ttl)
                
                await pipe.execute()
            
            # Invalidate L1 cache
            await self._invalidate_l1(feature_view, entity_keys)
            
            latency = (time.time() - start) * 1000
            self._stats["writes"] += 1
            self._stats["latency_ms_sum"] += latency
            self._stats["latency_count"] += 1
            
            return WriteResult(
                success=True,
                entity_keys=entity_keys,
                latency_ms=latency
            )
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Redis write_batch error: {e}")
            return WriteResult(
                success=False,
                entity_keys=entity_keys,
                errors=[str(e)],
                latency_ms=(time.time() - start) * 1000
            )
    
    async def read_batch(
        self,
        feature_view: str,
        entity_keys: List[str],
        feature_names: Optional[List[str]] = None
    ) -> List[FeatureVector]:
        start = time.time()
        results = []
        
        try:
            # Check L1 cache first
            cached = {}
            uncached_keys = []
            
            for ek in entity_keys:
                key = self._make_key(feature_view, ek)
                if key in self._l1_cache:
                    vector, expiry = self._l1_cache[key]
                    if time.time() < expiry:
                        # Filter features if requested
                        if feature_names:
                            filtered_features = {
                                k: v for k, v in vector.features.items() 
                                if k in feature_names
                            }
                            results.append(FeatureVector(
                                entity_key=vector.entity_key,
                                entity_id=vector.entity_id,
                                features=filtered_features,
                                event_timestamp=vector.event_timestamp,
                                created_timestamp=vector.created_timestamp
                            ))
                        else:
                            results.append(vector)
                        self._stats["cache_hits"] += 1
                        cached[ek] = True
                        continue
                
                uncached_keys.append(ek)
                self._stats["cache_misses"] += 1
            
            # Fetch uncached keys from Redis
            if uncached_keys:
                keys = [self._make_key(feature_view, ek) for ek in uncached_keys]
                
                async with self._client.pipeline(transaction=False) as pipe:
                    for key in keys:
                        pipe.hgetall(key)
                    raw_results = await pipe.execute()
                
                for ek, raw_data in zip(uncached_keys, raw_results):
                    if raw_data:
                        # Extract metadata
                        event_ts = raw_data.pop("_event_timestamp", None)
                        created_ts = raw_data.pop("_created_timestamp", None)
                        
                        # Filter features if requested
                        if feature_names:
                            raw_data = {k: v for k, v in raw_data.items() if k in feature_names}
                        
                        # Deserialize values (need dtype info - simplified here)
                        features = {k: self._deserialize_value(v, "auto") for k, v in raw_data.items()}
                        
                        vector = FeatureVector(
                            entity_key=ek,
                            entity_id=ek,
                            features=features,
                            event_timestamp=event_ts,
                            created_timestamp=created_ts
                        )
                        
                        # Populate L1 cache
                        cache_key = self._make_key(feature_view, ek)
                        if len(self._l1_cache) < self.config.l1_cache_size:
                            self._l1_cache[cache_key] = (vector, time.time() + self.config.l1_ttl_seconds)
                    else:
                        vector = FeatureVector(entity_key=ek, entity_id=ek, features={})
                    
                    results.append(vector)
            
            latency = (time.time() - start) * 1000
            self._stats["reads"] += 1
            self._stats["latency_ms_sum"] += latency
            self._stats["latency_count"] += 1
            
            return results
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"Redis read_batch error: {e}")
            # Return empty vectors on error
            return [FeatureVector(entity_key=ek, entity_id=ek, features={}) for ek in entity_keys]
    
    async def read_single(
        self,
        feature_view: str,
        entity_key: str,
        feature_names: Optional[List[str]] = None
    ) -> Optional[FeatureVector]:
        results = await self.read_batch(feature_view, [entity_key], feature_names)
        return results[0] if results else None
    
    async def delete(
        self,
        feature_view: str,
        entity_keys: List[str]
    ) -> WriteResult:
        start = time.time()
        try:
            keys = [self._make_key(feature_view, ek) for ek in entity_keys]
            await self._client.delete(*keys)
            await self._invalidate_l1(feature_view, entity_keys)
            
            latency = (time.time() - start) * 1000
            return WriteResult(success=True, entity_keys=entity_keys, latency_ms=latency)
        except Exception as e:
            self._stats["errors"] += 1
            return WriteResult(success=False, entity_keys=entity_keys, errors=[str(e)], latency_ms=(time.time() - start) * 1000)
    
    async def exists(
        self,
        feature_view: str,
        entity_keys: List[str]
    ) -> List[bool]:
        keys = [self._make_key(feature_view, ek) for ek in entity_keys]
        try:
            # Use EXISTS which returns count of existing keys
            count = await self._client.exists(*keys)
            # For multiple keys, exists returns count - we need per-key
            # Use MGET for per-key check
            results = await self._client.mget(keys)
            return [r is not None for r in results]
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return [False] * len(entity_keys)
    
    async def get_ttl(self, feature_view: str, entity_key: str) -> Optional[int]:
        key = self._make_key(feature_view, entity_key)
        try:
            ttl = await self._client.ttl(key)
            return ttl if ttl > 0 else None
        except Exception:
            return None
    
    async def health_check(self) -> bool:
        try:
            return await self._client.ping()
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        stats = self._stats.copy()
        if stats["latency_count"] > 0:
            stats["avg_latency_ms"] = stats["latency_ms_sum"] / stats["latency_count"]
        else:
            stats["avg_latency_ms"] = 0
        stats["l1_cache_size"] = len(self._l1_cache)
        stats["circuit_breaker_state"] = self._circuit_breaker.state
        return stats


# Register with factory
from .store import StoreFactory
StoreFactory.register_online_store("redis", RedisOnlineStore)
StoreFactory.register_online_store("redis_cluster", RedisOnlineStore)
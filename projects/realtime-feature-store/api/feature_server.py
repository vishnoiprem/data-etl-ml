"""
Feature Store API Server

High-performance feature serving via REST and gRPC.
Supports:
- Single/multi-entity feature lookup
- Feature vector retrieval for inference
- Batch feature export for training
- Health checks and metrics
"""

import asyncio
import time
import logging
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, Query, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from core.config import get_config, FeatureStoreConfig
from core.store import StoreFactory, FeatureVector, OnlineStore, OfflineStore
from core.feature_view import FeatureView
from core.feature import Feature, FeatureType, DataType

# Configure logging
import structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# Global stores
_online_store: Optional[OnlineStore] = None
_offline_store: Optional[OfflineStore] = None
_config: Optional[FeatureStoreConfig] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    global _online_store, _offline_store, _config
    
    _config = get_config()
    logger.info("Starting Feature Store API", config=_config.to_dict())
    
    # Initialize stores
    _online_store = StoreFactory.create_online_store({
        "type": _config.online_store.type,
        **_config.online_store.config
    })
    await _online_store.initialize()
    
    _offline_store = StoreFactory.create_offline_store({
        "type": _config.offline_store.type,
        **_config.offline_store.config
    })
    await _offline_store.initialize()
    
    logger.info("Feature Store API started")
    yield
    
    # Shutdown
    await _online_store.close()
    await _offline_store.close()
    logger.info("Feature Store API stopped")


app = FastAPI(
    title="Real-Time Feature Store API",
    description="High-performance feature serving for ML inference and training",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class EntityKey(BaseModel):
    entity: str
    key: str


class FeatureRequest(BaseModel):
    feature_view: str
    entities: List[EntityKey]
    features: Optional[List[str]] = None


class BatchFeatureRequest(BaseModel):
    feature_view: str
    entity_keys: List[str]
    features: Optional[List[str]] = None


class FeatureVectorResponse(BaseModel):
    entity: str
    key: str
    features: Dict[str, Any]
    event_timestamp: Optional[str] = None
    created_timestamp: Optional[str] = None


class BatchFeatureResponse(BaseModel):
    results: List[FeatureVectorResponse]
    latency_ms: float
    cache_hit_rate: float


class HealthResponse(BaseModel):
    status: str
    online_store: str
    offline_store: str
    version: str


class StatsResponse(BaseModel):
    online_store: Dict[str, Any]
    offline_store: Dict[str, Any]


# Dependency to get stores
def get_online_store() -> OnlineStore:
    if _online_store is None:
        raise HTTPException(status_code=503, detail="Online store not initialized")
    return _online_store


def get_offline_store() -> OfflineStore:
    if _offline_store is None:
        raise HTTPException(status_code=503, detail="Offline store not initialized")
    return _offline_store


# REST Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check(
    online: OnlineStore = Depends(get_online_store),
    offline: OfflineStore = Depends(get_offline_store)
):
    """Health check endpoint"""
    online_healthy = await online.health_check()
    offline_healthy = await offline.health_check()
    
    return HealthResponse(
        status="healthy" if online_healthy and offline_healthy else "degraded",
        online_store="healthy" if online_healthy else "unhealthy",
        offline_store="healthy" if offline_healthy else "unhealthy",
        version="1.0.0"
    )


@app.get("/stats", response_model=StatsResponse)
async def get_stats(
    online: OnlineStore = Depends(get_online_store),
    offline: OfflineStore = Depends(get_offline_store)
):
    """Get store statistics"""
    return StatsResponse(
        online_store=online.get_stats(),
        offline_store=offline.get_stats()
    )


@app.post("/features/v1/get-online-features", response_model=BatchFeatureResponse)
async def get_online_features(
    request: BatchFeatureRequest,
    online: OnlineStore = Depends(get_online_store)
):
    """
    Get features for multiple entities from online store.
    
    This is the primary endpoint for real-time inference.
    Target latency: p99 < 5ms
    """
    start = time.time()
    
    # All entities must be for the same feature view
    # In production, validate entity types match feature view
    
    results = await online.read_batch(
        feature_view=request.feature_view,
        entity_keys=request.entity_keys,
        feature_names=request.features
    )
    
    # Convert to response format
    response_results = [
        FeatureVectorResponse(
            entity=request.feature_view.split("_")[0],  # Simplified
            key=r.entity_key,
            features=r.features,
            event_timestamp=r.event_timestamp,
            created_timestamp=r.created_timestamp
        )
        for r in results
    ]
    
    latency = (time.time() - start) * 1000
    stats = online.get_stats()
    cache_hit_rate = 0
    if stats["cache_hits"] + stats["cache_misses"] > 0:
        cache_hit_rate = stats["cache_hits"] / (stats["cache_hits"] + stats["cache_misses"])
    
    return BatchFeatureResponse(
        results=response_results,
        latency_ms=latency,
        cache_hit_rate=cache_hit_rate
    )


@app.post("/features/v1/get-online-feature-vector")
async def get_online_feature_vector(
    request: FeatureRequest,
    online: OnlineStore = Depends(get_online_store)
):
    """
    Get feature vectors for multiple entities with different entity types.
    
    Used when a model needs features from multiple feature views
    (e.g., user features + item features for recommendation).
    """
    start = time.time()
    
    results = {}
    for entity in request.entities:
        vectors = await online.read_batch(
            feature_view=f"{entity.entity}_features",  # Convention
            entity_keys=[entity.key],
            feature_names=request.features
        )
        if vectors:
            results[f"{entity.entity}:{entity.key}"] = vectors[0].features
    
    latency = (time.time() - start) * 1000
    return {
        "results": results,
        "latency_ms": latency
    }


@app.get("/features/v1/feature-views")
async def list_feature_views():
    """List all registered feature views"""
    # In production, query registry database
    return {
        "feature_views": [
            {"name": "fraud_detection", "entity": "transaction", "features": 15, "online": True, "offline": True},
            {"name": "user_recommendation_features", "entity": "user", "features": 8, "online": True, "offline": True},
            {"name": "item_recommendation_features", "entity": "item", "features": 12, "online": True, "offline": True},
            {"name": "dynamic_pricing", "entity": "item", "features": 10, "online": True, "offline": True},
        ]
    }


@app.get("/features/v1/feature-views/{feature_view}")
async def get_feature_view(feature_view: str):
    """Get feature view definition"""
    # In production, query registry
    views = {
        "fraud_detection": {
            "name": "fraud_detection",
            "entity": "transaction",
            "features": [
                {"name": "amount", "type": "float64", "description": "Transaction amount"},
                {"name": "merchant_category", "type": "string", "description": "Merchant category"},
                {"name": "user_txn_count_1h", "type": "int64", "description": "User txn count 1h"},
                {"name": "user_txn_amount_sum_24h", "type": "float64", "description": "User amount sum 24h"},
                {"name": "merchant_fraud_rate_7d", "type": "float64", "description": "Merchant fraud rate 7d"},
                {"name": "user_behavior_embedding", "type": "float32[64]", "description": "User embedding"},
            ],
            "online": True,
            "offline": True,
        }
    }
    if feature_view not in views:
        raise HTTPException(status_code=404, detail=f"Feature view {feature_view} not found")
    return views[feature_view]


# Offline/Batch Endpoints (for training)
@app.post("/features/v1/get-historical-features")
async def get_historical_features(
    request: Dict[str, Any] = Body(...),
    offline: OfflineStore = Depends(get_offline_store)
):
    """
    Get historical features for training (point-in-time correct).
    
    Request body:
    {
        "entity_df": [...],  # List of {entity_key, event_timestamp}
        "feature_views": ["fraud_detection", "user_features"],
        "features": ["amount", "user_txn_count_1h", ...]  // optional
    }
    """
    entity_df = request.get("entity_df", [])
    feature_views = request.get("feature_views", [])
    features = request.get("features")
    
    if not entity_df or not feature_views:
        raise HTTPException(status_code=400, detail="entity_df and feature_views required")
    
    # Convert to DataFrame for offline store
    import pandas as pd
    df = pd.DataFrame(entity_df)
    
    result = await offline.get_historical_features(df, feature_views, features)
    
    return {
        "data": result.to_dict(orient="records"),
        "shape": list(result.shape),
        "columns": list(result.columns)
    }


@app.post("/features/v1/export-training-data")
async def export_training_data(
    request: Dict[str, Any] = Body(...),
    offline: OfflineStore = Depends(get_offline_store)
):
    """
    Export training dataset to file (Parquet/CSV).
    
    Request body:
    {
        "feature_view": "fraud_detection",
        "start_time": "2024-01-01",
        "end_time": "2024-01-31",
        "output_path": "s3://bucket/training/fraud_jan2024.parquet",
        "format": "parquet"
    }
    """
    feature_view = request.get("feature_view")
    start_time = request.get("start_time")
    end_time = request.get("end_time")
    output_path = request.get("output_path")
    format = request.get("format", "parquet")
    
    if not feature_view or not output_path:
        raise HTTPException(status_code=400, detail="feature_view and output_path required")
    
    df = await offline.read_as_dataframe(
        feature_view=feature_view,
        start_time=start_time,
        end_time=end_time
    )
    
    if format == "parquet":
        df.to_parquet(output_path)
    elif format == "csv":
        df.to_csv(output_path)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
    
    return {"status": "success", "rows": len(df), "path": output_path}


# Prometheus metrics endpoint
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response

REQUEST_COUNT = Counter('feature_store_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('feature_store_request_latency_seconds', 'Request latency', ['method', 'endpoint'])
ONLINE_STORE_SIZE = Gauge('feature_store_online_keys', 'Number of keys in online store')


@app.middleware("http")
async def metrics_middleware(request, call_next):
    start = time.time()
    response = await call_next(request)
    latency = time.time() - start
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(latency)
    
    return response


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    # Update gauge
    if _online_store:
        stats = _online_store.get_stats()
        # This is approximate - real implementation would track actual keys
        ONLINE_STORE_SIZE.set(stats.get("reads", 0))
    
    return Response(content=generate_latest(), media_type="text/plain")


def main():
    """Entry point for running the server"""
    config = get_config()
    uvicorn.run(
        "feature_server:app",
        host=config.api_host,
        port=config.api_port,
        workers=config.workers,
        log_level=config.monitoring.log_level.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()
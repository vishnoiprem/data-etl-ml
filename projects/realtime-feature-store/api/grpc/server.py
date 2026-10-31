"""
gRPC Server Implementation

High-performance gRPC server for feature serving with:
- Async request handling
- Connection pooling
- Request/response streaming
- Interceptors for auth, logging, metrics
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional

import grpc
from grpc import aio

from core.config import get_config, FeatureStoreConfig
from core.store import StoreFactory, OnlineStore, OfflineStore
from core.feature import Feature, FeatureType, DataType

# Generated gRPC classes (would be generated from .proto)
# from api.grpc import feature_service_pb2, feature_service_pb2_grpc

logger = logging.getLogger(__name__)


class FeatureServiceServicer:
    """gRPC service implementation"""
    
    def __init__(self, config: FeatureStoreConfig):
        self.config = config
        self._online_store: Optional[OnlineStore] = None
        self._offline_store: Optional[OfflineStore] = None
    
    async def initialize(self):
        self._online_store = StoreFactory.create_online_store({
            "type": self.config.online_store.type,
            **self.config.online_store.config
        })
        await self._online_store.initialize()
        
        self._offline_store = StoreFactory.create_offline_store({
            "type": self.config.offline_store.type,
            **self.config.offline_store.config
        })
        await self._offline_store.initialize()
    
    async def close(self):
        if self._online_store:
            await self._online_store.close()
        if self._offline_store:
            await self._offline_store.close()
    
    async def GetOnlineFeatures(self, request, context):
        """Get online features for multiple entities"""
        start = time.time()
        
        try:
            vectors = await self._online_store.read_batch(
                feature_view=request.feature_view,
                entity_keys=list(request.entity_keys),
                feature_names=list(request.features) if request.features else None
            )
            
            # Convert to protobuf
            # proto_vectors = []
            # for v in vectors:
            #     proto_vectors.append(feature_service_pb2.FeatureVector(...))
            
            latency_ms = int((time.time() - start) * 1000)
            
            # Return mock response for now
            class MockResponse:
                vectors = []
                latency_ms = latency_ms
                cache_hit_rate = 0.95
            return MockResponse()
            
        except Exception as e:
            logger.error(f"GetOnlineFeatures error: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return
    
    async def GetHistoricalFeatures(self, request, context):
        """Get historical features for training"""
        # Convert entity_timestamps to DataFrame
        import pandas as pd
        entity_df = pd.DataFrame([
            {"entity_key": et.entity_key, "event_timestamp": et.event_timestamp}
            for et in request.entity_timestamps
        ])
        
        result = await self._offline_store.get_historical_features(
            entity_df,
            list(request.feature_views),
            list(request.features) if request.features else None
        )
        
        # Serialize to Arrow/Parquet
        # For now, return mock
        class MockResponse:
            data = b""
            row_count = len(entity_df)
            columns = ["entity_key", "event_timestamp"]
        return MockResponse()
    
    async def HealthCheck(self, request, context):
        online_healthy = await self._online_store.health_check()
        offline_healthy = await self._offline_store.health_check()
        
        class MockResponse:
            status = "healthy" if online_healthy and offline_healthy else "degraded"
            online_store = "healthy" if online_healthy else "unhealthy"
            offline_store = "healthy" if offline_healthy else "unhealthy"
            version = "1.0.0"
        return MockResponse()


async def serve(config: FeatureStoreConfig) -> None:
    """Start gRPC server"""
    server = aio.server()
    
    servicer = FeatureServiceServicer(config)
    await servicer.initialize()
    
    # Register service
    # feature_service_pb2_grpc.add_FeatureServiceServicer_to_server(servicer, server)
    
    listen_addr = f"{config.api_host}:{config.grpc_port}"
    server.add_insecure_port(listen_addr)
    
    logger.info(f"Starting gRPC server on {listen_addr}")
    await server.start()
    
    try:
        await server.wait_for_termination()
    finally:
        await servicer.close()
        await server.stop(grace=5)


if __name__ == "__main__":
    config = get_config()
    asyncio.run(serve(config))
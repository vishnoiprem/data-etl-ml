"""
Feature View Definitions

Feature views are logical groupings of features that are served together.
They define the entity, the features, and how they're materialized.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .feature import Feature
from .entity import Entity


@dataclass
class FeatureView:
    """
    A feature view - a logical collection of features served together.
    
    Feature views are the primary unit of feature serving. They define:
    - Which entity they're for
    - Which features are included
    - How they're materialized (online/offline/both)
    - TTL and freshness requirements
    """
    name: str
    entity: Entity
    features: List[Feature]
    description: str = ""
    tags: List[str] = field(default_factory=list)
    owner: str = ""
    
    # Materialization
    online: bool = True
    offline: bool = True
    ttl_seconds: Optional[int] = None  # Time-to-live for online features
    
    # Streaming config (for real-time features)
    source: Optional[str] = None  # Kafka topic, CDC source, etc.
    event_timestamp_column: str = "event_timestamp"
    created_timestamp_column: Optional[str] = None
    
    # Batch config
    batch_source: Optional[str] = None  # Table, file path, query
    
    # Metadata
    version: int = 1
    status: str = "active"  # "active", "deprecated", "experimental"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        # Validate all features belong to the same entity
        for feature in self.features:
            if feature.entity != self.entity.name:
                raise ValueError(
                    f"Feature {feature.name} belongs to entity '{feature.entity}', "
                    f"but feature view entity is '{self.entity.name}'"
                )
    
    def get_feature_names(self) -> List[str]:
        return [f.name for f in self.features]
    
    def get_feature(self, name: str) -> Optional[Feature]:
        for f in self.features:
            if f.name == name:
                return f
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity": self.entity.to_dict(),
            "features": [f.to_dict() for f in self.features],
            "description": self.description,
            "tags": self.tags,
            "owner": self.owner,
            "online": self.online,
            "offline": self.offline,
            "ttl_seconds": self.ttl_seconds,
            "source": self.source,
            "event_timestamp_column": self.event_timestamp_column,
            "created_timestamp_column": self.created_timestamp_column,
            "batch_source": self.batch_source,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureView":
        data = data.copy()
        data["entity"] = Entity.from_dict(data["entity"])
        data["features"] = [Feature.from_dict(f) for f in data["features"]]
        return cls(**data)


# Example feature views for common use cases
def fraud_detection_view() -> FeatureView:
    from .feature import (
        numeric_feature, categorical_feature, embedding_feature,
        DataType, FeatureType
    )
    from .entity import transaction_entity
    
    entity = transaction_entity()
    
    features = [
        numeric_feature(
            "amount", "transaction",
            dtype=DataType.FLOAT64,
            description="Transaction amount in USD",
            transformation="amount",
        ),
        categorical_feature(
            "merchant_category", "transaction",
            description="Merchant category code",
            transformation="merchant_category",
        ),
        categorical_feature(
            "merchant_id", "transaction",
            description="Merchant identifier",
            transformation="merchant_id",
        ),
        numeric_feature(
            "user_txn_count_1h", "transaction",
            dtype=DataType.INT64,
            description="User transaction count in last hour",
            transformation="COUNT(*) OVER (PARTITION BY user_id ORDER BY event_timestamp RANGE BETWEEN INTERVAL '1' HOUR PRECEDING AND CURRENT ROW)",
            materialization="online",
            ttl_seconds=3600,
        ),
        numeric_feature(
            "user_txn_amount_sum_24h", "transaction",
            dtype=DataType.FLOAT64,
            description="User transaction amount sum in last 24 hours",
            transformation="SUM(amount) OVER (PARTITION BY user_id ORDER BY event_timestamp RANGE BETWEEN INTERVAL '24' HOUR PRECEDING AND CURRENT ROW)",
            materialization="online",
            ttl_seconds=86400,
        ),
        numeric_feature(
            "merchant_fraud_rate_7d", "transaction",
            dtype=DataType.FLOAT64,
            description="Merchant fraud rate over 7 days",
            transformation="AVG(CASE WHEN is_fraud THEN 1.0 ELSE 0.0 END) OVER (PARTITION BY merchant_id ORDER BY event_timestamp RANGE BETWEEN INTERVAL '7' DAY PRECEDING AND CURRENT ROW)",
            materialization="both",
            ttl_seconds=604800,
        ),
        embedding_feature(
            "user_behavior_embedding", "transaction",
            dimension=64,
            description="User behavioral embedding for fraud detection",
            transformation="ml_embedding(user_id, event_timestamp)",
            materialization="online",
            ttl_seconds=86400,
        ),
    ]
    
    return FeatureView(
        name="fraud_detection",
        entity=entity,
        features=features,
        description="Real-time fraud detection features for transaction scoring",
        tags=["fraud", "real-time", "high-priority"],
        owner="ml-platform-team",
        online=True,
        offline=True,
        ttl_seconds=86400,
        source="kafka:transactions",
        event_timestamp_column="event_timestamp",
        batch_source="warehouse.transactions",
    )


def recommendation_view() -> FeatureView:
    from .feature import (
        numeric_feature, categorical_feature, embedding_feature, array_feature,
        DataType, FeatureType
    )
    from .entity import user_entity, item_entity
    
    # For recommendation, we often need user-item pair features
    # This is a simplified view - in practice you'd have separate user/item views
    user = user_entity()
    item = item_entity()
    
    user_features = [
        embedding_feature(
            "user_preference_embedding", "user",
            dimension=128,
            description="User preference embedding from collaborative filtering",
            transformation="als_embedding(user_id)",
            materialization="online",
            ttl_seconds=86400,
        ),
        array_feature(
            "user_recent_items", "user",
            dimension=50,
            dtype=DataType.INT64,
            description="Recently interacted item IDs",
            transformation="COLLECT_LIST(item_id) OVER (PARTITION BY user_id ORDER BY event_timestamp ROWS BETWEEN 49 PRECEDING AND CURRENT ROW)",
            materialization="online",
            ttl_seconds=3600,
        ),
        numeric_feature(
            "user_session_count_7d", "user",
            dtype=DataType.INT64,
            description="User session count in last 7 days",
            transformation="COUNT(DISTINCT session_id) OVER (PARTITION BY user_id ORDER BY event_timestamp RANGE BETWEEN INTERVAL '7' DAY PRECEDING AND CURRENT ROW)",
            materialization="both",
        ),
    ]
    
    item_features = [
        embedding_feature(
            "item_content_embedding", "item",
            dimension=128,
            description="Item content embedding from BERT/CLIP",
            transformation="content_embedding(item_id)",
            materialization="online",
            ttl_seconds=604800,
        ),
        categorical_feature(
            "item_category", "item",
            description="Item category hierarchy",
            transformation="category_path",
        ),
        numeric_feature(
            "item_popularity_score", "item",
            dtype=DataType.FLOAT64,
            description="Item popularity score (log-scaled)",
            transformation="LOG(1 + COUNT(*)) OVER (PARTITION BY item_id ORDER BY event_timestamp RANGE BETWEEN INTERVAL '30' DAY PRECEDING AND CURRENT ROW)",
            materialization="both",
        ),
    ]
    
    # Return user view (item view would be separate)
    return FeatureView(
        name="user_recommendation_features",
        entity=user,
        features=user_features,
        description="User features for real-time recommendation ranking",
        tags=["recommendation", "ranking", "real-time"],
        owner="recommendation-team",
        online=True,
        offline=True,
        source="kafka:user_events",
        event_timestamp_column="event_timestamp",
    )


def dynamic_pricing_view() -> FeatureView:
    from .feature import numeric_feature, categorical_feature, DataType
    from .entity import item_entity
    
    entity = item_entity()
    
    features = [
        numeric_feature(
            "current_price", "item",
            dtype=DataType.FLOAT64,
            description="Current listed price",
            transformation="price",
        ),
        numeric_feature(
            "competitor_price_avg", "item",
            dtype=DataType.FLOAT64,
            description="Average competitor price",
            transformation="AVG(competitor_price) OVER (PARTITION BY item_id ORDER BY event_timestamp RANGE BETWEEN INTERVAL '1' DAY PRECEDING AND CURRENT ROW)",
            materialization="both",
        ),
        numeric_feature(
            "demand_velocity_1h", "item",
            dtype=DataType.FLOAT64,
            description="Demand velocity (units/hour)",
            transformation="COUNT(*) / 1.0 OVER (PARTITION BY item_id ORDER BY event_timestamp RANGE BETWEEN INTERVAL '1' HOUR PRECEDING AND CURRENT ROW)",
            materialization="online",
            ttl_seconds=3600,
        ),
        numeric_feature(
            "inventory_level", "item",
            dtype=DataType.INT64,
            description="Current inventory level",
            transformation="inventory_count",
            materialization="online",
            ttl_seconds=300,  # Very fresh
        ),
        numeric_feature(
            "price_elasticity_estimate", "item",
            dtype=DataType.FLOAT64,
            description="Estimated price elasticity",
            transformation="ml_price_elasticity(item_id)",
            materialization="offline",
        ),
    ]
    
    return FeatureView(
        name="dynamic_pricing",
        entity=entity,
        features=features,
        description="Real-time features for dynamic pricing optimization",
        tags=["pricing", "optimization", "real-time"],
        owner="pricing-team",
        online=True,
        offline=True,
        source="kafka:pricing_events",
        event_timestamp_column="event_timestamp",
        batch_source="warehouse.pricing_events",
    )
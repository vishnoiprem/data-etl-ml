"""
Feature Definitions and Types

Core data structures for defining features with rich type information,
validation, and metadata.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import json


class FeatureType(Enum):
    """High-level feature categories"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    EMBEDDING = "embedding"
    ARRAY = "array"
    STRUCT = "struct"
    TIMESTAMP = "timestamp"


class DataType(Enum):
    """Primitive data types"""
    INT32 = "int32"
    INT64 = "int64"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    STRING = "string"
    BOOL = "bool"
    BYTES = "bytes"
    TIMESTAMP = "timestamp"
    DATE = "date"


@dataclass
class Feature:
    """
    A feature definition with full metadata.
    
    This is the core abstraction - every computable attribute in the
    feature store is a Feature with a well-defined type, transformation,
    and storage configuration.
    """
    name: str
    entity: str  # Entity name this feature belongs to
    feature_type: FeatureType
    dtype: DataType
    description: str = ""
    dimension: Optional[int] = None  # For embeddings/arrays
    default_value: Any = None
    tags: List[str] = field(default_factory=list)
    owner: str = ""
    
    # Transformation definition
    transformation: Optional[str] = None  # SQL, Python, or Flink SQL
    transformation_config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Upstream feature names
    
    # Materialization config
    materialization: str = "online"  # "online", "offline", "both", "ondemand"
    ttl_seconds: Optional[int] = None
    online_config: Dict[str, Any] = field(default_factory=dict)
    offline_config: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    version: int = 1
    status: str = "active"  # "active", "deprecated", "experimental"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.dimension is not None and self.feature_type not in [FeatureType.EMBEDDING, FeatureType.ARRAY]:
            raise ValueError(f"dimension only valid for EMBEDDING or ARRAY types, got {self.feature_type}")
        
        if self.default_value is not None:
            self._validate_default_value()
    
    def _validate_default_value(self):
        """Validate default value matches declared dtype"""
        validators = {
            DataType.INT32: lambda v: isinstance(v, int) and -2**31 <= v < 2**31,
            DataType.INT64: lambda v: isinstance(v, int),
            DataType.FLOAT32: lambda v: isinstance(v, (int, float)),
            DataType.FLOAT64: lambda v: isinstance(v, (int, float)),
            DataType.STRING: lambda v: isinstance(v, str),
            DataType.BOOL: lambda v: isinstance(v, bool),
            DataType.BYTES: lambda v: isinstance(v, bytes),
        }
        
        if self.dtype in validators and not validators[self.dtype](self.default_value):
            raise ValueError(f"Default value {self.default_value} doesn't match dtype {self.dtype}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "entity": self.entity,
            "feature_type": self.feature_type.value,
            "dtype": self.dtype.value,
            "description": self.description,
            "dimension": self.dimension,
            "default_value": self.default_value,
            "tags": self.tags,
            "owner": self.owner,
            "transformation": self.transformation,
            "transformation_config": self.transformation_config,
            "dependencies": self.dependencies,
            "materialization": self.materialization,
            "ttl_seconds": self.ttl_seconds,
            "online_config": self.online_config,
            "offline_config": self.offline_config,
            "version": self.version,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Feature":
        data = data.copy()
        data["feature_type"] = FeatureType(data["feature_type"])
        data["dtype"] = DataType(data["dtype"])
        return cls(**data)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), default=str)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Feature":
        return cls.from_dict(json.loads(json_str))


# Convenience factory functions
def numeric_feature(
    name: str,
    entity: str,
    dtype: DataType = DataType.FLOAT64,
    description: str = "",
    **kwargs
) -> Feature:
    return Feature(
        name=name,
        entity=entity,
        feature_type=FeatureType.NUMERIC,
        dtype=dtype,
        description=description,
        **kwargs
    )


def categorical_feature(
    name: str,
    entity: str,
    dtype: DataType = DataType.STRING,
    description: str = "",
    **kwargs
) -> Feature:
    return Feature(
        name=name,
        entity=entity,
        feature_type=FeatureType.CATEGORICAL,
        dtype=dtype,
        description=description,
        **kwargs
    )


def embedding_feature(
    name: str,
    entity: str,
    dimension: int,
    dtype: DataType = DataType.FLOAT32,
    description: str = "",
    **kwargs
) -> Feature:
    return Feature(
        name=name,
        entity=entity,
        feature_type=FeatureType.EMBEDDING,
        dtype=dtype,
        dimension=dimension,
        description=description,
        **kwargs
    )


def array_feature(
    name: str,
    entity: str,
    dimension: int,
    dtype: DataType = DataType.FLOAT64,
    description: str = "",
    **kwargs
) -> Feature:
    return Feature(
        name=name,
        entity=entity,
        feature_type=FeatureType.ARRAY,
        dtype=dtype,
        dimension=dimension,
        description=description,
        **kwargs
    )
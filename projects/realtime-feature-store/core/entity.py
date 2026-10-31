"""
Entity Definitions

Entities are the primary keys around which features are organized.
Examples: user_id, transaction_id, session_id, device_id
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class EntityType(Enum):
    """Entity categories for governance and optimization"""
    USER = "user"
    ITEM = "item"
    TRANSACTION = "transaction"
    SESSION = "session"
    DEVICE = "device"
    ORGANIZATION = "organization"
    CUSTOM = "custom"


@dataclass
class Entity:
    """
    An entity definition - the primary key for feature lookup.
    
    Entities define the join keys used to retrieve features at serving time.
    They can have composite keys (e.g., (user_id, item_id) for recommendation).
    """
    name: str
    primary_key: str  # Column name for the primary key
    entity_type: EntityType = EntityType.CUSTOM
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)  # Additional metadata columns
    join_keys: List[str] = field(default_factory=list)  # For composite keys
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.join_keys and self.primary_key not in self.join_keys:
            self.join_keys.insert(0, self.primary_key)
        elif not self.join_keys:
            self.join_keys = [self.primary_key]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "primary_key": self.primary_key,
            "entity_type": self.entity_type.value,
            "description": self.description,
            "properties": self.properties,
            "join_keys": self.join_keys,
            "owner": self.owner,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Entity":
        data = data.copy()
        data["entity_type"] = EntityType(data["entity_type"])
        return cls(**data)


# Common entity factories
def user_entity(
    name: str = "user",
    primary_key: str = "user_id",
    **kwargs
) -> Entity:
    return Entity(
        name=name,
        primary_key=primary_key,
        entity_type=EntityType.USER,
        description="User entity for personalization and analytics",
        **kwargs
    )


def item_entity(
    name: str = "item",
    primary_key: str = "item_id",
    **kwargs
) -> Entity:
    return Entity(
        name=name,
        primary_key=primary_key,
        entity_type=EntityType.ITEM,
        description="Item entity for recommendation and catalog features",
        **kwargs
    )


def transaction_entity(
    name: str = "transaction",
    primary_key: str = "transaction_id",
    **kwargs
) -> Entity:
    return Entity(
        name=name,
        primary_key=primary_key,
        entity_type=EntityType.TRANSACTION,
        description="Transaction entity for fraud detection and financial features",
        **kwargs
    )


def session_entity(
    name: str = "session",
    primary_key: str = "session_id",
    **kwargs
) -> Entity:
    return Entity(
        name=name,
        primary_key=primary_key,
        entity_type=EntityType.SESSION,
        description="Session entity for behavioral and engagement features",
        **kwargs
    )
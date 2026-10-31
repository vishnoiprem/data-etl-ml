"""
Configuration Management

Centralized configuration for the feature store with support for
environment variables, config files, and programmatic overrides.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pathlib import Path
import yaml


@dataclass
class OnlineStoreConfig:
    type: str = "redis"
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OfflineStoreConfig:
    type: str = "iceberg"
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RegistryConfig:
    type: str = "postgres"
    host: str = "localhost"
    port: int = 5432
    database: str = "feature_registry"
    user: str = "registry_user"
    password: str = "registry_password"


@dataclass
class KafkaConfig:
    bootstrap_servers: str = "localhost:9092"
    schema_registry_url: str = "http://localhost:8081"
    topics: Dict[str, str] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    enabled: bool = True
    prometheus_port: int = 9090
    grafana_url: str = "http://localhost:3000"
    alert_manager_url: str = "http://localhost:9093"
    log_level: str = "INFO"


@dataclass
class FeatureStoreConfig:
    """
    Main configuration class for the feature store.
    
    Can be loaded from:
    - YAML config file
    - Environment variables
    - Programmatic overrides
    """
    # Project info
    project_name: str = "feature-store"
    environment: str = "development"
    
    # Stores
    online_store: OnlineStoreConfig = field(default_factory=OnlineStoreConfig)
    offline_store: OfflineStoreConfig = field(default_factory=OfflineStoreConfig)
    
    # Registry
    registry: RegistryConfig = field(default_factory=RegistryConfig)
    
    # Streaming
    kafka: KafkaConfig = field(default_factory=KafkaConfig)
    
    # Monitoring
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # Feature serving
    api_host: str = "0.0.0.0"
    api_port: int = 8082
    grpc_port: int = 8083
    workers: int = 4
    
    # Cache
    l1_cache_enabled: bool = True
    l1_cache_size: int = 10000
    l1_cache_ttl: int = 60
    
    # Security
    auth_enabled: bool = False
    tls_enabled: bool = False
    
    @classmethod
    def from_yaml(cls, path: str) -> "FeatureStoreConfig":
        """Load configuration from YAML file"""
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeatureStoreConfig":
        """Create config from dictionary"""
        # Handle nested configs
        if "online_store" in data and isinstance(data["online_store"], dict):
            data["online_store"] = OnlineStoreConfig(**data["online_store"])
        if "offline_store" in data and isinstance(data["offline_store"], dict):
            data["offline_store"] = OfflineStoreConfig(**data["offline_store"])
        if "registry" in data and isinstance(data["registry"], dict):
            data["registry"] = RegistryConfig(**data["registry"])
        if "kafka" in data and isinstance(data["kafka"], dict):
            data["kafka"] = KafkaConfig(**data["kafka"])
        if "monitoring" in data and isinstance(data["monitoring"], dict):
            data["monitoring"] = MonitoringConfig(**data["monitoring"])
        
        return cls(**data)
    
    @classmethod
    def from_env(cls) -> "FeatureStoreConfig":
        """Load configuration from environment variables"""
        return cls(
            project_name=os.getenv("FS_PROJECT_NAME", "feature-store"),
            environment=os.getenv("FS_ENVIRONMENT", "development"),
            online_store=OnlineStoreConfig(
                type=os.getenv("FS_ONLINE_STORE_TYPE", "redis"),
                config={
                    "nodes": os.getenv("FS_REDIS_NODES", "localhost:7000,localhost:7001,localhost:7002").split(","),
                    "max_connections": int(os.getenv("FS_REDIS_MAX_CONN", "50")),
                }
            ),
            offline_store=OfflineStoreConfig(
                type=os.getenv("FS_OFFLINE_STORE_TYPE", "iceberg"),
                config={
                    "warehouse": os.getenv("FS_ICEBERG_WAREHOUSE", "s3a://feature-store/warehouse"),
                    "catalog_type": os.getenv("FS_ICEBERG_CATALOG", "hadoop"),
                }
            ),
            registry=RegistryConfig(
                host=os.getenv("FS_REGISTRY_HOST", "localhost"),
                port=int(os.getenv("FS_REGISTRY_PORT", "5432")),
                database=os.getenv("FS_REGISTRY_DB", "feature_registry"),
                user=os.getenv("FS_REGISTRY_USER", "registry_user"),
                password=os.getenv("FS_REGISTRY_PASSWORD", "registry_password"),
            ),
            kafka=KafkaConfig(
                bootstrap_servers=os.getenv("FS_KAFKA_BROKERS", "localhost:9092"),
                schema_registry_url=os.getenv("FS_SCHEMA_REGISTRY", "http://localhost:8081"),
            ),
            api_host=os.getenv("FS_API_HOST", "0.0.0.0"),
            api_port=int(os.getenv("FS_API_PORT", "8082")),
            grpc_port=int(os.getenv("FS_GRPC_PORT", "8083")),
            auth_enabled=os.getenv("FS_AUTH_ENABLED", "false").lower() == "true",
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "project_name": self.project_name,
            "environment": self.environment,
            "online_store": {
                "type": self.online_store.type,
                "config": self.online_store.config,
            },
            "offline_store": {
                "type": self.offline_store.type,
                "config": self.offline_store.config,
            },
            "registry": {
                "type": self.registry.type,
                "host": self.registry.host,
                "port": self.registry.port,
                "database": self.registry.database,
                "user": self.registry.user,
            },
            "kafka": {
                "bootstrap_servers": self.kafka.bootstrap_servers,
                "schema_registry_url": self.kafka.schema_registry_url,
            },
            "monitoring": {
                "enabled": self.monitoring.enabled,
                "prometheus_port": self.monitoring.prometheus_port,
            },
            "api_host": self.api_host,
            "api_port": self.api_port,
            "grpc_port": self.grpc_port,
            "auth_enabled": self.auth_enabled,
        }
    
    def to_yaml(self, path: str) -> None:
        """Save configuration to YAML file"""
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


# Global config instance
_config: Optional[FeatureStoreConfig] = None


def get_config() -> FeatureStoreConfig:
    """Get global configuration instance"""
    global _config
    if _config is None:
        # Try to load from standard locations
        config_paths = [
            Path.cwd() / "config.yaml",
            Path.cwd() / "feature_store.yaml",
            Path("/etc/feature-store/config.yaml"),
            Path.home() / ".feature-store" / "config.yaml",
        ]
        
        for path in config_paths:
            if path.exists():
                _config = FeatureStoreConfig.from_yaml(str(path))
                break
        
        if _config is None:
            _config = FeatureStoreConfig.from_env()
    
    return _config


def set_config(config: FeatureStoreConfig) -> None:
    """Set global configuration instance"""
    global _config
    _config = config
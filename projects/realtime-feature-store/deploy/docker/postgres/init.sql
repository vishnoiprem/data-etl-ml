# PostgreSQL Init Schema for Feature Store
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Entities
CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    primary_key VARCHAR(255) NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature Definitions
CREATE TABLE IF NOT EXISTS features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    feature_type VARCHAR(50) NOT NULL, -- 'numeric', 'categorical', 'embedding', 'array', 'struct'
    data_type VARCHAR(50) NOT NULL, -- 'int32', 'int64', 'float32', 'float64', 'string', 'bool', 'bytes'
    dimension INT, -- for embeddings/arrays
    default_value JSONB,
    tags JSONB DEFAULT '[]',
    owner VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'deprecated', 'experimental'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(entity_id, name)
);

-- Feature Versions
CREATE TABLE IF NOT EXISTS feature_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_id UUID REFERENCES features(id) ON DELETE CASCADE,
    version INT NOT NULL,
    schema JSONB NOT NULL,
    transformation_logic TEXT, -- SQL, Python, or Flink SQL
    dependencies JSONB DEFAULT '[]', -- upstream feature IDs
    materialization VARCHAR(50) DEFAULT 'online', -- 'online', 'offline', 'both'
    ttl_seconds INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    UNIQUE(feature_id, version)
);

-- Feature Views (logical groupings)
CREATE TABLE IF NOT EXISTS feature_views (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    entity_id UUID REFERENCES entities(id),
    feature_ids UUID[] NOT NULL,
    tags JSONB DEFAULT '[]',
    owner VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ingestion Sources
CREATE TABLE IF NOT EXISTS ingestion_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'kafka', 'pulsar', 'cdc', 'batch', 'api'
    config JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature Materialization Jobs
CREATE TABLE IF NOT EXISTS materialization_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_version_id UUID REFERENCES feature_versions(id),
    job_type VARCHAR(50) NOT NULL, -- 'streaming', 'batch', 'on-demand'
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    config JSONB DEFAULT '{}',
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature Serving Logs (for monitoring)
CREATE TABLE IF NOT EXISTS serving_logs (
    id BIGSERIAL PRIMARY KEY,
    feature_view_id UUID REFERENCES feature_views(id),
    entity_keys JSONB NOT NULL,
    requested_features TEXT[] NOT NULL,
    latency_ms DOUBLE PRECISION,
    cache_hit BOOLEAN,
    error TEXT,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
) PARTITION BY RANGE (requested_at);

-- Create partitions for serving_logs (monthly)
CREATE TABLE IF NOT EXISTS serving_logs_y2024m01 PARTITION OF serving_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE IF NOT EXISTS serving_logs_y2024m02 PARTITION OF serving_logs
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- Indexes
CREATE INDEX idx_features_entity ON features(entity_id);
CREATE INDEX idx_feature_versions_feature ON feature_versions(feature_id);
CREATE INDEX idx_materialization_jobs_feature_version ON materialization_jobs(feature_version_id);
CREATE INDEX idx_serving_logs_feature_view ON serving_logs(feature_view_id);
CREATE INDEX idx_serving_logs_requested_at ON serving_logs(requested_at);
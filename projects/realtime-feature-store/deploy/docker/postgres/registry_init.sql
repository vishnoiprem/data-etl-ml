# PostgreSQL Init Schema for Feature Registry
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "ltree"; -- for hierarchical feature paths

-- Projects (top-level namespace)
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    owner VARCHAR(255),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Feature Groups (namespaced collections)
CREATE TABLE IF NOT EXISTS feature_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    path LTREE NOT NULL, -- e.g., 'fraud.detection.transaction'
    description TEXT,
    entity_type VARCHAR(255) NOT NULL,
    entity_key VARCHAR(255) NOT NULL,
    event_time_column VARCHAR(255),
    online_enabled BOOLEAN DEFAULT true,
    offline_enabled BOOLEAN DEFAULT true,
    ttl_days INT,
    owner VARCHAR(255),
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, name)
);

-- Features (individual feature definitions)
CREATE TABLE IF NOT EXISTS registry_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_group_id UUID REFERENCES feature_groups(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    feature_type VARCHAR(50) NOT NULL, -- 'numeric', 'categorical', 'embedding', 'array', 'struct', 'timestamp'
    dtype VARCHAR(50) NOT NULL, -- 'int32', 'int64', 'float32', 'float64', 'string', 'bool', 'bytes', 'timestamp'
    dimension INT, -- for embeddings/arrays
    default_value JSONB,
    tags JSONB DEFAULT '[]',
    owner VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(feature_group_id, name)
);

-- Feature Versions (immutable)
CREATE TABLE IF NOT EXISTS feature_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_id UUID REFERENCES registry_features(id) ON DELETE CASCADE,
    version INT NOT NULL,
    -- Schema
    schema JSONB NOT NULL, -- Avro/Protobuf JSON representation
    -- Transformation
    transformation_type VARCHAR(50) NOT NULL, -- 'sql', 'python', 'flink', 'spark', 'udf'
    transformation_logic TEXT NOT NULL,
    transformation_config JSONB DEFAULT '{}',
    -- Dependencies (lineage)
    upstream_feature_ids UUID[] DEFAULT '{}',
    upstream_source_ids UUID[] DEFAULT '{}',
    -- Materialization
    materialization VARCHAR(50) DEFAULT 'online', -- 'online', 'offline', 'both', 'ondemand'
    online_config JSONB DEFAULT '{}', -- Redis key format, TTL, etc.
    offline_config JSONB DEFAULT '{}', -- Partition columns, file format, etc.
    ttl_seconds INT,
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(255),
    changelog TEXT,
    UNIQUE(feature_id, version)
);

-- Lineage Edges (explicit DAG)
CREATE TABLE IF NOT EXISTS lineage_edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upstream_id UUID NOT NULL, -- feature_version_id or source_id
    upstream_type VARCHAR(50) NOT NULL, -- 'feature_version', 'source'
    downstream_id UUID NOT NULL, -- feature_version_id
    downstream_type VARCHAR(50) NOT NULL, -- 'feature_version'
    transformation_id UUID REFERENCES feature_versions(id),
    edge_type VARCHAR(50) DEFAULT 'transform', -- 'transform', 'aggregate', 'join', 'filter'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ingestion Sources
CREATE TABLE IF NOT EXISTS sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL, -- 'kafka', 'pulsar', 'cdc', 'database', 'api', 'file', 'stream'
    config JSONB NOT NULL, -- connection details, topic, query, etc.
    schema JSONB, -- inferred or explicit schema
    owner VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(project_id, name)
);

-- Materialization Jobs
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_version_id UUID REFERENCES feature_versions(id) ON DELETE CASCADE,
    job_name VARCHAR(255) NOT NULL,
    job_type VARCHAR(50) NOT NULL, -- 'flink_streaming', 'spark_batch', 'dbt', 'airflow', 'manual'
    orchestrator VARCHAR(50), -- 'kubernetes', 'airflow', 'dagster', 'prefect'
    config JSONB NOT NULL, -- job-specific config
    schedule VARCHAR(255), -- cron for batch, 'continuous' for streaming
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'active', 'paused', 'deprecated'
    last_run_id UUID,
    last_run_status VARCHAR(50),
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    owner VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(feature_version_id, job_name)
);

-- Job Runs
CREATE TABLE IF NOT EXISTS job_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
    run_id VARCHAR(255) NOT NULL, -- external orchestrator run ID
    status VARCHAR(50) NOT NULL, -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    records_processed BIGINT,
    bytes_processed BIGINT,
    error_message TEXT,
    metrics JSONB DEFAULT '{}',
    logs_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Access Control (RBAC)
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB NOT NULL, -- e.g., {"features": ["read", "write"], "models": ["read"]}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS role_bindings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    principal_type VARCHAR(50) NOT NULL, -- 'user', 'group', 'service_account'
    principal_id VARCHAR(255) NOT NULL,
    resource_type VARCHAR(50), -- 'project', 'feature_group', 'feature'
    resource_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(role_id, principal_type, principal_id, resource_type, resource_id)
);

-- Feature Usage Tracking
CREATE TABLE IF NOT EXISTS feature_usage (
    id BIGSERIAL PRIMARY KEY,
    feature_version_id UUID REFERENCES feature_versions(id),
    consumer_type VARCHAR(50) NOT NULL, -- 'model', 'dashboard', 'notebook', 'api'
    consumer_id VARCHAR(255) NOT NULL,
    access_count BIGINT DEFAULT 1,
    last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    UNIQUE(feature_version_id, consumer_type, consumer_id, period_start)
) PARTITION BY RANGE (period_start);

-- Documentation/Metadata
CREATE TABLE IF NOT EXISTS feature_docs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    feature_version_id UUID REFERENCES feature_versions(id) ON DELETE CASCADE,
    markdown TEXT NOT NULL,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generated_by VARCHAR(255),
    version INT DEFAULT 1
);

-- Indexes
CREATE INDEX idx_feature_groups_project ON feature_groups(project_id);
CREATE INDEX idx_feature_groups_path ON feature_groups USING GIST(path);
CREATE INDEX idx_registry_features_group ON registry_features(feature_group_id);
CREATE INDEX idx_feature_versions_feature ON feature_versions(feature_id);
CREATE INDEX idx_lineage_upstream ON lineage_edges(upstream_id, upstream_type);
CREATE INDEX idx_lineage_downstream ON lineage_edges(downstream_id, downstream_type);
CREATE INDEX idx_jobs_feature_version ON jobs(feature_version_id);
CREATE INDEX idx_job_runs_job ON job_runs(job_id);
CREATE INDEX idx_feature_usage_feature ON feature_usage(feature_version_id);
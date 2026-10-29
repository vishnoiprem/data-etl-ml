"""Provision every AWS resource this lab needs, idempotently.

Implements the README's console walkthrough as code, except for the Aurora Serverless
cluster itself -- that one is left to the console because the lab's IAM user cannot
create RDS clusters. Everything downstream of it is handled here:

  1. pgvector extension, bedrock_integration schema, bedrock_kb table and its indexes
     (over the RDS Data API, so no VPC access is required from your laptop)
  2. the S3 bucket and the source document upload
  3. the Bedrock Knowledge Base, its S3 data source, and the ingestion sync

Run it with:  python provision.py
Re-running is safe; existing resources are detected and reused.
"""

import json
import os
import sys
import time

import boto3
from botocore.exceptions import ClientError

import config


def log(msg):
    print(msg, flush=True)


# ----------------------------------------------------------------------------
# 1. Aurora vector store


def setup_database():
    log("\n=== 1. Aurora vector store ===")
    secrets = boto3.client("secretsmanager", **config.BOTO_KWARGS)
    password = json.loads(
        secrets.get_secret_value(SecretId=config.AURORA_SECRET_ARN)["SecretString"]
    )["password"]

    data = boto3.client("rds-data", **config.BOTO_KWARGS)

    def run(sql, label, tolerate=()):
        try:
            result = data.execute_statement(
                resourceArn=config.AURORA_CLUSTER_ARN,
                secretArn=config.AURORA_SECRET_ARN,
                database=config.AURORA_DATABASE,
                sql=sql,
            )
            log("  ok    %s" % label)
            return result
        except ClientError as exc:
            message = exc.response["Error"]["Message"]
            if any(token in message for token in tolerate):
                log("  skip  %s (already exists)" % label)
                return None
            log("  FAIL  %s -> %s" % (label, message))
            raise

    run("CREATE EXTENSION IF NOT EXISTS vector", "pgvector extension")
    version = run(
        "SELECT extversion FROM pg_extension WHERE extname='vector'", "pgvector version"
    )
    log("        pgvector %s" % version["records"][0][0]["stringValue"])

    run("CREATE SCHEMA IF NOT EXISTS bedrock_integration", "schema bedrock_integration")
    run(
        "CREATE ROLE bedrock_user WITH PASSWORD '%s' LOGIN" % password.replace("'", "''"),
        "role bedrock_user",
        tolerate=("already exists",),
    )
    run(
        "GRANT ALL ON SCHEMA bedrock_integration TO bedrock_user",
        "grant schema to bedrock_user",
    )
    # Titan Text Embeddings v2 emits 1024-dimensional vectors.
    run(
        """CREATE TABLE IF NOT EXISTS bedrock_integration.bedrock_kb (
               id uuid PRIMARY KEY,
               embedding vector(1024),
               chunks text,
               metadata json)""",
        "table bedrock_kb",
    )
    run(
        "GRANT ALL ON TABLE bedrock_integration.bedrock_kb TO bedrock_user",
        "grant table to bedrock_user",
    )
    run(
        "CREATE INDEX IF NOT EXISTS bedrock_kb_chunks_fts "
        "ON bedrock_integration.bedrock_kb USING gin (to_tsvector('simple', chunks))",
        "GIN full-text index",
    )
    run(
        "CREATE INDEX IF NOT EXISTS bedrock_kb_embedding_hnsw "
        "ON bedrock_integration.bedrock_kb USING hnsw (embedding vector_cosine_ops) "
        "WITH (ef_construction=256)",
        "HNSW vector index",
    )


# ----------------------------------------------------------------------------
# 2. S3 data source


CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".html": "text/html",
    ".csv": "text/csv",
}


def setup_bucket():
    log("\n=== 2. S3 bucket ===")
    s3 = boto3.client("s3", **config.BOTO_KWARGS)

    # In us-east-1, re-creating a bucket you already own succeeds silently rather than
    # raising BucketAlreadyOwnedByYou, so check for existence explicitly.
    try:
        s3.head_bucket(Bucket=config.S3_BUCKET)
        log("  bucket %s already exists" % config.S3_BUCKET)
    except ClientError:
        try:
            # us-east-1 must not be given a LocationConstraint.
            s3.create_bucket(Bucket=config.S3_BUCKET)
            log("  created bucket %s" % config.S3_BUCKET)
        except ClientError as exc:
            if exc.response["Error"]["Code"] not in (
                "BucketAlreadyOwnedByYou",
                "BucketAlreadyExists",
            ):
                raise
            log("  bucket %s already exists" % config.S3_BUCKET)

    if not config.S3_SOURCE_FILES:
        log("  no S3_SOURCE_FILES configured -- nothing to upload")
        return

    for path in config.S3_SOURCE_FILES:
        if not os.path.exists(path):
            log("  MISSING %s -- skipped" % path)
            continue
        key = os.path.basename(path)
        extra = {}
        content_type = CONTENT_TYPES.get(os.path.splitext(key)[1].lower())
        if content_type:
            extra["ContentType"] = content_type
        s3.upload_file(path, config.S3_BUCKET, key, ExtraArgs=extra or None)
        log("  uploaded s3://%s/%s" % (config.S3_BUCKET, key))


# ----------------------------------------------------------------------------
# 3. Bedrock Knowledge Base


def setup_knowledge_base():
    log("\n=== 3. Bedrock Knowledge Base ===")
    agent = boto3.client("bedrock-agent", **config.BOTO_KWARGS)

    kb_id = None
    for summary in agent.list_knowledge_bases(maxResults=100).get(
        "knowledgeBaseSummaries", []
    ):
        if summary["name"] == config.KB_NAME:
            kb_id = summary["knowledgeBaseId"]
            log("  reusing knowledge base %s" % kb_id)
            break

    if not kb_id:
        # A freshly created IAM role is eventually consistent, so Bedrock can briefly
        # reject it as unassumable. Retry rather than fail the whole run.
        for attempt in range(1, 13):
            try:
                response = agent.create_knowledge_base(
                    name=config.KB_NAME,
                    description="RAG over SageMaker vs Bedrock docs (Cloud Lab)",
                    roleArn=config.KB_EXECUTION_ROLE_ARN,
                    knowledgeBaseConfiguration={
                        "type": "VECTOR",
                        "vectorKnowledgeBaseConfiguration": {
                            "embeddingModelArn": config.EMBEDDING_MODEL_ARN
                        },
                    },
                    storageConfiguration={
                        "type": "RDS",
                        "rdsConfiguration": {
                            "credentialsSecretArn": config.AURORA_SECRET_ARN,
                            "databaseName": config.AURORA_DATABASE,
                            "resourceArn": config.AURORA_CLUSTER_ARN,
                            "tableName": config.AURORA_TABLE,
                            "fieldMapping": {
                                "primaryKeyField": "id",
                                "vectorField": "embedding",
                                "textField": "chunks",
                                "metadataField": "metadata",
                            },
                        },
                    },
                )
                kb_id = response["knowledgeBase"]["knowledgeBaseId"]
                log("  created knowledge base %s" % kb_id)
                break
            except ClientError as exc:
                message = exc.response["Error"]["Message"]
                if attempt < 12:
                    log("  attempt %d failed (%s); retrying in 10s"
                        % (attempt, message[:120]))
                    time.sleep(10)
                    continue
                raise

    for _ in range(60):
        kb = agent.get_knowledge_base(knowledgeBaseId=kb_id)["knowledgeBase"]
        if kb["status"] == "ACTIVE":
            break
        if kb["status"] in ("FAILED", "DELETING"):
            log("  knowledge base %s: %s" % (kb["status"], kb.get("failureReasons")))
            sys.exit(1)
        time.sleep(5)
    log("  knowledge base ACTIVE")

    ds_id = None
    for summary in agent.list_data_sources(
        knowledgeBaseId=kb_id, maxResults=100
    ).get("dataSourceSummaries", []):
        if summary["name"] == config.DATA_SOURCE_NAME:
            ds_id = summary["dataSourceId"]
            log("  reusing data source %s" % ds_id)
            break
    if not ds_id:
        response = agent.create_data_source(
            knowledgeBaseId=kb_id,
            name=config.DATA_SOURCE_NAME,
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {"bucketArn": "arn:aws:s3:::" + config.S3_BUCKET},
            },
        )
        ds_id = response["dataSource"]["dataSourceId"]
        log("  created data source %s" % ds_id)

    job_id = agent.start_ingestion_job(knowledgeBaseId=kb_id, dataSourceId=ds_id)[
        "ingestionJob"
    ]["ingestionJobId"]
    log("  syncing (job %s)" % job_id)
    for _ in range(90):
        job = agent.get_ingestion_job(
            knowledgeBaseId=kb_id, dataSourceId=ds_id, ingestionJobId=job_id
        )["ingestionJob"]
        if job["status"] in ("COMPLETE", "FAILED"):
            log("  sync %s -- %s" % (job["status"], json.dumps(job.get("statistics", {}))))
            if job["status"] == "FAILED":
                log("  reasons: %s" % job.get("failureReasons"))
                sys.exit(1)
            break
        time.sleep(10)

    return kb_id, ds_id


# ----------------------------------------------------------------------------


def main():
    identity = boto3.client("sts", **config.BOTO_KWARGS).get_caller_identity()
    log("account %s as %s" % (identity["Account"], identity["Arn"].rsplit("/", 1)[-1]))

    setup_database()
    setup_bucket()
    kb_id, ds_id = setup_knowledge_base()

    rows = boto3.client("rds-data", **config.BOTO_KWARGS).execute_statement(
        resourceArn=config.AURORA_CLUSTER_ARN,
        secretArn=config.AURORA_SECRET_ARN,
        database=config.AURORA_DATABASE,
        sql="SELECT count(*) FROM bedrock_integration.bedrock_kb",
    )["records"][0][0]["longValue"]

    log("\n=== done ===")
    log("  chunks in Aurora : %d" % rows)
    log("  KNOWLEDGE_BASE_ID: %s" % kb_id)
    log("  DATA_SOURCE_ID   : %s" % ds_id)
    if kb_id != config.KNOWLEDGE_BASE_ID:
        log("\n  NOTE: update KNOWLEDGE_BASE_ID in aws.env to %s" % kb_id)
    log("\nNext: streamlit run app.py")


if __name__ == "__main__":
    main()

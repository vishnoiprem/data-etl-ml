# notebooks/05_downstream_integration.py
"""
Downstream Integration for Search, RAG, and Analytics
Preparing processed documents for consumption
"""

import json
from typing import Dict, List, Optional, Any
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from dataclasses import dataclass
from enum import Enum


class ChunkingStrategy(Enum):
    """Strategies for document chunking"""
    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    OVERLAP = "overlap"
    RECURSIVE = "recursive"


@dataclass
class ChunkConfig:
    """Configuration for document chunking"""
    strategy: ChunkingStrategy
    chunk_size: int = 1000
    chunk_overlap: int = 200
    separator: str = "\n\n"
    keep_separator: bool = False


class DownstreamProcessor:
    """Processes documents for downstream consumption"""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def create_gold_layer(self,
                          silver_table: str = "silver.processed_documents",
                          gold_path: str = None) -> None:
        """Create Gold layer tables for consumption"""

        # Document-level gold table
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS gold.documents (
                document_id STRING NOT NULL,
                file_name STRING NOT NULL,
                content_type STRING,
                page_count INT,
                total_word_count INT,
                confidence_score FLOAT,
                model_used STRING,
                processing_date DATE,
                extracted_content STRING,
                key_value_pairs ARRAY<STRUCT<
                    key: STRING,
                    value: STRING,
                    confidence: FLOAT
                >>,
                entities ARRAY<STRUCT<
                    category: STRING,
                    subcategory: STRING,
                    content: STRING,
                    confidence: FLOAT
                >>,
                document_metadata STRUCT<
                    file_size: LONG,
                    checksum: STRING,
                    ingestion_time: TIMESTAMP,
                    processing_time: TIMESTAMP
                >,
                quality_metrics STRUCT<
                    has_tables: BOOLEAN,
                    has_handwriting: BOOLEAN,
                    is_scanned: BOOLEAN,
                    avg_confidence_per_page: FLOAT
                >
            )
            USING DELTA
            LOCATION '{gold_path}/documents'
            PARTITIONED BY (processing_date)
            TBLPROPERTIES (
                delta.enableChangeDataFeed = true,
                delta.autoOptimize.optimizeWrite = true
            )
        """)

        # Chunks table for RAG applications
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS gold.document_chunks (
                chunk_id STRING GENERATED ALWAYS AS (uuid()),
                document_id STRING NOT NULL,
                chunk_index INT NOT NULL,
                chunk_text STRING NOT NULL,
                chunk_size INT NOT NULL,
                token_count INT,
                page_range STRUCT<start: INT, end: INT>,
                embedding_vector ARRAY<FLOAT>,
                metadata STRUCT<
                    contains_table: BOOLEAN,
                    contains_formula: BOOLEAN,
                    language: STRING,
                    chunk_type: STRING
                >,
                created_at TIMESTAMP NOT NULL
            )
            USING DELTA
            LOCATION '{gold_path}/chunks'
            PARTITIONED BY (document_id)
        """)

        # Search index table
        self.spark.sql(f"""
            CREATE TABLE IF NOT EXISTS gold.search_index (
                search_id STRING GENERATED ALWAYS AS (uuid()),
                document_id STRING NOT NULL,
                field_name STRING NOT NULL,
                field_value STRING NOT NULL,
                field_type STRING,
                importance_score FLOAT,
                indexed_at TIMESTAMP NOT NULL
            )
            USING DELTA
            LOCATION '{gold_path}/search_index'
        """)

        print("Created Gold layer tables")

    def populate_gold_layer(self,
                            silver_table: str = "silver.processed_documents") -> DataFrame:
        """Populate Gold layer from Silver"""

        gold_documents = self.spark.sql(f"""
            SELECT 
                document_id,
                file_name,
                content_type,
                page_count,
                total_word_count,
                confidence_score,
                model_used,
                DATE(processing_time) as processing_date,
                extracted_content,
                key_value_pairs,
                entities,
                STRUCT(
                    file_size,
                    checksum,
                    ingestion_time,
                    processing_time
                ) as document_metadata,
                STRUCT(
                    ARRAY_SIZE(tables) > 0 as has_tables,
                    -- Placeholder for handwriting detection
                    false as has_handwriting,
                    -- Placeholder for scanned detection
                    content_type LIKE '%image%' as is_scanned,
                    confidence_score as avg_confidence_per_page
                ) as quality_metrics
            FROM {silver_table}
            WHERE processing_status = 'success'
        """)

        return gold_documents

    def create_document_chunks(self,
                               documents_df: DataFrame,
                               chunk_config: ChunkConfig = None) -> DataFrame:
        """Create chunks from documents for RAG applications"""

        if chunk_config is None:
            chunk_config = ChunkConfig(
                strategy=ChunkingStrategy.RECURSIVE,
                chunk_size=1000,
                chunk_overlap=200
            )

        # Register chunking UDF
        @udf(ArrayType(
            StructType([
                StructField("chunk_text", StringType()),
                StructField("page_start", IntegerType()),
                StructField("page_end", IntegerType())
            ])
        ))
        def chunk_document_udf(content: str,
                               pages: List[Row],
                               chunk_size: int,
                               chunk_overlap: int) -> List[Dict]:

            from utils.chunking import DocumentChunker
            chunker = DocumentChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )

            if pages and len(pages) > 0:
                # Use page-aware chunking
                return chunker.chunk_by_pages(content, pages)
            else:
                # Use content-based chunking
                return chunker.chunk_content(content)

        # Apply chunking
        chunked_df = documents_df.withColumn(
            "chunks",
            chunk_document_udf(
                col("extracted_content"),
                col("pages"),
                lit(chunk_config.chunk_size),
                lit(chunk_config.chunk_overlap)
            )
        )

        # Explode chunks into rows
        exploded_df = chunked_df.select(
            "document_id",
            posexplode("chunks").alias("chunk_index", "chunk_data")
        ).select(
            "document_id",
            "chunk_index",
            col("chunk_data.chunk_text").alias("chunk_text"),
            col("chunk_data.page_start").alias("page_start"),
            col("chunk_data.page_end").alias("page_end"),
            length(col("chunk_data.chunk_text")).alias("chunk_size")
        )

        return exploded_df

    def generate_embeddings(self,
                            chunks_df: DataFrame,
                            embedding_model: str = "text-embedding-ada-002") -> DataFrame:
        """Generate embeddings for document chunks"""

        # Register embedding UDF
        @udf(ArrayType(FloatType()))
        def generate_embedding_udf(text: str) -> List[float]:
            from utils.embeddings import EmbeddingGenerator
            generator = EmbeddingGenerator(model=embedding_model)
            return generator.generate_embedding(text)

        # Apply embeddings
        embedded_df = chunks_df.withColumn(
            "embedding_vector",
            generate_embedding_udf(col("chunk_text"))
        ).withColumn(
            "token_count",
            length(split(col("chunk_text"), " "))  # Simple token count
        )

        return embedded_df

    def create_search_index(self,
                            documents_df: DataFrame,
                            index_fields: List[str] = None) -> DataFrame:
        """Create search index from document metadata"""

        if index_fields is None:
            index_fields = [
                "file_name",
                "extracted_content",
                "key_value_pairs",
                "entities"
            ]

        # Flatten key-value pairs for indexing
        kv_exploded = documents_df.select(
            "document_id",
            explode("key_value_pairs").alias("kv_pair")
        ).select(
            "document_id",
            col("kv_pair.key").alias("field_name"),
            col("kv_pair.value").alias("field_value"),
            lit("key_value").alias("field_type"),
            col("kv_pair.confidence").alias("importance_score")
        )

        # Flatten entities for indexing
        entities_exploded = documents_df.select(
            "document_id",
            explode("entities").alias("entity")
        ).select(
            "document_id",
            col("entity.category").alias("field_name"),
            col("entity.content").alias("field_value"),
            lit("entity").alias("field_type"),
            col("entity.confidence").alias("importance_score")
        )

        # Add content chunks for full-text search
        content_chunks = documents_df.select(
            "document_id",
            explode(split(col("extracted_content"), "\n\n")).alias("field_value")
        ).select(
            "document_id",
            lit("content_chunk").alias("field_name"),
            "field_value",
            lit("content").alias("field_type"),
            lit(0.5).alias("importance_score")  # Medium importance
        )

        # Combine all index entries
        search_index = kv_exploded.union(entities_exploded).union(content_chunks)

        # Filter out empty values and add timestamp
        search_index = search_index.filter(
            col("field_value").isNotNull() & (col("field_value") != "")
        ).withColumn(
            "indexed_at",
            current_timestamp()
        )

        return search_index

    def export_to_azure_search(self,
                               index_df: DataFrame,
                               search_service: str,
                               index_name: str,
                               api_key: str) -> None:
        """Export data to Azure AI Search"""

        from azure.search.documents import SearchClient
        from azure.core.credentials import AzureKeyCredential

        # Convert to Azure Search documents
        @udf(StringType())
        def create_search_document_udf(row: Row) -> str:
            document = {
                "id": row.document_id + "_" + row.field_name + "_" + str(hash(row.field_value)),
                "document_id": row.document_id,
                "field_name": row.field_name,
                "field_value": row.field_value,
                "field_type": row.field_type,
                "importance_score": row.importance_score
            }
            return json.dumps(document)

        # Create search documents
        search_docs = index_df.withColumn(
            "search_document",
            create_search_document_udf(struct(*index_df.columns))
        )

        # Collect and upload in batches
        documents = search_docs.select("search_document").collect()

        client = SearchClient(
            endpoint=f"https://{search_service}.search.windows.net",
            index_name=index_name,
            credential=AzureKeyCredential(api_key)
        )

        # Upload in batches of 1000
        batch_size = 1000
        for i in range(0, len(documents), batch_size):
            batch = [
                json.loads(doc.search_document)
                for doc in documents[i:i + batch_size]
            ]

            try:
                result = client.upload_documents(documents=batch)
                print(f"Uploaded batch {i // batch_size + 1}: {len(batch)} documents")

                # Log failed documents
                failed = [doc for doc, res in zip(batch, result)
                          if not res.succeeded]

                if failed:
                    print(f"Failed to upload {len(failed)} documents")

            except Exception as e:
                print(f"Error uploading batch: {e}")

    def export_to_blob_storage(self,
                               df: DataFrame,
                               container: str,
                               path: str,
                               format: str = "parquet") -> None:
        """Export data to blob storage for external consumption"""

        output_path = f"abfss://{container}@{STORAGE_ACCOUNT}.dfs.core.windows.net/{path}"

        df.write \
            .format(format) \
            .mode("overwrite") \
            .option("compression", "snappy") \
            .save(output_path)

        print(f"Exported data to {output_path}")

    def create_consumption_views(self) -> None:
        """Create SQL views for easy consumption"""

        # Document summary view
        self.spark.sql("""
            CREATE OR REPLACE VIEW vw_document_summary AS
            SELECT 
                document_id,
                file_name,
                content_type,
                page_count,
                total_word_count,
                confidence_score,
                processing_date,
                document_metadata.file_size,
                document_metadata.ingestion_time,
                quality_metrics.has_tables,
                quality_metrics.is_scanned
            FROM gold.documents
            WHERE processing_date >= DATE_SUB(CURRENT_DATE(), 30)
        """)

        # Searchable content view
        self.spark.sql("""
            CREATE OR REPLACE VIEW vw_searchable_content AS
            SELECT 
                chunk_id,
                document_id,
                chunk_text,
                token_count,
                embedding_vector,
                metadata.chunk_type,
                created_at
            FROM gold.document_chunks
            WHERE token_count BETWEEN 50 AND 2000  -- Filter reasonable chunks
        """)

        # Processing metrics view
        self.spark.sql("""
            CREATE OR REPLACE VIEW vw_processing_metrics AS
            SELECT 
                processing_date,
                COUNT(*) as documents_processed,
                AVG(page_count) as avg_pages_per_doc,
                AVG(total_word_count) as avg_words_per_doc,
                AVG(confidence_score) as avg_confidence,
                SUM(CASE WHEN quality_metrics.has_tables THEN 1 ELSE 0 END) as docs_with_tables,
                SUM(CASE WHEN quality_metrics.is_scanned THEN 1 ELSE 0 END) as scanned_docs
            FROM gold.documents
            GROUP BY processing_date
            ORDER BY processing_date DESC
        """)

        print("Created consumption views")


class RAGPreparer:
    """Prepares documents for Retrieval-Augmented Generation applications"""

    def __init__(self, spark: SparkSession):
        self.spark = spark

    def prepare_rag_dataset(self,
                            min_chunk_size: int = 100,
                            max_chunk_size: int = 2000,
                            include_metadata: bool = True) -> DataFrame:
        """Prepare dataset optimized for RAG applications"""

        # Get chunks with their source documents
        rag_df = self.spark.sql(f"""
            SELECT 
                c.chunk_id,
                c.document_id,
                c.chunk_index,
                c.chunk_text,
                c.chunk_size,
                c.token_count,
                c.embedding_vector,
                c.created_at,
                d.file_name,
                d.content_type,
                d.page_count,
                d.confidence_score,
                d.processing_date,
                d.document_metadata.file_size,
                d.document_metadata.checksum,
                d.quality_metrics.has_tables,
                d.quality_metrics.is_scanned
            FROM gold.document_chunks c
            JOIN gold.documents d ON c.document_id = d.document_id
            WHERE c.token_count BETWEEN {min_chunk_size} AND {max_chunk_size}
            AND c.embedding_vector IS NOT NULL
            AND d.confidence_score >= 0.7  -- Minimum confidence threshold
        """)

        if include_metadata:
            # Add metadata column for RAG systems
            @udf(StringType())
            def create_metadata_udf(file_name: str,
                                    content_type: str,
                                    page_count: int,
                                    confidence_score: float,
                                    has_tables: bool) -> str:
                metadata = {
                    "source": file_name,
                    "type": content_type,
                    "pages": page_count,
                    "confidence": float(confidence_score),
                    "has_tables": bool(has_tables)
                }
                return json.dumps(metadata)

            rag_df = rag_df.withColumn(
                "metadata",
                create_metadata_udf(
                    col("file_name"),
                    col("content_type"),
                    col("page_count"),
                    col("confidence_score"),
                    col("has_tables")
                )
            )

        return rag_df

    def create_vector_index(self,
                            rag_df: DataFrame,
                            index_name: str,
                            vector_column: str = "embedding_vector") -> None:
        """Create vector index for similarity search"""

        # Using Databricks Vector Search (preview feature)
        try:
            self.spark.sql(f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON gold.document_chunks ({vector_column})
                USING VECTOR
                OPTIONS (
                    vector_dimension = 1536,  -- OpenAI ada-002 dimension
                    vector_data_type = 'FLOAT32',
                    index_type = 'FLAT'  -- or 'IVF_FLAT' for larger datasets
                )
            """)
            print(f"Created vector index: {index_name}")

        except Exception as e:
            print(f"Note: Vector search may require premium tier. Error: {e}")

    def generate_rag_test_queries(self,
                                  sample_size: int = 100) -> DataFrame:
        """Generate test queries for RAG system evaluation"""

        # Sample chunks to generate queries from
        sample_chunks = self.spark.sql(f"""
            SELECT 
                chunk_text,
                file_name,
                content_type
            FROM vw_searchable_content
            TABLESAMPLE ({sample_size} ROWS)
        """).collect()

        # Generate queries based on chunk content
        queries = []
        for chunk in sample_chunks:
            text = chunk.chunk_text
            source = chunk.file_name

            # Simple query generation (in practice, use LLM or more sophisticated method)
            sentences = text.split('. ')
            if len(sentences) > 1:
                query = sentences[0] + "?"
                queries.append({
                    "query": query,
                    "expected_source": source,
                    "query_type": "content_based"
                })

        # Create DataFrame of queries
        queries_df = self.spark.createDataFrame(queries)
        return queries_df

    def evaluate_rag_performance(self,
                                 queries_df: DataFrame,
                                 search_function: callable) -> Dict:
        """Evaluate RAG system performance"""

        results = []

        for query_row in queries_df.collect():
            query = query_row["query"]
            expected_source = query_row["expected_source"]

            # Perform search
            search_results = search_function(query, top_k=5)

            # Calculate metrics
            precision = 0
            recall = 0
            found = False

            if search_results:
                # Check if expected source is in results
                result_sources = [r["source"] for r in search_results]
                if expected_source in result_sources:
                    found = True
                    precision = 1.0 / len(search_results)  # Simple precision
                    recall = 1.0  # Found the expected document

                results.append({
                    "query": query,
                    "found_expected": found,
                    "precision": precision,
                    "recall": recall,
                    "num_results": len(search_results),
                    "top_result_source": search_results[0]["source"] if search_results else None
                })

        # Calculate overall metrics
        total_queries = len(results)
        if total_queries > 0:
            success_rate = sum(1 for r in results if r["found_expected"]) / total_queries
            avg_precision = sum(r["precision"] for r in results) / total_queries
            avg_recall = sum(r["recall"] for r in results) / total_queries
        else:
            success_rate = avg_precision = avg_recall = 0

        return {
            "total_queries": total_queries,
            "success_rate": success_rate,
            "average_precision": avg_precision,
            "average_recall": avg_recall,
            "detailed_results": results
        }
"""apex-rag-omni: Sovereign RAG platform for 100M docs.

3 domains (finance, legal, medical) served by one API. Hybrid BM25+vector
retrieval over a 10-shard Qdrant cluster with shadow index for embedding
upgrades. Flink CDC for 5-min freshness. Eval harness with Recall@8,
nDCG@10, LLM-as-judge. Anti-hallucination via structured evidence_json.
"""
__version__ = "0.1.0"

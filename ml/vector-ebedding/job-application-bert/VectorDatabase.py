class VectorDatabase:
    def __init__(self, api_key: str, environment: str, index_name: str):
        """
        Initialize Pinecone vector database
        """
        pinecone.init(api_key=api_key, environment=environment)
        self.index_name = index_name

        # Create index if it doesn't exist
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=384,  # Dimension for all-MiniLM-L6-v2
                metric='cosine'
            )

        self.index = pinecone.Index(index_name)

    def upsert_jobs(self, job_embeddings: List[Tuple[str, np.ndarray, Dict]]):
        """
        Upload job embeddings to vector database
        """
        vectors = []
        for job_id, embedding, metadata in job_embeddings:
            vectors.append({
                'id': job_id,
                'values': embedding.tolist(),
                'metadata': metadata
            })

        # Batch upsert
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)

    def search_similar_jobs(self, query_embedding: np.ndarray,
                            top_k: int = 10, filters: Dict = None) -> List[Dict]:
        """
        Search for similar jobs using vector similarity
        """
        search_results = self.index.query(
            vector=query_embedding.tolist(),
            top_k=top_k,
            include_metadata=True,
            filter=filters
        )

        return search_results['matches']

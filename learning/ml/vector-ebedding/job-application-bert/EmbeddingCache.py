import pickle
import os


class EmbeddingCache:
    def __init__(self, cache_dir: str = "embedding_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def get_cache_key(self, text: str) -> str:
        import hashlib
        return hashlib.md5(text.encode()).hexdigest()

    def get_embedding(self, text: str, model) -> np.ndarray:
        cache_key = self.get_cache_key(text)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")

        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)

        # Generate new embedding
        embedding = model.encode(text)

        # Cache it
        with open(cache_file, 'wb') as f:
            pickle.dump(embedding, f)

        return embedding

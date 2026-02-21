"""
Embedding generation utilities for RAG (Retrieval Augmented Generation)
"""

import numpy as np
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class EmbeddingModelType(Enum):
    """Supported embedding model types"""
    OPENAI_ADA = "openai_ada_002"
    SENTENCE_TRANSFORMERS = "sentence_transformers"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation"""
    model_type: EmbeddingModelType = EmbeddingModelType.SENTENCE_TRANSFORMERS
    model_name: str = "all-MiniLM-L6-v2"
    batch_size: int = 32
    max_length: int = 512
    device: str = "cpu"
    openai_api_key: Optional[str] = None
    openai_endpoint: Optional[str] = None
    azure_deployment: Optional[str] = None


class EmbeddingGenerator:
    """Generate embeddings for text chunks"""

    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.model = None
        self.tokenizer = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the embedding model"""
        try:
            if self.config.model_type == EmbeddingModelType.SENTENCE_TRANSFORMERS:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(
                    self.config.model_name,
                    device=self.config.device
                )
                logger.info(f"Loaded SentenceTransformer model: {self.config.model_name}")

            elif self.config.model_type == EmbeddingModelType.OPENAI_ADA:
                import openai
                if self.config.openai_api_key:
                    openai.api_key = self.config.openai_api_key
                else:
                    logger.warning("OpenAI API key not provided")

            elif self.config.model_type == EmbeddingModelType.AZURE_OPENAI:
                import openai
                openai.api_type = "azure"
                openai.api_key = self.config.openai_api_key
                openai.api_base = self.config.openai_endpoint
                openai.api_version = "2023-05-15"

            else:
                raise ValueError(f"Unsupported model type: {self.config.model_type}")

        except ImportError as e:
            logger.error(f"Failed to import required library: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {e}")
            raise

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not text or not text.strip():
            return [0.0] * 384  # Return zero vector for empty text

        try:
            if self.config.model_type == EmbeddingModelType.SENTENCE_TRANSFORMERS:
                if self.model is None:
                    raise ValueError("Model not initialized")

                # Clean and truncate text if needed
                clean_text = self._preprocess_text(text)

                # Generate embedding
                embedding = self.model.encode(
                    clean_text,
                    convert_to_numpy=True,
                    normalize_embeddings=True,
                    show_progress_bar=False
                )

                return embedding.tolist()

            elif self.config.model_type in [EmbeddingModelType.OPENAI_ADA, EmbeddingModelType.AZURE_OPENAI]:
                import openai

                # Clean text
                clean_text = self._preprocess_text(text)

                # Call OpenAI API
                if self.config.model_type == EmbeddingModelType.AZURE_OPENAI:
                    response = openai.Embedding.create(
                        input=clean_text,
                        engine=self.config.azure_deployment
                    )
                else:
                    response = openai.Embedding.create(
                        input=clean_text,
                        model="text-embedding-ada-002"
                    )

                return response['data'][0]['embedding']

            else:
                raise ValueError(f"Unsupported model type: {self.config.model_type}")

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return a zero vector as fallback
            dimension = self.get_embedding_dimension()
            return [0.0] * dimension

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        if not texts:
            return []

        try:
            if self.config.model_type == EmbeddingModelType.SENTENCE_TRANSFORMERS:
                if self.model is None:
                    raise ValueError("Model not initialized")

                # Preprocess texts
                clean_texts = [self._preprocess_text(text) for text in texts]

                # Generate embeddings in batches
                all_embeddings = []
                for i in range(0, len(clean_texts), self.config.batch_size):
                    batch = clean_texts[i:i + self.config.batch_size]
                    embeddings = self.model.encode(
                        batch,
                        convert_to_numpy=True,
                        normalize_embeddings=True,
                        show_progress_bar=False
                    )
                    all_embeddings.extend(embeddings.tolist())

                return all_embeddings

            elif self.config.model_type in [EmbeddingModelType.OPENAI_ADA, EmbeddingModelType.AZURE_OPENAI]:
                # For OpenAI, process sequentially or in small batches
                embeddings = []
                for text in texts:
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                return embeddings

            else:
                raise ValueError(f"Unsupported model type: {self.config.model_type}")

        except Exception as e:
            logger.error(f"Error generating embeddings batch: {e}")
            # Return zero vectors as fallback
            dimension = self.get_embedding_dimension()
            return [[0.0] * dimension for _ in range(len(texts))]

    def _preprocess_text(self, text: str) -> str:
        """Preprocess text before embedding generation"""
        if not text:
            return ""

        # Remove extra whitespace
        text = ' '.join(text.split())

        # Truncate if too long
        if len(text) > 8000:  # Rough character limit
            text = text[:8000]

        return text

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings generated by this model"""
        if self.config.model_type == EmbeddingModelType.SENTENCE_TRANSFORMERS:
            if self.model is None:
                # Common dimensions for popular models
                if "miniLM" in self.config.model_name.lower():
                    return 384
                elif "mpnet" in self.config.model_name.lower():
                    return 768
                else:
                    return 384  # Default
            return self.model.get_sentence_embedding_dimension()
        elif self.config.model_type in [EmbeddingModelType.OPENAI_ADA, EmbeddingModelType.AZURE_OPENAI]:
            return 1536  # OpenAI ada-002 dimension
        else:
            return 384  # Default

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0.0

        # Convert to numpy arrays
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Ensure vectors are normalized
        vec1_norm = vec1 / np.linalg.norm(vec1)
        vec2_norm = vec2 / np.linalg.norm(vec2)

        # Calculate cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)

        return float(similarity)

    def find_similar_chunks(self,
                            query_embedding: List[float],
                            chunk_embeddings: List[List[float]],
                            chunk_texts: List[str],
                            top_k: int = 5,
                            similarity_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find chunks similar to query embedding"""
        if not query_embedding or not chunk_embeddings:
            return []

        similarities = []
        for i, chunk_embedding in enumerate(chunk_embeddings):
            similarity = self.calculate_similarity(query_embedding, chunk_embedding)
            if similarity >= similarity_threshold:
                similarities.append({
                    'index': i,
                    'similarity': similarity,
                    'text': chunk_texts[i] if i < len(chunk_texts) else ""
                })

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        # Return top-k results
        return similarities[:top_k]

    @staticmethod
    def create_default_config() -> EmbeddingConfig:
        """Create default embedding configuration"""
        return EmbeddingConfig(
            model_type=EmbeddingModelType.SENTENCE_TRANSFORMERS,
            model_name="all-MiniLM-L6-v2",
            batch_size=32,
            max_length=512,
            device="cpu"
        )
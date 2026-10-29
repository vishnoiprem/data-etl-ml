import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Example: Simple word embeddings (in reality, these would be 100-300 dimensions)
# Let's say these represent semantic features of words
word_embeddings = {
    'king': [0.8, 0.2, 0.9, 0.1],      # Royal, male, power, etc.
    'queen': [0.7, 0.8, 0.9, 0.1],     # Royal, female, power, etc.
    'man': [0.1, 0.2, 0.3, 0.8],       # Not royal, male, common, etc.
    'woman': [0.1, 0.8, 0.3, 0.8],     # Not royal, female, common, etc.
    'dog': [0.0, 0.1, 0.1, 0.9]        # Not royal, not human, etc.
}

def calculate_cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    magnitude1 = np.linalg.norm(vec1)
    magnitude2 = np.linalg.norm(vec2)
    return dot_product / (magnitude1 * magnitude2)

# Compare similarities
print("Word Similarity Comparisons:")
print(f"King vs Queen: {calculate_cosine_similarity(word_embeddings['king'], word_embeddings['queen']):.3f}")
print(f"King vs Man: {calculate_cosine_similarity(word_embeddings['king'], word_embeddings['man']):.3f}")
print(f"King vs Dog: {calculate_cosine_similarity(word_embeddings['king'], word_embeddings['dog']):.3f}")
print(f"Man vs Woman: {calculate_cosine_similarity(word_embeddings['man'], word_embeddings['woman']):.3f}")

# Using sklearn for verification
vectors = list(word_embeddings.values())
similarity_matrix = cosine_similarity(vectors)
print("\nSimilarity Matrix:")
words = list(word_embeddings.keys())
for i, word1 in enumerate(words):
    for j, word2 in enumerate(words):
        print(f"{word1} vs {word2}: {similarity_matrix[i][j]:.3f}")

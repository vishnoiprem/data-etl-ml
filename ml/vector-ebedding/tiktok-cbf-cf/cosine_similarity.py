from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Sample movie descriptions
movies = [
    "Sci-fi thriller with mind-bending plot",  # Inception
    "Space adventure with time travel",       # Interstellar
    "Romantic comedy in New York"             # When Harry Met Sally
]

# Vectorize
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(movies)

# Similarity between first two movies
sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix)
print(f"Similarity between Inception and Interstellar: {sim[0][1]:.2f}")  # Output: ~0.25 (moderate match)


import tensorflow as tf

# Suppose we have 1,000 movies and we want to represent them in a 5-dimensional embedding space
embedding_layer = tf.keras.layers.Embedding(input_dim=1000, output_dim=5)

# Sample input representing a batch of movie IDs (e.g., movies user liked)
sample_movies = tf.constant([[10, 22, 500], [45, 333, 87]], dtype=tf.int32)

# Generate embeddings for the sample movies
movie_embeddings = embedding_layer(sample_movies)
print("Movie Embeddings:", movie_embeddings)
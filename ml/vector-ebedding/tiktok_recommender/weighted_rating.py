import pandas as pd



# Load the MovieLens metadata
metadata = pd.read_csv('../../data/movies_metadata.csv', low_memory=False)

# Calculate C: mean rating across all movies
C = metadata['vote_average'].mean()
print(f"Mean rating (C): {C}")

# Calculate m: minimum votes (90th percentile)
m = metadata['vote_count'].quantile(0.90)
print(f"Minimum votes (m): {m}")

# Filter movies with votes >= m
q_movies = metadata.copy().loc[metadata['vote_count'] >= m]
print(f"Qualified movies shape: {q_movies.shape}")

# Define weighted rating function
def weighted_rating(x, m=m, C=C):
    v = x['vote_count']
    R = x['vote_average']
    return (v / (v + m) * R) + (m / (v + m) * C)

# Apply weighted rating to qualified movies
q_movies['score'] = q_movies.apply(weighted_rating, axis=1)

# Sort by score and select top 10
q_movies = q_movies.sort_values('score', ascending=False)
top_movies = q_movies[['title', 'vote_count', 'vote_average', 'score']].head(10)

# Output results
print("\nTop 10 Movies:")
print(top_movies)
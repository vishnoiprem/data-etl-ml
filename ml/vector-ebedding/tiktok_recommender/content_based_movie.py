from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import pandas as pd

# Load data
metadata = pd.read_csv('../../data/movies_metadata.csv', low_memory=False)

# Preprocess
metadata['overview'] = metadata['overview'].fillna('')
metadata['title_lower'] = metadata['title'].str.lower()  # For case-insensitive matching

# TF-IDF Vectorization
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(metadata['overview'])

# Similarity matrix
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

# Create index mapping (case-insensitive)
indices = pd.Series(metadata.index, index=metadata['title_lower']).drop_duplicates()


def get_recommendations(title, cosine_sim=cosine_sim):
    try:
        # Case-insensitive lookup
        title_lower = title.lower()
        idx = indices[title_lower]

        # Get similarity scores
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

        # Get top 10 similar movies (excluding itself)
        movie_indices = [i[0] for i in sim_scores[1:11]]
        return metadata['title'].iloc[movie_indices]

    except KeyError:
        similar_titles = metadata[metadata['title'].str.contains(title, case=False)]['title']
        if not similar_titles.empty:
            return f"Title not found. Did you mean: {', '.join(similar_titles[:3])}?"
        return "Title not found in dataset."

print(metadata['title'].head(20))         # first 20 titles

# Test with error handling
print('Lost Path 539')

print(get_recommendations('Lost Path 539'))


print('Broken Game')
print(get_recommendations('Broken Game 1'))
# print(get_recommendations('Inception Point'))
# print(get_recommendations('Non-existent Movie'))
#
#
# print(get_recommendations('Toy Story'))
# print(get_recommendations('Jumanji'))
# print(get_recommendations('Grumpier Old Men'))
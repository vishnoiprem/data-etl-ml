import  numpy as np
import pandas as pd
def dcg_at_k(relevance_scores, k):
    relevance_scores = relevance_scores[:k]
    return sum(rel / np.log2(idx + 2) for idx, rel in enumerate(relevance_scores))


def ndcg_at_k(relevance_scores, k):
    dcg = dcg_at_k(relevance_scores, k)
    ideal_relevance_scores = sorted(relevance_scores, reverse=True)
    idcg = dcg_at_k(ideal_relevance_scores, k)
    return dcg / idcg if idcg > 0 else 0
relevance_scores = [3, 2, 3, 0, 1]
k = 5
print(f"nDCG@{k}: {ndcg_at_k(relevance_scores, k):.4f}")


# Simulated user session data
session_data = {
    'user_id': np.random.randint(1, 100, size=100),
    'bookings': np.random.randint(0, 2, size=100),
    'search_results': np.random.randint(1, 20, size=100),
}

df_sessions = pd.DataFrame(session_data)
df_sessions['conversion_rate'] = df_sessions['bookings'] / df_sessions['search_results']

print("Average Conversion Rate:", df_sessions['conversion_rate'].mean())


from sklearn.utils import resample

# Simulate imbalanced data
train_data = pd.DataFrame({
    'booking': np.random.choice([0, 1], size=1000, p=[0.95, 0.05]),
    'features': np.random.rand(1000, 5).tolist()
})

# Upsample minority class
minority = train_data[train_data['booking'] == 1]
majority = train_data[train_data['booking'] == 0]

minority_upsampled = resample(minority, replace=True, n_samples=len(majority), random_state=42)
balanced_data = pd.concat([majority, minority_upsampled])

print("Balanced Data Distribution:", balanced_data['booking'].value_counts())


from sklearn.metrics.pairwise import cosine_similarity

# Simulated listing embeddings
existing_listings = np.random.rand(10, 5)
new_listing = np.random.rand(1, 5)

# Compute similarity
similarities = cosine_similarity(new_listing, existing_listings)
most_similar_idx = np.argmax(similarities)
print(f"Most similar listing index: {most_similar_idx}, Similarity: {similarities[0, most_similar_idx]:.4f}")
import numpy as np
import pandas as pd
from two_tower_model import TwoTowerModel
from ann_index import ANNIndex


class TikTokRecommender:
    def __init__(self, model_path, index_path, mappings_path):
        # Load trained model
        self.model = tf.keras.models.load_model(model_path)

        # Initialize ANN index
        self.ann_index = ANNIndex()
        self.ann_index.load_index(index_path)
        self.idx_to_video = self.ann_index.load_mappings(mappings_path)

    def recommend_for_user(self, user_id, user_features, k=10):
        """Generate recommendations for a user"""
        # Get user embedding
        dummy_item = np.zeros((1, 1))
        dummy_item_features = np.zeros((1, 2))
        user_embedding = self.model.predict({
            'user_id': np.array([[user_id]]),
            'user_features': np.array([user_features]),
            'item_id': dummy_item,
            'item_features': dummy_item_features
        })

        # Search ANN index
        indices, scores = self.ann_index.search(user_embedding, k)

        # Return recommended videos with scores
        return [(self.idx_to_video[idx], float(score))
                for idx, score in zip(indices, scores)]


# Example usage
if __name__ == "__main__":
    recommender = TikTokRecommender(
        model_path='models/two_tower.h5',
        index_path='models/faiss_index.index',
        mappings_path='models/idx_to_video.pkl'
    )

    # Mock user data (age, gender)
    recommendations = recommender.recommend_for_user(
        user_id=42,
        user_features=[25, 1],  # 25 years old, female
        k=5
    )

    print("Top Recommendations:")
    for video_id, score in recommendations:
        print(f"Video {video_id} (score: {score:.3f})")
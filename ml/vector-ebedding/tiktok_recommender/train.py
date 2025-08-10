import pandas as pd
import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Dense, Concatenate, Flatten
from tensorflow.keras.models import Model

# 1. Load Data
print("Loading data...")
users = pd.read_csv('data/users.csv')
videos = pd.read_csv('data/videos.csv')
interactions = pd.read_csv('data/interactions.csv')

# 2. Prepare Features
print("Preparing features...")
# Convert categories to numeric IDs
users['gender'] = users['gender'].map({'M': 0, 'F': 1})
videos['category'] = videos['category'].astype('category').cat.codes

# Create user/item indices
user_ids = interactions['user_id'].unique()
video_ids = interactions['video_id'].unique()
user_to_idx = {id: i for i, id in enumerate(user_ids)}
video_to_idx = {id: i for i, id in enumerate(video_ids)}

# 3. Build Two-Tower Model
print("Building model...")


def build_model(num_users, num_videos):
    # User Tower
    user_id_input = Input(shape=(1,), name='user_id')
    user_embed = Flatten()(Embedding(num_users, 32)(user_id_input))  # Flatten the embedding

    user_features_input = Input(shape=(2,), name='user_features')  # age, gender
    user_tower = Concatenate()([user_embed, user_features_input])
    user_tower = Dense(64, activation='relu')(user_tower)

    # Video Tower
    video_id_input = Input(shape=(1,), name='video_id')
    video_embed = Flatten()(Embedding(num_videos, 32)(video_id_input))  # Flatten the embedding

    video_features_input = Input(shape=(2,), name='video_features')  # category, duration
    video_tower = Concatenate()([video_embed, video_features_input])
    video_tower = Dense(64, activation='relu')(video_tower)

    # Dot Product Similarity
    dot_product = tf.reduce_sum(user_tower * video_tower, axis=1, keepdims=True)

    return Model(
        inputs=[user_id_input, user_features_input,
                video_id_input, video_features_input],
        outputs=dot_product
    )


model = build_model(len(user_ids), len(video_ids))
model.compile(optimizer='adam', loss='mse')

# 4. Prepare Training Data
print("Preparing training data...")
train_data = {
    'user_id': interactions['user_id'].map(user_to_idx).values.reshape(-1, 1),
    'user_features': interactions.merge(users, on='user_id')[['age', 'gender']].values,
    'video_id': interactions['video_id'].map(video_to_idx).values.reshape(-1, 1),
    'video_features': interactions.merge(videos, on='video_id')[['category', 'duration_sec']].values
}
labels = interactions['liked'].values.reshape(-1, 1)

# 5. Train
print("Training...")
history = model.fit(
    train_data,
    labels,
    batch_size=256,
    epochs=10,
    validation_split=0.2
)

# 6. Save Model
print("Saving model...")
model.save('models/two_tower.h5')
print("Training complete! Model saved to models/two_tower.h5")
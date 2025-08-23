# ml/vector-ebedding/tiktok_recommender/train.py

import os
import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, Model, Input


# os → to create directories for saving the trained model.
#
# pandas → read and process CSV data (users, videos, interactions).
#
# numpy → array operations, type conversions.
#
# tensorflow → ML framework for building the neural network.
#
# tensorflow.keras → Keras API inside TensorFlow for defining layers and models.




# 1) Load Data
print("Loading data...")
users = pd.read_csv("data/users.csv")
videos = pd.read_csv("data/videos.csv")
interactions = pd.read_csv("data/interactions.csv")

# Reads 3 datasets:
#
# users.csv — demographic & profile info for each user.
#
# videos.csv — metadata for each video (category, duration, etc.).
#
# interactions.csv — history of which user interacted with which video and whether they liked


# 2) Prepare Features
print("Preparing features...")

# Encodings
users["gender"] = users["gender"].map({"M": 0, "F": 1}).fillna(0).astype("int32")
videos["category"] = videos["category"].astype("category").cat.codes.astype("int32")

# Converts:
#
# Gender → M = 0, F = 1.
#
# Category → maps each category string to a unique integer code.

# astype("int32") → required for embedding layers.

print(videos.head())

# Create user/item indices from interactions
user_ids = interactions["user_id"].unique()
video_ids = interactions["video_id"].unique()
user_to_idx = {uid: i for i, uid in enumerate(user_ids)}
video_to_idx = {vid: i for i, vid in enumerate(video_ids)}

print('user_ids', user_ids,user_to_idx)


#
# Maps actual user IDs → numeric indices.
#
# Same for video IDs.
#
# Embedding layers require consecutive integer IDs starting from 0.


# Basic normalization for continuous features
users["age"] = users["age"].fillna(users["age"].median())
videos["duration_sec"] = videos["duration_sec"].clip(lower=1)

age_mean, age_std = users["age"].mean(), users["age"].std() + 1e-6
dur_mean, dur_std = videos["duration_sec"].mean(), videos["duration_sec"].std() + 1e-6

# Missing ages → replaced with median.
#
# Duration → at least 1 second (avoids divide-by-zero in normalization).
#
# Calculates mean & std for z-score normalization later.


print(age_mean,age_std)
# 3) Build Two-Tower Model




print("Building model...")

def build_model(num_users: int, num_videos: int, embed_dim: int = 32) -> Model:
    # ---- User tower ----
    user_id_input = Input(shape=(1,), name="user_id", dtype="int32")
    u = layers.Embedding(input_dim=num_users + 1, output_dim=embed_dim, name="user_id_emb")(user_id_input)
    u = layers.Flatten()(u)

    print(u,user_ids)

    #
    # Input: single integer (user ID index).
    # Embedding: maps each user to a embed_dim-sized vector.
    # Flatten: removes extra dimensions.


    user_features_input = Input(shape=(2,), name="user_features", dtype="float32")  # [age,zscore, gender]
    u = layers.Concatenate()([u, user_features_input])
    u = layers.Dense(64, activation="relu")(u)
    u = layers.Dense(embed_dim, activation=None, name="user_repr")(u)

    # Second input: age & gender.
    #
    # Concatenate embeddings with features.
    #
    # Dense(64, relu) → transforms features.
    #
    # Dense(embed_dim) → final user representation vector.


    # ---- Video tower ----
    video_id_input = Input(shape=(1,), name="video_id", dtype="int32")
    v = layers.Embedding(input_dim=num_videos + 1, output_dim=embed_dim, name="video_id_emb")(video_id_input)
    v = layers.Flatten()(v)

    video_features_input = Input(shape=(2,), name="video_features", dtype="float32")  # [category, duration_z]
    v = layers.Concatenate()([v, video_features_input])
    v = layers.Dense(64, activation="relu")(v)
    v = layers.Dense(embed_dim, activation=None, name="video_repr")(v)

    # ---- Similarity → probability ----
    score = layers.Dot(axes=1, name="dot_product")([u, v])
    prob = layers.Activation("sigmoid", name="like_prob")(score)

    #
    # Dot product → measures similarity between user & video vectors.
    #
    # Sigmoid → outputs probability of "like" between 0 and 1.

    model = Model(
        inputs=[user_id_input, user_features_input, video_id_input, video_features_input],
        outputs=prob,
        name="two_tower"
    )
    model.compile(
        optimizer="adam",
        loss="binary_crossentropy",
        metrics=[tf.keras.metrics.AUC(name="AUC"), "accuracy"]
    )
    return model

model = build_model(len(user_ids), len(video_ids))

# num_users → total number of unique users in training.
#
# num_videos → total number of unique videos in training.
#
# embed_dim → size of embedding vectors.



# 4) Prepare Training Data (keep row order aligned with interactions)
print("Preparing training data...")

# ID indices (Embedding requires int32)
u_idx = interactions["user_id"].map(user_to_idx).fillna(-1).astype("int32").values.reshape(-1, 1)
i_idx = interactions["video_id"].map(video_to_idx).fillna(-1).astype("int32").values.reshape(-1, 1)

# Merge features in interactions order
user_feats_df = interactions[["user_id"]].merge(
    users[["user_id", "age", "gender"]], on="user_id", how="left"
)
user_feats_df["age"] = ((user_feats_df["age"].fillna(age_mean) - age_mean) / age_std).astype("float32")
user_feats_df["gender"] = user_feats_df["gender"].fillna(0).astype("float32")
user_feats = user_feats_df[["age", "gender"]].values


# Joins interaction rows with user features.
#
# Normalizes age.
#
# Keeps two columns: normalized age & gender.
#



video_feats_df = interactions[["video_id"]].merge(
    videos["video_id category duration_sec".split()], on="video_id", how="left"
)
video_feats_df["duration_sec"] = ((video_feats_df["duration_sec"].fillna(dur_mean) - dur_mean) / dur_std).astype("float32")
video_feats_df["category"] = video_feats_df["category"].fillna(0).astype("float32")
video_feats = video_feats_df[["category", "duration_sec"]].values






train_data = {
    "user_id": u_idx,
    "user_features": user_feats.astype("float32"),
    "video_id": i_idx,
    "video_features": video_feats.astype("float32"),
}

labels = interactions["liked"].astype("float32").values.reshape(-1, 1)

# 5) Train
print("Training...")
history = model.fit(
    train_data,
    labels,
    batch_size=256,
    epochs=10,
    validation_split=0.2,
    verbose=1
)

# Trains for 10 epochs, batch size = 256.
#
# Splits 20% of data for validation.


# 6) Save Model (modern formats)
print("Saving model...")
os.makedirs("models", exist_ok=True)
model.save("models/two_tower.keras")                # Keras v3 format
# Optional TF SavedModel for serving:
# model.export("models/two_tower_savedmodel")

print("Training complete! Model saved to models/two_tower.keras")
# Creates models directory if missing.
#
# Saves model in Keras v3 format (.keras).
#
# Prints confirmation.
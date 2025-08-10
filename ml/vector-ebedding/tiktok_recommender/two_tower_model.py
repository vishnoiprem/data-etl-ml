import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Dense, Concatenate


class TwoTower(tf.keras.Model):
    def __init__(self, num_users, num_items):
        super().__init__()
        # User Tower
        self.user_embed = Embedding(num_users, 64)
        self.user_dense = Dense(32, activation='relu')

        # Item Tower
        self.item_embed = Embedding(num_items, 64)
        self.item_dense = Dense(32, activation='relu')

    def call(self, inputs):
        # User embeddings
        u_emb = self.user_embed(inputs['user_id'])
        u_feat = self.user_dense(inputs['user_features'])
        user_vec = tf.concat([u_emb, u_feat], axis=-1)

        # Item embeddings
        i_emb = self.item_embed(inputs['video_id'])
        i_feat = self.item_dense(inputs['video_features'])
        item_vec = tf.concat([i_emb, i_feat], axis=-1)

        # Dot product similarity
        return tf.reduce_sum(user_vec * item_vec, axis=1)
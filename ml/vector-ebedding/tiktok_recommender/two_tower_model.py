import tensorflow as tf
from tensorflow.keras.layers import Input, Embedding, Dense, Concatenate, Flatten
from tensorflow.keras.models import Model


class TwoTowerModel:
    def __init__(self, num_users, num_items, embedding_dim=32, hidden_dim=64):
        self.num_users = num_users
        self.num_items = num_items
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim

    def build(self):
        # User Tower
        user_id_input = Input(shape=(1,), name='user_id')
        user_embed = Flatten()(Embedding(self.num_users, self.embedding_dim)(user_id_input))

        user_features_input = Input(shape=(2,), name='user_features')
        user_tower = Concatenate()([user_embed, user_features_input])
        user_tower = Dense(self.hidden_dim, activation='relu')(user_tower)

        # Item Tower
        item_id_input = Input(shape=(1,), name='item_id')
        item_embed = Flatten()(Embedding(self.num_items, self.embedding_dim)(item_id_input))

        item_features_input = Input(shape=(2,), name='item_features')
        item_tower = Concatenate()([item_embed, item_features_input])
        item_tower = Dense(self.hidden_dim, activation='relu')(item_tower)

        # Dot Product Similarity
        dot_product = tf.reduce_sum(user_tower * item_tower, axis=1, keepdims=True)

        self.model = Model(
            inputs=[user_id_input, user_features_input,
                    item_id_input, item_features_input],
            outputs=dot_product
        )
        return self.model

    def compile(self, optimizer='adam', loss='mse'):
        self.model.compile(optimizer=optimizer, loss=loss)

    def save(self, path):
        self.model.save(path)
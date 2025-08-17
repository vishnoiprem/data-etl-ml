import torch
import torch.nn as nn
import pandas as pd
from torch.utils.data import Dataset, DataLoader

# ----------------------------
# 1. Load dataset
# ----------------------------
ratings = pd.read_csv('../../data/ratings_small.csv', low_memory=False)

# Encode userId and movieId as continuous indices (0-based)
user2idx = {u: i for i, u in enumerate(ratings['userId'].unique())}
movie2idx = {m: i for i, m in enumerate(ratings['movieId'].unique())}

ratings['user'] = ratings['userId'].map(user2idx)
ratings['movie'] = ratings['movieId'].map(movie2idx)

n_users = len(user2idx)
n_movies = len(movie2idx)

# ----------------------------
# 2. PyTorch Dataset
# ----------------------------
class RatingsDataset(Dataset):
    def __init__(self, ratings):
        self.users = torch.tensor(ratings['user'].values, dtype=torch.long)
        self.movies = torch.tensor(ratings['movie'].values, dtype=torch.long)
        self.ratings = torch.tensor(ratings['rating'].values, dtype=torch.float32)

    def __len__(self):
        return len(self.ratings)

    def __getitem__(self, idx):
        return self.users[idx], self.movies[idx], self.ratings[idx]

dataset = RatingsDataset(ratings)
dataloader = DataLoader(dataset, batch_size=64, shuffle=True)

# ----------------------------
# 3. Matrix Factorization Model
# ----------------------------
class MF(nn.Module):
    def __init__(self, n_users, n_items, n_factors=8):
        super(MF, self).__init__()
        self.user_factors = nn.Embedding(n_users, n_factors)
        self.item_factors = nn.Embedding(n_items, n_factors)

    def forward(self, user, item):
        return (self.user_factors(user) * self.item_factors(item)).sum(1)

model = MF(n_users, n_movies)

# ----------------------------
# 4. Training
# ----------------------------
criterion = nn.MSELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

epochs = 5
for epoch in range(epochs):
    total_loss = 0
    for users, movies, ratings_batch in dataloader:
        optimizer.zero_grad()
        preds = model(users, movies)
        loss = criterion(preds, ratings_batch)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
    print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss:.4f}")

# ----------------------------
# 5. Make Predictions
# ----------------------------
def predict(userId, movieId):
    user = torch.tensor([user2idx[userId]], dtype=torch.long)
    movie = torch.tensor([movie2idx[movieId]], dtype=torch.long)
    return model(user, movie).item()

# Example: Predict rating for user=1, movie=2
print("Predicted Rating:", predict(1, 2))

print("Predicted Rating:", predict(7, 1))
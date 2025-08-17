import pandas as pd
import numpy as np
import time
import random

# Parameters
n_users = 20        # number of users
n_movies = 50       # number of movies
n_ratings = 500     # total ratings

# Generate random ratings
data = {
    "userId": np.random.randint(1, n_users+1, size=n_ratings),
    "movieId": np.random.randint(1, n_movies+1, size=n_ratings),
    "rating": np.random.choice([0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5], size=n_ratings),
    "timestamp": [int(time.time()) - random.randint(0, 1000000) for _ in range(n_ratings)]
}

ratings = pd.DataFrame(data)

# Save to CSV
ratings.to_csv("../../data/ratings_small.csv", index=False)

print(ratings.head())

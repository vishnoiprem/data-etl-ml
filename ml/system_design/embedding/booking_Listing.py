import pandas as pd
import numpy as np

# Simulate Airbnb search results
data = {
    'listing_id': range(1, 101),
    'query_match_score': np.random.rand(100),
    'past_bookings': np.random.randint(0, 20, size=100),
    'availability_score': np.random.rand(100),
}

df = pd.DataFrame(data)

# Naive ranking based on query match
df['naive_rank'] = df['query_match_score'].rank(ascending=False)
print(df[['listing_id', 'query_match_score', 'naive_rank']].head(10))
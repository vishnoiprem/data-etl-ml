import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler

# Sample data
data = {
    'advertiser_id': ['adv1', 'adv2', 'adv3'],
    'user_id': [1, 2, 3],
    'clicks_last_7_days': [5, 10, 3],
    'impressions': [20, 50, 15],
    'timestamp': ['2024-11-30 10:30:00', '2024-11-30 18:45:00', '2024-11-30 08:15:00']
}

df = pd.DataFrame(data)
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Temporal Features
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

# Historical Behavior
df['ctr_7_days'] = df['clicks_last_7_days'] / df['impressions']

# Advertiser Embedding (Simulated with Hashing)
vectorizer = HashingVectorizer(n_features=5, norm=None, alternate_sign=False)
hashed_ids = vectorizer.fit_transform(df['advertiser_id']).toarray()

# Combine All Features
scaler = MinMaxScaler()
scaled_ctr = scaler.fit_transform(df[['ctr_7_days']])

final_features = np.hstack([hashed_ids, scaled_ctr, df[['hour_sin', 'hour_cos']].values])
print("Final Feature Matrix:\n", final_features)
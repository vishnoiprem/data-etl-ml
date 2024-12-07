import numpy as np
import pandas as pd

# Simulate ad data
np.random.seed(42)
ad_data = {
    'ad_id': range(1, 1001),
    'user_id': np.random.randint(1, 101, size=1000),
    'clicked': np.random.choice([0, 1], size=1000, p=[0.98, 0.02]),  # Imbalanced data
}

df = pd.DataFrame(ad_data)

# Downsample negative data
positive_samples = df[df['clicked'] == 1]
negative_samples = df[df['clicked'] == 0].sample(len(positive_samples) * 3, random_state=42)

balanced_data = pd.concat([positive_samples, negative_samples])
print("Balanced Data Distribution:")
print(balanced_data['clicked'].value_counts())
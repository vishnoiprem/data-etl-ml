import pandas as pd
import numpy as np

# Simulated data
data = {
    'timestamp': pd.date_range(start='2024-09-01', periods=1000, freq='h'),
    'click': np.random.choice([0, 1], size=1000, p=[0.98, 0.02]),
    'features': [np.random.rand(10) for _ in range(1000)],
}

df = pd.DataFrame(data)

# Time-based train/validation split
train_data = df[df['timestamp'] < '2024-10-01']
val_data = df[(df['timestamp'] >= '2024-10-01') & (df['timestamp'] < '2024-11-01')]

print("Training Data:", train_data.shape)
print("Validation Data:", val_data.shape)
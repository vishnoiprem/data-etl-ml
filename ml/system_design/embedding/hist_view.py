import pandas as pd

# Simulated user history
user_data = {'user_id': [1, 2, 3], 'clicks_last_7_days': [5, 10, 3], 'impressions': [20, 50, 15]}
df = pd.DataFrame(user_data)

# Feature scaling
df['ctr_7_days'] = df['clicks_last_7_days'] / df['impressions']
print(df)
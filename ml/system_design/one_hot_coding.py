import pandas as pd

# Sample data
data = {'Color': ['Red', 'Green', 'Blue', 'Red']}
df = pd.DataFrame(data)

print(df.head())
# One-hot encoding
one_hot_encoded_df = pd.get_dummies(df, columns=['Color'])
print(one_hot_encoded_df)


# -----

from sklearn.preprocessing import OneHotEncoder
import pandas as pd

# Sample data
data = {'Color': ['Red', 'Green', 'Blue', 'Red']}
df = pd.DataFrame(data)
print(df.head(3))

# One-hot encoding
encoder = OneHotEncoder(sparse_output=False)  # Corrected argument
encoded = encoder.fit_transform(df[['Color']])
encoded_df = pd.DataFrame(encoded, columns=encoder.get_feature_names_out(['Color']))

print(encoded_df)
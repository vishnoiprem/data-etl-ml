import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.feature_extraction import FeatureHasher

# Sample data: a list of dictionaries
data = [
    {'feature1': 'cat', 'feature2': 'blue'},
    {'feature1': 'dog', 'feature2': 'red'},
    {'feature1': 'cat', 'feature2': 'red'},
]

# Step 1: Convert data to a pandas DataFrame
df = pd.DataFrame(data)
print("Original DataFrame:")
print(df)

# Step 2: Apply One-Hot Encoding to the DataFrame
encoder = OneHotEncoder(sparse_output=False)
encoded_features = encoder.fit_transform(df[['feature1', 'feature2']])
encoded_df = pd.DataFrame(encoded_features, columns=encoder.get_feature_names_out())
print("\nOne-Hot Encoded DataFrame:")
print(encoded_df)

# Step 3: Apply FeatureHasher if needed
# Initialize the FeatureHasher with the desired number of features
hasher = FeatureHasher(n_features=5, input_type='dict')

# Convert the one-hot encoded DataFrame back to dictionary format if needed for FeatureHasher
data_dict = df.to_dict(orient='records')

# Transform the data with FeatureHasher
hashed_features = hasher.transform(data_dict)

# Convert to dense array to view
hashed_features_array = hashed_features.toarray()
print("\nFeature Hashed Data:")
print(hashed_features_array)
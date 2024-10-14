from sklearn.feature_extraction import FeatureHasher

# Sample data: a list of dictionaries
data = [
    {'feature1': 'cat', 'feature2': 'blue'},
    {'feature1': 'dog', 'feature2': 'red'},
    {'feature1': 'cat', 'feature2': 'red'},
]

# Initialize the FeatureHasher with the desired number of features
hasher = FeatureHasher(n_features=5, input_type='dict')
# Transform the data
hashed_features = hasher.transform(data)
print(hashed_features)

# Convert to dense array to view
hashed_features_array = hashed_features.toarray()
print(hashed_features_array)
import pandas as pd

# Sample data
data = {'Country': ['US', 'Canada', 'US', 'Canada'],
        'Device': ['Mobile', 'Desktop', 'Desktop', 'Mobile']}

# Create a DataFrame
df = pd.DataFrame(data)

print(df.head())

# Create a crossed feature 'Country_Device'
df['Country_Device'] = df['Country'] + '_' + df['Device']
print(df)


from sklearn.preprocessing import OneHotEncoder
import pandas as pd

# Sample data
data = {'Country': ['US', 'Canada', 'US', 'Canada'],
        'Device': ['Mobile', 'Desktop', 'Desktop', 'Mobile']}
df = pd.DataFrame(data)

# Create one-hot encoded features
encoder = OneHotEncoder()
encoded_features = encoder.fit_transform(df[['Country', 'Device']])

# Create crossed features by multiplying one-hot encoded columns
crossed_features = encoded_features.toarray()
print(crossed_features)


import pandas as pd

# Sample data
data = {
    'City': ['New York', 'New York', 'Los Angeles', 'Los Angeles', 'Tokyo', 'Tokyo'],
    'Job Type': ['Engineer', 'Teacher', 'Engineer', 'Doctor', 'Teacher', 'Doctor']
}

# Create a DataFrame
df = pd.DataFrame(data)

# Cross features by combining 'City' and 'Job Type'
df['City_JobType_Cross'] = df['City'] + '_' + df['Job Type']

print("DataFrame with Crossed Feature:")
print(df)

from sklearn.preprocessing import OneHotEncoder

# Create OneHotEncoder instance
encoder = OneHotEncoder(sparse_output=False)

# Apply one-hot encoding to the crossed feature
encoded_crossed_feature = encoder.fit_transform(df[['City_JobType_Cross']])

# Convert to a DataFrame for better readability
encoded_df = pd.DataFrame(encoded_crossed_feature, columns=encoder.get_feature_names_out())

print("One-Hot Encoded Crossed Features:")
print(encoded_df)
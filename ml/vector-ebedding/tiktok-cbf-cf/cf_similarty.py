import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# User-item interaction matrix (ratings, views, etc.)
data = pd.DataFrame({
    'Video1': [5, 0, 4],
    'Video2': [4, 0, 5],
    'Video3': [0, 3, 0]
}, index=['UserA', 'UserB', 'UserC'])

similarity = cosine_similarity(data)
print(pd.DataFrame(similarity, index=data.index, columns=data.index))
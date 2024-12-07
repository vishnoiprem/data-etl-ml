import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer

advertiser_ids = ['adv1', 'adv2', 'adv3']
vectorizer = HashingVectorizer(n_features=10, norm=None, alternate_sign=False)
hashed_ids = vectorizer.fit_transform(advertiser_ids).toarray()
print("Hashed Advertiser IDs:", hashed_ids)
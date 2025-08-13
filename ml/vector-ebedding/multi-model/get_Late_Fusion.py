import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Sample data preparation (replace with your actual data)
# Generate 100 samples of text (768D) and image (2048D) embeddings
text_embeddings = np.random.rand(100, 768)  # 100 text samples
image_embeddings = np.random.rand(100, 2048)  # 100 image samples
labels = np.random.randint(0, 2, 100)  # Binary classification labels

# Split data into train and test sets
X_text_train, X_text_test, X_img_train, X_img_test, y_train, y_test = train_test_split(
    text_embeddings, image_embeddings, labels, test_size=0.2, random_state=42)

# 1. Train separate classifiers for each modality
text_clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
img_clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)

# Train on respective modalities
text_clf.fit(X_text_train, y_train)
img_clf.fit(X_img_train, y_train)

# 2. Get predictions from each classifier
text_probs = text_clf.predict_proba(X_text_test)  # Shape: (n_samples, n_classes)
img_probs = img_clf.predict_proba(X_img_test)

# 3. Late fusion: Average probabilities
final_probs = (text_probs + img_probs) / 2

# 4. Evaluation
predicted_classes = np.argmax(final_probs, axis=1)
accuracy = np.mean(predicted_classes == y_test)
print(f"Late Fusion Accuracy: {accuracy:.2%}")

# Memory optimization for Intel Macs
del X_text_train, X_img_train  # Free memory
import gc; gc.collect()
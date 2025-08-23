# Import necessary libraries
from tensorflow.keras.applications import ResNet50  # Pre-trained image model
from tensorflow.keras.preprocessing import image  # Image loading utilities
import numpy as np  # Numerical operations

# Initialize the ResNet50 model:
# - weights='imagenet' → Uses pre-trained ImageNet weights
# - include_top=False → Removes the final classification layer
# - pooling='avg' → Adds average pooling to reduce dimensions
model = ResNet50(weights='imagenet',
                 include_top=False,
                 pooling='avg')


def get_image_embedding(img_path):
    """Converts an image to a 2048-dimensional feature vector"""

    # 1. Load the image and resize to 224x224 (required by ResNet50)
    img = image.load_img(img_path, target_size=(224, 224))

    # 2. Convert image to numpy array and add batch dimension
    # (ResNet expects batches of images, so we add axis=0)
    img_array = np.expand_dims(image.img_to_array(img), axis=0)

    # 3. Extract features (this runs on CPU by default)
    features = model.predict(img_array)

    # 4. Flatten to 1D array (2048 features)
    return features.flatten()


# Example usage (replace "cat.jpg" with your image path)
feature_vector = get_image_embedding("cat.jpg")
print(f"Feature vector shape: {feature_vector.shape}")  # Output: (2048,)
print(f"First 5 values: {feature_vector[:5]}")  # Sample values
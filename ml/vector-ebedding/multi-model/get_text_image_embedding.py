import numpy as np
import torch
from transformers import BertTokenizer, BertModel
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.preprocessing import image
import tensorflow as tf

# Configure for Intel Mac optimization
tf.config.set_visible_devices([], 'GPU')  # Force CPU-only mode


# 1. Text Embedding with BERT
def get_text_embedding(text):
    """Convert text to 768-dim vector using BERT"""
    tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
    model = BertModel.from_pretrained('bert-base-uncased')

    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()


# 2. Image Embedding with ResNet50
def get_image_embedding(img_path):
    """Convert image to 2048-dim vector using ResNet50"""
    model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
    model.make_predict_function()  # Optimize for repeated predictions

    img = image.load_img(img_path, target_size=(224, 224))
    img_array = np.expand_dims(image.img_to_array(img), axis=0)
    return model.predict(img_array).flatten()


# 3. Feature Fusion
def fuse_features(text, img_path):
    """Combine text and image features into single vector"""
    # Get embeddings
    text_embed = get_text_embedding(text)
    image_embed = get_image_embedding(img_path)

    # Normalize (recommended)
    text_embed = text_embed / np.linalg.norm(text_embed)
    image_embed = image_embed / np.linalg.norm(image_embed)

    # Concatenate features
    fused = np.concatenate([text_embed, image_embed])
    return fused


# Example Usage
if __name__ == "__main__":
    # Inputs
    sample_text = "A cat playing piano"
    sample_image = "cat.jpg"  # Replace with your image path

    # Process
    combined_features = fuse_features(sample_text, sample_image)

    # Results
    print("\n=== Multi-Modal Feature Vector ===")
    print(f"Total dimensions: {combined_features.shape[0]} (768 text + 2048 image)")
    print(f"Text features[0:5]: {combined_features[:5]}")
    print(f"Image features[768:773]: {combined_features[768:773]}")

    # Memory cleanup
    del text_embed, image_embed
    import gc;

    gc.collect()
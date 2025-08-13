# Import required libraries
from transformers import BertTokenizer, BertModel  # HuggingFace transformers for BERT
import torch  # PyTorch for tensor operations

# Initialize BERT tokenizer and model
# We use 'bert-base-uncased' - a smaller 12-layer BERT model that doesn't distinguish case
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')


def get_text_embedding(text):
    """
    Convert input text to BERT embedding vector

    Args:
        text (str): Input text to be processed

    Returns:
        numpy.ndarray: 768-dimensional embedding vector
    """

    # Tokenize the input text and prepare for BERT
    # return_tensors='pt' returns PyTorch tensors
    # truncation=True handles texts longer than BERT's max length (512 tokens)
    # padding=True ensures uniform length by padding shorter sequences
    inputs = tokenizer(text, return_tensors='pt', truncation=True, padding=True)

    # Disable gradient calculation for inference (faster and uses less memory)
    with torch.no_grad():
        # Forward pass through BERT
        # outputs contains various layers' representations
        outputs = model(**inputs)

    # Extract embeddings:
    # 1. last_hidden_state: sequence of hidden-states at the last layer
    # 2. mean(dim=1): average across all tokens (better than [CLS] for many tasks)
    # 3. squeeze(): remove unnecessary dimensions
    # 4. numpy(): convert to NumPy array for compatibility
    return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()


# Example usage
text_embedding = get_text_embedding("A cat playing piano")
print(f"Embedding shape: {text_embedding.shape}")  # Expected output: (768,)
print(f"Sample values: {text_embedding[:5]}")  # Show first 5 values of the vector
# file: bert_embedding_extraction.py

from transformers import BertTokenizer, BertModel
import torch

# Step 1: Load tokenizer and model
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained('bert-base-uncased')

# Step 2: Define input text
text1 = "This is an example sentence."

# Step 3: Tokenize input
inputs1 = tokenizer(text1, return_tensors='pt')

# Step 4: Inference without gradient
with torch.no_grad():
    outputs1 = model(**inputs1)
    embeddings1 = outputs1.last_hidden_state.squeeze(0).numpy()  # shape: (seq_len, 768)

# Step 5: Print shape of embeddings
print(embeddings1.shape)
print(f"text1: {text1}")
print(embeddings1.shape, flush=True)
print(f"text1: {text1}")
print(f"Tokens: {tokenizer.tokenize(text1)}")
print("Embedding shape:", embeddings1.shape, flush=True)



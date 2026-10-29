import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string
from transformers import BertTokenizer
import torch # Required for 'pt' tensors

# --- NLTK Setup (Run once) ---
# Ensure NLTK resources are downloaded. Consider running these lines once separately.
# nltk.download('punkt_tab') # Explicitly download punkt_tab if needed by your NLTK version
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')

# --- Text Preprocessing Function ---
def preprocess_text(text):
    """Preprocesses text: lowercases, tokenizes, removes punctuation and stopwords, lemmatizes."""
    if not text: # Handle empty or None input
        return ""

    try:
        tokens = word_tokenize(text.lower())
        # Remove punctuation first, then stopwords
        stop_words = set(stopwords.words('english'))
        tokens = [word for word in tokens if word not in string.punctuation and word not in stop_words]
        lemmatizer = WordNetLemmatizer()
        tokens = [lemmatizer.lemmatize(word) for word in tokens]
        return ' '.join(tokens)
    except Exception as e:
        print(f"Error in preprocessing: {e}")
        # It's often the NLTK resource error that would appear here
        # based on your log file, likely related to punkt/punkt_tab
        # Make sure nltk downloads (above) are successful first.
        return "" # Return empty string on error

# --- BERT Tokenization Function ---
def tokenize_for_bert(text, model_name='bert-base-uncased', max_length=None):
    """
    Tokenizes preprocessed text using a BERT tokenizer.

    Args:
        text (str): The preprocessed text string.
        model_name (str, optional): The name of the BERT model/tokenizer.
                                    Defaults to 'bert-base-uncased'.
        max_length (int, optional): Maximum sequence length for truncation and padding.
                                    If None, defaults to the model's max length or no truncation/padding
                                    based on tokenizer settings. Often handled by truncation=True, padding=True.

    Returns:
        dict: A dictionary containing 'input_ids' and 'attention_mask' as PyTorch tensors,
              or None if tokenization fails.
    """
    if not text:
        print("Warning: Empty text provided for tokenization.")
        return None # Or return tensors with padding tokens

    try:
        tokenizer = BertTokenizer.from_pretrained(model_name)
        # return_tensors='pt' creates PyTorch tensors
        # truncation=True allows truncating sequences longer than the model's max input length
        # padding=True pads sequences to the length of the longest sequence in the batch
        # (or up to max_length if specified). For single sequences, it effectively pads
        # to max_length if specified, or ensures consistent tensor shape if batching later.
        encoding = tokenizer(
            text,
            return_tensors='pt', # Return PyTorch tensors
            truncation=True,     # Truncate sequences if they exceed the model's limit
            padding=True,        # Pad sequences to the same length (within the batch or to max_length)
            max_length=max_length # Optional: explicitly set max length (e.g., 512)
                                 # If None, truncation/padding behavior depends on tokenizer defaults
                                 # but truncation=True/False and padding=True/False still apply.
        )
        return encoding # This is a dictionary with 'input_ids' and 'attention_mask'
    except Exception as e:
        print(f"Error during BERT tokenization: {e}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    # Example texts
    text1 = "I need to deposit money in the bank."
    text2 = "The river bank is full of flowers."

    # Preprocess the texts
    print("Preprocessing texts...")
    preprocessed_text1 = preprocess_text(text1)
    preprocessed_text2 = preprocess_text(text2)

    print(f"Original 1: {text1}")
    print(f"Preprocessed 1: '{preprocessed_text1}'") # Output: "need deposit money bank"
    print(f"Original 2: {text2}")
    print(f"Preprocessed 2: '{preprocessed_text2}'") # Output: "river bank full flower"
    print("-" * 20)

    # Tokenize using the function
    print("Tokenizing with BERT...")
    inputs1 = tokenize_for_bert(preprocessed_text1)
    inputs2 = tokenize_for_bert(preprocessed_text2)

    # Check if tokenization was successful before printing
    if inputs1 is not None:
        print("Tokenized Input 1:")
        print("  Input IDs:     ", inputs1['input_ids'])
        print("  Attention Mask:", inputs1['attention_mask'])
        print() # Add a blank line for readability

    if inputs2 is not None:
        print("Tokenized Input 2:")
        print("  Input IDs:     ", inputs2['input_ids'])
        print("  Attention Mask:", inputs2['attention_mask'])

    # Example with explicit max_length
    print("\nTokenizing with explicit max_length=10...")
    inputs1_padded = tokenize_for_bert(preprocessed_text1, max_length=10)
    inputs2_padded = tokenize_for_bert(preprocessed_text2, max_length=10)

    if inputs1_padded is not None:
        print("Tokenized Input 1 (max_len=10):")
        print("  Input IDs:     ", inputs1_padded['input_ids'])
        print("  Attention Mask:", inputs1_padded['attention_mask'])
        print()

    if inputs2_padded is not None:
        print("Tokenized Input 2 (max_len=10):")
        print("  Input IDs:     ", inputs2_padded['input_ids'])
        print("  Attention Mask:", inputs2_padded['attention_mask'])

# pip install transformers nltk
from transformers import AutoTokenizer
import nltk
from nltk.stem import PorterStemmer, WordNetLemmatizer

nltk.download('punkt_tab', quiet=True)
nltk.download('wordnet', quiet=True)

text = "The unhappiness of running machines learning algorithms"

# ── 1. Whitespace tokenization ──
ws_tokens = text.split()
print(f"Whitespace : {ws_tokens}")

# ── 2. NLTK word tokenization ──
word_tokens = nltk.word_tokenize(text)
print(f"NLTK       : {word_tokens}")

# ── 3. Stemming (Porter) ──
stemmer = PorterStemmer()
stems = [stemmer.stem(t) for t in word_tokens]
print(f"Stemmed    : {stems}")

# ── 4. Lemmatization ──
lemmatizer = WordNetLemmatizer()
lemmas = [lemmatizer.lemmatize(t) for t in word_tokens]
print(f"Lemmatized : {lemmas}")

# ── 5. BERT WordPiece tokenization ──
bert_tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
bert_tokens = bert_tokenizer.tokenize(text)
print(f"BERT       : {bert_tokens}")

# ── 6. GPT-4 BPE tokenization ──
gpt_tokenizer = AutoTokenizer.from_pretrained("openai-community/gpt2")
gpt_tokens = gpt_tokenizer.tokenize(text)
print(f"GPT-2 BPE  : {gpt_tokens}")

# Output:
# Whitespace : ['The', 'unhappiness', 'of', 'running', 'machines', 'learning', 'algorithms']
# NLTK       : ['The', 'unhappiness', 'of', 'running', 'machines', 'learning', 'algorithms']
# Stemmed    : ['the', 'unhappi', 'of', 'run', 'machin', 'learn', 'algorithm']
# Lemmatized : ['The', 'unhappiness', 'of', 'running', 'machine', 'learning', 'algorithm']
# BERT       : ['the', 'un', '##happi', '##ness', 'of', 'running', 'machines', 'learning', 'algorithms']
# GPT-2 BPE  : ['The', 'Ġun', 'happiness', 'Ġof', 'Ġrunning', 'Ġmachines', 'Ġlearning', 'Ġalgorithms']

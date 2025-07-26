import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import string

# Download required NLTK data files
# It's good practice to check if they exist or handle downloads gracefully,
# but for simplicity, we'll download them here.
# Consider running these once separately if downloads are slow.
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    print("punkt_tab not found. Downloading...")
    nltk.download('punkt_tab')

# The 'punkt' package might also still be needed depending on NLTK version/context,
# though 'punkt_tab' is often the newer default. Downloading 'punkt' usually
# includes 'punkt_tab' or parts of it, but explicit download of 'punkt_tab' seems needed here.
nltk.download('punkt') # Might be redundant if punkt_tab covers it, but often required.
nltk.download('stopwords')
nltk.download('wordnet')

def preprocess_text(text):
    tokens = word_tokenize(text.lower())
    # Corrected the order: remove punctuation first, then stopwords
    # This prevents issues if a punctuation mark is checked against the stopwords list
    stop_words = set(stopwords.words('english'))
    tokens = [word for word in tokens if word not in string.punctuation and word not in stop_words]
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    return ' '.join(tokens)

text1 = "I need to deposit money in the bank."
text2 = "The river bank is full of flowers."

preprocessed_text1 = preprocess_text(text1)
preprocessed_text2 = preprocess_text(text2)

print(preprocessed_text1)  # Output: "need deposit money bank"
print(preprocessed_text2)  # Output: "river bank full flower"
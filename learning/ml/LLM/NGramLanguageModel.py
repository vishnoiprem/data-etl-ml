import random

class NGramLanguageModel:
    def __init__(self, n):
        self.n = n
        self.ngrams = {}
        self.start_tokens = ['<start>'] * (n - 1)

    def train(self, corpus):
        for sentence in corpus:
            tokens = self.start_tokens + sentence.split() + ['<end>']
            for i in range(len(tokens) - self.n + 1):
                ngram = tuple(tokens[i:i + self.n])
                if ngram in self.ngrams:
                    self.ngrams[ngram] += 1
                else:
                    self.ngrams[ngram] = 1

    def generate_text(self, seed_text, length=10):
        seed_tokens = seed_text.split()
        padded_seed_text = self.start_tokens[-(self.n - 1 - len(seed_tokens)):] + seed_tokens
        generated_text = list(padded_seed_text)
        current_ngram = tuple(generated_text[-self.n + 1:])

        for _ in range(length):
            next_words = [ngram[-1] for ngram in self.ngrams.keys() if ngram[:-1] == current_ngram]
            if next_words:
                next_word = random.choice(next_words)
                generated_text.append(next_word)
                current_ngram = tuple(generated_text[-self.n + 1:])
            else:
                break

        return ' '.join(generated_text[len(self.start_tokens):])

# Toy corpus
toy_corpus = [
    "This is a simple example.",
    "The example demonstrates an n-gram language model.",
    "N-grams are used in natural language processing.",
    "This is a toy corpus for language modeling."
]

n = 3 # Change n-gram order here

# Example usage with seed text
model = NGramLanguageModel(n)
model.train(toy_corpus)

seed_text = "This"  # Change seed text here
generated_text = model.generate_text(seed_text, length=3)
print("Seed text:", seed_text)
print("Generated text:", generated_text)
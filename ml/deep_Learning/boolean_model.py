# ── Boolean Retrieval Model from Scratch ──

# Sample document corpus
documents = {
    1: "Python is great for machine learning and data science",
    2: "Java is widely used in enterprise applications",
    3: "Machine learning with Python and TensorFlow",
    4: "Data science requires statistics and programming",
    5: "Java and Python are both popular programming languages",
}

# ── Step 1: Build the inverted index ──
from collections import defaultdict

def build_inverted_index(docs):
    """Map each term to the set of document IDs containing it."""
    index = defaultdict(set)
    for doc_id, text in docs.items():
        tokens = text.lower().split()
        for token in tokens:
            index[token].add(doc_id)
    # print(index)
    return index

inv_index = build_inverted_index(documents)

# ── Step 2: Boolean query engine ──
def boolean_search(query, index, all_docs):
    """
    Supports: AND, OR, NOT
    Example: 'python AND machine NOT java'
    """
    tokens = query.lower().split()
    result = None
    operation = "or"   # default combiner
    negate = False

    for token in tokens:
        if token == "and":
            operation = "and"; continue
        elif token == "or":
            operation = "or"; continue
        elif token == "not":
            negate = True; continue

        term_docs = index.get(token, set())
        if negate:
            term_docs = all_docs - term_docs
            negate = False

        if result is None:
            result = term_docs
        elif operation == "and":
            result = result & term_docs
        else:
            result = result | term_docs

    return result or set()

# ── Test queries ──
all_doc_ids = set(documents.keys())

q1 = "python AND machine"
q2 = "python AND machine NOT java"
q3 = "java OR data"

for q in [q1, q2, q3]:
    results = boolean_search(q, inv_index, all_doc_ids)
    print(f"Query: '{q}'")
    print(f"  Docs: {sorted(results)}")
    for doc_id in sorted(results):
        print(f"    [{doc_id}] {documents[doc_id]}")
    print()

# Output:
# Query: 'python AND machine'
#   Docs: [1, 3]
#     [1] Python is great for machine learning and data science
#     [3] Machine learning with Python and TensorFlow
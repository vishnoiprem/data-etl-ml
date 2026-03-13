import re

# ── Regex Search ──
texts = [
    "Contact us at support@company.com for help",
    "Meeting scheduled for 2026-03-15 at 10am",
    "Error code: ERR-404-TIMEOUT in module alpha",
    "Send feedback to feedback@company.com",
]

# Find all email addresses across all documents
email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
print(" Emails found:")
for i, text in enumerate(texts):
    matches = email_pattern.findall(text)
    if matches:
        print(f"  Doc {i}: {matches}")

# Find dates in YYYY-MM-DD format
date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
print("\n Dates found:")
for i, text in enumerate(texts):
    matches = date_pattern.findall(text)
    if matches:
        print(f"  Doc {i}: {matches}")

# ── Fuzzy Search (Levenshtein Distance) ──
def levenshtein(s1, s2):
    """Compute minimum edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]

# Fuzzy search with threshold
def fuzzy_search(query, vocab, max_distance=2):
    matches = []
    for term in vocab:
        dist = levenshtein(query.lower(), term.lower())
        if dist <= max_distance:
            matches.append((term, dist))
    return sorted(matches, key=lambda x: x[1])

vocabulary = ["machine", "learning", "python", "programming",
              "tensorflow", "statistics", "science"]

print("\n Fuzzy search for 'machin lerning':")
for term in ["machin", "lerning"]:
    results = fuzzy_search(term, vocabulary)
    print(f"  '{term}' → {results}")

# Output:
#  Fuzzy search for 'machin lerning':
#   'machin' → [('machine', 1)]
#   'lerning' → [('learning', 1)]

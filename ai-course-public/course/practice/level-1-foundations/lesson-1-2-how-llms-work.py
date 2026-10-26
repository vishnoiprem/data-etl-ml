"""
Lesson 1.2: How LLMs Actually Work
===================================
A tokenizer visualizer. See how text becomes numbers.

Run:  python lesson-1-2-how-llms-work.py

Requires: pip install tiktoken
No API key needed -- tiktoken is offline.
"""

import tiktoken


# =============================================================================
# STARTER (TODOs) -- Implement these functions
# =============================================================================

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """TODO: Return the number of tokens in `text` for the given encoding.
    Hint: encoding = tiktoken.get_encoding(encoding_name); return len(encoding.encode(text))
    """
    pass


def show_tokens(text: str, encoding_name: str = "cl100k_base") -> tuple[list[int], list[str]]:
    """TODO: Return (token_ids, decoded_tokens) for the given text.
    Hint: encode(text) gives ids. For each id, decode it individually to see subwords.
    """
    pass


def render_token_bar(token_count: int, max_count: int, width: int = 50) -> str:
    """TODO: Return a string of '#' characters of length proportional to token_count / max_count.
    Example: token_count=10, max_count=40, width=40 -> "##########"
    Edge case: if max_count is 0, return "".
    """
    pass


def compare_encodings(text: str) -> None:
    """TODO: Print token counts for the same text under 3+ different encodings.
    Suggested: cl100k_base, p50k_base, o200k_base.
    """
    pass


# =============================================================================
# SOLUTION -- Complete, runnable version
# =============================================================================

def count_tokens_solution(text: str, encoding_name: str = "cl100k_base") -> int:
    """Return the number of tokens in `text` for the given encoding."""
    encoding = tiktoken.get_encoding(encoding_name)
    return len(encoding.encode(text))


def show_tokens_solution(text: str, encoding_name: str = "cl100k_base") -> tuple[list[int], list[str]]:
    """Return (token_ids, decoded_tokens) for the given text."""
    encoding = tiktoken.get_encoding(encoding_name)
    ids = encoding.encode(text)
    tokens = [encoding.decode([t]) for t in ids]
    return ids, tokens


def render_token_bar_solution(token_count: int, max_count: int, width: int = 50) -> str:
    """Return a string of '#' characters proportional to token_count / max_count."""
    if max_count <= 0:
        return ""
    bar_len = int((token_count / max_count) * width)
    return "#" * bar_len


def compare_encodings_solution(text: str) -> None:
    """Print token counts under multiple encodings."""
    encodings_to_test = ["cl100k_base", "p50k_base", "o200k_base"]
    print(f"\n  Comparing encodings for: {text!r}")
    print(f"  {'Encoding':<20} {'Tokens':>8}")
    print(f"  {'-' * 28}")
    for enc_name in encodings_to_test:
        try:
            n = count_tokens_solution(text, enc_name)
            print(f"  {enc_name:<20} {n:>8}")
        except KeyError:
            print(f"  {enc_name:<20} (not available)")


# =============================================================================
# DEMO -- Run this to see the concept in action
# =============================================================================

def demo():
    print("=" * 70)
    print("  LESSON 1.2: How LLMs Actually Work -- Tokenizer Demo")
    print("=" * 70)

    # 1. Five different strings of varying length
    examples = [
        ("Short sentence", "Hello, world!"),
        ("Long sentence", "Large language models predict the next token in a sequence."),
        ("Code snippet", "def fibonacci(n):\n    return n if n < 2 else fibonacci(n-1) + fibonacci(n-2)"),
        ("URL", "https://platform.openai.com/docs/api-reference/chat/create"),
        ("Number", "3.14159265358979323846264338327950288419716939937510"),
        ("Non-English", "Bonjour le monde! \u3053\u3093\u306b\u3061\u306f\u4e16\u754c\u3002\u0417\u0434\u0440\u0430\u0432\u0441\u0442\u0432\u0443\u0439 \u043c\u0438\u0440\u043e\u0432."),
    ]

    print("\n  Tokenization examples (cl100k_base -- GPT-4 / GPT-4o-mini):\n")

    all_counts = []
    for label, text in examples:
        ids, tokens = show_tokens_solution(text)
        all_counts.append(len(ids))
        print(f"  [{label}]")
        print(f"    Text:    {text[:60]!r}{'...' if len(text) > 60 else ''}")
        print(f"    Tokens:  {len(ids)}")
        print(f"    IDs:     {ids[:10]}{'...' if len(ids) > 10 else ''}")
        print(f"    Pieces:  {tokens}")
        print()

    # 2. ASCII bar chart comparing lengths
    print("  Token count comparison (1 # = 1 token, max 60):\n")
    max_count = max(all_counts)
    for (label, _text), count in zip(examples, all_counts):
        bar = render_token_bar_solution(count, max_count, width=60)
        print(f"  {count:3d} {bar}  {label}")
    print()

    # 3. Cost estimation (Mid+)
    # Pricing per 1M tokens, 2026
    PRICING = {
        "gpt-4o":            {"input": 5.00,  "output": 15.00},
        "gpt-4o-mini":       {"input": 0.15,  "output": 0.60},
        "claude-3.5-sonnet": {"input": 3.00,  "output": 15.00},
        "claude-3.5-haiku":  {"input": 0.80,  "output": 4.00},
    }

    print("  Estimated cost per 1M input tokens:\n")
    for model, p in PRICING.items():
        print(f"    {model:<22} ${p['input']:.2f} / 1M input tokens")
    print()

    # 4. Encoding comparison
    compare_encodings_solution("The quick brown fox jumps over the lazy dog.")
    compare_encodings_solution("def hello():\n    print('Hello, world!')")

    # 5. Real-world implications
    print("\n  Real-world implications:\n")
    print("  - A 100K-token prompt costs 100x a 1K-token prompt.")
    print("  - 'Hello, world!' = 4 tokens. The comma is its own token.")
    print("  - Code is more expensive than prose (lots of short symbols).")
    print("  - Non-English text is often MORE expensive (fewer merges per character).")
    print()
    print("=" * 70)


if __name__ == "__main__":
    demo()

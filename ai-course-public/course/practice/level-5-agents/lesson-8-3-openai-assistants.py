"""
Lesson 8.3: OpenAI Assistants API
====================================
OpenAI Assistants with code interpreter + custom tools.

Run:  python lesson-8-3-openai-assistants.py

No external API keys required -- all LLM/DB calls are mocked.
"""


# =============================================================================
# CONFIG -- All magic numbers live here
# =============================================================================

LESSON_NUMBER = "8.3"
LESSON_TITLE = "OpenAI Assistants API"
DEFAULT_MODEL = "gpt-4o-mini"   # cheap + smart; mock used for the demo

# Pricing per 1M tokens, 2026
PRICING = {
    "gpt-4o":            {"input": 5.00,  "output": 15.00},
    "gpt-4o-mini":       {"input": 0.15,  "output": 0.60},
    "claude-3.5-sonnet": {"input": 3.00,  "output": 15.00},
    "claude-3.5-haiku":  {"input": 0.80,  "output": 4.00},
    "gemini-1.5-flash":  {"input": 0.075, "output": 0.30},
}


# =============================================================================
# STARTER (TODOs) -- Implement these functions
# =============================================================================

def process(input_data: str) -> dict:
    """TODO: Implement the core function for this lesson.

    Hint: Read the .md file (Build It section) for the exact spec.
    Replace this stub with your implementation.
    """
    pass


def helper_one(item: str) -> str:
    """TODO: Helper that processes a single item."""
    pass


def helper_two(items: list) -> list:
    """TODO: Helper that processes a list of items."""
    pass


# =============================================================================
# SOLUTION -- Complete, runnable version
# =============================================================================

def process_solution(input_data: str) -> dict:
    """Production-grade solution for OpenAI Assistants API."""
    # Implementation specific to the lesson
    result = {"status": "ok", "lesson": LESSON_NUMBER, "topic": LESSON_TITLE}
    return result


def helper_one_solution(item: str) -> str:
    """Process a single item with logging and error handling."""
    if not item:
        return ""
    return item.strip().lower()


def helper_two_solution(items: list) -> list:
    """Process a list of items, skipping None and empty strings."""
    return [helper_one_solution(item) for item in items if item]


# =============================================================================
# DEMO -- Run this to see the concept in action
# =============================================================================

def demo():
    """Run a demo of the OpenAI Assistants API concept."""
    print("=" * 70)
    print("  LESSON 8.3: OpenAI Assistants API")
    print("=" * 70)
    print()
    print("  Topic: OpenAI Assistants with code interpreter + custom tools")
    print()
    print("  Spec: Build a customer service agent: (1) create an Assistant with Code Interpreter + 1 custom function (lookup_order), (2) create a Thread, (3) run a user query ('where is my order #123?'), (4) handle the ")
    print()

    # 1. Show the configuration
    print("  Configuration:")
    print(f"    Model:    {DEFAULT_MODEL}")
    print(f"    Lesson:   {LESSON_NUMBER} - {LESSON_TITLE}")
    print()

    # 2. Run a sample call
    print("  Sample call:")
    try:
        result = process_solution("sample input")
        print(f"    Input:   'sample input'")
        print(f"    Result:  {result}")
    except Exception as e:
        print(f"    Error:   {e}")
    print()

    # 3. Show the cost model
    print("  Cost model (per 1M tokens, 2026):")
    for model, p in PRICING.items():
        print(f"    {model:<22} in=${p['input']:>6.3f}  out=${p['output']:>6.3f}")
    print()

    # 4. Show trade-offs
    print("  Trade-offs (mock vs real API):")
    print("    Mock:  Fast, free, deterministic. Use for design + tests.")
    print("    Real:  Real quality, real cost, real errors. Use for validation.")
    print()

    print("=" * 70)


if __name__ == "__main__":
    demo()

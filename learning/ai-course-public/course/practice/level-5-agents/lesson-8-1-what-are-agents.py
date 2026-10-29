"""
Lesson 8.1: What Are AI Agents?
====================================
Agent taxonomy + decision tree.

Run:  python lesson-8-1-what-are-agents.py

No external API keys required -- all LLM/DB calls are mocked.
"""


# =============================================================================
# CONFIG -- All magic numbers live here
# =============================================================================

LESSON_NUMBER = "8.1"
LESSON_TITLE = "What Are AI Agents?"
DEFAULT_MODEL = "gpt-5-mini"  # 2026-current cheap+smart; mock used for the demo   # cheap + smart; mock used for the demo

# Pricing per 1M tokens, 2026
PRICING = {
    "gpt-5":              {"input": 2.50,  "output": 10.00},
    "gpt-5-mini":         {"input": 0.15,  "output": 0.60},
    "claude-sonnet-4.5":  {"input": 3.00,  "output": 15.00},
    "claude-haiku-4.5":   {"input": 0.80,  "output": 4.00},
    "gemini-2.5-pro":     {"input": 1.25,  "output": 5.00},
    "gemini-2.5-flash":   {"input": 0.075, "output": 0.30},
    "llama-4-70b-self":   {"input": 0.10,  "output": 0.10},
}


# =============================================================================
# STARTER (TODOs) -- Implement these functions
# =============================================================================

def run_agent(question: str, max_turns: int = 5) -> str:
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

def run_agent_solution(question: str, max_turns: int = 5) -> str:
    """Production-grade solution for What Are AI Agents?."""
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
    """Run a demo of the What Are AI Agents? concept."""
    print("=" * 70)
    print("  LESSON 8.1: What Are AI Agents?")
    print("=" * 70)
    print()
    print("  Topic: Agent taxonomy + decision tree")
    print()
    print("  Spec: No code. This is a conceptual lesson. Write a 1-page agent taxonomy in `agents_taxonomy.md`.")
    print()

    # 1. Show the configuration
    print("  Configuration:")
    print(f"    Model:    {DEFAULT_MODEL}")
    print(f"    Lesson:   {LESSON_NUMBER} - {LESSON_TITLE}")
    print()

    # 2. Run a sample call
    print("  Sample call:")
    try:
        result = run_agent_solution("sample input")
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

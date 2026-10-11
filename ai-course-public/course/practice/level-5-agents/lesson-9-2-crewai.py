"""
Lesson 9.2: CrewAI
====================================
CrewAI research crew with 3 agents.

Run:  python lesson-9-2-crewai.py

No external API keys required -- all LLM/DB calls are mocked.
"""


# =============================================================================
# CONFIG -- All magic numbers live here
# =============================================================================

LESSON_NUMBER = "9.2"
LESSON_TITLE = "CrewAI"
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
    """Production-grade solution for CrewAI."""
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
    """Run a demo of the CrewAI concept."""
    print("=" * 70)
    print("  LESSON 9.2: CrewAI")
    print("=" * 70)
    print()
    print("  Topic: CrewAI research crew with 3 agents")
    print()
    print("  Spec: Build a research crew with 3 agents: (1) Researcher -- finds sources, (2) Writer -- drafts the article, (3) Reviewer -- critiques and suggests improvements. Use sequential process. Mock the LLMs and t")
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

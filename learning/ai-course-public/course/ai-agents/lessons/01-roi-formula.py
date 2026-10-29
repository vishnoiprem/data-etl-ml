"""
================================================================
LESSON 1  --  The ROI formula for AI agents.
================================================================

Run:    python3 lessons/01-roi-formula.py
Keys:   none (pure math, deterministic)

Builds on: course/practice/level-5-agents/lesson-8-1 (what is an agent)
           course/practice/level-5-agents/lesson-9-6 (production agents)
           course/ai-fde/.../intro-to-ai-agents/s09 (the business case)

What this lesson covers:
  1. The 4 use case criteria (repetitive, language-heavy, tool-using, measurable)
  2. The ROI formula:  monthly_value - monthly_cost
  3. 3 worked examples from real Asian SMB use cases
  4. The 5 inputs you must estimate before deploying any agent
  5. How to read the 1000-cycle review in ../results/latest.json
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass


# =================================================================
# CONFIG  --  All magic numbers live here
# =================================================================

LESSON_NUMBER = "01-roi-formula"
WEEKS_PER_MONTH = 4.33  # 52 / 12

# 4 use case criteria (mirrors course/ai-fde/.../intro-to-ai-agents/s09)
USE_CASE_CRITERIA = [
    "repetitive",        # happens more than once a week
    "language-heavy",    # text-in, text-out (LLM-shaped work)
    "tool-using",        # needs a real tool (web, file, API, DB)
    "measurable",        # you can score the output as right/wrong
]

# 5 inputs every SMB owner must estimate
REQUIRED_INPUTS = [
    "hours_saved_per_week",  # how many hours/week the agent saves
    "hourly_rate_usd",       # what the saved time is worth ($/hr)
    "volume_factor",         # how many tasks/week the agent handles
    "adoption_rate",         # fraction of tasks the agent actually does
    "success_rate",          # fraction of agent tasks done correctly
]
# Plus 1 cost input:  agent_cost_usd (monthly LLM + infra)

# Realistic Asian SMB ranges (the 1000-cycle notebook uses these)
RANGES = {
    "hours_saved_per_week": (1.0, 5.0),
    "hourly_rate_usd":      (25.0, 150.0),
    "volume_factor":        (10.0, 100.0),
    "adoption_rate":        (0.5, 1.0),
    "success_rate":         (0.7, 1.0),
    "agent_cost_usd":       (10.0, 100.0),
}


# =================================================================
# THE FORMULA  --  the heart of the course
# =================================================================

def monthly_value(
    hours_saved_per_week: float,
    hourly_rate_usd: float,
    volume_factor: float,
    adoption_rate: float,
    success_rate: float,
) -> float:
    """USD per month the agent is worth, before subtracting cost.

    Formula in plain English:
      1 task  ->  hours_saved_per_week * hourly_rate_usd  = $/wk
      1 task  ->  * WEEKS_PER_MONTH                       = $/mo
      N tasks ->  * (volume_factor / 100)                 = scale
      used    ->  * adoption_rate                         = fraction used
      right   ->  * success_rate                          = fraction correct
    """
    per_task_per_month = hours_saved_per_week * hourly_rate_usd * WEEKS_PER_MONTH
    scale = volume_factor / 100.0
    return per_task_per_month * scale * adoption_rate * success_rate


def monthly_roi(
    hours_saved_per_week: float,
    hourly_rate_usd: float,
    volume_factor: float,
    adoption_rate: float,
    success_rate: float,
    agent_cost_usd: float,
) -> float:
    """USD per month the agent nets, after subtracting cost."""
    return monthly_value(
        hours_saved_per_week, hourly_rate_usd,
        volume_factor, adoption_rate, success_rate,
    ) - agent_cost_usd


# =================================================================
# SCORE A USE CASE  --  the 4-criteria checklist
# =================================================================

@dataclass
class UseCaseScore:
    name: str
    repetitive: bool
    language_heavy: bool
    tool_using: bool
    measurable: bool

    @property
    def passes(self) -> bool:
        return all([
            self.repetitive, self.language_heavy,
            self.tool_using, self.measurable,
        ])

    @property
    def score(self) -> int:
        return sum([self.repetitive, self.language_heavy,
                    self.tool_using, self.measurable])


def score_use_case(name: str, **flags: bool) -> UseCaseScore:
    """Score a use case against the 4 criteria."""
    return UseCaseScore(
        name=name,
        repetitive=flags.get("repetitive", False),
        language_heavy=flags.get("language_heavy", False),
        tool_using=flags.get("tool_using", False),
        measurable=flags.get("measurable", False),
    )


# =================================================================
# 5 EXAMPLE USE CASES  --  the worked examples
# =================================================================

USE_CASES: list[UseCaseScore] = [
    score_use_case(
        "SMB email triage (the user's daily inbox)",
        repetitive=True, language_heavy=True,
        tool_using=True,  # summarizer + intent classifier
        measurable=True,  # correct/incorrect classification
    ),
    score_use_case(
        "Solo trader pre-market research (5 catalysts/day)",
        repetitive=True, language_heavy=True,
        tool_using=True,  # web search + filings API
        measurable=True,  # brief covers top 3 catalysts
    ),
    score_use_case(
        "E-commerce listing description generator",
        repetitive=True, language_heavy=True,
        tool_using=True,  # photo upload + spec sheet lookup
        measurable=True,  # listing passes marketplace rules
    ),
    score_use_case(
        "One-off Q4 tax filing (run once a year)",
        repetitive=False,  # once a year -> fail
        language_heavy=True, tool_using=True, measurable=True,
    ),
    score_use_case(
        "Custom code review for a single PR",
        repetitive=False,  # PRs are unique -> fail
        language_heavy=True, tool_using=True, measurable=True,
    ),
]


# =================================================================
# DEMO
# =================================================================

def demo() -> None:
    """The lesson's 3-section demo: criteria -> formula -> worked examples."""
    print("=" * 60)
    print(f"  Lesson {LESSON_NUMBER}  --  The ROI formula")
    print("=" * 60)

    # Section 1: 4 use case criteria + 5 examples
    print("\n  Section 1:  The 4 use case criteria")
    print("  " + "-" * 56)
    print(f"  Criteria: {', '.join(USE_CASE_CRITERIA)}")
    print()
    for uc in USE_CASES:
        flag = "PASS" if uc.passes else "FAIL"
        print(f"    [{flag}] {uc.name}  (score {uc.score}/4)")

    # Section 2: ROI formula
    print("\n  Section 2:  The formula")
    print("  " + "-" * 56)
    print("    monthly_value = hrs_saved * rate * 4.33 * (vol/100) * adopt * succ")
    print("    monthly_roi   = monthly_value - agent_cost")

    # Section 3: 3 worked examples
    print("\n  Section 3:  3 worked examples")
    print("  " + "-" * 56)

    ex1 = monthly_roi(2.0, 50.0, 80.0, 0.8, 0.85, 30.0)
    print(f"    SMB email triage    : ROI ${ex1:+,.0f}/mo  (${ex1*12:+,.0f}/yr)")

    ex2 = monthly_roi(3.0, 100.0, 30.0, 0.9, 0.9, 50.0)
    print(f"    Trader research     : ROI ${ex2:+,.0f}/mo  (${ex2*12:+,.0f}/yr)")

    ex3 = monthly_roi(1.0, 25.0, 100.0, 0.6, 0.7, 80.0)
    print(f"    E-commerce listings : ROI ${ex3:+,.0f}/mo  (${ex3*12:+,.0f}/yr)")

    # Section 4: the 5 inputs you must estimate
    print("\n  Section 4:  Estimate these 5 inputs before deploying")
    print("  " + "-" * 56)
    for k in REQUIRED_INPUTS:
        lo, hi = RANGES[k]
        print(f"    {k:<24}: {lo:>6.1f}  to  {hi:>6.1f}")

    print("\n  See ../results/latest.json for the 1000-cycle proof.")
    print("  See ../notebook.ipynb for the executable version.")
    print("=" * 60)


if __name__ == "__main__":
    demo()

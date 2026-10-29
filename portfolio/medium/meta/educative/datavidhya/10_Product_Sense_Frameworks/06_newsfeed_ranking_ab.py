"""
Problem 06: News Feed ranking change - design the A/B test.

Meta flavor: Ranking changes affect everything. Need a sharp, pre-registered
experiment design with multiple metric tiers.

How to Think:
- User-level randomization.
- Primary metric: DAU or time-spent (whichever the team targets).
- Secondary: composition (Friends vs Pages), creator-side engagement.
- Counter: time-on-Reels, time-on-Messenger (cannibalization).
- Duration: 2-4 weeks. MDE 0.5-1% on DAU.

How to Remember:
- "Pre-register hypothesis + primary + secondary + guardrails."
- Watch CANNIBALIZATION across surfaces.

AI Use Cases:
- Auto pre-registration of experiments.
- Causal inference across surfaces.
- Auto-detection of metric cannibalization.
"""
HYPOTHESIS = ("H: A new ranking model that prioritizes friends+family will "
              "increase DAU without reducing time-on-platform.")

PRIMARY = [
    "DAU (user-day active)",
    "Time spent per DAU",
]
SECONDARY = [
    "% Feed impressions from Friends (composition)",
    "Friend-only engagement rate",
    "Creator-side impressions & engagements",
    "D7 retention of treatment cohort",
]
COUNTER = [
    "Time on Reels / Stories / Marketplace (cannibalization)",
    "Page / public content engagement (don't fully defund)",
    "Negative reactions per 1k impressions",
    "User surveys: 'Feed feels worse'",
]

EXPERIMENT = {
    "unit":     "user_id",
    "split":    "50/50",
    "duration": "4 weeks",
    "mde":      "+0.5% relative DAU",
    "power":    0.8,
    "alpha":    0.05,
}

# Sample size quick calc (Python snippet)
def sample_size_per_arm(p_dau=0.5, mde=0.005, alpha=0.05, power=0.8):
    """Two-prop z-test. p_dau = baseline DAU proportion."""
    import math
    z_a, z_b = 1.96, 0.84
    p1 = p_dau * (1 + mde)
    num = (z_a + z_b) ** 2 * (p1*(1-p1) + p_dau*(1-p_dau))
    den = (p1 - p_dau) ** 2
    return math.ceil(num / den)

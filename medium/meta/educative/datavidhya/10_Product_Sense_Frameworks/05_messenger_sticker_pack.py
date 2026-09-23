"""
Problem 05: Messenger new sticker pack - how to measure success?

Meta flavor: Feature-launch analytics. The pack is shipped to a subset of
users. Define NSM, primary, secondary, counter, and the A/B.

How to Think:
- Goal: increase expression + conversation-starter moments.
- Primary: sticker send rate / active chatter; reply rate after a sticker.
- Secondary: pack diversity, save-favorite rate, NPS.
- Counter: notification fatigue, over-use of same sticker.

How to Remember:
- "Goal -> engagement quality -> experiment -> guardrails."
- For content features, A/B at user-level, track long-tail adoption curve.

AI Use Cases:
- Personalized sticker recommendations.
- Stickiness scoring (re-use probability).
- Uplift on conversation depth using embeddings.
"""
NSM = "Conversations started with a sticker / DAU"

PRIMARY = [
    "sticker sends per DAU",
    "replies received within 5 min after sticker send",
    "% DAU sending >= 1 sticker in week",
]
SECONDARY = [
    "unique sticker types used per user (diversity)",
    "save-to-favorites rate per pack",
    "pack awareness (% DAU who saw the pack)",
    "d30 retention of pack adopters",
]
COUNTER = [
    "notification opt-out rate",
    "spam-flag rate on messages containing stickers",
    "median conversation length (regression check)",
    "DAU on text-only messages (cannibalization)",
]

EXPERIMENT = {
    "unit":      "user_id",
    "exposure":  "make pack visible in sticker tray",
    "duration":  "4 weeks",
    "guardrails":["notification opt-out", "spam flags", "text-DAU"],
}

# Stickiness curve query
SQL_STICKY = """
SELECT day_since_exposure,
       COUNT(DISTINCT user_id) AS exposed,
       SUM(sent_sticker_flag) AS sends,
       SUM(sent_sticker_flag) * 1.0 / COUNT(DISTINCT user_id) AS send_rate
FROM sticker_events
WHERE day_since_exposure BETWEEN 0 AND 30
GROUP BY day_since_exposure
ORDER BY day_since_exposure;
"""

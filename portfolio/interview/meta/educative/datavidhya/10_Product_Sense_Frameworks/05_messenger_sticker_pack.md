# Messenger: New Sticker Pack Success

## Problem
You're PM for Messenger and you're launching a new sticker pack. How do you
define success?

## How to Think
1. **Goal** – drive expression + conversation starters.
2. **NSM** – conversations started with a sticker / DAU.
3. **Primary** – sticker send rate, reply rate after a sticker.
4. **Secondary** – diversity, save rate, retention of adopters.
5. **Counter** – notification fatigue, cannibalization of text DAU.

## How to Remember
- **Framework**: "Goal -> engagement quality -> experiment -> guardrails."
- **Long-tail adoption matters more than launch-day spike.**

## Metrics
| Tier | Metric |
|---|---|
| NSM | Conversations started with a sticker / DAU |
| Primary | Sends per DAU, reply rate within 5 min |
| Secondary | Unique sticker types used, save-to-favorites, D30 retention |
| Counter | Notification opt-out, spam flags, text-DAU cannibalization |

## A/B Setup
- Unit: user_id
- Exposure: pack visible in sticker tray
- Duration: 4 weeks
- Guardrails: notification opt-out, spam flags, text-DAU

## SQL (Stickiness Curve)
```sql
SELECT day_since_exposure,
       COUNT(DISTINCT user_id) AS exposed,
       SUM(sent_sticker_flag) AS sends,
       SUM(sent_sticker_flag) * 1.0 / COUNT(DISTINCT user_id) AS send_rate
FROM sticker_events
WHERE day_since_exposure BETWEEN 0 AND 30
GROUP BY day_since_exposure
ORDER BY day_since_exposure;
```

## Common Mistakes
- Only measuring launch-day sends (novelty bias).
- Ignoring cannibalization of text messages.
- Forgetting sender-receiver pair (one-sided measurement).

## AI Use Cases
- Personalized sticker recommendations from embeddings.
- Stickiness forecasting (Bayesian survival).
- Conversation-depth uplift via graph embeddings.

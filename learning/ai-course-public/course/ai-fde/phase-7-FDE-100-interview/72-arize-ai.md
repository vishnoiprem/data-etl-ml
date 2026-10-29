# Arize AI — FDE (LLM Observability)

## Company Snapshot
- **HQ**: Berkeley, CA
- **Team Size**: ~20–40
- **Comp**: $160K–$220K; TC $260K–$400K
- **What they deploy**: LLM observability / eval FDEs
- **Travel**: 15–25%

## Interview Process
1. Recruiter
2. Coding (medium)
3. LLM eval platform design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### Observability case
**Q:** *"Customer wants production LLM observability."*
**A (winner):** *"Arize Phoenix + Arize AX for tracing, drift, eval. Instrument the LLM app with OpenTelemetry. Build custom evaluators (LLM-as-judge + human). Eval dashboard per app + per user cohort. Pilot: 1 app, 30 days. Alerting on regression."*
**Why it worked:** Right OTel + LLM-eval framing.

---

## ❌ REJECTION STORIES
### Observability
**Q:** *"Spans are noisy."*
**A (loser):** "Sample less."
**What they should have said:** *"Add a session_id + user_id to spans; aggregate per cohort. Disable unused spans. Add tail-based sampling. Investigate any sudden 50× spike — usually a chatty user or retry loop."*

---

## 📚 Reading List
1. Arize Phoenix docs
2. OpenTelemetry docs
3. *"Building evals"* — Hamel Husain / Shreya Shankar
4. levels.fyi Arize
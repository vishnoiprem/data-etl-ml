# Moveworks — FDE

## Company Snapshot
- **HQ**: Mountain View, CA
- **Team Size**: ~40–80
- **Comp**: $170K–$230K; TC $270K–$450K
- **What they deploy**: IT support AI agents for enterprise (Copilot for IT)
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (medium + Python)
3. IT agent design
4. Loop — coding, IT scenario, customer scenario

---

## ✅ SUCCESS STORIES

### IT agent case
**Q:** *"Customer wants to deflect 60% of IT tickets in 6 months."*
**A (winner):** *"Moveworks for IT Service Desk + a Custom Agent for their top 3 use cases (password reset, app access, laptop issues). Integrations: ServiceNow, Okta, AD, Workspace ONE. Reasoning Engine maps natural language → API calls. Ground truth: top 1,000 ticket transcripts. Eval: deflection rate, mean time to resolution, rep CSAT. Rollout: 1 BU for 4 weeks → 100% by month 6."*
**Why it worked:** Moveworks-native (Reasoning Engine, ServiceNow/Okta integrations), metrics-driven rollout.

---

## ❌ REJECTION STORIES
### IT scenario
**Q:** *"Agent gave wrong access to wrong user."*
**A (loser):** "We'll fix the bug."
**What they should have said:** *"Add identity verification step (MFA re-check), least-privilege defaults (read-only first), audit log + reversible action, escalation to human for high-risk ops (write to user ACLs). Policy-as-code for every tool."*

---

## 📚 Reading List
1. Moveworks blog + customer stories
2. ServiceNow IntegrationHub docs
3. r/ITServiceManagement
4. levels.fyi Moveworks

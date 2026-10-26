# Glean — FDE

## Company Snapshot
- **HQ**: Palo Alto, CA
- **Team Size**: ~50–100
- **Comp**: $170K–$230K; TC $280K–$500K
- **What they deploy**: Enterprise search AI + agent deployments (Glean Search, Assistant, Agents)
- **Travel**: 20–40%

## Interview Process
1. Recruiter
2. Coding (medium)
3. Enterprise search / agent design
4. Loop — coding, customer scenario

---

## ✅ SUCCESS STORIES

### Enterprise search case
**Q:** *"A customer wants Glean to index 50+ SaaS apps."*
**A (winner):** *"Glean's connector framework with 100+ native connectors + custom connector SDK. Identity resolution via SCIM + Okta. Permissions: Glean respects source ACLs (no over-permission). Reasoning layer (Work AI) for cross-app workflows. Eval: relevance on 100 hand-labeled queries + click-through. Pilot: 3 apps for 30 days, expand by 5 apps/week."*
**Why it worked:** Glean-native (connectors, ACL-respecting, Work AI), structured rollout.

---

## ❌ REJECTION STORIES
### Search case
**Q:** *"Customer complains results are off."*
**A (loser):** "Add more docs."
**What they should have said:** *"Is it freshness, permission mismatch, or relevance? Often it's permission (we indexed but the ACL filter is wrong). Run a per-source recall check + per-source freshness SLA."*

---

## 📚 Reading List
1. Glean docs + customer case studies
2. Enterprise search papers (ACL-respecting indexing)
3. r/EnterpriseSearch
4. levels.fyi Glean
# Northrop Grumman — Defense AI / Cleared FDE

## Company Snapshot
- **HQ**: Falls Church, VA
- **Team Size**: ~80–150
- **Comp**: $130K–$190K; TC $180K–$320K
- **What they deploy**: Defense AI; cleared FDE
- **Travel**: 15–25%

## Interview Process
1. Recruiter (security clearance check)
2. Coding (medium)
3. Defense / systems design
4. Loop — coding, scenario, security

---

## ✅ SUCCESS STORIES

### Defense scenario
**Q:** *"USAF wants to deploy NG AI on SIPRNet."*
**A (winner):** *"STIGs-hardened container, PKI-cert auth, hardened kernel. RMF package, ATO at Impact Level 5. Air-gapped deployment. 90-day ATO timeline with customer ISSM. Eval per acceptance test plan."*
**Why it worked:** Right DoD compliance arc.

---

## ❌ REJECTION STORIES
### Defense scenario
**Q:** *"Latency unacceptable."*
**A (loser):** "Tune."
**What they should have said:** *"Investigate network hops, batch up sensitive ops, edge-deploy critical ML. Often it's cross-domain (SIPRNet ↔ NIPRNet) hops; consolidate."*

---

## 📚 Reading List
1. NIST RMF / 800-53
2. DoD STIGs (DISA)
3. r/DefenseIndustry
4. levels.fyi Northrop
# Rebellion Defense — FDE (Defense AI)

## Company Snapshot
- **HQ**: Washington, DC
- **Team Size**: ~30–60
- **Comp**: $150K–$200K; TC $230K–$380K
- **What they deploy**: Defense AI / DoD deployments (Rebellion OS)
- **Travel**: heavy; on-site

## Interview Process
1. Recruiter (often ex-DoD)
2. Coding (medium)
3. Defense systems design
4. Loop — coding, defense scenario, customer scenario (military)

---

## ✅ SUCCESS STORIES

### Defense scenario
**Q:** *"A DoD customer wants our software deployed on NIPRNet."*
**A (winner):** *"NIPRNet deployment requires ATO (Authority to Operate) at the customer's Impact Level. We start with a security package: STIGs, SBOM, RMF controls. Air-gapped if classified. Pilot deployment in their dev enclave for 4 weeks; production ATO in 12 weeks. Coordinate with customer's ISSM for boundary protection. We'd staff 1 FDE + 1 cleared security engineer on-site."*
**Why it worked:** Knew DoD acronyms (NIPRNet, ATO, STIGs, SBOM, RMF, ISSM).

---

## ❌ REJECTION STORIES
### Defense scenario
**Q:** *"Customer says our AI is too slow for ops tempo."*
**A (loser):** "We'll optimize."
**What they should have said:** *"Profile. Common cause: cross-domain hops (NIPRNet → SIPRNet). Edge-deployed model (Jetson) or pre-computed batch outputs. Quantize the model. Use coarse-grained classifications."*

---

## 📚 Reading List
1. DoD RMF + NIST 800-53
2. STIGs (DISA)
3. Rebellion blog (if available)
4. r/DefenseIndustry
5. levels.fyi Rebellion
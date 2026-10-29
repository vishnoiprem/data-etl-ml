# Microsoft — Industry Solutions FDE

## Company Snapshot
- **HQ**: Redmond, WA
- **Team Size**: ~1,000+ FDEs across Industry Solutions (MACC-attached)
- **Comp**: Base $160K–$220K; TC $250K–$450K+
- **What they deploy**: Azure AI / Copilot / Dynamics deployments; MACC-attached
- **Travel**: 30–50% (often ~Mon-Thu on-site)

## Interview Process
1. Recruiter
2. Coding screen (LeetCode mid)
3. System design screen (Azure-flavored)
4. Loop (3-4 hours)
   - Coding 2
   - Azure architecture
   - Customer scenario with industry SME
   - Bar-raiser

---

## ✅ SUCCESS STORIES

### Azure architecture
**Q:** *"Design a Copilot deployment for a hospital on Azure, with strict HIPAA + HITRUST."*
**A (winner):**
- **Tenant**: dedicated, with Customer Lockbox.
- **Data**: stored in Azure Health Data Services; PHI tokens issued via Azure API for FHIR.
- **Copilot stack**: Azure OpenAI Service (PTU reserved), content filtering at ingress/egress, Private Endpoint only (no public egress).
- **Identity**: Entra ID with Conditional Access + Privileged Identity Management.
- **Audit**: Sentinel for SIEM; logs in immutable blob with WORM retention.
- **HITRUST**: pre-built control mapping with our HITRUST CSF accelerator; SOC2 + ISO 27001 baseline.
**Why it worked:** Used Microsoft-native terminology (PTU, Entra ID, Customer Lockbox, Sentinel, Health Data Services), mapped to actual certs, hit every compliance angle.

---

### Customer scenario
**Q:** *"Customer wants Copilot to read Outlook + Teams. Their legal team says no — too much PII. Your move?"*
**A (winner):** *"Microsoft Purview can scope by sensitivity label. We'd label the sensitive mail/Teams as 'Highly Confidential' and exclude those from Copilot ingestion. Plus Purview Insider Risk to detect over-share. The PII is the bug; Purview is the fix. I'd run a 2-week pilot measuring % of items excluded and quality on the remaining."*
**Why it worked:** Named the actual Microsoft SKU (Purview), reframed as a labeling problem, offered measurement.

---

### Coding
**Q:** *"Merge two sorted linked lists."*
**A (winner):** Iterative with a dummy head, O(n+m), explained the recursive variant, unit-tested both. Asked *"do you want it to be in-place or a new list?"* before coding.

---

## ❌ REJECTION STORIES

### Azure architecture
**Q:** *"Design a global SaaS on Azure."*
**A (loser):** Generic AWS-pattern answer with no Azure specifics.
**Why it failed:** Microsoft wants Azure, not generic cloud.
**What they should have said:** Azure Front Door, Cosmos DB multi-region writes, AKS cluster per region, Azure Monitor + App Insights, BCDR with paired-region failover.

---

### Customer scenario
**Q:** *"Customer wants their data to never leave Ireland."*
**A (loser):** *"We'll keep it in our data center."*
**Why it failed:** Microsoft doesn't have "data centers" in that sense — they have Azure regions.
**What they should have said:** *"Azure has Ireland region (North Europe). EU Data Boundary ensures no EU customer data leaves the EU for processing. We can pin resources to that region, use Customer Lockbox for support access, and Azure Confidential Computing for in-use encryption. Here are the regulatory mappings."*

---

## 📚 Reading List
1. Microsoft Learn — Azure Architecture Center
2. Azure Architecture Center FDE scenarios
3. *"Hitachi Solutions: Microsoft FDE"*
4. Microsoft Industry blogs (healthcare, financial, retail)
5. Microsoft Mechanics YouTube
6. levels.fyi Microsoft Industry Solutions FDE
7. r/AZURE + r/Microsoft threads
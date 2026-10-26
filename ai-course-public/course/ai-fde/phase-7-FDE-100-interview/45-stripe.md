# Stripe — Solutions / Deployment Engineer

## Company Snapshot
- **HQ**: South San Francisco, CA
- **Team Size**: ~50–100
- **Comp**: $200K–$260K base; TC $350K–$550K
- **What they deploy**: Payments AI / Issuing deployments to enterprise
- **Travel**: 15–30%

## Interview Process
1. Recruiter
2. Coding (medium-hard, Ruby/Python/Go)
3. Payment system design
4. Loop — coding, customer scenario

---

## ✅ SUCCESS STORIES

### Payment scenario
**Q:** *"Customer wants to integrate Stripe Issuing for a corporate-card launch in 30 days."*
**A (winner):** *"Issuing API: KYC/KYB via Stripe Identity, card creation, authorization webhooks, ledger reconciliation, dispute flow. Sandbox first, then test-mode in week 2. Production closed beta in week 3. SLA: 99.99% uptime. Compliance: PCI-DSS, AML. Eval: end-to-end authorization rate vs incumbent. Rollout: 100 cards in week 4, 10K by month 2."*
**Why it worked:** Stripe-native (Issuing, Identity, webhooks), phased.

---

## ❌ REJECTION STORIES
### Payment scenario
**Q:** *"Customer complains about webhook failures."*
**A (loser):** "Retry harder."
**What they should have said:** *"Idempotency keys, exponential backoff with jitter, dead-letter queue + alert on retries>5. Verify signed webhooks (stripe-signature). Add a replay tool. Monitor delivery rate."*

---

## 📚 Reading List
1. Stripe docs (Issuing, webhooks, Identity)
2. PCI-DSS primer
3. r/StripeDev
4. levels.fyi Stripe
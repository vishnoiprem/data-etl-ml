# Stripe — Forward Deployed Engineer (Payments Infrastructure / AI)

> Stripe's FDE / Solutions Engineer role is the **payments-infrastructure + AI-for-developers + financial-services** variant. Unlike pure model API companies, Stripe's FDE ships AI into **payments + fraud + financial compliance** — they care about **idempotency, ACID, regulatory compliance, and the developer-experience** as much as the model. The FDE signal: a candidate who can talk about **Stripe's API design philosophy + idempotency keys + AI agents for fraud detection + the financial-services compliance boundary** — is signaling they can own a payments-grade AI deployment.

---

## TL;DR (1 page)

**Stripe's Solutions Engineer / Forward Deployed Engineer role** sits between Sales Engineering and Product Engineering. The work: ship **Stripe's payment APIs + AI agents for fraud detection + Stripe Sigma + financial-services compliance** into a Stripe enterprise customer (fintech, marketplace, SaaS, e-commerce). The interview loop tests 4 things: (1) can you design a payment flow that handles **idempotency + ACID + circuit breaker** correctly? (2) can you reason about **fraud detection with ML + the false-positive vs false-negative tradeoff**? (3) can you handle the **financial-services stakeholder map** (risk, compliance, finance, security)? (4) can you own the handoff to the customer's payments team? The candidate who names the **idempotency key + the ACID transaction + the circuit breaker + the ML fraud model + the audit log** — is signaling they can own a payments-grade AI deployment.

---

## Why Stripe is the right target

The 4 reasons a Stripe FDE interview is different from a generic FDE loop:

1. **The payment API is the system.** Stripe's core product is the **payments API** — the candidate who can describe `POST /v1/charges` with an idempotency key, a customer ID, and an amount is signaling they understand the system.
2. **Idempotency is the operational boundary.** Network retries are common; the idempotency key ensures the customer is charged once. The candidate who names **idempotency key + at-least-once delivery + the dedup window** is signaling they operate payment systems.
3. **AI for fraud detection is the new wave.** Stripe Radar (the ML fraud model) is a billion-dollar product. The candidate who can talk about **feature engineering + model training + the false-positive vs false-negative tradeoff + the cost matrix** is signaling they ship ML in production.
4. **The financial-services compliance boundary.** PCI-DSS, SOC 2, regional regulations (PSD2 in EU, etc.). The candidate who names **PCI-DSS scope + the audit log + the data residency boundary** is signaling they operate financial services.

---

## The Stripe FDE loop (5-6 rounds)

The typical Stripe Solutions Engineer / FDE loop:

| Round | Format | Duration | Tests |
|---|---|---|---|
| 1. Recruiter | Phone (behavioral + resume) | 30 min | Communication, motivation, Stripe fit |
| 2. Coding (technical screen) | HackerRank / CoderPad | 60 min | Algorithms + Python + SQL |
| 3. **Payments System Design** (signature) | Live system design | 60 min | Payment flow + idempotency + ACID + circuit breaker |
| 4. **Customer Sim** | Live roleplay | 45 min | Stakeholder handling, scoping, compliance |
| 5. **Stripe API deep dive** | Live technical | 60 min | Stripe API + webhooks + Radar + Sigma |
| 6. HM / Behavioral | Final loop | 60 min | Stripe values + ownership + handoff story |

**Total time-spend:** 5-8 hours over 3-5 weeks. **Pass rate:** 4-6% (most candidates fail the Payments System Design round — the idempotency + ACID + circuit breaker is what Stripe cares about).

---

## The 5 things Stripe tests that other FDE loops don't

1. **Idempotency keys.** Every payment has an idempotency key. The candidate who can describe **the dedup window + the hash-based key + the safe-retry pattern** is signaling they operate payment systems.
2. **ACID transactions.** Money movement is ACID. The candidate who can describe **the database transaction + the rollback + the compensating transaction** is signaling they understand financial systems.
3. **Circuit breaker on the payment processor.** The payment processor (Stripe's internal system, or an external one) can fail. The candidate who names **circuit breaker + exponential backoff + the fallback (queue for retry)** is signaling they understand the operational boundary.
4. **Stripe Radar (ML fraud detection).** Stripe Radar is a ML model that scores every charge for fraud risk. The candidate who can describe **the feature engineering + the model training + the false-positive vs false-negative tradeoff + the cost matrix** is signaling they ship ML.
5. **The developer-experience lens.** Stripe's product is the **API**. The candidate who treats the API as the first-class artifact (clear endpoints, idempotency, webhooks, SDKs) — instead of "the payment system" — is signaling they fit the developer-first culture.

---

## The signature question

> "Design a payment flow for a marketplace (e.g., Airbnb, Uber). Customers pay the marketplace; the marketplace pays the sellers (minus a fee). 10K transactions/day, $100 average transaction, 30-second end-to-end latency. The system should never double-charge the customer, never lose money, and never leave a transaction in a 'pending' state. The marketplace wants to use Stripe Connect to handle the split-payment flow."

**The FDE answer shape:**

1. **Clarify (5 min):** What's the user? (Customers paying; sellers receiving). What's the scale? (10K transactions/day, $100 average). What's the constraint? (Never double-charge, never lose money, never pending). What's the failure mode? (Network timeout; chargeback; seller dispute). What's the timeline? (MVP in 4 weeks; full scale in 8 weeks).
2. **Decompose (10 min):** Entities (Payment, Payout, Customer, Seller, Refund, Dispute). Services (PaymentAPI, ConnectService, RefundService, WebhookReceiver). Flows (Customer pays → PaymentAPI creates PaymentIntent → ConnectService splits to seller → webhook to merchant → idempotency key prevents double-charge → refund flow returns money to customer).
3. **Design (15 min):** API (POST /payments with idempotency key, customer, amount; GET /payments/{id}; POST /refunds; webhook receiver for async events). Data model (payments + payouts + customers + sellers + refunds + disputes). Deployment (Stripe API + Postgres for the audit log + Redis for the idempotency key cache + a circuit breaker on the Stripe API).
4. **Tradeoffs (10 min):** (a) **Direct charges vs destination charges vs separate charges + transfers.** Direct charges are simpler; destination charges are better for marketplaces; separate charges + transfers give more control. Pick destination charges for most marketplaces. (b) **Synchronous confirmation vs webhook-driven.** Synchronous is simpler; webhook-driven is more reliable. Pick synchronous for MVP; pick webhook-driven for scale. (c) **Idempotency key in the request vs derived from the request.** Request key is flexible (client can choose). Derived key is consistent (server computes). Pick request key for client retries; pick derived for server-side deduplication.
5. **Closing line:** "For 10K transactions/day at $100 average with never-double-charge and 30-second end-to-end, I'd use Stripe Connect with destination charges, idempotency keys on every POST, a circuit breaker on the Stripe API, and a webhook receiver for async events. The cost is Stripe's per-transaction fee + $X/month for the audit log, under the $X ceiling. The failure mode is network timeout; the fallback is the idempotency key retry. The compliance boundary is PCI-DSS + the audit log + the data residency boundary."

---

## The Stripe prep plan (8 weeks)

**Weeks 1-2: Stripe API literacy**
- Read the Stripe API documentation end-to-end. The candidate who can recite the **PaymentIntent + Charge + Refund + Customer + Connect** lifecycles is signaling they understand the system.
- Build a small payment flow in the Stripe test mode. Run 10 transactions. Trigger 5 webhooks. **Measure the latency** from PaymentIntent creation to charge confirmation.
- Read the Stripe Connect documentation (Standard, Express, Custom accounts). Read the Stripe Radar documentation (the ML fraud model).

**Weeks 3-4: The payment flow + idempotency**
- Build a payment flow with idempotency keys. Test the safe-retry pattern (send the same request 5 times; verify the customer is charged once).
- Build a refund flow. Test the partial refund + the webhook for the refund confirmation.
- Build a webhook receiver that handles out-of-order events + duplicates.
- **The canonical artifact:** a `payment_guide.md` that walks a customer through the payment flow + idempotency + webhooks + the audit log.

**Weeks 5-6: The customer sim + decomposition drills**
- Practice 5 customer sims: (a) marketplace wants split-payment + KYC; (b) SaaS wants subscription billing + dunning; (c) fintech wants real-time payments + fraud detection; (d) e-commerce wants checkout optimization + Stripe Radar; (e) creator economy wants Connect Express + instant payouts.
- Practice 3 decomposition questions: design a payment flow, design a refund flow, design a fraud detection system.
- **The closing line:** "For X workload at Y scale with Z constraint, I'd use Stripe Connect + idempotency keys + circuit breaker + webhook receiver + the audit log. The compliance boundary is PCI-DSS + the audit log + the data residency boundary. The handoff is the payment_guide.md + the runbook + the on-call rotation."

**Weeks 7-8: Mock loop + STAR rehearsal**
- Mock the 5-round loop with an AI assistant. Time yourself at 60 min per round.
- Rehearse 5 STAR stories: (1) shipped a Stripe Connect integration for a marketplace; (2) handled a PCI-DSS conversation with a fintech; (3) debugged a webhook ordering bug; (4) wrote a payment guide for a customer; (5) handed off a payment integration to a customer's payments team.

---

## The 5 anti-patterns for Stripe

1. **Skipping the idempotency key.** The candidate who doesn't mention idempotency is signaling they don't operate payment systems.
2. **Skipping the ACID transaction.** The candidate who doesn't mention ACID + the rollback + the compensating transaction is signaling they don't understand financial systems.
3. **Skipping the circuit breaker.** The candidate who doesn't mention the circuit breaker on the Stripe API is signaling they don't understand the operational boundary.
4. **Skipping the audit log.** The candidate who doesn't mention the audit log + the data residency + the PCI-DSS scope is signaling they don't operate financial services.
5. **Skipping the handoff story.** The candidate who doesn't mention the **handoff artifact (payment_guide.md + runbook + the customer's payments team handoff)** is signaling they don't own the delivery.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "What if the customer retries the same payment 5 times?" | "The idempotency key deduplicates. The first request creates the PaymentIntent; the next 4 return the same response. The customer is charged once." |
| 2. "What if the webhook is lost?" | "The customer's system reconciles by polling the PaymentIntent. The webhook is the optimization; the polling is the safety net. The audit log records every state transition." |
| 3. "How do you handle a chargeback?" | "Stripe sends a dispute.created webhook. The customer's system updates the order. The customer can submit evidence via the Stripe API. The Radar model updates the seller's risk score." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../system-design/05-transactional.md` | The ACID + idempotency + circuit breaker pattern |
| `../system-design/03-async-jobs.md` | The webhook + retry + dead-letter queue pattern |
| `../decomposition/README.md` | The 4-step framework applied to a payment flow |

---

## The thesis

**Stripe's FDE role is the payments-infrastructure + AI-for-developers + financial-services variant.** The candidate who names **idempotency keys + ACID transactions + circuit breaker + Stripe Radar + the audit log + PCI-DSS** — is signaling they can own a payments-grade AI deployment.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The signature question — "design a payment flow for a marketplace with Stripe Connect" — is the worked example. Practice it out loud, time yourself at 60 minutes, and rehearse with an AI assistant.

**General prep gets you past the resume screen. Stripe prep gets you past the centerpiece round at Stripe, Square, Adyen, Plaid, and fintech AI deployments.**

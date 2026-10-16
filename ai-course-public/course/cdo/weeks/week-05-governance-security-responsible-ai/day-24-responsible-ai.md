# Lesson 24: Responsible AI

> **Week 5 · Day 24 · 90 min**
> **Deliverable:** The AI governance framework + the AI Act compliance posture.

## 🎯 Architect Level
Staff.

## 🧠 Concept

Responsible AI is the discipline of ensuring AI systems are **fair, transparent, accountable, safe, and privacy-preserving**. It is the license to operate AI in a regulated world. The CDO who treats it as an "ethics thing" loses; the CDO who treats it as a product (with regulators and customers as the users) wins.

The 5 principles (the OECD / EU / NIST framing):

| Principle | What it means | Implementation |
|---|---|---|
| **Fairness** | No discriminatory outcomes across protected groups | Bias testing on training + serving; disparate impact analysis |
| **Transparency** | The system is explainable; the user knows it's AI | Model cards; system cards; user disclosure |
| **Accountability** | A human owns the outcome; a process exists to challenge it | Model registry; named owner; appeal process |
| **Safety** | The system fails safely; doesn't cause harm | Guardrails; eval harness; red-team testing |
| **Privacy** | Personal data is protected; consent is respected | Data minimization; PII filtering; consent records |

The EU AI Act (in force from 2024, full effect 2026) classifies AI systems by risk:

| Risk class | Examples | Requirements |
|---|---|---|
| **Unacceptable** | Social scoring, biometric surveillance | Banned |
| **High** | Credit, employment, education, biometric ID | Conformity assessment, human oversight, transparency, accuracy, robustness |
| **Limited** | Chatbots, deepfakes | User disclosure |
| **Minimal** | Spam filters, games | None |

For a retailer, the high-risk systems are: credit decisioning (BNPL), employment (hiring), biometric ID (fraud detection with face/voice). Each needs:
- Risk classification documented
- Conformity assessment completed
- Human oversight mechanism
- Transparency disclosure
- Robustness + accuracy benchmarked

The single biggest mistake is to **deploy a high-risk system without a conformity assessment**. The penalty is up to 7% of global revenue. The CEO will notice.

The second biggest mistake is to **not have a model registry**. "Which models are in production? Who owns them? When were they last evaluated?" must be answerable in 60 seconds.

The third biggest mistake is to **skip red-team testing**. A model that hasn't been adversarially tested is a model that will fail on the first adversarial input.

## 🛠️ Build It

**Spec:** Build the AI governance framework for the retailer. Map each AI use case to its risk class. Name the controls per class.

**Acceptance:**
- 5 principles named
- AI use cases × risk class
- Controls per risk class
- Model registry fields
- Eval harness dimensions
- 1 paragraph on the AI Act posture

**Starter:** Use Day 14's 8 commercial AI patterns. Classify each.

**Solution (AI governance, abridged):**

| Use case | Risk class | Controls |
|---|---|---|
| Demand forecasting | Minimal | Standard monitoring |
| Customer 360 / NBO | Limited | Disclosure; opt-out |
| Dynamic pricing | Limited | Disclosure; price-cap |
| Credit decisioning (BNPL) | **High** | Conformity assessment; human oversight; bias testing; transparency |
| Churn / retention | Limited | Disclosure; opt-out |
| Document intelligence (RAG) | Limited | Guardrails; eval harness |
| AI customer support | Limited | Guardrails; human escalation |
| Biometric fraud detection | **High** | Conformity assessment; human oversight; transparency |
| Hiring / HR AI | **High** | Conformity assessment; human oversight; bias testing |

**Model registry fields:** model name, version, owner, training data version, eval metrics, deployment date, last review date, risk class, human oversight mechanism.

**Eval harness dimensions:** faithfulness, relevance, harmlessness, bias, accuracy, robustness, latency, cost.

**AI Act posture:** Risk classification for every model. Conformity assessment for high-risk. Human oversight documented. Transparency disclosure in user-facing flows. Quarterly review.

## 🏛️ Architect Notes

- **Trade-off:** Speed vs. compliance. Default: comply. The cost of non-compliance (7% of global revenue) dwarfs the cost of compliance.
- **Capacity / cost:** An AI governance program needs 2-4 dedicated people (registry, eval, policy, audit) for a 10-20 model portfolio.
- **When NOT to use:** Don't deploy a high-risk model without human oversight. "The model decides and the human reviews 10% of cases" is not human oversight.
- **Production checklist:**
  - [ ] 5 principles named
  - [ ] Use cases × risk class
  - [ ] Controls per risk class
  - [ ] Model registry fields
  - [ ] Eval harness dimensions
  - [ ] AI Act posture named

## 🌙 Reflect

- Which AI use case in your portfolio is the highest-risk? Pre-write the answer.
- Who would you put on the AI ethics committee? Why?
- Write 3 sentences you'll say out loud tomorrow.

---

**Next:** Day 25 — Executive crisis.
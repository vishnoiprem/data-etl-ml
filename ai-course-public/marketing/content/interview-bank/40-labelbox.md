# 40. Labelbox

- **Role:** ML Engineer / Forward Deployed Engineer (Labeling Platform, Catalog, Model Foundry)
- **Tech stack:** Python, PyTorch, TensorFlow, React/Typescript, GraphQL, Postgres, Kubernetes, Spark
- **Comp band:** $200K-$550K (L3-L5); senior crosses $700K+; RSUs + cash, 4-year vest
- **Cumulative pass rate:** ~3-4%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Mission alignment (training data), comp, fit | 1 week | ~55% advance |
| 2. **Technical phone screens (2)** | 1 coding + 1 ML/system | 1-2 weeks | ~45% advance |
| 3. **Onsite (4 rounds)** | Coding, system design, ML, behavior | 1-2 days | ~35% advance |
| 4. **Hiring committee (Tech Panel)** | Cross-org panel review | 1-2 weeks | ~60% advance |
| 5. **Offer** | Comp, team match | 1 week | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Why Labelbox?"
**Answer:** "Labelbox is the only platform that unifies data labeling, model evaluation, and active learning in a single system. The *Model Foundry* + *Catalog* + *Annotate* stack is what every AI team builds internally. I want to ship the data platform that 300+ AI companies build on top of."
**Tip:** Reference *Annotate*, *Catalog*, *Model Foundry*, *Model* (eval), *Boost* (active learning) — distinct products.

### Q1.2: "Tell me about a data platform or labeling tool you built"
**Answer:** STAR with focus on *labeling UI/UX*, *consensus algorithms*, and *model-assisted labeling*.
**Tip:** Show you understand the labeling workflow deeply — not just "I labeled some data."

## Stage 2: Technical phone screens (90 min)

### Q2.1: Coding: "Implement a debounce function"
**Answer:** Closure with timer/timeout. Edge cases: leading vs trailing edge, cancel, max wait.
```python
def debounce(fn, wait, leading=False):
    timer = None
    def debounced(*args, **kwargs):
        nonlocal timer
        def call():
            fn(*args, **kwargs)
        if leading and timer is None: call()
        if timer: timer.cancel()
        timer = Timer(wait, call); timer.start()
    return debounced
```
**Tip:** Async, debounce/throttle, and concurrent data-structure questions are common.

### Q2.2: ML/System: "Design Labelbox's model-assisted labeling pipeline"
**Answer:** (1) Customer uploads data; (2) Pre-label with their model; (3) Annotators review/correct via Labelbox UI; (4) Active learning — pick highest-uncertainty examples; (5) Iterative loop; (6) Consensus + adjudication; (7) Export to customer's training pipeline; (8) Model evaluation on the labeled data.
**Tip:** Reference *Model Foundry* (train models in-platform) and *Boost* (active learning).

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min, 2 questions)
- Q: LRU cache. O(1) get/put.
- Q: Merge K sorted lists. Min-heap.
- Optional 3rd: Async / Promise.all pattern in Python.

### Round 3.2: System design (60 min)
- Q: Design a multi-tenant labeling platform. Project/ontology management, role-based access, queue management, annotator assignment, throughput, and latency.
- Q: Design an active learning loop at scale. Uncertainty sampling, batch diversity, label budget optimization, model retraining, and integration with the labeling UI.

### Round 3.3: ML deep-dive (60 min)
- Q: How would you design an eval pipeline for a customer's object detection model? Ground truth import, prediction upload, IoU-based metrics, confusion matrix, slice analysis, and model comparison.
- Q: How would you build a consensus algorithm for subjective labels (e.g., sentiment)? Multi-rater agreement (Krippendorff's alpha), adjudication workflow, rater weighting, and training.

### Round 3.4: Behavioral (60 min)
- Q: Tell me about a time you worked with a customer to debug a labeling pipeline. Labelbox is customer-centric.
- Q: A time you shipped a feature in a fast iteration loop.
- Q: Disagreement with a PM on prioritization.

## Stage 4: Hiring committee
A panel of senior engineers + product reviews. They look for: (1) ML bar for the level, (2) customer empathy, (3) Labelbox values (Customer-First, Ownership, Curiosity, Speed, Inclusion), (4) data-platform depth. Vote is "Strong Hire / Hire / No Hire / Strong No Hire."

## Stage 5: Offer
Cash + RSUs. Labelbox is competitive for the size — below FAANG top-of-band. Negotiation is moderate. Team match after loop. SF HQ is main hub; some roles remote-US.

## Tips for the Labelbox loop
- Reference *Annotate*, *Catalog*, *Model Foundry*, *Boost* — distinct products.
- For ML rounds, emphasize *data quality* and *eval rigor*.
- For system design, multi-tenant labeling + active learning are bread-and-butter.
- Labelbox has a strong *customer success* culture — show you can partner with customers.
- For behavioral, "Customer First" stories score well.
- Labelbox is smaller than Scale — show you can wear multiple hats.
- Reference *Labelbox 2024* releases — they've shipped a lot recently.

## Real candidate report
> "Loop for ML Platform (Annotate + Foundry). 4 rounds in 1 day. The system design was a multi-tenant labeling platform with role-based access. The ML deep-dive was on active learning loops at scale. Behavioral was 'customer first' flavored. Offer at L4, ~$380K total, 4 weeks." — Blind, 2025-08

## Sources
- [Labelbox Careers](https://labelbox.com/careers/)
- [Levels.fyi Labelbox salaries](https://www.levels.fyi/companies/labelbox/salaries)
- [Labelbox blog](https://labelbox.com/blog/)
- [Labelbox docs](https://docs.labelbox.com/)
- [Glassdoor Labelbox interviews](https://www.glassdoor.com/Interview/Labelbox-Interview-Questions-E3268993.htm)

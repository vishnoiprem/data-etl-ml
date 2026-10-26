# Scale AI — Deployment Engineer

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~400+ Deployment Engineers
- **Comp**: Mid $170K–$200K base, Sr $215K–$255K, Staff $270K–$320K; TC mid $250K–$340K, staff $470K–$640K
- **What they deploy**: Donovan (Scale's defense/enterprise AI platform) + custom LLM/agent stacks to gov + commercial
- **Travel**: 25–50% (gov customers, often on-site)

## Interview Process
1. Recruiter screen
2. Coding phone screen
3. Technical phone (Python + Linux + data engineering flavor)
4. On-site / loop (3 sessions)
   - Coding
   - Data/infra design
   - Customer / defense scenario
5. Final with hiring manager

---

## ✅ SUCCESS STORIES

### Coding
**Q:** *"Parse a 10GB YAML file with embedded includes and produce a flat dict. Do it in < 2GB memory."*
**A (winner):** Used a streaming YAML loader with a recursive include resolver, kept state via dict-of-promises, walked the tree twice (first pass to discover includes, second pass to flatten), tested on a synthetic 10GB file before submitting. Finished at 1.4GB peak.
**Why it worked:** Showed they know real-world constraints (memory), used streaming idioms, validated with measurement.

---

### Data/infra design
**Q:** *"Scale wants to deploy a fine-tuned Llama-derivative into a SCIF-classified customer. Design the stack."*
**A (winner):**
- **Hardware**: a self-hosted cluster on Customer's air-gapped network (no AWS GovCloud — GovCloud is connected).
- **Model**: Llama 3 quantized (AWQ 4-bit) for an 8×A100 box.
- **Serving**: vLLM with chunked prefill + continuous batching.
- **Security**: every prompt + response logged to a write-once audit store; no telemetry leaves the perimeter; nightly golden-eval run in-custody.
- **CI/CD**: GitLab-on-prem with a signed-image registry.
**Why it worked:** Spoke Scale's actual world (defense customers, SCIFs, air-gapped). Right tool choices for the constraints.

---

### Customer scenario
**Q:** *"You're 6 weeks into a deployment. The customer wants to switch from classification to a generative agent. The contracts say 'scope change.' How do you handle it?"*
**A (winner):** *"This is a scope change, not a feature request. I'd (1) acknowledge the value, (2) re-estimate the cost + timeline (4-6 weeks additional), (3) put it in writing — a 1-page amendment with a clear SOW, (4) propose scope trade (defer X to phase 2). Then I'd reconfirm stakeholder alignment — usually one person wants this and the actual buyer doesn't. I'd protect the relationship above the deal."*
**Why it worked:** Triaged the situation (scope vs feature), priced it, offered a trade, protected relationship. Sounds like someone who's done this before.

---

## ❌ REJECTION STORIES

### Coding
**Q:** *"Build a streaming JSON diff tool."*
**A (loser):** Loaded entire file into memory, raised MemoryError on test 3.
**Why it failed:** Didn't stream, didn't test on a big file, didn't ask about input size.
**What they should have said:** *"I'll assume large files. Let me use ijson or a generator and process line-by-line. If you want true diff I'd run a Myers diff over key streams."*

---

### Defense scenario
**Q:** *"Customer says they're worried about data exfiltration via the model. Your response?"*
**A (loser):** *"We have a SOC 2, we're secure, we don't train on customer data."*
**Why it failed:** Generic marketing. Didn't address *how* exfiltration could happen (prompt injection, egress from inference, model stealing, etc.).
**What they should have said:** *"Here's the threat model: (1) prompt injection — we mitigate with system-prompt isolation + input classifiers, (2) model exfiltration — we run offline + offer a 'no endpoints out' deployment, (3) data leak via response — we strip PII on the way out. Show me your specific concern and we'll design around it."*

---

## 📚 Reading List
1. Scale AI engineering blog (Defense / Donovan posts)
2. vLLM repo + docs (the serving framework Scale uses)
3. AWQ quantization paper
4. SCIF accreditation 101 — DoD manuals
5. levels.fyi Scale AI debriefs
6. r/MachineLearning "Scale" threads

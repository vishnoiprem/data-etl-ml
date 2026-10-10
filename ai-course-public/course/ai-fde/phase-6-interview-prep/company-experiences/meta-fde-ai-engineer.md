# Meta — Forward Deployed / AI Solutions Engineer (Llama / GenAI)

> Meta's FDE / AI Solutions Engineer role is the **graph + Llama + on-device** variant. Unlike Anthropic / OpenAI / Sierra (pure API), Meta's FDE ships **open-weight Llama models** into customer infra — they care about PyTorch export, on-device serving, and the cost ceiling when running on a customer-owned GPU. The FDE signal: a candidate who can talk about **PyTorch + ONNX + ExecuTorch + Llama Serving** AND the **on-device latency budget** — is signaling they can own a Llama deployment.

---

## TL;DR (1 page)

**Meta's FDE / AI Solutions Engineer role** sits between Sales Engineering and Applied Research. The work: ship Llama (2 / 3 / 4) into a customer (banks, telcos, governments) running on **their** cloud or **their** device — not Meta's. The interview loop tests 4 things: (1) can you debug a customer's PyTorch checkpoint into an ONNX export? (2) can you reason about the **on-device** latency budget (4 GB RAM, 150 ms first token)? (3) can you handle the **safety** conversation when a customer wants to fine-tune away RLHF? (4) can you own the handoff to the customer's ML team? The candidate who names the **ExecuTorch + Llama Serving + an eval set as the regression check** is signaling they can land a Llama deployment at a bank.

---

## Why Meta is the right target

The 4 reasons a Meta FDE interview is different from a generic FDE loop:

1. **Open-weight means your customer's infra is your infra.** Llama is open, so the customer runs it on their hardware. The FDE has to ship a model that runs on a 4090, on a H100, on an iPhone, and on a Raspberry Pi. **Your infra boundary is the customer's hardware ceiling**, not Meta's API.
2. **PyTorch + ONNX + ExecuTorch + Llama Serving.** The Meta stack is opinionated. The candidate who names **ExecuTorch for on-device** + **Llama Serving for cloud** + **PyTorch + ONNX as the export path** is showing they know the deployment story.
3. **The safety conversation is political.** Customers ask "can we fine-tune away the safety guardrails?" The candidate who names **Llama Guard + the safety eval set + the "we don't ship models that we wouldn't ship to our own kids" framing** is showing they understand the responsible-AI posture.
4. **The AI company signal.** Meta AI ships Llama, the FDE ships Llama to customers. The candidate who treats Llama as a first-class engineering system (model card, eval set, deployment guide) — instead of "just an open-weight model" — is showing they can own an AI platform.

---

## The Meta FDE loop (5-6 rounds)

The typical Meta AI Solutions Engineer / FDE loop:

| Round | Format | Duration | Tests |
|---|---|---|---|
| 1. Recruiter | Phone (behavioral + resume) | 30 min | Communication, motivation, Meta fit |
| 2. Coding (technical screen) | HackerRank / CoderPad | 60 min | Algorithms + Python + PyTorch basics |
| 3. **Llama Deployment** (signature) | Live system design | 60 min | Model export, serving stack, on-device latency |
| 4. **Customer Sim** | Live roleplay | 45 min | Stakeholder handling, scoping, safety conversation |
| 5. **Decomposition** | Take-home or live | 60 min | The 4-step framework + decompose a deployment |
| 6. HM / Behavioral | Final loop | 60 min | Meta values + ownership + handoff story |

**Total time-spend:** 5-8 hours over 3-5 weeks. **Pass rate:** 4-6% (most candidates fail the Llama Deployment round — the open-weight + on-device + safety conversation is what Meta cares about).

---

## The 5 things Meta tests that other FDE loops don't

1. **PyTorch → ONNX → ExecuTorch export.** The candidate who can describe the export path (trace, optimize, quantize, validate accuracy) is showing they understand the deployment. The candidate who only knows "we serve via vLLM" is signaling they think API-first, not deployment-first.
2. **On-device latency budget.** Llama-3.2-1B on an iPhone 15 with 4 GB RAM: ~50 ms first token. Llama-3-70B on an H100: ~200 ms first token. The candidate who names the **first-token budget + per-token decode budget + memory ceiling** is showing they understand the on-device story.
3. **The safety eval set.** Llama Guard, Prompt Guard, Code Shield. The candidate who names **Llama Guard as a separate model + a safety eval set + the "we don't fine-tune away safety" stance** is signaling they understand the political/ethical boundary.
4. **Cross-platform serving.** Llama runs on Nvidia, AMD, Apple Silicon, CPU. The candidate who names **ROCm for AMD + MPS for Apple + CUDA for Nvidia + the quantization ladder (FP16, INT8, INT4)** is showing they can ship to a heterogeneous fleet.
5. **The Meta values + the AI Lab signal.** Meta moves fast ("ship fast and break things" carries through), but the AI Lab / GenAI org has a different rhythm (responsible AI, safety evals, model cards). The candidate who can talk about both — shipping fast AND shipping safely — is signaling they fit the org.

---

## The signature question

> "Walk me through how you'd ship Llama-3-8B to a bank that wants to run it on-premise for fraud detection. They have 2×H100 GPUs, 50 ms latency budget per request, and need SOC2 + PCI compliance."

**The FDE answer shape:**

1. **Clarify (5 min):** What's the workload? (fraud detection on transactions; < 50 ms P95). What's the deployment target? (2×H100 on-prem). What's the compliance boundary? (SOC2 + PCI — no data leaves the customer's network). What's the eval set? (precision + recall on the bank's fraud labels). What's the timeline? (PoC in 4 weeks; full deploy in 12 weeks).
2. **Decompose (10 min):** Entities (Transaction, Prediction, ModelVersion, EvalResult). Services (Exporter, Quantizer, Server, EvalRunner). Flows (PyTorch checkpoint → ONNX export → INT8 quantization → Llama Serving → eval against the bank's fraud labels).
3. **Design (15 min):** API (POST /predict returns score + explanation). Data model (transactions + predictions + model versions + eval runs). Deployment (Llama Serving on 2×H100 with INT8 quantization). Monitoring (Prometheus + JSON logger + eval-set-as-spec regression check).
4. **Tradeoffs (10 min):** (a) **Full vs INT8 quantization.** Full precision = best accuracy; INT8 = 2× throughput at < 1% accuracy loss. Pick INT8 for the latency budget. (b) **Llama Serving vs vLLM vs Triton.** Llama Serving is Meta-maintained and Llama-aware. vLLM has PagedAttention but is third-party. Triton is Nvidia-only. Pick Llama Serving for Meta-aligned deployments. (c) **On-prem vs Meta-hosted.** On-prem = SOC2/PCI compliance but customer owns ops. Pick on-prem for compliance-bound workloads.
5. **Closing line:** "For Llama-3-8B on 2×H100 with 50 ms P95 and SOC2 compliance, I'd use PyTorch → ONNX → INT8 quantization, Llama Serving with PagedAttention, and the bank's fraud labels as the eval set. The eval set is the spec. The cost ceiling is the customer's hardware budget, not Meta's API cost. The failure mode is data drift; the mitigation is the eval-set-as-spec regression check + model retraining on a quarterly cadence. The safety conversation is Llama Guard as a separate model + the bank's compliance team signs off on the eval set."

---

## The Meta prep plan (8 weeks)

**Weeks 1-2: Llama literacy**
- Read the Llama 3 paper + the model card. The candidate who can recite the model card sections (training data, eval results, intended use, limitations, safety considerations) is signaling they treat the model as a first-class artifact.
- Run Llama-3.2-1B locally via ollama. Run Llama-3-8B via vLLM on a single H100 or A100. **Get the first-token latency on your hardware.** The candidate who has measured the latency on their own laptop is signaling they ship AI.
- Read the Llama Guard paper + the Llama Stack documentation.

**Weeks 3-4: The deployment stack**
- Convert a Llama-3-8B checkpoint from PyTorch to ONNX. Quantize to INT8 with `bitsandbytes` or `quanto`. Validate accuracy against the original FP16 model on a 100-row eval set.
- Deploy via Llama Serving on a single H100 (or A100) with PagedAttention. Measure first-token latency + per-token decode latency under load.
- Deploy via ExecuTorch on an iPhone 15 or a Raspberry Pi 5. Measure latency under a 4 GB RAM budget.
- **The canonical artifact:** a `deployment_guide.md` that walks a customer through the export + serving + monitoring steps. The artifact the FDE ships to the bank.

**Weeks 5-6: The customer sim + decomposition drills**
- Practice 5 customer sims: (a) bank wants to fine-tune away safety; (b) telco wants to run Llama-3-70B on 4×A100 not 8; (c) government wants the model behind an airgap; (d) startup wants Llama-3-405B on 8×H100 but only has budget for 4; (e) healthcare needs HIPAA + Llama Guard + an audit log.
- Practice 3 decomposition questions: ship Llama to a customer, debug a customer's deployment, scale Llama to 10K QPS.
- **The closing line:** "For X workload at Y scale with Z constraint, I'd use Llama-3-NB, exported via PyTorch → ONNX → INT8, served via Llama Serving on customer hardware, with the eval set as the regression check. The safety posture is Llama Guard + the customer's compliance signoff. The handoff is the deployment_guide.md + the runbook + the on-call rotation."

**Weeks 7-8: Mock loop + STAR rehearsal**
- Mock the 5-round loop with an AI assistant. Time yourself at 60 min per round.
- Rehearse 5 STAR stories: (1) shipped an open-weight model to a customer on their hardware; (2) handled a safety conversation with a customer; (3) wrote a model card for an open-weight release; (4) debugged a customer's PyTorch → ONNX export; (5) handed off a Llama deployment to a customer's ML team.

---

## The 5 anti-patterns for Meta

1. **Treating Llama as "just an open-weight model."** Meta treats Llama as a first-class engineering system (model card, eval set, safety guardrails). The candidate who treats it as "the alternative to GPT" is signaling they don't get the platform.
2. **Skipping the on-device latency budget.** The candidate who doesn't mention **first-token + per-token + memory ceiling** is signaling they think API-first, not deployment-first.
3. **Skipping the safety conversation.** The candidate who doesn't mention **Llama Guard + the safety eval set + the "we don't fine-tune away safety" stance** is signaling they don't understand the responsible-AI posture.
4. **Skipping the cross-platform story.** Meta serves Llama on Nvidia, AMD, Apple, CPU. The candidate who only knows CUDA is signaling they can't ship to heterogeneous fleets.
5. **Skipping the handoff story.** Meta's FDE hands off to the customer's ML team. The candidate who doesn't mention the **handoff artifact (deployment_guide.md + runbook + on-call rotation)** is signaling they don't own the delivery.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you handle a customer wanting to fine-tune away the safety guardrails?" | "We don't ship a model that we wouldn't ship to our own kids. We fine-tune for the customer's domain but we keep the safety eval set as a separate hold-out. If the fine-tuned model fails the safety eval, we don't ship it." |
| 2. "What if the customer's hardware is over-provisioned (8×H100 but they only need 2)?" | "Right-size. Quantize to INT4. Use speculative decoding with a 1B draft model. The cost ceiling is the customer's hardware budget, so saving GPUs saves them money." |
| 3. "How do you handle data drift in production?" | "Eval-set-as-spec regression check on a weekly cadence. If eval metrics drop > 5%, trigger a model retraining on the latest 30 days of labeled data. The customer signs off on the new model before promotion." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../system-design/09-agentic-ai.md` | The Llama-as-tool-used-by-an-agent pattern |
| `../system-design/04-distributed-storage.md` | The model-versioning + eval-run persistence |
| `../decomposition/README.md` | The 4-step framework applied to a Llama deployment |

---

## The thesis

**Meta's FDE role is the open-weight + on-device + safety variant.** The candidate who names **ExecuTorch + Llama Serving + the on-device latency budget + Llama Guard + the deployment_guide.md handoff** — is signaling they can own a Llama deployment at a bank, a telco, or a government.

**The 4-step framework (clarify → decompose → design → tradeoffs) is the muscle memory.** The signature question — "ship Llama to a bank on 2×H100 with 50 ms latency and SOC2 compliance" — is the worked example. Practice it out loud, time yourself at 60 minutes, and rehearse with an AI assistant.

**General prep gets you past the resume screen. Meta prep gets you past the centerpiece round at Meta GenAI, Meta AI Labs, and Llama enterprise deployments.**

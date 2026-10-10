# GenAI Sub-Lesson 3 — Production Deployment (the canonical FDE GenAI primer)

> **Production deployment is the canonical FDE GenAI primer.** Every FDE GenAI system at AI companies (Anthropic, OpenAI, Sierra, LangChain, Meta, Google, Microsoft) must be **deployed, monitored, and operated**. The FDE signal: a candidate who can explain **model serving + streaming + cost ceiling + circuit breaker + observability + the eval set as the regression check** — is signaling they can operate a GenAI system at scale.

---

## Why production deployment is the FDE signal

The 4 things the interviewer is testing:

1. **Can you explain model serving?** vLLM, TGI, Triton, Llama Serving, OpenAI API, Anthropic API. The candidate who names **vLLM (PagedAttention) + TGI + Triton** is signaling they know the open-source stack.
2. **Can you explain streaming?** SSE, WebSocket, server-sent events. The candidate who names **SSE for hosted APIs + WebSocket for bidirectional** is signaling they understand the latency budget.
3. **Can you name the operational patterns?** Circuit breaker, rate limiter, cost ceiling, fallback model, eval-set-as-spec regression check. The candidate who names **all 5** is signaling they operate AI systems.
4. **Can you name the observability stack?** Prometheus, Grafana, OpenTelemetry, Langfuse, LangSmith, Datadog. The candidate who names **Prometheus + Grafana + OpenTelemetry + LLM-specific observability (Langfuse, LangSmith)** is signaling they ship AI.

**The FDE pattern:** name the serving stack + name the streaming protocol + name the operational patterns + name the observability stack. The depth of the answer matches the depth of the FDE role.

---

## The 4 sections of the canonical production-deployment answer

### Section 1: Model serving (60 seconds)

**The 3 ways to serve a model:**

1. **Hosted API (OpenAI, Anthropic, Google, Cohere).** Easiest. No ops. Variable cost per token. The default for MVPs and small-scale deployments.
2. **Hyperscaler-hosted (Bedrock, Vertex AI, Azure OpenAI).** Frontier model quality with hyperscaler compliance envelope (IAM, VPC, audit log). For enterprise customers with compliance needs.
3. **Self-hosted (vLLM, TGI, Triton, Llama Serving).** Open weights in the customer's VPC. Full control. Quality gap (90-95% of frontier). Ops burden.

**The 4 open-source serving stacks:**

- **vLLM.** PagedAttention (virtual memory for KV cache). 2-3× higher throughput than naive serving. The de facto standard for self-hosted LLMs.
- **TGI (Text Generation Inference).** HuggingFace's serving stack. Multi-GPU, quantization, streaming. Good for HuggingFace ecosystem.
- **Triton Inference Server.** Nvidia's serving stack. Multi-framework, multi-model, dynamic batching. Best for GPU-heavy deployments.
- **Llama Serving.** Meta-maintained, Llama-aware. The default for Meta-aligned deployments.

**The 2 things to add for depth:**

1. **Quantization.** INT8, INT4, FP8. 2-4× throughput improvement with < 1% accuracy loss. The cost model depends on the quantization.
2. **Speculative decoding.** Small draft model proposes tokens; large model verifies in parallel. 2-3× faster generation with no quality loss.

---

### Section 2: Streaming (60 seconds)

**The 3 streaming protocols:**

1. **SSE (Server-Sent Events).** Server-to-client only. Used by OpenAI, Anthropic, Google. Simple, well-supported, works through proxies.
2. **WebSocket.** Bidirectional. Used for chat apps, real-time collaboration, agent loops. More complex; better for bidirectional.
3. **Long polling.** Legacy. Server holds the connection until data is ready. Replaced by SSE for most LLM use cases.

**The 3 latency numbers that matter:**

1. **Time to first token (TTFT).** ~200-500ms for hosted; ~100-200ms for self-hosted. The user sees this as the "loading" time.
2. **Per-token decode latency.** ~10-30ms per token for hosted; ~20-50ms for self-hosted. The user sees this as the "typing" speed.
3. **Total latency.** TTFT + (tokens × per-token latency). For a 200-token response: TTFT 300ms + 200 × 20ms = 4.3 seconds.

**The pattern:** streaming is non-negotiable. Users will not wait 5 seconds for a complete response. SSE for hosted APIs; WebSocket for bidirectional. The latency budget is enforced by the timeout in the client; the server should be tuned to meet it.

---

### Section 3: Operational patterns (90 seconds)

**The 5 patterns every FDE should know:**

1. **Circuit breaker.** If the LLM API fails N times in a row, open the circuit. Return a fallback (cached response, "I'm having trouble, please try again"). Reset after cooldown. **The library:** `pybreaker`, `resilience4j`, `gobreaker`.
2. **Rate limiter.** Token bucket or sliding window. Per-user, per-endpoint, per-API-key. The candidate who names **token bucket + per-user-per-minute** is signaling they understand the rate-limit problem.
3. **Cost ceiling.** Track per-token cost. If the daily cost exceeds the ceiling, fail closed (return a fallback) or switch to a cheaper model. **The pattern:** the cost ceiling is operational, not contractual.
4. **Fallback model.** If the primary model is down or over-budget, fall back to a cheaper model (e.g., GPT-4o → GPT-4o-mini) or a different provider. **The pattern:** the fallback is configured, not improvised.
5. **Eval-set-as-spec regression check.** Run the eval set on every deploy. If any metric drops > 5%, block the deploy. **The pattern:** the eval set is the contract.

**The 3 things to add for depth:**

1. **Tiered fallback.** Primary model → secondary model → cached response → static response. Each tier is cheaper + more reliable.
2. **Idempotency key.** For transactional LLM calls, attach an idempotency key so retries don't double-charge.
3. **PII redaction.** Strip PII from prompts before sending to the LLM. The PacificFreight in-process redaction is the canonical example.

---

### Section 4: Observability (60 seconds)

**The 4 layers of observability:**

1. **Metrics (Prometheus + Grafana).** Request rate, latency, error rate, token usage, cost. The "four golden signals" + the LLM-specific ones.
2. **Logs (structured JSON).** Every request logged with `request_id`, `user_id`, `prompt_tokens`, `completion_tokens`, `cost_usd`, `latency_ms`, `model_version`. Searchable in CloudWatch, Datadog, or Loki.
3. **Traces (OpenTelemetry).** End-to-end trace from the API gateway through the retriever, the LLM, and the response. The candidate who names **OpenTelemetry + distributed tracing** is signaling they ship AI.
4. **LLM-specific (Langfuse, LangSmith, Helicone).** Prompt + completion logging, eval runs, user feedback. The LLM observability layer on top of the generic infra.

**The 3 things to add for depth:**

1. **Cost attribution.** Tag every request with a cost center (customer, project, feature). The dashboard breaks down the bill.
2. **Drift monitoring.** Compare the embedding distribution of the latest queries to the baseline. If the KL divergence exceeds a threshold, alert.
3. **Eval dashboard.** The eval set runs on a schedule; the results are visualized. The candidate who names **the eval dashboard** is signaling they ship a RAG system.

---

## The 5 most common production-deployment questions

| Question | The FDE answer (60 sec) |
|---|---|
| 1. "How do you serve a 70B model on 1 GPU?" | "Quantization (INT4, INT8). PagedAttention (vLLM). Speculative decoding. Model parallelism (tensor parallel across 2-4 GPUs). You can serve a 70B model on 1×H100 with INT4 at 30 tokens/sec." |
| 2. "How do you handle a model going down?" | "Circuit breaker. Tiered fallback (primary → secondary → cached). The fallback is configured, not improvised. The circuit breaker resets after cooldown." |
| 3. "How do you stay under the cost ceiling?" | "Track per-token cost. If the daily cost exceeds the ceiling, fail closed (return a fallback) or switch to a cheaper model. The cost ceiling is operational, not contractual." |
| 4. "How do you monitor a RAG system?" | "RAGAS metrics on a schedule. Drift monitoring on the embedding distribution. Latency + cost + error rate. Eval dashboard with slice-level reporting. The eval set is the contract." |
| 5. "How do you handle PII in the prompt?" | "In-process redaction (regex + NER) before sending to the LLM. Audit log of every redaction. The redaction layer is deterministic, not probabilistic." |

---

## The 5 anti-patterns for production deployment

1. **Skipping the circuit breaker.** The candidate who doesn't name the circuit breaker is signaling they don't operate AI systems.
2. **Skipping the cost ceiling.** The candidate who doesn't mention the cost ceiling + tiered fallback is signaling they don't think about the operational boundary.
3. **Skipping the streaming protocol.** The candidate who doesn't name **SSE + TTFT + per-token latency** is signaling they don't think about the user experience.
4. **Skipping the eval set as the spec.** The candidate who doesn't name the eval-set-as-spec regression check is signaling they don't ship AI.
5. **Skipping the LLM observability.** The candidate who only knows **Prometheus + Grafana** (generic) but not **Langfuse / LangSmith / Helicone** (LLM-specific) is signaling they don't ship RAG systems.

---

## The 3 most common follow-up questions

| Question | The FDE answer |
|---|---|
| 1. "How do you scale to 10K QPS?" | "Horizontal scaling behind a load balancer. KV cache reuse for repeated prompts. Speculative decoding. The bottleneck is GPU memory bandwidth; the fix is more GPUs + PagedAttention." |
| 2. "How do you handle a model upgrade (GPT-4o → GPT-5)?" | "Version pinning. A/B test on a small percentage of traffic. The eval set is the regression check. If the new model fails the eval, rollback. The eval set is the contract." |
| 3. "How do you handle PII in the logs?" | "Don't log the prompt; log the metadata. If you must log the prompt, redact PII first. The audit log records who accessed what, not the content." |

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../system-design/09-agentic-ai.md` | The agent architecture with production deployment |
| `../company-experiences/meta-fde-ai-engineer.md` | The on-device + cloud serving story |
| `../company-experiences/aws-fde-customer-simulation.md` | The Well-Architected Framework's operational excellence pillar |

---

## The thesis

**Production deployment is the canonical FDE GenAI primer.** The candidate who names **vLLM (PagedAttention) + SSE streaming + circuit breaker + cost ceiling + tiered fallback + Prometheus + Langfuse + the eval set as the spec** — is signaling they can operate a GenAI system at scale.

**The 4-section answer (serving, streaming, operational patterns, observability) is the muscle memory.** The 5 questions are the practice bank. The 5 anti-patterns are the disqualifiers.

**General prep gets you past the resume screen. Production deployment prep gets you past the GenAI depth round at Anthropic, OpenAI, Sierra AI, LangChain, Meta, Google, and Microsoft.**

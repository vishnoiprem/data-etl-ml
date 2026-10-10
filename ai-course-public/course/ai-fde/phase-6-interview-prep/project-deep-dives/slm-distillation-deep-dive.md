# The SLM Distillation Deep Dive (the 45-minute script, alt #2)

> **This is the alt-#2 deep-dive script.** Use it when the company wants an ML or cost-optimization angle instead of a service-architecture angle. The signal: a candidate who can deliver this script without notes, in 45 minutes, with a working Qwen-1.5B + LoRA serving on their laptop, is showing they can train and serve a production-grade SLM.

---

## Slide 1: Title (1 min)

> "Today I'm going to walk you through the SLM distillation I did for PacificFreight in Phase 4 P3. I took the Phase 2 drafter (GPT-4o-mini, $0.50/week) and distilled it into a fine-tuned Qwen-2.5-1.5B with a LoRA adapter. The result: 91% of GPT-4o-mini's quality at 0.5% of its cost. The model is served on Mei's laptop via ollama; the bill is $0.00/month. The customer can take the model card to their CFO as a proof-of-concept that the LLM line item is a one-time training cost, not a recurring API bill."

**Cue:** 1 minute. Don't go over.

---

## Slide 2: The customer (2 min)

> "Same PacificFreight team — Mei (CS), Sarah (ops), Daniel (IT). The Phase 2 drafter was running on GPT-4o-mini at $0.50/week. Daniel had asked 'can we get the bill lower?' The constraint: stay under 91% of GPT-4o-mini's quality on the eval set (the 30-row golden set that the Phase 2 eval established). The cost ceiling: $0.00/month LLM API. The deliverable: a self-hosted SLM with a model card + an eval-set-as-spec regression check."

**The signal:** same 3 stakeholders, new cost constraint. The deliverable is the model card.

---

## Slide 3: The problem (3 min)

> "GPT-4o-mini is $0.15/1M input tokens, $0.60/1M output tokens. At 150 emails/day, with ~500 input tokens + ~200 output tokens per email, the bill is $0.50/week. At 10× growth (1500 emails/day), the bill is $5/week = $20/month. The CFO's threshold: $5/month LLM. We're at $2.17/month now; the projected $20/month at growth is over the threshold. We have 3 options: (1) rate-limit aggressively (Mei doesn't want this; she wants all emails drafted). (2) raise the ceiling (CFO said no). (3) distill to an SLM. We chose (3)."

**The signal:** the cost math, the 3 options, the choice. A senior FDE names the trade-off.

---

## Slide 4: The constraint (1 min)

> "The SLM must (1) achieve ≥ 91% of GPT-4o-mini's quality on the Phase 2 eval set (faithfulness, ansrel, context_precision, context_recall). (2) Run on Mei's laptop (M-series Mac, 16GB RAM) or Daniel's VM (1×H100, 80GB). (3) Serve at < 500ms P95 first-token latency. (4) Be fine-tunable on the customer's data (LoRA, not full fine-tune). (5) Have a model card that meets the Meta/HF standard: training data, eval results, intended use, limitations, safety considerations."

**The signal:** the 5 constraints. A senior FDE names the boundary.

---

## Slide 5: The architecture (5 min, with diagram)

```
[Phase 2-3 usage.jsonl: 1000 (prompt, response) pairs]
      ↓
[dataset.py: 70/15/15 train/eval/hold-out split, filter thumbs-up only]
      ↓
[train.py: LoRA fine-tune of Qwen-2.5-1.5B-Instruct]
      ↓
[adapter saved to slm/adapters/pf-drafter-lora (50MB)]
      ↓
[serve.py: ollama create pf-drafter -f slm/Modelfile]
      ↓
[eval.py: run the Phase 2 eval set against the SLM; report 4 metrics]
      ↓
[model_card.md: the artifact that survives the FDE's exit]
```

**The 5 design choices:**

1. **Qwen-2.5-1.5B-Instruct** as the base model. Small enough to run on a laptop; large enough to capture the drafter's style; license allows commercial use.
2. **LoRA (rank 16, alpha 32, target q_proj + v_proj)** instead of full fine-tune. 50MB adapter; 30-min training on Mac M-series; preserves the base model's general capability.
3. **Train on thumbs-up only.** Filter out thumbs-down drafts. The eval set is the high-quality signal.
4. **70/15/15 split.** 700 train, 150 eval, 150 hold-out. The hold-out is the regression check; the eval is the iteration tool.
5. **ollama serving.** The `Modelfile` references the base model + the LoRA adapter. ollama handles the runtime, the quantization (INT4 by default), and the API.

---

## Slide 6: The dataset prep (3 min)

```python
# slm/dataset.py
def build_dataset(usage_jsonl: str) -> list[dict]:
    pairs = []
    for line in open(usage_jsonl):
        row = json.loads(line)
        if row.get("thumbs") == "up":  # filter thumbs-up only
            pairs.append({
                "prompt": format_prompt(row["email"], row["retrieved_context"]),
                "response": row["final_draft"],  # Mei's edits, not the raw LLM output
            })
    return pairs
```

**The 5 dataset decisions:**

1. **Filter thumbs-up only.** Thumbs-down drafts are bad signal; the model would learn to mimic failures.
2. **Use Mei's final draft, not the raw LLM output.** Mei edits 18% of drafts. Her edits are the high-quality signal.
3. **70/15/15 split.** 700 train, 150 eval (the iteration tool), 150 hold-out (the regression check).
4. **No customer PII.** Strip emails + names + addresses before training. The model card documents this.
5. **Document the dataset.** The model card has a "Training Data Summary" section: 1000 drafts, 70% thumbs-up, 18% Mei-edited, dates 2026-01-01 to 2026-09-30.

**The signal:** the dataset is the contract. The candidate who names the 5 decisions is signaling they understand the ML lifecycle.

---

## Slide 7: The training (3 min)

```python
# slm/train.py
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

base = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",
    load_in_4bit=True,  # 4-bit quantization for memory
)
lora_cfg = LoraConfig(
    r=16, lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
)
model = get_peft_model(base, lora_cfg)
trainer = SFTTrainer(model=model, train_dataset=pf_dataset, ...)
trainer.train()
trainer.save_adapter("slm/adapters/pf-drafter-lora")
```

**The 3 training decisions:**

1. **4-bit quantization** (bitsandbytes) to fit the 1.5B model + activations in 16GB RAM.
2. **LoRA rank 16, alpha 32** — small enough to train on a laptop in 30 min; large enough to capture the drafter's style.
3. **Target q_proj + v_proj** — the canonical LoRA targets; alternative is q_proj + k_proj + v_proj + o_proj (more expressive, more memory).

**The signal:** the training is reproducible. 30 min on Mac M-series, 50MB adapter, full hyperparameters in the model card.

---

## Slide 8: The serving (3 min)

```bash
# slm/Modelfile
FROM qwen2.5:1.5b
ADAPTER /path/to/slm/adapters/pf-drafter-lora
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER stop "<|im_end|>"

# Serve
ollama create pf-drafter -f slm/Modelfile
ollama serve
```

```python
# slm/serve.py
import requests
def draft_slm(email: str, context: str) -> str:
    prompt = format_prompt(email, context)
    r = requests.post("http://localhost:11434/api/generate", json={
        "model": "pf-drafter",
        "prompt": prompt,
        "stream": False,
    })
    return r.json()["response"]
```

**The signal:** the serving is one command. The drafter's API contract doesn't change. Mei's CS tool keeps working.

---

## Slide 9: The eval (3 min)

```python
# slm/eval.py
from phase_2_core_build.eval import run_eval
metrics = run_eval(
    draft_fn=draft_slm,  # the SLM
    eval_set="shared/eval_set.jsonl",  # the Phase 2 eval set
)
print(metrics)
# {"faithfulness": 0.84, "ansrel": 0.79, "context_precision": 0.87, "context_recall": 0.81}
# vs GPT-4o-mini baseline: {"faithfulness": 0.91, "ansrel": 0.88, "context_precision": 0.93, "context_recall": 0.89}
# Quality ratio: 0.92, 0.90, 0.94, 0.91 → average 0.92 → PASS (≥ 0.91 threshold)
```

**The signal:** the eval set is the spec. The SLM passes the threshold. The cost is $0.00/month.

---

## Slide 10: The numbers (3 min)

> "The numbers from the 4-week pilot: (1) Quality: 92% of GPT-4o-mini (vs 91% threshold). (2) Cost: $0.00/month LLM API (vs $2.17/month). (3) Latency: 280ms P95 first-token on Mac M-series (vs 200ms for GPT-4o-mini; +40% but under the 500ms budget). (4) Throughput: 30 drafts/min on Mac M-series (vs 1500/min for GPT-4o-mini; but Mei only needs 10/min peak). (5) Model size: 50MB adapter (vs 1.5GB for the full Qwen model). The CFO's reaction: 'this is a one-time training cost, not a recurring line item. Approved.'"

**The signal:** the numbers are concrete. 92% quality, $0.00/month, 280ms P95, 50MB adapter.

---

## Slide 11: The model card (3 min)

```markdown
# Model Card: PacificFreight Drafter (Qwen-2.5-1.5B + LoRA)

## Training Data Summary
- 1000 (prompt, response) pairs from usage.jsonl (2026-01-01 to 2026-09-30)
- 70% thumbs-up filtered
- 18% Mei-edited (Mei's edits are the high-quality signal)
- PII stripped (emails, names, addresses)

## Eval Results
| Metric | GPT-4o-mini | This model | Ratio |
|---|---|---|---|
| Faithfulness | 0.91 | 0.84 | 0.92 |
| Answer relevance | 0.88 | 0.79 | 0.90 |
| Context precision | 0.93 | 0.87 | 0.94 |
| Context recall | 0.89 | 0.81 | 0.91 |
| **Average** | **0.90** | **0.83** | **0.92** |

## Intended Use
- Customer service email drafting for PacificFreight (12-person cross-border logistics SMB)
- English + Vietnamese (Vietnamese coverage is 78% of GPT-4o-mini's)

## Limitations
- Trained on PacificFreight-specific data; not generalizable to other logistics companies
- Vietnamese coverage is lower than English; recommend human review for Vietnamese-only customers
- 4-bit quantization reduces accuracy by ~1% vs FP16

## Safety Considerations
- No fine-tuning away the safety guardrails; the base model's safety behavior is preserved
- The eval set includes 5 adversarial queries (jailbreak attempts) that the model correctly refuses
- The customer is responsible for the safety eval; this model card documents the intended use
```

**The signal:** the model card is the artifact. The candidate who can write this model card is signaling they treat the model as a first-class engineering system.

---

## Slide 12: The handoff (3 min)

> "The handoff to Daniel + Mei was 4 weeks. The artifacts: (1) the LoRA adapter (`slm/adapters/pf-drafter-lora`, 50MB). (2) the serving setup (`slm/Modelfile` + `ollama` commands). (3) the eval pipeline (`slm/eval.py` runs the Phase 2 eval set; the threshold is 91%; the SLM passes at 92%). (4) the model card (this slide, exported to `slm/model_card.md`). (5) the runbook with the 5 most common failure modes (adapter corrupted, ollama crashed, eval regression, Mac M-series memory pressure, Vietnamese accuracy drop). The 5-question 'FDE has left' test: 5/5 passed. Daniel can re-train the adapter when usage.jsonl grows past 5K rows."

**The signal:** the handoff is concrete. 5 artifacts, 5/5 questions passed, the team can re-train.

---

## The 5 follow-up Q&A

**Q1: "Why Qwen-2.5-1.5B and not Llama-3.2-1B or Phi-3.5-mini?"**

> "Qwen-2.5-1.5B has the best eval results on the Phase 2 eval set (92% of GPT-4o-mini vs 89% for Llama-3.2-1B vs 87% for Phi-3.5-mini). The license is Apache 2.0 (commercial use OK). The tokenizer is multilingual (English + Vietnamese coverage). I tested all 3 on a 100-row subset before committing to Qwen."

**Q2: "What if the eval set is too small (150 rows)?"**

> "The Phase 2 eval set is 30 rows; the SLM eval set is 150 rows (the train/eval/hold-out split). The hold-out is the regression check; it's never seen during training. The candidate who says '150 rows is too small' is right — for a customer-facing model, I'd want 500+ rows. The Phase 5 lift is to grow the eval set to 500 rows as usage.jsonl grows past 5K drafts."

**Q3: "How do you handle Vietnamese accuracy (lower than English)?"**

> "The model card documents the limitation. The recommendation: human review for Vietnamese-only customers (the CS team includes 2 Vietnamese speakers). The Phase 5 lift: collect a Vietnamese eval set (50 rows) and measure the gap. If the gap is > 10%, fine-tune on Vietnamese-only data."

**Q4: "What if ollama crashes mid-day?"**

> "The Phase 2 drafter (GPT-4o-mini) is the fallback. The serve.py has a try/except: if ollama returns 5xx, fall back to the hosted API. The cost is $0.50/week if ollama is down for a week; the cost is $0.00/week if ollama is up. The runbook documents the fallback."

**Q5: "Why not just use GPT-4o-mini and accept the $2.17/month bill?"**

> "The CFO said no. The $5/month LLM ceiling is the operational boundary. The SLM makes the cost ceiling scale-invariant: at 10× growth, the bill is still $0.00/month (vs $20/month for GPT-4o-mini). The SLM is the FDE's proof to the CFO that the LLM line item is a one-time training cost, not a recurring API bill. That's the value the FDE brings to the customer."

---

## The cross-reference: how this maps to Phase 6

| Phase | The FDE skill it proves |
|---|---|
| `../generative-ai/01-llm-fundamentals.md` | The transformer + pre-training vs fine-tuning story |
| `../company-experiences/meta-fde-ai-engineer.md` | The open-weight + on-device story (Meta variant) |
| `../company-experiences/huggingface-fde-open-source.md` | The Hub + PEFT/LoRA + Inference Endpoints story |

---

## The thesis

**The SLM distillation deep-dive is the alt-#2 45-minute script.** The signal: a candidate who can deliver it without notes, with a working Qwen-1.5B + LoRA on their laptop, the 150-row eval set passing the 91% threshold, the model card, and the 5-question "FDE has left" test — is showing they can train and serve a production-grade SLM.

**The 12 slides are the muscle memory.** The 5 follow-up Q&A are the practice bank. The model card is the artifact.

**Use this script when the company wants an ML or cost-optimization angle.** The PacificFreight deep-dive is the single-service angle. The multi-agent dispatcher deep-dive is the multi-agent angle. Choose the one that matches the company's signature round.

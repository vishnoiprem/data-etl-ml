# L4.3: Fine-tuning and distillation — the levers of last resort

> **FDE framing in one line:** fine-tuning and distillation are the levers of last resort. The FDE escalates to them only when prompt engineering has been exhausted AND the cost ceiling is binding. The SLM at 10× cost reduction is the canonical example.

## The 3 things you'll learn

1. The 3 conditions for fine-tuning: (a) prompt engineering exhausted, (b) cost ceiling binding, (c) the task distribution is stable.
2. The LoRA + Qwen2.5-1.5B pattern: the FDE-distilled SLM that ships at 10× cost reduction and 90-95% of the API model's quality.
3. The model card as the artifact: training data summary, eval results, intended use, limitations — the artifact that survives the FDE's exit.

## Concept

Fine-tuning and distillation are the levers of last resort. The FDE escalates to them only when two conditions are both met: (a) prompt engineering has been exhausted (the system prompt + few-shot examples + CoT have been tuned and the model still falls short), AND (b) the cost ceiling is binding (the per-run cost exceeds the customer's budget). **If either condition is missing, the FDE does not scale — they stay with prompt engineering.**

The 3 conditions for fine-tuning:

1. **Prompt engineering exhausted.** The system prompt has been tuned; the few-shot examples have been curated; chain-of-thought has been added; the model still falls short of the target accuracy on the test set. If the model is at 90% accuracy with good prompting, do not fine-tune — fine-tuning costs $5K-$50K in GPU time + dataset curation, and the marginal gain is rarely worth it.
2. **Cost ceiling binding.** The per-run cost exceeds the customer's budget. For a CS-drafter at $0.005/run with 150 runs/day, the monthly cost is $22.50 — well within a $100/month budget. If the customer has 10 teams (1500 runs/day), the monthly cost is $225 — still within a $500/month budget. If the customer has 100 teams (15000 runs/day), the monthly cost is $2250 — over budget. **Fine-tune only when the cost ceiling is binding.**
3. **Task distribution is stable.** The fine-tuned model is trained on a specific distribution; if the distribution shifts (new tool, new domain, new customer), the fine-tuned model degrades. Fine-tune only when the task distribution is stable for at least 6 months. If the customer is in a fast-moving domain (new product launches every quarter), the fine-tune will be obsolete before it pays back.

The LoRA + Qwen2.5-1.5B pattern is the canonical FDE distillation recipe. LoRA (Low-Rank Adaptation) fine-tunes a small adapter (~50MB) on top of a frozen base model; the adapter captures the domain-specific behavior; the base model retains its general capabilities. Qwen2.5-1.5B is a small-but-capable model that runs on a Mac M-series with MPS acceleration. **The combination trains in ~30 minutes on a Mac and ships at 10× cost reduction and 90-95% of the API model's quality.**

The model card as the artifact is the recognition that the fine-tuned model is the artifact that survives the FDE's exit. The model card contains: training data summary (how many examples, what distribution, what filtering), eval results (the test set metrics, the comparison to the API model), intended use (the task, the customer, the budget), and limitations (the failure modes, the distribution shifts that would invalidate the model). **The model card is the runbook for the fine-tuned model; without it, the model is a black box the customer cannot maintain.**

## The pattern

The fine-tuning decision rubric:

```python
@dataclass
class FineTuneDecision:
    prompt_accuracy: float        # current accuracy with prompting (0.0 - 1.0)
    cost_ceiling_usd_per_month: float
    current_cost_usd_per_month: float
    distribution_stable_months: int

def should_fine_tune(d: FineTuneDecision) -> bool:
    """Decide whether to fine-tune or stay with prompting."""
    if d.prompt_accuracy >= 0.90:
        return False  # Prompting is good enough; fine-tuning is not justified
    if d.current_cost_usd_per_month <= d.cost_ceiling_usd_per_month:
        return False  # Cost is within budget; no need to distill
    if d.distribution_stable_months < 6:
        return False  # Distribution will shift; fine-tune will be obsolete
    return True  # All 3 conditions met; fine-tune
```

The LoRA training loop (skeleton):

```python
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# Load the base model in 4-bit (saves memory)
base = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen2.5-1.5B-Instruct",
    load_in_4bit=True,
    device_map="auto",
)

# Add LoRA adapter
lora_cfg = LoraConfig(
    r=16,                  # Low-rank dimension
    lora_alpha=32,        # Scaling factor
    target_modules=["q_proj", "v_proj"],  # Apply to attention layers
    lora_dropout=0.05,
)
model = get_peft_model(base, lora_cfg)

# Train on the customer's usage data (filtered for high-quality examples)
trainer = SFTTrainer(
    model=model,
    train_dataset=pf_dataset,             # (prompt, response) pairs from usage.jsonl
    args=TrainingArguments(
        num_train_epochs=3,
        per_device_train_batch_size=4,
        learning_rate=2e-4,
        output_dir="./adapters/pf-drafter-lora",
    ),
)
trainer.train()
trainer.save_adapter("./adapters/pf-drafter-lora")  # ~50MB adapter
```

The serving pattern:

```bash
# Build the ollama model with the adapter
ollama create pf-drafter -f Modelfile
# Modelfile:
# FROM qwen2.5:1.5b
# ADAPTER ./adapters/pf-drafter-lora
```

```python
# Serve via ollama's API (mirrors the OpenAI API)
import ollama
response = ollama.chat(
    model="pf-drafter",
    messages=[{"role": "user", "content": email}],
)
```

The pattern that wins interviews is the "3 conditions + LoRA + model card" pattern. The candidate who says "I fine-tune only when (a) prompting is exhausted at < 90% accuracy, (b) the cost ceiling is binding, AND (c) the distribution is stable for 6+ months. The recipe is LoRA on Qwen2.5-1.5B with a 50MB adapter, training on the customer's filtered usage data, ~30 minutes on a Mac. The artifact is the model card: training data summary, eval results, intended use, limitations" is the candidate who demonstrates the distillation-mindset.

## Code or example

The dataset preparation (the FDE's most important fine-tuning decision):

```python
def prepare_fine_tune_dataset(usage_jsonl: str, min_thumbs_up: int = 1) -> list[dict]:
    """Convert usage.jsonl to a (prompt, response) training set.

    Filter: only thumbs-up examples (Mei's edits are the gold standard).
    Format: the system prompt + retrieved context + email -> Mei's final draft.
    """
    examples = []
    for line in open(usage_jsonl):
        record = json.loads(line)
        if record.get("thumbs_up", 0) < min_thumbs_up:
            continue  # Filter out thumbs-down
        if not record.get("final_draft"):
            continue  # Filter out drafts Mei never edited
        prompt = render_training_prompt(record)  # system + context + email
        response = record["final_draft"]
        examples.append({"prompt": prompt, "response": response})
    return examples

# Result: 800-1000 examples from 4 weeks of usage at 150 emails/day.
# Filter rate: ~50% (half the drafts are thumbs-down or unedited).
# Training time: ~30 min on Mac M-series with 4-bit quantization.
```

The eval-driven regression check (the FDE's quality gate):

```python
def eval_slm(slm_fn, baseline_fn, eval_set: list[dict]) -> dict:
    """Compare SLM to baseline on the eval set."""
    slm_scores = [score_draft(slm_fn(ex["email"]), ex["expected_draft"]) for ex in eval_set]
    baseline_scores = [score_draft(baseline_fn(ex["email"]), ex["expected_draft"]) for ex in eval_set]
    slm_avg = sum(slm_scores) / len(slm_scores)
    baseline_avg = sum(baseline_scores) / len(baseline_scores)
    ratio = slm_avg / baseline_avg
    return {
        "slm_avg": slm_avg,
        "baseline_avg": baseline_avg,
        "ratio": ratio,
        "passes_90_pct_bar": ratio >= 0.90,
    }

# Result: ratio = 0.92 (SLM is 92% of baseline quality)
# Cost: SLM = $0.0005/run vs baseline = $0.005/run = 10× cost reduction
# Verdict: ship the SLM.
```

The model card:

```markdown
# Model Card: pf-drafter-lora (v1.0.0)

## Training data
- Source: PacificFreight CS-drafter usage.jsonl (4 weeks, 2026-09-12 to 2026-10-10)
- Examples: 847 (filtered from 1,624 drafts; 50% thumbs-up, 50% thumbs-down or unedited)
- Format: (system prompt + retrieved context + email) -> Mei's final draft
- Distribution: 30% status, 20% refund, 20% translation, 10% escalation, 20% other

## Eval results
- Test set: 100 held-out examples (not in training)
- Baseline (gpt-5-mini): 0.85 avg score
- SLM (Qwen2.5-1.5B + LoRA): 0.78 avg score
- Ratio: 0.92 (passes 90% bar)

## Intended use
- Customer: PacificFreight CS team (Mei, Sarah)
- Task: draft replies to customer emails about shipments, refunds, translations, escalations
- Budget: $5/month for 150 emails/day (vs $22.50/month for gpt-5-mini)
- Deployment: ollama on Daniel's VM, behind the same MCP server as the API model

## Limitations
- Distribution shift: if PacificFreight adds a new service (e.g., freight forwarding), the SLM will degrade. Retrain quarterly.
- Edge cases: the SLM is 85% accurate on the long tail (5% of emails are complex multi-shipment requests). Use the API model as fallback.
- PII: the SLM does not have the same PII redaction as the API model. Run the redaction layer before serving.

## Rollback plan
- If the SLM accuracy drops below 85%, revert to gpt-5-mini via the circuit breaker.
- The eval set is run weekly; the rollback is triggered automatically.
```

## Production addendum

The fine-tuning question is the answer to "when do you fine-tune vs prompt." The 60-second script:

> "Three conditions for fine-tuning. Prompt engineering exhausted at < 90% accuracy. Cost ceiling binding (the API model's monthly cost exceeds the customer's budget). Task distribution stable for 6+ months. **If any condition is missing, do not fine-tune — stay with prompting.** The recipe when all 3 are met: LoRA on Qwen2.5-1.5B with a 50MB adapter, training on the customer's filtered usage data (~800-1000 examples), ~30 min on a Mac. The eval-driven regression check: the SLM must hit 90% of the API model's quality on the held-out test set. The artifact is the model card: training data summary, eval results, intended use, limitations, rollback plan. The wrong choice is fine-tuning for the sake of it (5-10× cost without proportional gain). The wrong choice is staying with prompting when the cost ceiling is binding (the customer churns because the bill is too high). The right choice is the 3 conditions + the eval-driven gate + the model card."

This is the difference between a candidate who says "I fine-tuned a model" and a candidate who says "3 conditions for fine-tuning; LoRA on Qwen2.5-1.5B; eval-driven gate at 90%; model card as the artifact." The latter is who gets hired.

## Cross-references

- **Practice code**: `course/practice/level-6-production/lesson-10-3-lora-qlora.py` — the LoRA training loop.
- **Reference implementation**: `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/slm/train.py` — the production fine-tuning pipeline.
- **Phase 1 module**: `course/ai-fde/phase-1-foundations/README.md` — the SLM as a first-class pattern.
- **Phase 4 project**: `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/` — the canonical FDE distillation recipe.
- **Interview prep**: `course/ai-fde/phase-6-interview-prep/system-design/09-agentic-ai.md` — distillation as a system design pattern.

## The 3 questions this lecture preps you for

1. **"When do you fine-tune vs prompt?"** Answer: fine-tune only when 3 conditions are met — prompting exhausted at < 90% accuracy, cost ceiling binding, distribution stable for 6+ months. If any condition is missing, stay with prompting. The recipe is LoRA on a small base (Qwen2.5-1.5B), trained on the customer's filtered usage data, eval-driven gate at 90% of the API model's quality.
2. **"What is LoRA and why use it?"** Answer: LoRA (Low-Rank Adaptation) fine-tunes a small adapter (~50MB) on top of a frozen base model. The adapter captures domain-specific behavior; the base model retains general capabilities. LoRA trains in ~30 min on a Mac M-series with 4-bit quantization, vs ~8 hours for full fine-tune on a cluster. The 10× training cost reduction makes the FDE distillation practical.
3. **"What is the model card and why is it important?"** Answer: the model card is the artifact that survives the FDE's exit. It contains: training data summary (how many examples, what distribution, what filtering), eval results (test set scores, comparison to baseline), intended use (task, customer, budget), limitations (failure modes, distribution shifts), rollback plan (when to revert to the API model). The model card is the runbook for the fine-tuned model; without it, the model is a black box the customer cannot maintain.

## Read next

`S5-architecture-patterns/L5-1-the-single-agent-pattern.md` — Section 5 dives into the 6 canonical architecture patterns: single agent, orchestrator + sub-agents, multi-agent system, hierarchical task network, debate-style agents, and simulation. The 7 ingredients + the levers compose into these patterns; the FDE's job is to pick the right pattern for the task.
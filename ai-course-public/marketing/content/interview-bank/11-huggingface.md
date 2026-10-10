# 11. Hugging Face

- **Role:** ML Engineer
- **Tech stack:** Python, PyTorch, JAX, Transformers, Diffusers, Datasets, Rust (safetensors/tokenizers)
- **Comp band:** $200K-$700K (NYC/Paris/SF, L3-L6)
- **Cumulative pass rate:** ~3-5%

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. **Recruiter screen** | Background, open-source contribution check | 1 week | ~60% advance |
| 2. **Technical phone screen** | 1-2 coding + ML fundamentals, transformers-heavy | 1-2 weeks | ~40% advance |
| 3. **Onsite (4 rounds, 1 day)** | Coding → open-source PR-style review → ML deep-dive → behavioral | 1-2 days | ~30% advance |
| 4. **Reference + offer** | Comp negotiation real; open-source is the bar | 1-2 weeks | — |

## Stage 1: Recruiter screen (30 min)

### Q1.1: "Tell me about your background"
**Answer:** I'm an ML engineer with 5 years in open-source ML — most recently at [X] where I shipped [Y] library that hit 1M monthly downloads. Relevant: my PRs to [transformers / diffusers / tokenizers] added [specific feature]. I'm targeting Hugging Face because the open-source ML platform thesis is the bet I want to be closest to.
**Tip:** Hugging Face grades open-source contribution heavily; bring GitHub specifics.

### Q1.2: "Why Hugging Face?"
**Answer:** I want to work on the Hub because the model+dataset+space trifecta is the platform for open-source ML. The 1 thing I'd test: whether the Hub can support federated fine-tuning across 100K contributors without centralizing their data. I disagree with the closed-Enterprise Hub pricing — keep the Hub open.
**Tip:** Open-source + Hub is the Hugging Face bet.

## Stage 2: Technical phone screen (60 min)

### Q2.1: "Implement a custom Trainer callback for early stopping on plateau"
**Answer:**
```python
from transformers import TrainerCallback
class EarlyStopPlateau(TrainerCallback):
    def __init__(self, patience=3): self.patience, self.best, self.wait = patience, float("inf"), 0
    def on_evaluate(self, args, state, control, metrics, **kwargs):
        cur = metrics.get("eval_loss", float("inf"))
        if cur < self.best: self.best, self.wait = cur, 0
        else:
            self.wait += 1
            if self.wait >= self.patience: control.should_training_stop = True
```
The Hugging Face warmup. Know the Trainer API.
**Tip:** Trainer + callbacks + safetensors is the HF-canonical stack.

## Stage 3: Onsite (4 rounds)

### Round 3.1: Coding (60 min)

### Q3.1.1: "Implement a text streaming generator with backpressure"
**Answer:**
```python
def stream_tokens(prompt, model, tokenizer, max_new=200):
    ids = tokenizer(prompt, return_tensors="pt").input_ids
    past = None
    for _ in range(max_new):
        out = model(input_ids=ids if past is None else ids[:, -1:], past_key_values=past, use_cache=True)
        past = out.past_key_values
        nxt = out.logits[:, -1].argmax(dim=-1, keepdim=True)
        ids = torch.cat([ids, nxt], dim=-1)
        yield tokenizer.decode(nxt[0])
        if nxt.item() == tokenizer.eos_token_id: break
```
KV cache reuse via `past_key_values`. Hugging Face grades streaming + cache reuse.
**Tip:** KV cache + streaming is the HF-canonical answer.

### Q3.1.2: "Merge two safetensors files into one"
**Answer:** `st1 = safetensors.torch.load_file("a.safetensors"); st2 = safetensors.torch.load_file("b.safetensors"); merged = {**st1, **st2}; safetensors.torch.save_file(merged, "out.safetensors")`. Use safetensors (not pickle) for memory-mapped, zero-copy loading.
**Tip:** safetensors + memory mapping is the HF performance answer.

### Round 3.2: Open-source PR review (60 min)

### Q3.2.1: "Review this PR for a transformers feature"
**Answer:** The grader hands you a real PR. Look for: (1) tests added (unit + integration), (2) backward compatibility, (3) docstring updated, (4) edge cases (empty input, OOV, device mismatch). The wrong answer: only check the diff. The right answer: check the doc, the tests, the examples, the breaking-change note.
**Tip:** Match the transformers PR template (description, tests, docs, breaking change).

### Round 3.3: ML deep-dive (60 min)

### Q3.3.1: "How would you add a new model architecture to transformers?"
**Answer:** Five files: (1) `modeling_newarch.py` (the model class), (2) `configuration_newarch.py` (the config), (3) `convert_xxx.py` (a converter from a reference impl), (4) `tests/test_modeling_newarch.py`, (5) docs in `docs/source/en/model_doc/newarch.md`. Use the `_prepare_4class_inputs` pattern from the existing tests. Add a slow tokenizer if needed.
**Tip:** 5-file PR + the convert script is the HF-canonical contribution.

### Q3.3.2: "Implement distributed data parallel (DDP) training with accelerate"
**Answer:**
```python
from accelerate import Accelerator
accelerator = Accelerator()
model, optimizer, dataloader, scheduler = accelerator.prepare(model, optimizer, dataloader, scheduler)
for batch in dataloader:
    out = model(**batch); loss = out.loss
    accelerator.backward(loss); optimizer.step(); scheduler.step(); optimizer.zero_grad()
```
DDP: each process holds a full model copy; gradients are all-reduced across processes. Trade-off: DDP (simpler, more memory) vs. DeepSpeed ZeRO (sharded, less memory).
**Tip:** Accelerate + DDP is the HF-canonical distributed pattern.

### Round 3.4: Behavioral (45 min)

### Q3.4.1: "Tell me about a PR you shipped"
**Answer:** I shipped [PR #] to [transformers / diffusers / tokenizers] that added [specific feature]. The PR went through 3 review rounds; I addressed every comment; it merged 2 weeks after opening. The feature now processes 100K models on the Hub.
**Tip:** Specific PR + specific impact is the HF-canonical answer.

### Q3.4.2: "Why Hugging Face?"
**Answer:** I want to work on the Hub because the model+dataset+space trifecta is the platform for open-source ML. The 1 thing I'd test: whether the Hub can support federated fine-tuning across 100K contributors without centralizing their data. I disagree with the closed-Enterprise pricing — keep the Hub open.

## Stage 4: Hiring committee

The committee weighs open-source contribution + ML depth + HF mission fit. They look for: (1) GitHub profile with merged PRs to transformers/diffusers/tokenizers, (2) coherent open-source narrative, (3) "would I want this person reviewing my PR?" 1-2 week turnaround.

## Stage 5: Offer

Hugging Face comp is base + RSU + sign-on. NYC / Paris / SF hubs. Cash component is decent. The play: anchor with a competing offer (if you have one). Sign-on is real for senior candidates.

## Tips for the Hugging Face loop

- **Open-source is the bar.** Bring your GitHub; merged PRs win.
- **Trainer + callbacks + safetensors.** The canonical stack.
- **PR review is graded.** Check tests + docs + backward compat + edge cases.
- **5-file model PR.** Modeling, config, converter, tests, docs.
- **Accelerate + DDP.** The distributed pattern.
- **Why HF needs the Hub bet.** Open-source + platform.
- **NYC / Paris / SF.** Loop is on-site; travel reimbursed.

## Real candidate report

> *"Hugging Face's interview is unique — they grade on open-source contribution as much as on ML depth. I brought a printout of my GitHub profile and walked through my top 3 merged PRs. The PR-review round was real — they handed me an actual PR and asked for a code review. The candidate who treats it like a generic ML interview loses."*
> — Glassdoor candidate report, paraphrased from 2026 loops

## Sources

- [Hugging Face](https://huggingface.co/)
- [Transformers Documentation](https://huggingface.co/docs/transformers)
- [Safetensors](https://github.com/huggingface/safetensors)
- [Accelerate](https://huggingface.co/docs/accelerate)
- [Levels.fyi — Hugging Face compensation](https://www.levels.fyi)
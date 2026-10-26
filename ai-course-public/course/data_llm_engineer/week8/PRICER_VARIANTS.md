# The three pricer services — which one to use

`week8/` contains three files that all do the same thing (price an item from a
description using a QLoRA-fine-tuned Llama 3.2-3B). They are **not
interchangeable**, and nothing in the repo says which is current. This note is
that missing explanation.

| File | Modal primitive | Model loads | Use it for |
|---|---|---|---|
| `pricer_ephemeral.py` | `@app.function` | **Every call** | Teaching the problem. See the cost. |
| `pricer_service.py` | `@app.cls` + `@modal.enter()` | **Once, at container start** | Anything real. **This is the one to keep.** |
| `pricer_service2.py` | `@app.cls` + `@modal.enter()` (with a persistent HF cache volume) | **Once, at container start** | The production version with the `hf-hub-cache` volume. |

---

## The distinction, precisely

### `@app.function` — ephemeral

```python
@app.function(image=image, secrets=secrets, gpu=GPU, timeout=1800)
def price(description: str) -> float:
    # model is loaded HERE, inside the function body
    base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL, ...)
    fine_tuned_model = PeftModel.from_pretrained(base_model, ...)
```

Every invocation of `price()` re-imports torch, re-loads the base model from
the Hub, and re-applies the LoRA adapter. For a 3B model in 4-bit on a T4,
that is roughly **20–40 seconds of pure setup** before a single token is
generated.

Modal bills by the second, and a `@app.function` container spins down after
~2 minutes idle. So the cost profile is brutal: you pay container-start +
model-load + inference, every single call.

**Why it exists:** it's the honest first version. It demonstrates that you can
get a fine-tuned model running in the cloud at all. Week 8 Day 1 builds it
this way on purpose so the improvement in Day 1's later lecture lands.

### `@app.cls` — a service

```python
@app.cls(image=..., secrets=secrets, gpu=GPU, timeout=1800, min_containers=MIN_CONTAINERS)
class Pricer:
    @modal.enter()
    def setup(self):
        # model is loaded HERE, once
        self.tokenizer = ...
        self.base_model = ...
        self.fine_tuned_model = ...

    @modal.method()
    def price(self, description: str) -> float:
        # inference only — no loading
```

`@modal.enter()` runs **once per container lifetime**. Every subsequent call
to `Pricer().price(...)` reuses the loaded model. A warm call is sub-second.

This is the difference between a demo and a service.

---

## Cost comparison (the number that motivates the change)

Say inference takes 0.8s and model load takes 30s.

| | Load per call | Warm latency | 1,000 calls, batched 50× |
|---|---|---|---|
| `@app.function` | 30s | ~31s | 20 containers × ~16 min ≈ **$11** |
| `@app.cls` (min=0) | once per container | ~0.8s | 1 container, ~3 min of GPU ≈ **$0.10** |

The exact numbers depend on Modal's current pricing — **check
[modal.com/pricing](https://modal.com/pricing) rather than trusting this
table.** The *ratio* is the durable part: the ephemeral version is roughly
two orders of magnitude more expensive for identical output, because you are
paying to re-read the same weights off disk 1,000 times.

---

## `MIN_CONTAINERS` — the latency/cost dial

```python
# Change this to 1 if you want Modal to be always running, otherwise it will go cold after 2 mins
MIN_CONTAINERS = 0
```

| Value | Behaviour | Use when |
|---|---|---|
| `0` (default) | Scales to zero. First request after idle pays cold-start (~30s). | Batch jobs, demos, anything not latency-sensitive. |
| `1` | One container always warm. No cold start. You pay for idle GPU time. | User-facing APIs where a 30s first response is unacceptable. |

`pricer_service.py` ships with `0`. For the course's price scanner that's
correct — it's a batch tool. If you put this behind a web request, set it to
`1` and accept the cost.

---

## `pricer_service2.py` adds one thing: the HF cache Volume

The only functional difference between `pricer_service.py` and
`pricer_service2.py` is this pair of lines:

```python
# pricer_service2.py only
CACHE_DIR = "/cache"
hf_cache_volume = Volume.from_name("hf-hub-cache", create_if_missing=True)

@app.cls(
    image=image.env({"HF_HUB_CACHE": CACHE_DIR}),
    volumes={CACHE_DIR: hf_cache_volume},
    ...
)
```

`HF_HUB_CACHE` is where transformers writes downloaded weights. By default
that's the container's ephemeral filesystem, so it dies with the container.

**Why this matters as soon as you have more than one container:** Modal scales
to N containers to handle concurrent requests. Without a shared volume, each
of the N independently downloads ~6GB of Llama 3.2 weights from the Hub —
N× the network cost and N× the cold-start latency, forever. With the volume,
the first container populates it and the rest mount it instantly.

If you go multi-replica, this line is not optional. It's also the reason
`pricer_service2.py`'s image omits `"huggingface"` from `pip_install` while
`pricer_service.py` includes it — a leftover from the two files diverging
during the notebooks. Harmless either way; `transformers` pulls it in.

---

## The fine-tuned model reference is pinned, and that's deliberate

All three files hardcode:

```python
RUN_NAME = "2025-11-28_18.47.07"
REVISION = "b19c8bfea3b6ff62237fbb0a8da9779fc12cefbd"
FINETUNED_MODEL = f"{HF_USER}/{PROJECT_RUN_NAME}"
```

`REVISION` is a **commit SHA on the HuggingFace Hub**, not a branch. This is
correct and important:

- `PeftModel.from_pretrained(model, "ed-donner/price-2025-11-28_18.47.07")`
  would resolve to whatever the repo's `main` points at *today*.
- If the author pushes a new checkpoint, your production service silently
  changes behaviour with no diff in your code.

Pinning the SHA makes the deployment reproducible. **Keep this when you adapt
these files.** If you re-run week 7's fine-tuning, your new revision SHA goes
here.

---

## What to change when you adapt this

1. **Use `pricer_service.py` as the base.** Delete or ignore the other two.
2. **Point `HF_USER` at your own HuggingFace account**, or leave `ed-donner`
   to reproduce the course's exact numbers (his comment in the file says this
   is intentional and allowed).
3. **Confirm your Modal secret name.** The files call
   `modal.Secret.from_name("huggingface-secret")`; the comment warns your
   account may call it `hf-secret`.
4. **Replace `CACHE_DIR` volume wiring** if you go multi-container — the
   `Volume.from_name("hf-hub-cache", ...)` is what keeps three replicas from
   each re-downloading 6GB.

---

## A real bug worth knowing about

`self.tokenizer.padding_side = "right"` appears in `pricer_service.py`. For
**generation** with a single prompt and no batching, padding side is
irrelevant — there's nothing to pad. It's carried over from the week 7
training notebook, where the opposite convention matters.

It's harmless here. It becomes a real bug the moment you batch. If you extend
this service to batch inference, **set `padding_side = "left"`** or your
generations will be corrupted by trailing pad tokens.

---

**Last updated:** 2026-10-21
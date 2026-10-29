# ML — Classical ML, Deep Learning, and LLM Foundations

> **The foundations half of the portfolio.** Everything that came before
> RAG, agents, eval — and everything the agentic systems rely on at the
> tensor level. From a college-level linear regression to a fine-tuned
> GPT-2 in production.

This directory exists for one reason: when the production system breaks,
someone has to know what happens at layer 17 of the transformer, or why
a quantization step matters, or which loss function the reranker is
actually minimizing. That someone is me. The directories below are the
notes, the experiments, and the reference implementations that keep
that knowledge honest.

---

## What's in this directory

### Foundation / coursework

| Directory | What it is | Status |
|-----------|------------|--------|
| [**calculas/**](./calculas/) | The math that every ML paper is secretly written in: optimization, probability, linear algebra | Notes + exercises |
| [**linear/**](./linear/) | Linear / logistic regression from first principles: bias/variance, regularization, gradient descent | Reference implementation |
| [**clustering/**](./clustering/) | k-means, DBSCAN, hierarchical. With the textbook caveats spelled out | Reference |
| [**k-mean-cluser/**](./k-mean-cluser/) | A second pass on k-means, with eval: silhouette, elbow, stability | Eval-disciplined |
| [**cn/**](./cn/) | Convolutional networks, from LeNet to ResNet, with PyTorch | Reference |
| [**neural_network/**](./neural_network/) | MLP from scratch, autograd, backprop | Reference |
| [**deep_Learning/**](./deep_Learning/) | Deeper architectures, regularization, augmentation | Reference |
| [**vector-ebedding/**](./vector-ebedding/) | Word2Vec / GloVe / sentence embeddings, the history before transformers | Reference |
| [**diffusion/**](./diffusion/) | Diffusion models (DDPM, score-based), with the math spelled out | Reference |
| [**notebooks/**](./notebooks/) | Sandboxes / scratch / experiments in flight | Sandbox |
| [**data/**](./data/) | Datasets that don't belong anywhere else | Data |
| [**system_design/**](./system_design/) | System-design angle: how ML systems survive at scale | Notes |

### LLM-specific

| Directory | What it is | Status |
|-----------|------------|--------|
| [**LLM/**](./LLM/) | The LLM half: GPT-2 from scratch, fine-tuning, RAG, eval, model selection | Reference + production |
| [**ai-agent/**](./ai-agent/) | Early agentic patterns, predates the `../agentic-ai/` directory | Reference |
| [**GenAI-Pinnacle-Master/**](./GenAI-Pinnacle-Master/) | The 12-week GenAI mastery coursework: from prompt to production | Curriculum |

---

## What you'll find here

- **From-scratch implementations** of the algorithms every ML interview
  asks about: linear regression, logistic regression, k-means, MLP,
  CNN, ResNet, Word2Vec, GPT-2.
- **Eval-first projects** — the ones that have RAGAS / DeepEval / a
  custom metric. If a project has eval, it's here.
- **Coursework-quality work** that I'm not embarrassed to show a hiring
  manager. The exercises, the derivations, the proofs. The boring parts
  that turn out to matter.

## What you will NOT find here

- **Production code for a paying customer.** That's in
  [`../data-engineering/`](../data-engineering/) and
  [`../ai-engineering/`](../ai-engineering/) — those directories are
  the production half. This one is the foundation.
- **A polished ML curriculum for paying students.** That's
  [`../ai-course-public/`](../ai-course-public/) — a separate,
  student-facing set of materials.
- **The "explanation of an LLM from first principles" content.** Some
  of that lives in [`../medium/`](../medium/), in long-form. This
  directory is the code-and-experiments side.

---

## How to use this directory

- **Hire me for a Staff role:** you don't need to read this directory.
  [`../README.md`](../README.md) is the entry point. This directory is
  the "I've seen the algorithm from the inside" half — read it if you
  want the depth.
- **Study ML the way I studied it:** start at `linear/`, then `cn/`,
  then `deep_Learning/`. The progression is roughly the order a
  textbook would set. The LLM-specific work (`LLM/`) assumes you've
  been through the foundation.
- **Want a guided tour:** `GenAI-Pinnacle-Master/` is the structured
  12-week curriculum.

---

## Honest scope notes

A few things worth saying out loud so you don't expect too much:

- **The math is correct, but the implementations are learning
  implementations.** They are clear and runnable, but they're not
  optimized. Production code, where the bottleneck matters, lives
  elsewhere.
- **Some directories are still WIP.** The `notebooks/` directory in
  particular is a working scratchpad; not every notebook is finished.
- **LLM/ has both education and production-shaped work.** The
  `fine_tuned_gpt2/` and `rag/` subdirectories are production-shaped;
  `transformers_gpt2.py` and `NGramLanguageModel.py` are educational.
  I tried to keep the lines clear in the project READMEs.

---

## Related directories

- [`../ai-engineering/`](../ai-engineering/) — 40 production LLM
  projects. The "ship a system" half.
- [`../agentic-ai/`](../agentic-ai/) — 18 production agents. The
  "compose the system" half.
- [`../data-engineering/`](../data-engineering/) — 18 data-platform
  projects. The "the model has data to train on" half.
- [`../ai-course-public/`](../ai-course-public/) — 197 lines, the
  public-facing ML curriculum.
- [`../medium/`](../medium/) — long-form articles on many of the
  topics here, if you want the prose version.

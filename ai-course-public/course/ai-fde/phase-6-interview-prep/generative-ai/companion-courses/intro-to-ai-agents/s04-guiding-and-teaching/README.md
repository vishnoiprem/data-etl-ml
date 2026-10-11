# Section 4: Guiding and teaching AI agents (3 lectures, 8 min)

> **The three lectures in this section answer the question "how do you teach the agent what to do?"** The 7 ingredients from Section 2 + the topologies from Section 3 give the FDE the shape of the agent; Section 4 gives the FDE the content. The system prompt, the few-shot examples, and the chain-of-thought scaffolding are the levers that turn a generic LLM into a domain-specific agent.

## In 60 seconds

The three ideas you must recite from this section:

1. **6 prompting patterns:** zero-shot, few-shot, chain-of-thought, ReAct, system-prompt-as-spec, structured-output.
2. **Fine-tune vs prompt:** prompt first, fine-tune when the prompt is stable + the cost ceiling is exceeded + you have ≥1,000 labeled examples. **The right choice for 80% of FDE use cases is *don't fine-tune*.**
3. **3-loop iteration cadence:** daily (eval set), weekly (postmortem), monthly (re-train). The eval set is the spec; the cost model is the test.

**If you only read one lecture, read L4-1** — the 6 prompting patterns are the candidate's most-tested vocabulary in the screening round.

## The 3 lectures in this section

| # | File | Topic | Read time | Interview signal |
|---|---|---|---|---|
| L4.1 | `L4-1-prompt-engineering-for-agents.md` | The 5-section system prompt; the contract between the model and the agent. | ~3 min | "How do you write a good agent system prompt?" |
| L4.2 | `L4-2-few-shot-examples-and-cot.md` | Few-shot examples as the most reliable prompt-engineering lever; chain-of-thought for multi-step reasoning. | ~3 min | "When do you use few-shot examples vs zero-shot?" |
| L4.3 | `L4-3-fine-tuning-and-distillation.md` | When to fine-tune (cost ceiling exceeded), when to distill (SLM at 10× cost reduction), when to do neither. | ~2 min | "When do you fine-tune vs prompt?" |

## The 1-sentence framing

The 3 levers for guiding an agent are: (1) the system prompt (5 sections, rendered at startup, version-controlled), (2) few-shot examples (the most reliable way to teach output format), (3) fine-tuning / distillation (the lever of last resort, when the cost ceiling is the binding constraint). **Default to prompt engineering; escalate to fine-tuning only when the cost-quality curve demands it.**

## How to read this section

1. Read `L4-1` first — the system prompt is the primary lever; the other two are escalations.
2. Then `L4-2` — few-shot examples are the most reliable way to teach output format and behavior; chain-of-thought is the lever for multi-step reasoning.
3. Then `L4-3` — fine-tuning and distillation are the levers of last resort; the FDE escalates to them only when prompt engineering has been exhausted and the cost ceiling is binding.

## The Phase 1-5 cross-reference

This section maps to **Phase 1 (Foundations) + Phase 4 (Capstone — SLM project)** of the FDE curriculum. The system prompt in L4.1 is implemented in `course/practice/level-2-prompt-engineering/lesson-3-5-system-prompts.py`. The few-shot examples in L4.2 are implemented in `course/practice/level-2-prompt-engineering/lesson-3-2-few-shot.py`. The fine-tuning and distillation in L4.3 is implemented in `course/practice/level-6-production/lesson-10-3-lora-qlora.py` and the capstone `course/ai-fde/phase-4-capstone/projects/03-distilled-slm/`.

## What this section preps you for

- Anthropic FDE: § 2 design round is "show me your system prompt + your few-shot examples"
- LangChain FDE: § 2 design round is "how do you teach the agent the output format"
- OpenAI: warm-up is "what are the levers for guiding an LLM"
- Databricks AI FDE: decomposition question #4 is "is the system prompt well-structured"
- Sierra AI: § 2-3 take-home is "write the system prompt for this agent"

## The thesis

**The 3 levers are ordered by leverage and cost.** The system prompt is the highest-leverage, lowest-cost lever; it should be tried first and tuned carefully. Few-shot examples are the second lever; they are the most reliable way to teach output format and behavior. Fine-tuning and distillation are the levers of last resort; they are expensive (GPU time, dataset curation, eval) and reserved for cases where prompt engineering has been exhausted. **The FDE candidate who can name all 3 levers and explain when to escalate is the candidate who can ship a well-behaved agent on a budget.**

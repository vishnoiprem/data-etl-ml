# Scaling AI Performance: The Five Techniques

> **Section 2 deliverable.** Maps to *RAG and Fine-Tuning* (16:09),
> *AI Agents vs Workflows* (20:37), *Frontier vs Open-Source* (18:49).
>
> The core commercial skill: choosing the *cheapest technique that clears the
> quality bar*. Not the most capable one.

---

## The decision, in order

Most teams skip straight to the most impressive technique. That's backwards.
Work down this list and stop at the first one that clears your quality bar:

```
  1. PROMPT           ← try this first, costs ~$0 to iterate
  2. RAG              ← adds your knowledge, still cheap
  3. FINE-TUNE        ← changes behaviour, costs real money
  4. AGENT            ← adds autonomy, costs real money + audit cost
  5. NEW MODEL        ← a bigger model, which also costs real money
```

**Each step costs roughly 5–10× the previous one in both money and
maintenance.** The failure mode is skipping to 3 or 4 because that's what the
demo showed.

---

## The table

| Technique | What it changes | Cost/mo | Maintenance | Use when |
|---|---|---|---|---|
| **Prompt** | How you ask | ~$0 | Hours | Task is well-specified; the model knows the domain generically |
| **RAG** | What it knows | $50–500 | Weekly doc upkeep | Your knowledge is proprietary and changes often |
| **Fine-tune** | How it behaves | $500–5k | Retrain + eval on change | You need a consistent style/format, or a classification task at volume |
| **Agent** | What it decides | $500–10k+ | Agent eval + guardrails | The task genuinely requires multi-step planning with variable steps |
| **New model** | Its ceiling | $2k–50k | Migration | Nothing above clears the bar |

---

## RAG vs fine-tuning — the question everyone asks

**The distinction that resolves 90% of it:**

| | RAG | Fine-tuning |
|---|---|---|
| Changes | **Facts** | **Behaviour** |
| Updates | Edit a document | Retrain a model |
| Cost to change knowledge | ~$0 | Hundreds–thousands |
| Cost to change style | Won't do it | This is the use case |
| Hallucination risk | Lower (grounds answers) | Can increase (more confident) |
| Auditability | High — you can cite the doc | Low |

> **If your knowledge changes monthly, you want RAG.** Fine-tuning knowledge
> that goes stale is the single most expensive mistake in this table.

**The right sequence:** RAG first. Add fine-tuning *later*, only if you have a
measured quality gap that RAG closed nowhere near — typically a formatting or
tone problem, not a knowledge problem.

---

## Agent or workflow? (Lecture 8's whole argument)

This is the highest-leverage decision on the page, because agents are where
budgets go to die.

**A workflow has a fixed, known sequence of steps. An agent decides its own
steps at runtime.**

| | Workflow | Agent |
|---|---|---|
| Steps | Fixed, known in advance | Chosen at runtime |
| Cost per run | Predictable | Variable |
| Audit | Easy — you can trace it | Hard — depends on model decisions |
| Failure mode | Predictable | Novel, emergent |
| Good for | Most business processes | Genuinely open-ended tasks |

**Decision rule:** if you can write down the steps, write a workflow. An agent
is only justified when the steps genuinely *depend on what the agent discovers
mid-task* — and you should be able to name two or three tasks like that in
your business. If you can't, you want a workflow.

The cost difference is not subtle. A 5-step workflow has bounded token spend.
An agent that loops until it "thinks it's done" can spend 50× that on a single
task, with no upper bound you've specified.

---

## Frontier vs open-source

*Not* "open-source is cheaper." The real comparison:

| | Frontier (closed) | Open weights |
|---|---|---|
| Best quality | ✅ Highest | Gap varies, narrowing |
| Data privacy | ❌ Your data leaves the building | ✅ Runs inside your VPC |
| Customisation | Prompt + RAG only | Fine-tune, quantise, distil |
| Ops burden | None | You own GPUs, serving, patching |
| Regulatory defensibility | Weak | Strong |

**The decision hinges on one question: can your data leave the building?**

- **Yes** → frontier. You will not out-engineer a frontier lab's serving
  stack, and paying to do so is a bad use of engineering time.
- **No** (healthcare, legal, defence, most financial services) → open weights
  are not an optimisation choice, they're a constraint. Plan for the ops cost
  from day one.

The trap: choosing open weights for "cost reasons" without counting GPU
engineer-hours. A model that costs $0 per API call and 2 FTE to serve is
expensive.

---

## The scaling laws, briefly

Quality per dollar improves fast for frontier models and then flattens. The
practical implication for leaders:

> **Don't build your strategy on a specific model's capability. Re-evaluate
> model choice every quarter.**

Teams that picked a model 18 months ago and never revisited are leaving
performance on the table. Teams that chase every new release are shipping
nothing. The discipline is: revisit on a fixed quarterly cadence, change only
if the gap is material to your measured workload.

---

**Last updated:** 2026-10-21
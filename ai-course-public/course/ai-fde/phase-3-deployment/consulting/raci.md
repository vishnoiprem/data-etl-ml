# RACI matrix — PacificFreight drafter

> **Owner:** Sarah (ops manager). **Last reviewed:** 2026-10-09. **Re-review:** quarterly, or after any FDE transition.

This is the decision-rights matrix for the PacificFreight drafter. For each of the 12 artifacts, the matrix names who is **R**esponsible (does the work), **A**ccountable (signs off — exactly one A per row), **C**onsulted (asked before the change), and **I**nformed (told after the change). The matrix is the C1 stakeholder map made operational.

---

## The 4 stakeholders

| Symbol | Name | Role |
|---|---|---|
| **Mei** | Mei Tanaka | CS lead. Daily user. Signs off on prompt voice and draft quality. |
| **Sarah** | Sarah Lim | Ops manager. Reviews success metrics weekly. Signs off on scope and GO/NO-GO. |
| **Daniel** | Daniel Ng | IT owner. Owns the VM, the model choice, the cost ceiling, the security policy. |
| **FDE** | (rotating) | Forward-deployed engineer. Owns the build, the eval set, the runbook during the build period. |

The FDE column changes when an FDE exits. The other 3 are stable for the life of the drafter.

---

## The 12-artifact matrix

| # | Artifact | Mei | Sarah | Daniel | FDE |
|---|---|---|---|---|---|
| 1 | **Prompt** (`service/rag.py::build_rag_prompt`) | **R, A** | C | I | C |
| 2 | **Eval set** (`shared/eval_set.jsonl`) | C | **A** | I | **R** (during build) / Mei (post-handoff) |
| 3 | **Baseline** (`shared/baseline.jsonl`) | I | **A** | I | **R** |
| 4 | **RAG index** (corpus: policy + shipments) | C | I | **A, R** | C |
| 5 | **Model choice** (`PF_MODEL` env var) | I | C | **A, R** | C |
| 6 | **Cost ceiling** ($5/month) | I | C | **A, R** | I |
| 7 | **VM / infrastructure** | I | I | **A, R** | I |
| 8 | **Deployment** (CI/CD, when to push) | I | I | **A, R** | C |
| 9 | **Monitoring** (`/metrics` dashboard, alerts) | C | C | **A, R** | I |
| 10 | **Runbook** (`consulting/04-runbook.md`) | C | C | **A, R** | **R** (during build) |
| 11 | **ADR log** (`decisions/ADR-NNNN.md`) | C | C | I | **R, A** |
| 12 | **Style guide** (source of truth for prompt voice) | **R, A** | I | I | C |

**The matrix has exactly one A per row.** If a row has 0 A's or 2 A's, the decision-right is ambiguous — fix it before the next SEV.

---

## Row-by-row rationale

### 1. Prompt

**A = Mei.** Mei is the operator. The prompt wording is what she sees in the drafter. She signs off on tone, voice, and what "polite" means in Vietnamese vs English.

**R = Mei.** She writes the prompt (with FDE consultation during the build).

**C = Sarah, FDE.** Sarah consults because the prompt affects the success metric. The FDE consults because they wrote the original.

**I = Daniel.** Daniel is informed but does not approve prompt wording.

### 2. Eval set

**A = Sarah.** The eval set is the spec for "good." Sarah signs off on what "good" means.

**R = FDE (during build) / Mei (post-handoff).** During the build, the FDE writes the rows (with Mei's input from thumbs-down notes). Post-handoff, Mei owns the rows.

**C = Mei.** Mei provides the qualitative signal (thumbs-down notes) that become the new rows.

**I = Daniel.** Daniel is informed but does not approve eval set rows.

### 3. Baseline

**A = Sarah, R = FDE.** The baseline is the frozen eval-set run that defines "last week's good." Sarah signs off because it defines the regression threshold. The FDE writes it.

### 4. RAG index

**A, R = Daniel.** The RAG index lives on the VM. Daniel owns the infrastructure. Mei and FDE are consulted when new content is added (e.g., a new style guide section).

### 5. Model choice

**A, R = Daniel.** The model is a deployment decision. Daniel picks the model, the cost ceiling, and the provider. Sarah is consulted because the model choice affects the success metric.

### 6. Cost ceiling

**A, R = Daniel.** The cost ceiling is a deployment decision. Sarah is consulted because the ceiling affects scope (e.g., "we can't add Mandarin because the cost would 3×").

### 7. VM / infrastructure

**A, R = Daniel.** Mei, Sarah, and the FDE are not in the loop. The VM is Daniel's domain.

### 8. Deployment

**A, R = Daniel.** When to push is a deployment decision. FDE is consulted during the build (they write the code). Mei and Sarah are informed after the deploy.

### 9. Monitoring

**A, R = Daniel.** The `/metrics` dashboard and the alerts are infrastructure. Mei and Sarah are consulted on what metrics matter (e.g., "P95 latency is the patience ceiling — alert at 4s").

### 10. Runbook

**A, R = Daniel.** Daniel is the on-call engineer; he owns the runbook. The FDE writes it during the build (R), then hands it off. Mei and Sarah are consulted on the SEV definitions.

### 11. ADR log

**R, A = FDE.** The FDE writes the ADR for every shipped change. Post-handoff, the FDE column is empty — the next FDE inherits the log. Mei, Sarah, Daniel are consulted on the change before it's written; informed after.

### 12. Style guide

**A, R = Mei.** The style guide is Mei's source of truth. The prompt derives from the style guide. The FDE consults because they translate the style guide into the prompt.

---

## The 4 anti-patterns the matrix prevents

### Anti-pattern 1: "Mei changed the prompt and Daniel didn't know"

If Mei changes the prompt and Daniel is not informed, Daniel finds out when `/metrics` shows a quality shift. **Fix: the I column.** Daniel is in the I column for the prompt. After Mei's change, an automated email goes to Daniel. The next FDE wires this into the prompt-change CI step.

### Anti-pattern 2: "Daniel deployed a new model and Mei found out from a thumbs-down"

If Daniel changes the model without consulting Mei, Mei sees the quality shift in the next hour. **Fix: the C column.** Sarah is in the C column for the model. Sarah asks Mei "is this OK?" before Daniel deploys.

### Anti-pattern 3: "The eval set grew to 100 rows and nobody owns pruning it"

If the FDE added 70 rows during the build, the eval set is now bloated. **Fix: the A column.** Sarah is the A. Sarah reviews the eval set quarterly and prunes the rows that no longer represent a meaningful failure mode.

### Anti-pattern 4: "FDE exited and the runbook is 2 years old"

If the FDE exited without running the fire-drill, the runbook is fiction. **Fix: the R column shift.** When the FDE exits, the R for the runbook shifts from FDE to Daniel. Daniel re-reviews quarterly. The next FDE inherits a current runbook or updates it as their first act.

---

## How to use this matrix

When you're about to make a change, ask:

1. **What artifact am I changing?** Find the row.
2. **Am I the A?** If yes, you sign off. If no, you need the A's sign-off.
3. **Am I the R?** If yes, you do the work. If no, the R does the work.
4. **Who is in the C column?** Those are the people I need to ask *before* I make the change.
5. **Who is in the I column?** Those are the people I email *after* I make the change.

If you can't answer #2 cleanly, the matrix is wrong — update it before you make the change. **A matrix that doesn't change with the project is a matrix nobody reads.**

---

## Re-review schedule

- **Quarterly:** Sarah reviews every row. Confirms the A's are still in their roles.
- **On FDE transition:** The incoming FDE reads the matrix on day 1. If the FDE column needs updating, do it before the first experiment.
- **On any SEV:** Daniel reviews the row that failed. If the RACI was unclear, update it in the postmortem.

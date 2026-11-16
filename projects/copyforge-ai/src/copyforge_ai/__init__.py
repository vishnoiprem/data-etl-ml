"""CopyForge AI — insert high-performing copy structures into a draft.

The pipeline is four steps, and the division of labour between them is
the design:

1. **Analyse** (`markdown.analyze`) — read the draft and work out what
   copy structures it is missing.
2. **Plan** (`planner.plan_copy`) — decide which framework fills which
   gap, and where in the article it belongs. Pure Python, deterministic,
   explainable.
3. **Write** (`writer.write_article`) — ask a local model for the words,
   and splice them into the draft. The author's own prose is never
   rewritten.
4. **Score** (`scoring.score_document`) — measure the result on a
   structural rubric, so the improvement is a number rather than a
   claim.

**The model is not in the decision path.** It writes. The plan decides
what gets written and where. That split is what makes the output
reproducible, the tests hermetic, and the decisions auditable.

Nothing here needs the network. The Ollama backend is optional; without
it the pipeline runs on a deterministic stub that produces real copy
rather than a placeholder.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]

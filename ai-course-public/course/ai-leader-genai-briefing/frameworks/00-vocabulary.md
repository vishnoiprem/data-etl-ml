# The Leader's Vocabulary

> **Section 1 vocabulary primer.** Maps to *Core AI Terms* (18:05),
> *Your Path to Driving Real AI Impact* (3:42).
>
> One page. For the leader who is the smartest person in the room on their
> business and the least informed on AI. There is no shame in this; the
> reverse is much more common.

---

## The one-sentence definitions

Every AI term you will be asked about, defined precisely enough to make a
decision and no further.

**LLM (Large Language Model).** A program trained to predict the next word
in text. It does this extraordinarily well, and that turns out to be enough
to do most of the things we mean when we say "AI." Today's frontier LLMs can
read, write, summarise, classify, reason step-by-step, write code, hold a
multi-turn conversation, and refuse to answer. They cannot browse the live
web unless given a tool that lets them, count their own tokens, or know
anything trained past their cut-off date.

**Transformer.** The architectural pattern almost every modern LLM is built
on. It matters because it scales — bigger models get predictably better, and
that predictability is the *scaling law* that justifies current investment.
You do not need to know the inside of a transformer; you need to know that
"bigger / more compute / more data" has been getting us quality gains since
2018 and shows no sign of stopping.

**Foundation model.** A large model that another system builds on top of, as
opposed to a model trained from scratch for one task. Most of what you are
buying when you buy "AI" is foundation models plus retrieval data plus
prompts.

**Gen AI (Generative AI).** AI that produces new artefacts — text, images,
video, code, structured data. Today's commercial story. The previous
decade's "AI" was almost entirely *predictive* — classification, ranking,
forecasting. Generative changes the budget math because generation is
expensive per call but cheap per artefact.

**Prompt.** The text you give the model. Increasing the quality of the
prompt is the highest-leverage activity in any LLM application and the one
most teams under-invest in.

**Tokens.** The units the model reads and writes. A rough conversion: 1
token ≈ ¾ of an English word. Models bill per token; agents burn tokens
quickly because they make many LLM calls per task.

**Context window.** The maximum text a model can hold in one call. Bigger
is better but costs more per call and slows the model. Don't fill the
context window "because you can" — overstuffing is one of the most common
production bugs.

**Temperature.** The model's "creativity" dial. 0 means almost always pick
the highest-probability next token (deterministic). 1 means sample from the
distribution (varied). For business tasks, lower is almost always right;
higher is for brainstorming. If your invoice-classifier gives three different
answers on three runs, temperature is set too high.

**Hallucination.** The model asserting something it does not know. The
single biggest failure mode business users see. **Mitigation is structural,
not magical**: ground the model in documents (RAG), ask it to cite, keep
humans in the loop on consequential decisions. There is no model update that
ends hallucination.

**Fine-tuning.** Training an existing model on your data to change *how*
it behaves. Expensive and rarely the right answer for the first version of
a workflow (RAG almost always is). The shortcut for "we want consistent
format / tone / terminology."

**RAG (Retrieval-Augmented Generation).** Give the model the relevant
documents before you ask the question. The cheap way to make a model know
your knowledge. Updateable by editing a document, not retraining.

**Agent.** A program that takes a goal and decides its own steps to reach
it, using tools and multiple model calls. Powerful for genuinely
open-ended tasks. Expensive and harder to audit than a workflow that has
fixed steps. Use sparingly.

**Eval (evaluation).** Automated tests that measure whether the model is
producing the right output. The single biggest predictor of whether an AI
project ships safely. Most teams under-invest in evals by a factor of 10.

**Guardrails.** Constraints the system enforces around the model — what's
allowed, what's logged, what requires human approval. Not the model's
"rules" — actual code around the model.

**Inference cost.** The price of running the model on a single request.
Frontier models: ~$0.001–$0.06 per call depending on size. Cost per
artefact matters more than cost per call: a model that costs more but
finishes the task in fewer calls is cheaper overall.

**Cut-off date.** The last date the model's knowledge reflects. Anything
younger must be supplied by RAG or a tool. This is why "real-time" AI uses
tools — the model itself is frozen in time.

---

## The two ideas that matter most

If you absorb nothing else from this page, absorb these.

### 1. The model is the cheap part.

The expensive part of an AI application is everything around it — the data,
the evals, the integration, the human-in-the-loop, the change management.
Teams that pay attention to "which model" and skip these other layers ship
projects that work in a demo and don't in production.

### 2. Capability gains come in waves; prepare for the next one.

Today's frontier is a snapshot. Six months ago the best models were notably
weaker; six months from now they will be notably stronger. **Do not lock your
architecture into a specific model's capabilities.** Build so that upgrading
the model is a config change, not a rewrite.

---

## Three questions to ask a vendor in 30 seconds

1. **"What's your cost per task at 10,000 users, in their unit economics,
   not yours?"** If they hedge, the unit economics are bad.
2. **"What's your eval set, and what does it look like in production?"** If
   they don't have one, they have not shipped.
3. **"Where does a human have to be in the loop for this to be safe?"** If
   the answer is "nowhere," either the task is trivial or the vendor hasn't
   thought it through.

---

**Last updated:** 2026-10-21
# Lesson 02 — Asking Better Questions

> **The 5-question framing framework.** 30 minutes. No code.

By the end of this lesson you can take a vague "use AI for X" request from a customer and turn it into a **testable scope** in 30 minutes. You have a 5-question framework, a worked example for PacificFreight, and the start of the 1-pager that you will finish in lesson 04.

---

## 🎯 Outcome

You produce **one artifact**:

- `framing-notes.md` — a 1-page markdown document with the 5 questions answered for PacificFreight, ready to be polished into the 1-pager in lesson 04.

When you finish, you can walk into a customer meeting, ask the 5 questions in order, and walk out with a draft scope.

## 🧠 Mindset

Most customer "AI" asks sound like:

> *"Can you use AI to handle our customer emails?"*

That sentence is **useless as a brief**. It has no user, no job, no success metric, no cost ceiling, no risk. You cannot build from it. If you try, you will build the wrong thing.

The FDE's job is to ask the 5 questions that turn that sentence into a buildable scope:

1. **Who** is the user (in their own words)?
2. **What** are they trying to do, end to end?
3. **What is the bottleneck** — the step that is most painful, slow, or error-prone?
4. **What would "fixed" look like** — measured how, by when?
5. **What is off the table** — what you will NOT do, even if asked?

If the customer can answer all 5, you have a scope. If they can't, you have more questions to ask.

> **FDE rule:** never start building from a brief that can't answer all 5 questions. If the customer can't answer them, schedule another meeting. The week you "just start" is the week you build the wrong thing.

## 🛠️ Practice

### The 5-question framework

For each question, I give the **question you ask**, the **why you ask it**, and a **red flag** that means you need to dig deeper.

#### Q1 — Who is the user?

> *"Who, specifically, is affected by this? Not 'the company' — a person, with a name, doing a job."*

**Why:** "User" is the most over-used word in AI briefs. If you don't know the user, you don't know what success looks like.

**Red flag:** the customer says "everyone." That means they haven't thought about it. Push back: "if you had to pick the one person who feels this pain most, who is it?"

#### Q2 — What are they trying to do?

> *"Walk me through the whole job, start to finish. Not just the AI-shaped part — the whole thing."*

**Why:** you need the *end-to-end* job, not just the part the customer thinks AI can solve. Often the AI-shaped part is downstream of a step you didn't know about, and the upstream step is the real bottleneck.

**Red flag:** the customer describes only the AI-shaped part ("summarize this email"). Ask "what do they do with the summary? What happens next?" The answer changes the tool.

#### Q3 — What is the bottleneck?

> *"Of all the steps you just described, which one is the most painful? Where does the time go? Where do errors happen?"*

**Why:** the bottleneck determines the tool. If the bottleneck is *retrieving* information, the tool is RAG. If the bottleneck is *writing*, the tool is a drafter. If the bottleneck is *deciding*, the tool is a classifier. Different bottlenecks, different tools.

**Red flag:** the customer says "all of it." That usually means they haven't measured. Push for: "if you had to time one step, which would it be?"

#### Q4 — What would "fixed" look like?

> *"How will we know, in 4 weeks, that this worked? What is the number that moves?"*

**Why:** if you can't measure success, you can't ship. A good success metric has a **number**, a **direction**, and a **timeframe**. "CS time per email goes from 5 min to 30 sec within 4 weeks" is a good metric. "Make CS happier" is not.

**Red flag:** the customer gives a vanity metric ("we want to be known as an AI-forward company"). That's a marketing goal, not a success metric. You need both, but the success metric for the tool is operational.

#### Q5 — What is off the table?

> *"What is one thing I should NOT do, even if it would be cool?"*

**Why:** every scope creep starts with "while you're at it, can you also..." The way to prevent it is to write down what is OFF the table in week 1. The customer can override later, but they have to override explicitly.

**Red flag:** the customer says "nothing is off the table." That means they haven't thought about risk. Push for: "what would embarrass you if the tool did it wrong?"

### Worked example — PacificFreight

You walk into the ops manager's office on day 2. The conversation:

> **You:** "Tell me about the email thing."
>
> **Sarah (ops):** "We get 150 'where is my parcel?' emails a day. Each one takes my CS team 4-7 minutes. We want to use AI to draft replies."
>
> **You:** "OK, let me ask 5 questions. First: who specifically feels this pain?"
>
> **Sarah:** "Mei — she's the CS lead. She and her team are the ones drafting."
>
> **You:** "What is Mei trying to do, end to end, when one of these lands?"
>
> **Sarah:** "Read the email, look up the shipment in the PHP tracker, draft a reply in our voice, copy-paste into Gmail, send. 4-7 minutes."
>
> **You:** "Of those 4 steps, which one is the bottleneck?"
>
> **Sarah:** "The drafting. The lookup is fast — 20 seconds. The drafting is the slow part. They rewrite every reply because they're scared of sounding robotic."
>
> **You:** "How will we know in 4 weeks if we fixed it?"
>
> **Sarah:** "If the per-email time drops below 1 minute and Mei's team says the drafts are usable 80% of the time as-is."
>
> **You:** "What is off the table?"
>
> **Sarah:** "Auto-sending. Never. We are not putting AI in front of customers without a human review. And no refunds — that's a manager decision."

You now have a scope. In `framing-notes.md`:

```markdown
# PacificFreight — Framing notes (lesson 02 draft)

## Q1 — Who is the user?
Mei (CS lead) and her 2-person CS team. They draft 150 emails/day.

## Q2 — What are they trying to do?
Read inbound email → look up shipment in PHP tracker → draft reply
in PacificFreight's voice → copy-paste into Gmail → send.

## Q3 — What is the bottleneck?
The DRAFTING step. Lookup is fast (~20s). Drafting is 4-6 of the
4-7 minutes per email. Root cause: fear of sounding robotic.

## Q4 — What would "fixed" look like?
- Per-email time: from 4-7 min to <1 min
- As-is ratio (drafts sent without edits): ≥80%
- Measured over a 2-week pilot, starting in week 3

## Q5 — What is off the table?
- Auto-sending without human review (never)
- Refund or credit decisions (manager-only)
- Replacing the PHP tracker (separate engagement)
- Multi-language reply generation (Phase 2+)
```

That is the 1-pager in draft form. Lesson 04 polishes it.

### A second example — a different customer (no real example, just for practice)

Imagine a logistics customer who says "we want AI to predict late deliveries." Run the 5 questions:

1. **User:** the ops manager? the customer? the CS team? — *all three feel pain, but the tool is different for each*
2. **Job:** what does each of them do today when a delivery is at risk? — *probably nothing, the customer finds out at 3pm on delivery day*
3. **Bottleneck:** getting the prediction, or acting on it? — *acting on it — the data is in the tracker, the workflow is missing*
4. **Success:** "we call customers before the delivery date" — what % of late deliveries, by when? — *30% of late ones contacted ≥2 days before, within 4 weeks*
5. **Off the table:** don't change the carrier; don't promise refunds based on prediction; don't add a customer-facing UI in Phase 1

Notice how different the scope becomes when you force the customer to answer all 5.

## 🏛️ FDE Lens — the technical reality underneath

Each of the 5 questions has a technical consequence:

| Question | Technical decision it drives |
|---|---|
| Q1 (who) | Determines the UI surface (terminal? web? Slack? email plugin?) |
| Q2 (what) | Determines the system boundaries (read-only? write-and-send?) |
| Q3 (bottleneck) | Determines the architecture (RAG? agent? classifier? drafter?) |
| Q4 (success) | Determines the eval harness (what to measure, what "good" means) |
| Q5 (off the table) | Determines the deployment story (where it runs, who can use it) |

When the customer says "I want AI to do X," these are the 5 questions that turn X into a buildable spec. Skip them and you will build for 4 weeks, demo to the customer, and hear "no, that's not what I wanted."

## 🌙 Reflect

Write 3-5 sentences:

1. Why is "everyone is the user" a red flag, not just an unhelpfully broad answer?
2. Q5 ("what is off the table?") feels confrontational. Why ask it in week 1, when the customer is most excited about the project?
3. The "as-is ratio" in Q4 is the single most important number in the engagement. Why is it 80% and not 100%?
4. A customer says: "I just want you to use AI to make our customer service better." Walk through how you would ask the 5 questions without making them feel interrogated.

**What's next** — Lesson 03 introduces the **prompting patterns and APIs** you will use in the technical track. The 5 questions from this lesson tell you *what* the tool is; lesson 03 starts teaching you *how* to talk to the model so it actually does the job. The 1-pager is finished in lesson 04.

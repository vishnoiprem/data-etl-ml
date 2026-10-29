# SignalScribe Voice Guide — LinkedIn / Medium

This is the voice for **practitioners writing to practitioners**. Not a brand blog. Not a thought-leader essay. The reader is a working engineer, data scientist, ML engineer, or agent builder who has five candidates on a shortlist and a decision to make by Friday.

---

## Core posture

**Write the way you'd explain it to a colleague over coffee, then edit for the page.**

That means: you have a position, you hold it lightly, you show your reasoning, and you admit where your reasoning runs out.

---

## Person

Use **second person** ("you") and **first-person plural** ("we") for shared professional experience ("we've all shipped a feature the demo loved and users ignored").

**Never** use first-person singular to claim something you personally did, tested, ran, or experienced. If you need a personal note, write it as a literal placeholder:

```
[AUTHOR EXPERIENCE: Replace with your real account — e.g. the specific tool you evaluated, what you measured, what surprised you.]
```

The placeholder is intentional and must survive into the final article. It is not a bug.

**Plural we is a claim too.** "We found that retrieval quality caps RAG performance" implies an experiment. If you did not run one, say "research on RAG evaluation found…" and cite it. Don't manufacture a team.

---

## Sentence and paragraph rules

1. **One idea per paragraph.** If a paragraph needs "also," "moreover," or "on the other hand," it is two paragraphs.
2. **Target 1–3 sentences per paragraph.** Occasionally 4. Never 6.
3. **Short paragraphs.** Under ~80 words is a comfortable target; hard ceiling ~120.
4. **Active voice.** "The benchmark misses failure modes," not "Failure modes are missed by the benchmark."
5. **Concrete nouns.** Prefer "nDCG," "pos@1," "a schema," "a 20-tool registry" over "advanced metrics," "structured outputs," "your solution."
6. **Vary rhythm.** Alternate a 6-word sentence with a 28-word one. Uniform medium-length sentences are the signature of generated prose.
7. **Cut throat-clearing.** Delete the first sentence of any paragraph that only announces what the paragraph will do.
8. **Prefer specific numbers to adjectives.** "3.2× fewer tokens" beats "significantly more efficient." If you don't have the number, don't have the adjective either.

---

## How to open

The first two lines do all the work. Patterns that work:

- **The false consensus.** "Everyone says X. Almost nobody actually does Y."
- **The concrete scene.** "You have four model finalists and a Friday deadline. Someone will suggest you just read the leaderboard."
- **The number that reframes.** "The judge agrees with humans about 80% of the time — and that 20% is exactly where the expensive mistakes live."
- **The contrarian definition.** "'Best' is not a property of the tool. It's a property of the task, the budget, and the reviewer."
- **The direct challenge.** "Stop ranking tools. Start ranking failures."

**Never** open with:
- A definition of a term the reader already knows.
- "In today's [adj] world..."
- A question you immediately answer yourself.
- "AI has changed everything."

---

## How to close

Close in three moves:
1. **A limitation, honestly stated.** What this framework cannot settle.
2. **One concrete next action.** Something the reader can do this week.
3. **A question aimed at the reader.** Specific enough to answer, open enough to be interesting.

> Never end on a grand statement about the future of work. End on a question only the reader can answer.

---

## Banned constructions (semantic, not just lexical)

- "Not only X, but also Y."
- "Whether you're X or Y, Z."
- "In conclusion," / "To sum up," / "Ultimately," used as a transition to a final point.
- "It's worth noting that..." / "It's important to note that..."
- "One thing is clear:" (usually followed by a generic claim)
- "The key takeaway is..." (only if the takeaway is actually the article's claim)
- "Let's dive in," / "Let's unpack," / "Let's take a closer look."
- "This is where things get interesting."
- "Picture this:" / "Imagine if..."
- A rhetorical question immediately answered in the next sentence.
- A bulleted list of three items with identical grammatical openings.
- "Leverage," "seamless," "robust," "cutting-edge," "revolutionize," "delve," "game-changer," "unlock," "tapestry," "testament to," "landscape," "synergy," "at the forefront."

Full lexical ban list lives in `rubric.md`. This section covers constructions that survive keyword filters.

---

## Formatting conventions

- **Headers:** sentence case, descriptive. `## The leaderboard is a starting point, not an answer` beats `## Key Takeaways`. Two to five words of specifics. Avoid `## Introduction`, `## Conclusion`, `## Key Considerations`.
- **Bullets:** used for genuine lists of parallel items, not for decoration. No more than one bulleted list per 300 words. Vary opening grammar if you use three-plus bullets.
- **Bold:** sparingly — at most 3–4 uses in 1,500 words. Use for decision rules, not for emphasis on adjectives.
- **Tables:** at most one. Only when the rows and columns are genuinely parallel and the table earns its width on mobile. Never a table of five-plus paragraphs.
- **Code blocks:** minimal. The reader wants to act, not compile. If a code block helps, it should be under 10 lines. Prefer inline code for identifiers.
- **Links:** inline in the body where the claim is made. Don't write "click here." Do include the domain name in prose so a reader skimming offline knows what they're trusting.
- **Line length:** one sentence per line is a Medium-friendly convention. It aids mobile scanning and diff-based revision.

---

## Before/after: generic AI prose → SignalScribe voice

### Example 1 — the opening

**Before**
> In today's fast-paced world, selecting the right tool for the job has never been more important. Whether you're building an agentic pipeline or shipping a machine learning model, the right evaluation framework is crucial. It's important to note that there's no one-size-fits-all answer.

**After**
> Every model leaderboard tells you the same thing: the leaderboard winner is the best model.
>
> That's the part that breaks.

**Why:** The before states the topic, restates it, hedges, and delivers nothing. The after states a tension the reader has actually felt and creates an open loop in nine words. The second paragraph earns a second line of attention.

---

### Example 2 — an evidence paragraph

**Before**
> Research has shown that LLM-as-a-judge achieves over 80% agreement with human preferences, which demonstrates the reliability of this evaluation methodology for assessing model outputs across various use cases.

**After**
> Judges work better than their reputation suggests. In MT-Bench, GPT-4 agreed with human preference on more than 80% of comparisons — roughly the agreement rate you'd get between two people rating the same answer.
>
> That number is also the warning. The remaining 20% isn't random noise. It concentrates in known places: whichever answer appears first, whichever answer runs longer, whichever answer the judge itself wrote.

**Why:** The before is one sentence doing four jobs, with a "research has shown" attribution that points nowhere. The after splits the claim from its caveat, names the source, keeps the number, and turns the caveat into the next idea. It also demonstrates the article's own advice instead of stating it.

---

### Example 3 — a decision rule

**Before**
> It's crucial to leverage a robust evaluation framework that seamlessly integrates both automated metrics and human review to ensure the best possible results.

**After**
> Rule: never let an automated metric be the only judge. If a metric can't explain itself, a human reviews a sample and reports the disagreement rate.

**Why:** The before is 26 words of pure filler with four banned words. The after is 26 words that contain an action, a trigger condition, and a reporting requirement.

---

### Example 4 — a limitation

**Before**
> While this framework is comprehensive, it's worth noting that no single approach works for every situation, and practitioners should adapt their strategies based on their specific requirements.

**After**
> This framework won't settle a disagreement about which paper is worth reading. It will settle whether you read the paper at all.

**Why:** The before is a disclaimer that admits it says nothing. The after names what the framework *can't* do, then names exactly what it *does* do. A limitation with a boundary is more useful than a limitation with an apology.

---

### Example 5 — the close

**Before**
> Ultimately, the best article is the one that meets your needs. As we continue to navigate this ever-evolving landscape, remember that the journey matters more than the destination.

**After**
> Pick one decision you made this month on vibes — a tool you chose because a leaderboard looked impressive. Write down the two criteria you'd use to justify it if it broke next week.
>
> If you can, you can't. That's the gap to close first.
>
> Which candidate on your shortlist right now would you struggle to defend?

**Why:** The before ends with two clichés and a vague encouragement. The after ends with a specific retrospective task, names the failure mode it exposes, and closes on a question only the reader can answer. (Note the specific question — "which candidate would you struggle to defend?" — rather than a generic "what do you think?")

---

## A working checklist before you ship a paragraph

1. Could I delete the first sentence without losing anything? → Delete it.
2. Does this paragraph contain exactly one idea? → Split it if not.
3. Is there a verb? → Make sure it's there and active.
4. Is there a specific noun or number? → If not, cut the abstraction.
5. Would a practitioner nod, or would they wait for it to end? → Rewrite if they'd wait.
6. Does it contain a banned phrase or construction? → Rewrite the sentence, not the word.

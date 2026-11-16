# RRK Spoken Delivery: How to Say It, Where to Pause, When to Stop

**Role:** Data & Analytics Lead, Google Cloud Consulting (Singapore) | Round 1 RRK, 60 min, virtual
**Purpose:** the other files say *what* to say. This one says *how*. The model answers in `ROUND_1_RRK.md` average 350 words; 21 of 35 run past two minutes aloud, and Q7 alone is four and a half minutes. Interviewers stop listening at two. These are 90-second spoken scripts for the ten highest-probability questions, with pause marks, stress and stop points, plus the rules that make an answer sound like a person who has done the work rather than a person who has read about it.

> **Public repo.** No employer names, customer names or real figures beyond those on the public resume. Figures marked *(resume)* come from it; figures in an *illustrative* line are placeholders with the right shape: make them real or cut them.

---

## 1. The notation

| Mark | Meaning |
|---|---|
| `//` | short pause, about half a second: a breath, a comma you can hear |
| `///` | long pause, one to two seconds: let the point land, make eye contact with the camera |
| **bold** | stress this word; land on it, slightly slower |
| `[slow]` `[normal]` `[quicker]` | pace change until the next mark |
| `⏹ STOP` | stop talking. Do not fill the silence. Let them probe. |
| `↳` | what to do if they interrupt or push here |

Pace: about 130 words a minute. 90 seconds is roughly 200 words. Every script below is 170 to 220 words.

---

## 2. Twelve delivery rules

1. **Restate in one sentence, then pause.** "So the question is whether the date or the scope moves. `///`" The pause is where they correct you if you've misheard. It also buys you three seconds to think.
2. **Signpost with numbers, not "and then".** "Three things. `//` One `//` ..." People can follow three. They cannot follow "and also".
3. **Land the outcome first, then earn it.** In a behavioural answer, the first sentence after the restate is the result with a number. Then the story.
4. **One idea per breath.** If you need two breaths for a sentence, it's two sentences.
5. **Stress the trade-off word.** "I chose B `//` **because** `//` the team had no platform headcount." The *because* is what they're grading.
6. **Numbers get a pause on both sides.** "The close went from `//` **five days** `//` to **two hours** `//` measured by finance sign-off time."
7. **Stop at the recommendation.** Say the recommendation, say the risk, say the measure, stop. Do not add "and also we could...". The silence after a clean stop is confidence; filling it is anxiety.
8. **Never say "um" to think. Say nothing.** A two-second silence reads as thought. "Um, so, like, basically" reads as bluffing.
9. **Say "I don't know" in five words, then bridge.** "I haven't run that in production. `//` Here's how I'd reason about it." Then reason. Interviewers at this level reward this and punish the bluff every time.
10. **"I", not "we", for decisions. "We" for the build.** "My team built it. `//` I made two calls that made it stick."
11. **When interrupted, stop mid-word.** Don't finish the sentence. Say "Yes" and answer the new question. You can return: "Coming back to the earlier point for ten seconds..."
12. **Virtual delivery.** Camera at eye level; look at the lens when landing a point, not at your own picture. Notes are fine: one page, large font, bullets only, below the camera. Say "let me think for a second" when you need to glance at them. Nobody minds.

---

## 3. The scripts

### 3.1 Opening: "Walk me through your background and why this role" (90 s)

> `[normal]` Fifteen years in data `//` the last eight leading platforms. `//` A VP role at a large e-commerce group `//` where I built a real-time logistics data platform processing over a hundred million events a day *(resume)*. `//` Then head of data engineering at a multi-country retail group `//` where I own data, analytics and AI strategy `//` and a **thirty-person** organisation *(resume)* across four domain squads. `///`
>
> `[slow]` The outcome I'd point to: `//` month-end financial close went from **five days** `//` to **two hours** *(resume)* `//` measured by the finance team's sign-off time `//` **because** we put reconciliation inside the pipeline `//` instead of in a spreadsheet afterwards. `///`
>
> `[normal]` Why this role. `//` I've been the customer in three large platform programmes. `//` I know where consulting engagements fail `//` which is **after** the architecture is right `//` and **before** the operating model exists. `//` I want to do that work across many enterprises instead of one. `///`
>
> `[slow]` And I'll be honest about the gap: `//` my production depth is on other clouds. `//` I've been closing it deliberately `//` and I'd expect to certify in my first quarter. `//` ⏹ STOP

**↳ "Which part was you?"** "Two decisions. `//` Reconciliation goes in the pipeline, not the close process. `//` And finance owns the metric definitions, not my team. `//` My team built it; those two calls made it stick." ⏹

**Why 10/10:** one number with its method; a reason for Google nobody else gives; the gap named before it's asked; stopped at 90 seconds.

---

### 3.2 Technical: "Late events and duplicates are corrupting aggregates at 10B rows a day" (90 s + probes)

> `[normal]` Let me restate: `//` the aggregates are wrong, and we don't yet know whether that's a **count** problem `//` double counting `//` or a **state** problem `//` an old update overwriting a newer one. `///` Can I ask two things? `//` Are the duplicates exact, same event ID `//` or near-duplicates, same business key, different payload? `//` And what's the lateness at **p99**, not the mean? `///`
>
> `[quicker]` If I can't get those, I'll assume exact duplicates from producer retries, and lateness under an hour at p99. `//`
>
> `[normal]` Then three layers. `//` **One**, contain this week: `//` dedupe at the sink with a `MERGE` on a deterministic event key `//` partition-scoped so reprocessing is cheap. `//` **Two**, the source: `//` producers assign a stable event ID and a sequence number `//` so retries are safe. `//` **Three**, the processing: `//` event-time windows `//` watermark and allowed lateness set from that measured p99 `//` and a dead-letter table for anything later `//` reconciled daily. `///`
>
> `[slow]` I'd measure it by duplicate rate at zero `//` and source-to-sink reconciliation within tolerance. `//` The risk: `//` if the producers can't change `//` sink idempotency becomes permanent architecture `//` so I'd design it as such. `//` ⏹ STOP

**↳ "What about Pub/Sub exactly-once?"** "It prevents **redelivery**. `//` It doesn't remove **producer** duplicates; a retried publish is a new message. `//` That's why the event ID has to come from the producer." ⏹

**↳ "MERGE on 10 billion rows is expensive."** "It is, if it's unbounded. `//` I'd bound the dedup window to, say, 48 hours of partitions `//` `require_partition_filter` on the target `//` and `maximum_bytes_billed` as a guardrail. `//` The question I'd ask is whether we need `MERGE` at all `//` or whether the Storage Write API with offsets gives us idempotent writes for free." ⏹

---

### 3.3 Code review: how to narrate reading code live (first 40 seconds)

The interviewer is grading your *order*, not your speed. Say the order aloud.

> `[slow]` Give me twenty seconds to read it before I say anything. `///` `(read it; actually read it)` `///`
>
> `[normal]` I'll go in this order: `//` correctness `//` idempotency `//` scale `//` semantics `//` security `//` maintainability. `//` And I'll lead with what **loses data**, because that's what I'd block a merge on. `///`
>
> `[slow]` **Two things lose data here.** `//` One: `//` every rerun duplicates every row. `//` The dedup is in memory, per batch `//` and the streaming insert generates a random insert ID per call `//` so nothing matches across a retry. `//` Two: `//` failed rows vanish silently. `//` The insert returns per-row errors `//` and they're ignored `//` and the function reports success anyway. `///`
>
> `[quicker]` Then correctness: unknown currency raises and kills the batch `//` floats for money `//` and `ts[:10]` puts a one-thirty a.m. plus-eight order on the wrong UTC date. `//` Dedup keeps first-seen, so a later version is dropped. `//` Scale: one list, one call, unbounded set. `//` Security: it logs raw rows, that's PII in logs. `///`
>
> `[slow]` The sentence: `//` this is correct on the happy path `//` and **only** if upstream guarantees one delivery and clean data `//` which nothing here enforces. `//` ⏹ STOP

**↳ "Which would you fix first?"** "The silent failure. `//` Duplicates I can find and remove later. `//` Rows that never landed and were reported as loaded, I can't." ⏹

---

### 3.4 Live design: how to narrate while drawing (first 60 seconds, then draw)

> `[normal]` Before I draw: `//` who decides what with this data, and how fast? `///` `(listen)` `//` So the decision latency is the budget. `//` Three numbers I'd want: `//` peak volume `//` freshness SLO `//` and availability. `//` Plus residency and who runs it after go-live. `//` If I can't get them I'll assume `[say your assumptions]`. `///`
>
> `[slow]` I'll draw left to right: `//` sources `//` ingest `//` raw, which is immutable `//` curated `//` serve `//` and governance as a bar across the bottom. `//` Then I'll walk one failure path `//` and tell you the two options I rejected. `///`
>
> `(draw; narrate each box in one sentence as you place it; say what flows on each arrow)`

**Rules while drawing.** Talk slower than feels natural. Name the arrow, not just the box: "transactions, about a thousand a second, into Pub/Sub". When you place governance, name three things: identity on the write path, perimeter, masking. Finish with: "The thing most likely to fail is `//` [X]. `//` I'd detect it by `//` [metric]. `//` Rollback is `//` [one statement or one switch]." ⏹ STOP.

**↳ "Why not [alternative]?"** Never defend. "That works too. `//` I rejected it **because** `//` [one reason tied to their constraint]. `//` If [constraint] changed, I'd reconsider." ⏹

---

### 3.5 Consulting: "A programme is 8 weeks in and off track. First 72 hours?" (90 s)

> `[normal]` I'll take it in three blocks of 24 hours. `///`
>
> **Hours zero to twenty-four.** `//` Listen and get facts. `//` Sponsor `//` delivery lead `//` two engineers `//` the customer's lead. `//` Pull plan versus actuals, the blocker log, the contract scope. `//` I'm separating **symptoms** `//` slipping dates `//` from **causes** `//` unclear scope, unmade decisions, wrong skills, a dependency, a bad estimate. `///`
>
> **Twenty-four to forty-eight.** `//` Diagnose. `//` Classify the causes `//` quantify the gap: done, left, realistic velocity `//` and find the top three blockers and which of them need an **executive** decision. `///`
>
> **Forty-eight to seventy-two.** `//` Reset. `//` The sponsor gets honest status `//` root causes `//` and three options: `//` cut scope `//` add capacity `//` move the date `//` each with cost and risk `//` and my recommendation `//` and the decision I need from them, with a date. `///`
>
> `[slow]` What I won't do: `//` hide the status `//` add people blindly `//` or promise the original date. `///` And I'd measure recovery by plan variance and blocker age `//` and run a short retrospective on how we missed it at week two `//` because the earlier warning is the lasting fix. `//` ⏹ STOP

**↳ "The sponsor refuses all three options."** "Then I ask what they'd accept, `//` and I say plainly which outcome their constraints produce. `//` A decision made with eyes open is theirs to make. `//` One made without the facts isn't." ⏹

---

### 3.6 Behavioural: "Tell me about pushing back on an executive" (STAR, 100 s)

> `[normal]` I'll give you the outcome first. `//` We hit the executive's deadline for the reports that mattered `//` and the close went from **five days** to **two hours** *(resume)*. `//` Here's how. `///`
>
> `[normal]` At a multi-country retail group *(resume)* `//` the CFO wanted the entire legacy finance reporting estate `//` about 180 reports `//` moved to the new lakehouse in **three months**, for year-end. `//` I owned the platform. `//` My estimate said three months covered the critical reports `//` but not all 180 without skipping dual-run across a month-end `//` and skipping dual-run on finance data is how you ship a wrong close. `///`
>
> `[slow]` So I asked one question: `//` **what decision actually needs the full estate by year-end?** `///` The answer was twelve statutory and board reports. `//` Seven percent of the estate. `///`
>
> `[normal]` I brought a one-page plan with three options: `//` all 180, no parallel run, stated risk of a misstated close `//` the twelve in three months with a full dual-run, the rest in two waves over four months `//` or all 180 with six contractors at roughly four hundred thousand extra. `//` I recommended the second `//` and asked the CFO to own the choice of twelve. `///`
>
> `[slow]` Twelve reports live in eleven weeks `//` zero reconciliation differences signed by finance `//` remaining waves done by month seven. `//` The CFO sponsored the next programme. `///` What I'd do differently: `//` I built that one-pager **after** the first tense meeting. `//` I should have walked in with it. `//` ⏹ STOP

*Illustrative, replace with real:* 180, 12, 11 weeks, $400K, month 7.

**↳ "What if the CFO had picked option one?"** "Then I'd have written down the risk, `//` put a reconciliation gate on every report anyway, `//` and delivered. `//` A recommendation, not a veto." ⏹

---

### 3.7 Practice: "Utilisation, margin, capacity: which matters most?" (90 s)

> `[normal]` **Margin.** `///` Because it's the outcome. `//` Utilisation is an input `//` and a healthy utilisation number can hide every leak that kills margin. `///`
>
> `[normal]` Let me put numbers on it. `//` A consultant at two hundred thousand fully loaded `//` about eighteen hundred available hours `//` so roughly a hundred and ten an hour. `//` Billed at two-fifty `//` at seventy-eight percent utilisation `//` that's about forty-three percent margin before overhead. `///`
>
> `[quicker]` Three leaks. `//` **Over-delivery:** sixteen hundred hours worked on fixed price, fourteen hundred recognised `//` utilisation looks fine, margin drops eight points. `//` **Mix:** a senior at one-sixty an hour doing ninety-dollar work `//` margin on that work falls by a third. `//` **Rate:** two-fifty discounted to two-twenty `//` twelve points gone at the same cost. `///`
>
> `[normal]` My band: mid-seventies for seniors, higher for delivery staff `//` with the rest **deliberately** spent on assets, pre-sales and enablement `//` because that's what scales the practice beyond its people. `///`
>
> `[slow]` And the honest line: `//` I've owned a three-million-dollar platform budget and a thirty-person organisation *(resume)* `//` not a consulting P&L. `//` The mechanics transfer. `//` The rate card here, I'd learn in my first thirty days. `//` ⏹ STOP

**↳ "How much over-delivery is acceptable?"** "Any amount decided in advance for a reason. `//` Zero discovered after the fact." ⏹

---

### 3.8 People: "A senior architect is underperforming" (90 s + story)

> `[normal]` Diagnose before I judge. `//` Is it **skill** `//` a gap against the level `//` **will** `//` motivation `//` or **situation** `//` unclear expectations, wrong project, something outside work? `//` And I want evidence against the written bar `//` design quality, delivery, stakeholder feedback `//` not impressions. `///`
>
> `[normal]` Then the conversation: `//` private `//` direct `//` **early**. `//` Here's the bar, here's what I'm seeing, what's your view? `//` And I listen for obstacles I own. `///`
>
> `[quicker]` Then a ninety-day plan with three measurable outcomes `//` a mentor or pairing `//` weekly check-ins `//` written follow-ups. `//` If they improve, I say so publicly. `//` If not, a formal process with HR, with dignity `//` a role change if there's a better fit `//` otherwise a managed exit. `//` And I protect the team's delivery meanwhile `//` because ignoring it costs me the team's trust. `///`
>
> `[slow]` I'll give you one. `//` `(story from ROUND_1_RRK_MOCK_10.md, Round 9 numbered: the squad lead who wanted to be a principal)` `//` What I'd do differently: `//` I waited two quarters to look at the evidence properly. `//` The signal was there after one. `//` ⏹ STOP

---

### 3.9 The gap question: "You've never run production on Google Cloud" (45 s)

Say this one slowly. It is a trust test, not a technical one.

> `[slow]` That's right. `///` My production depth is on two other clouds `//` and I've designed and run the same classes of problem there: `//` streaming at a hundred million events a day *(resume)* `//` lakehouse at ten billion rows a day *(resume)* `//` regulated data across fifteen-plus countries *(resume)*. `///`
>
> `[normal]` What I've done about it: `//` `[the true statement: labs built locally, which services, what's deployed, certification booked for which date]`. `//` What I haven't done: `//` operated a BigQuery estate at scale through an incident. `///`
>
> `[slow]` The architecture logic transfers. `//` The operational scar tissue I'd earn in the first two quarters `//` and I'd be honest with customers about which is which. `//` ⏹ STOP

Never say "built and tested in my own GCP project" unless it is literally true today.

---

### 3.10 Closing: your two questions (60 s)

> `[normal]` Two questions, if there's time. `///`
>
> What separates the practice leads who **thrive** here in their first year `//` from the ones who struggle? `///` `(listen; one follow-up at most)`
>
> And where is the practice tightest right now: `//` pre-sales capacity `//` delivery capacity `//` or reusable assets? `///`
>
> `[slow]` Thank you. `//` What I heard today is a role that's half architect, half practice builder `//` and that's the job I want. `//` ⏹

---

## 4. Cutting a long answer to 90 seconds

For the 21 answers in `ROUND_1_RRK.md` that run over two minutes, apply this in order until you're under 220 words:

1. Delete every sentence that lists a product without a reason.
2. Keep the restate, the options, the recommendation, the risk, the measure. Delete everything else.
3. Move examples to the probe tail: "I can give you an example of that if useful."
4. Keep one number per point. Two numbers in a sentence means one gets lost.
5. Replace "and also" with a full stop.

Priority list: Q7 (581 words), Q23 (558), Q6 (531), Q12 (430), Q13 (413), Q22 (412), Q8, Q21, Q25, Q18, Q16.

---

## 5. The 10/10 checklist, per answer

- [ ] Restated in one sentence, paused
- [ ] Asked one or two clarifying questions, or stated assumptions aloud
- [ ] Outcome or recommendation in the first thirty seconds
- [ ] Every number had a pause on both sides and a method behind it
- [ ] Said "because" at the trade-off
- [ ] Named a risk and a measure
- [ ] Said "I" for the decisions
- [ ] One honest miss or gap, unprompted
- [ ] Stopped under two minutes and let the silence sit
- [ ] Handled the interruption by stopping mid-word

**Practice method:** record every answer on your phone. Listen for three things only: filler words, numbers said without a pause, and whether you stopped or trailed off. Fix those three and the content takes care of itself.

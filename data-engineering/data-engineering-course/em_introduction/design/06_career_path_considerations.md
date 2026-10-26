# 06 — Career Path Considerations (IC vs Manager fork)

> **Lesson 6 of 6 — EM Introduction** · ~15 min (Bonus lesson)

The 4 career archetypes past L5, the IC vs manager fork as a
real decision, how to reverse a manager decision if you make
it and regret it, and 3 real stories of EMs who went back to
the IC ladder.

---

## 1. The 4 career archetypes

Past the L5 / E5 / Senior level, the engineering org splits
into 4 distinct career paths. Most engineers default to the
"people manager" path because it's the visible one — but
the other 3 are real, well-compensated, and often a better
fit.

| # | Archetype | What they do | Why it fits some people |
|---|---|---|---|
| 1 | **People Manager (EM)** | Hire, coach, and grow a team of 4-8 ICs. Write perf packets, run 1:1s, handle conflict. | You find people work energizing, you want to multiply output, you don't need to code daily. |
| 2 | **Tech-Lead Manager (TLM)** | Manage 4-8 ICs *and* stay hands-on technically — design, code review, occasional IC. | You want to stay close to the code but you've outgrown pure IC work; the hybrid is the right shape. |
| 3 | **Tech IC (Staff → Principal)** | Stay IC. Drive cross-team technical direction, set architecture, mentor informally, write the hard RFCs. | You love the technical work, you have a specific area you want to be known for, and people work is a tax. |
| 4 | **Individual-Contributor-Staff / Principal (the deep specialist)** | Stay IC, but narrow and deep. The "tech fellow" or "distinguished engineer" path. | You want to be the deepest expert in a specific area (ML infra, query optimization, distributed systems) and the org is okay with a narrow role. |

The 4 archetypes are *not* a ladder — they're 4 different
ladders, and the moves between them are real but require
deliberate effort. A few patterns worth knowing:

- **Archetypes 1 and 2 share the manager ladder.** The move
  from EM to TLM is lateral; the move from TLM to EM is
  also lateral. The move from either to Director is
  upward.
- **Archetypes 3 and 4 share the IC ladder.** The move from
  Staff to Principal is upward; the move from Staff to
  "tech fellow" is rare and usually only at FAANG-scale
  companies.
- **Cross-archetype moves are real but cost ~12-18 months.**
  Moving from EM to Staff IC means re-establishing your
  technical credibility. Moving from Staff IC to EM means
  re-learning the people-work muscle. Neither is a
  weekend.

The decision at L5/L6 is which *first* archetype you'll
commit to. You can change later (see Section 4), but the
first choice has gravity.

---

## 2. The fork as a real decision

A worked framework for the fork. The questions are not
"which is better" (no answer) but "which is better *for
you, given your specific history and energy*."

### The 4-question framework

| # | Question | If you answer "yes" to most, you lean toward... |
|---|---|---|
| 1 | Do you have evidence (not aspiration) that people work is the most energizing part of your week? | ...Manager (EM or TLM). |
| 2 | Do you have a specific technical area you want to be known for over the next 5 years? | ...IC (Staff → Principal). |
| 3 | When you imagine your 50-year-old self, do you imagine leading a team or building a system? | ...Team → Manager. System → IC. |
| 4 | Are you willing to give up the daily "I shipped this" dopamine for the slower "this person I hired just got promoted" dopamine? | ...Yes → Manager. No → IC. |

The honest answer to #3 and #4 is the deciding factor. Most
engineers I've worked with can predict their own answer to
#1 and #2 if they sit with it for 10 minutes. The hard
question is #3 — the 50-year-old self test. It's the question
that cuts through the comp, the title, and the mimetic
desire.

### The "what would I miss" test

A useful second pass. Make a list of 10 things you did at
work in the last 30 days. For each, score 1-5 on "would I
miss this if I stopped doing it." Then count:

- **8+ items scored 3+ → IC.** The work is the point; the
  people stuff is the supporting cast.
- **5-7 items scored 3+ → TLM.** The work matters but the
  people stuff is starting to matter too.
- **3-4 items scored 3+ → EM.** The work is the supporting
  cast; the people stuff is the point.
- **0-2 items scored 3+ → re-evaluate.** You may be in the
  wrong job, period — and the fork may not be the
  question to ask yet.

This is the most predictive framework I've found. It works
because it's *behavioral*, not aspirational — it's based on
what you actually do, not what you say you want.

### The 4 archetypes as a 2x2

A simpler way to think about the fork: the 2 dimensions
that matter are (a) *do you want to manage people* and (b)
*do you want to stay technical*.

| | Stay technical | Go less technical |
|---|---|---|
| **Manage people** | TLM | EM (people manager) |
| **Don't manage** | IC (deep specialist or Staff/Principal) | (rare — this is "VP of nothing," usually a transition state) |

The bottom-right cell is mostly a transition state. Most
people who want to "stop coding" don't want to stop
*working* — they want to stop *coding*. The move to the
top-right (EM) gives them that, but at the cost of
managing. The move to the bottom-left (IC) keeps them
working but at the cost of staying technical.

The TLM cell (top-left) is the most underrated. It lets
you keep both, but the time you spend on each is roughly
halved. The TLM is the right answer for engineers who
*like both* but haven't yet picked a favorite.

---

## 3. Real stories of EMs who went back

The reversibility story is real but undersold. Three
worked examples (composites, not real names, but the
patterns are common):

### Story 1: "I managed for 3 years, then went back to Staff"

**Sam**, 8 years experience, L6 at a large search company.
Spent 3 years as an EM managing a 6-person infra team.
Loved the people work for the first 18 months; got
bureaucratic and tired of the calendar by year 3.

**The move back:** Sam told his director "I want to go back
to IC. I'd like to land as a Staff engineer on the team I
used to manage, and I'd like a 6-month transition where I
co-manage with my replacement." The director agreed.

**What worked:** Sam had stayed technical during his EM
years (he ran design reviews, wrote 2 internal RFCs a year,
attended the team's architecture meetings). The credibility
gap was small. He went from EM to Staff in 6 months with
the same manager, same team, and a 6-month overlap with
his EM replacement.

**What didn't work:** Sam's reports were confused for the
first 3 months. The 1:1s he'd been running as a manager
were now "skip-levels" with a different power dynamic. He
had to actively rebuild the relationship as a peer, not a
boss.

**Sam's advice:** "If you're going to make the move back,
make it before year 4. By year 4, the technical credibility
gap is real. And do it with a 6-month overlap, not a clean
break."

### Story 2: "I went from Staff to EM and back to Staff within 18 months"

**Priya**, 7 years experience, Staff at a payments company.
Took an EM role at a smaller startup, hated it (the
infrastructure was bad, the hiring market was bad, the
compensation was bad), and negotiated a return to her old
company as Staff.

**The move back:** Priya's old manager at the payments
company had a Staff req open. She reached out 10 months
into her EM stint and said "I'd like to come back. Here's
the 3 things I shipped as an EM that I think transfer."
The manager agreed.

**What worked:** Priya had been a top performer at the
payments company for 4 years before leaving. The brand was
strong. The EM stint, even though it didn't work, gave
her a credibility boost — she'd been a manager, which
read as "more senior" even for the Staff role.

**What didn't work:** Priya lost 12 months of vesting, lost
2 levels of seniority (L7 → L6), and the comp at the new
Staff role was lower than what she'd been making as an
EM.

**Priya's advice:** "The first 6 months of any new job are
the most reversible. If it's not working, decide by month
6 — don't wait for the vesting cliff."

### Story 3: "I went from EM to TL-eM to TLM and stayed"

**Jordan**, 9 years experience, L6 at a data infra company.
Started as an EM (purely people work), missed the technical
work, negotiated a "tech-lead EM" role (50/50), and has
been in that role for 4 years.

**The move:** Jordan's director was willing to let him
keep managing his team while taking on a 50% technical
load. The 50% was specifically the architecture and design
review work, not the day-to-day coding.

**What worked:** Jordan explicitly named the trade-off
("I'll cut my technical output by 50% in exchange for
keeping my hand in") and the director agreed. The TLM
role became a real, durable position on the team.

**What didn't work:** Jordan's reports sometimes feel
ambiguous about whether he's "the manager" or "the tech
lead." The dual role requires constant communication about
which hat he's wearing.

**Jordan's advice:** "The TLM role is real, but it only
works if your director is bought in. If your director
wants a pure EM and a pure tech lead, the TLM role will
get squeezed."

---

## 4. How to reverse a manager decision (the playbook)

If you've made the move and want to go back, the playbook
is the same regardless of company. The 4 steps:

1. **Decide early.** The first 6 months are reversible.
  After 18 months, the gap is real.
2. **Stay technical during your EM years.** Run design
  reviews. Write 1-2 RFCs a year. Pair on hard bugs. The
  "I haven't coded in 18 months" gap is what kills the
  return.
3. **Have a specific role in mind.** "I want to go back to
  IC" is not actionable. "I want to land as a Staff
  engineer on the platform team I used to be on" is.
4. **Negotiate the transition, not the break.** Ask for a
  3-6 month overlap with your EM replacement. The overlap
  is what makes the return feel like a "next step" and
  not a "step back."

The conversation with your current manager (the "I want
to go back" talk) is its own pitch. The structure is
similar to the pitch in Lesson 03:

- **The evidence:** "I've been doing this for 12 months.
  Here's the work I've enjoyed and the work I haven't."
- **The "why now":** "I'd like to make the move in the
  next 3-6 months, not because the role has been bad but
  because the work I'd do as a Staff engineer is a better
  fit for my long-term career."
- **The ask:** "I'd like your help in two ways: (1) a
  specific role to move into, and (2) a 3-6 month
  transition plan so the team isn't disrupted."
- **The fallback:** "If the timing doesn't work, I want to
  give the EM role another 6 months before deciding."

---

## 5. The 4 archetypes past L6

The archetypes shift as you go up. At L7/L8, the "deep
specialist" IC path becomes rarer (most companies don't
have enough L7+ ICs to have a real "fellow" track) and
the "generalist Staff" IC path becomes the norm. The
manager path at L7/L8 is mostly Director / Sr. Director
/ VP.

A rough map of where the archetypes cluster at each level:

| Level | Most common path | Possible but rare |
|---|---|---|
| L5 (Senior) | IC or EM | TLM (rare) |
| L6 (Staff) | Staff IC, EM, or TLM | — |
| L7 (Sr. Staff / Sr. EM) | Sr. Staff IC, Sr. EM, or Director | Tech Fellow (rare, FAANG) |
| L8 (Principal / Director+) | Principal IC, Director, or VP | Tech Fellow (very rare) |

The "very rare" paths exist but are usually at 1-2
companies per industry. Don't optimize for them; optimize
for the path that's available *at your company* and
*for your energy*.

---

## Try it

The final self-check. Answer these 4 questions in writing,
in 10 minutes, with no notes.

1. **Of the 4 archetypes, which one most fits the work
   I've been doing in the last 12 months?** (Not the work
   I want to do. The work I've been doing.)
2. **Of the 4 archetypes, which one most fits the work I
   want to be doing in 5 years?** (Aspirational is okay
   here.)
3. **If #1 and #2 are different, what would have to be
   true for me to close the gap in 12-18 months?**
4. **If a manager offer landed on my desk tomorrow, would
   I take it?** (Yes / no / "I'd want to talk to 3 people
   first." All three are valid answers.)

If #1 and #2 are the same archetype, you have a clear
direction. If they're different, the gap in #3 is your
*next* project. If #4 is "I'd want to talk to 3 people
first," talk to the 3 people — and use Lesson 03's
self-check as the framework for the conversation.

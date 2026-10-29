# 06 — Cover Letters

> **Lesson 6 of 9** · ~12 min

When to write one, the 4-paragraph structure, and a full sample
cover letter for a data engineer applying to Databricks.

---

## 1. The unpopular truth: most tech cover letters don't matter

For most tech roles — especially at the data engineering level
in the US — **the cover letter is optional**. Many companies
won't even read it. Some ATS systems will treat it as a separate
attachment and not surface it to the recruiter.

This is not a reason to skip the cover letter. It's a reason
to write it *correctly* when you do:

- **Don't write a generic cover letter.** A 4-paragraph essay
  about your passion for data and your interest in the role
  reads exactly like every other candidate's cover letter. The
  recruiter will skim it, find nothing specific, and move on.
- **Don't write a 1-page cover letter.** 200-300 words, 4 short
  paragraphs. Anything longer is padding.
- **Don't repeat your resume.** The cover letter is for things
  the resume *can't* say: why this company, why this role,
  what you'd do in the first 90 days.

The exception — when the cover letter **does** matter:

- **The JD explicitly asks for one.** Always write it.
- **The role is a "stretch" (e.g. you're 1 YoE short of the
  listed minimum).** A cover letter is the only place to make
  the case for why you're a fit anyway.
- **The role is at a senior+ level (Staff+).** Senior roles
  are evaluated on judgment and intent, not just skills. A
  cover letter is where you demonstrate both.
- **The role is at a company where the recruiter will read it.**
  Smaller companies, mission-driven orgs, consulting, finance.
  FAANG-scale companies mostly won't.

The default for senior+ data engineering applications:
**write a 200-300 word cover letter for every role you apply to,
unless the JD explicitly says optional and you're at a company
where the recruiter won't read it.**

---

## 2. The 4-paragraph structure

Every cover letter in this track has 4 paragraphs, in this
order, in this length:

| Paragraph | Length | Job |
|---|---|---|
| **1. Hook** | 1-2 sentences | Name the role, name a specific thing about the company that resonates with you |
| **2. Why them** | 2-3 sentences | What the company is doing that you find interesting, with a specific reference (a product, a recent post, a tech stack decision) |
| **3. Why you** | 3-5 sentences | Your 1-2 most relevant accomplishments, in XYZ format, mapped to the JD's pain |
| **4. The ask** | 1-2 sentences | A clear ask for the next step, with a specific reason you're excited to talk |

Total: 200-300 words. The whole letter should fit on a single
screen when the recruiter opens the PDF.

**What the 4-paragraph structure is *not***: a place to repeat
your resume. The resume is in the resume. The cover letter is
the *positioning* document — it answers the questions "why this
company" and "why this role," which the resume literally cannot
answer.

---

## 3. The hook — what to put in paragraph 1

The hook is one or two sentences that name:

- The role you're applying to (exact title from the JD)
- A *specific* thing about the company that made you want to apply

Bad hook (generic, no specific reference):

> *I'm writing to apply for the Senior Data Engineer position at
> Databricks. I'm excited about this opportunity because Databricks
> is a leader in the data space.*

The recruiter reads this and learns nothing they didn't already
know from the JD. This is the cover letter equivalent of
"responsible for" — it exists, but it doesn't do work.

Good hook (specific, with a real reference):

> *I'm applying for the Senior Data Engineer role on the Lakehouse
> Platform team. I read the engineering blog post on the Unity
> Catalog GA launch in May, and the design choices around
> cross-workspace governance are the kind of problem I want to
> spend the next 5 years on.*

The recruiter reads this and thinks: "this person did 10 minutes
of research, knows what team they're applying to, and has a
specific reason for being here." That's the signal.

**Where to find the "specific thing":**

- The company's engineering blog (most have one)
- A recent product launch (search "[company] launch" or
  "[company] GA")
- A recent open-source release (most data companies have
  GitHub orgs with public repos)
- A conference talk by an employee (YouTube, conference sites)
- A specific JD phrase that caught your eye ("we're rebuilding
  our data platform," "scaling 10x this year")

The "specific thing" should be **about the work**, not about the
company's culture or mission. "I love Databricks' mission to
democratize data" is generic. "The Unity Catalog cross-workspace
governance design is the kind of problem I want to work on" is
specific.

---

## 4. The "why them" and "why you" — the meat of the letter

**Paragraph 2 (Why them):** 2-3 sentences expanding on the
specific thing from the hook. The goal is to demonstrate that
you understand the company's *technical context*, not just its
marketing. The recruiter should finish paragraph 2 thinking
"this person knows what we do."

**Paragraph 3 (Why you):** 3-5 sentences. This is where your
1-2 best bullets go, rewritten for the JD's pain. The format:

1. **Lead with the JD's pain**, not your career. ("I noticed the
   JD emphasizes scaling data quality tooling across product
   teams...")
2. **Map your accomplishment to that pain.** ("In my current
   role, I built...")
3. **End with the outcome.** ("...which cut data quality
   incidents 70% and was adopted by 3 other teams.")

You get one or two of these per cover letter. Three or more
becomes a list. The cover letter is not the resume.

---

## 5. The ask — what to put in paragraph 4

The last paragraph is a single, specific ask. It should:

- Be **direct** ("I'd love to talk")
- Reference a *specific reason* you're excited to talk (the
  problem, the team, the stack)
- Not be sycophantic or over-eager

Bad ask:

> *I would be incredibly grateful for the opportunity to discuss
> this role with you. I am confident I would be a great fit and
> am available at your earliest convenience.*

Good ask:

> *I'd love to talk through how the platform team's data quality
> roadmap intersects with my work on dbt + Great Expectations
> at MidPay. I'm flexible on timing and can work around your
> schedule.*

The good ask names a *specific topic* for the conversation. It
turns the cover letter from "I'm available" into "I have
something to say."

---

## 6. Full sample: cover letter for a Databricks Senior DE role

```
─────────────────────────────────────────────────────────────────────
Jordan Park
jordan.park@email.com · linkedin.com/in/jordanparkdev

April 14, 2026

Databricks, Inc.
San Francisco, CA

Re: Senior Data Engineer, Lakehouse Platform

I'm applying for the Senior Data Engineer role on the Lakehouse
Platform team. I read the engineering blog post on the Unity
Catalog GA launch, and the design choices around cross-workspace
governance and column-level lineage are the kind of problem I
want to spend the next 5 years working on.

What stood out from the JD is that the team is rebuilding how
metadata and governance are surfaced to the data platform — not
as a side feature, but as a first-class product surface. I've
spent the last 3 years in similar territory: at MidPay, I built
the dbt + Great Expectations layer that now serves 4 product
teams and is the basis for our internal data contracts. The
adjacent problems — cross-team ownership, schema drift, the gap
between "data quality" and "data product" — are exactly the
ones the Unity Catalog work seems to be tackling.

My most relevant work: I led the migration of a 14 TB on-prem
Hadoop cluster to AWS (S3 + Glue + Redshift) at MidPay, and
authored our internal "Data Engineering Handbook" (60 pages,
adopted by 12+ new hires). Both were less about the specific
tech and more about the organizational scaffolding — getting
4 product teams to agree on data contracts, ownership, and
quality SLAs. The handbook is the part I'm proudest of; it's
the closest thing I've shipped to the Lakehouse Platform
team's charter.

I'd love to talk through how the data-quality and governance
roadmap at Databricks intersects with the work I'm doing at
MidPay. I'm flexible on timing and can work around your
schedule. Thanks for reading.

Best,
Jordan Park
─────────────────────────────────────────────────────────────────────
```

That letter is ~270 words. It took ~30 minutes to write. It
references a *specific* blog post, *specific* work at MidPay,
and *specific* topics for the screen call. It is not a template.
It is a real cover letter for a real role.

---

## 7. The mistakes to avoid

In rough order of how often I see them:

| # | Mistake | Why it kills the letter | Fix |
|---|---|---|---|
| 1 | **Generic opening ("I am writing to apply...")** | Reads like every other letter | Skip the meta-opening. Start with the role and the specific hook. |
| 2 | **No specific company reference** | Signals you sent the same letter to 100 companies | Reference a blog post, a product, a tech stack decision. |
| 3 | **Repeating the resume** | Wastes the space the cover letter is supposed to occupy | Cover letter = why them + why you + ask. Resume = what you did. |
| 4 | **3+ paragraphs of "why I'm a great fit"** | Becomes a list; reads as desperate | 1-2 best accomplishments, mapped to the JD's pain. |
| 5 | **Sycophantic close ("I would be incredibly grateful...")** | Reads as junior; signals lack of senior-level intent | Be direct. "I'd love to talk" + a specific reason. |
| 6 | **1-page cover letter** | Signals inability to prioritize; same anti-pattern as a 2-page resume | 200-300 words, 4 paragraphs, single screen. |
| 7 | **"I am a perfect fit" / "I am the best candidate"** | The recruiter decides that, not you | Let the work speak. |
| 8 | **Spelling the company name wrong** | Instant reject | Triple-check. |

---

## Try it

Pick 1 of the targeted resumes you built in Lesson 04. Write a
cover letter for it, using the 4-paragraph structure.

Checklist:

- [ ] Paragraph 1 names the role and 1 specific company reference
- [ ] Paragraph 2 expands on the reference (technical context, not culture)
- [ ] Paragraph 3 has 1-2 accomplishments, in XYZ format, mapped to the JD's pain
- [ ] Paragraph 4 is a direct ask, with a specific conversation topic
- [ ] Total: 200-300 words
- [ ] No "responsible for," no "I am a perfect fit," no sycophantic close

Save as `cover_letter_<company>_<role>.md`. Time yourself. 30
minutes is the target.

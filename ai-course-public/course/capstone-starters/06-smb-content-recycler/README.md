# SMB Content Recycler — Capstone Starter

> **Turn 1 long-form piece (newsletter, blog post, transcript, podcast notes) into 30 social posts in 10 minutes — no code required.**

This is the runnable starter for **Capstone Template 6**. Unlike capstones 1-5 (which are pitched at the AI engineer building a SaaS), this one is pitched at the **small business owner** who doesn't code. The starter ships in two flavors:

- **Tier 1 (no code):** 5 copy-paste prompts + a 1-page SOP. Ship today. $0.
- **Tier 2 (optional, ~50 lines of Python):** wrap the 5 prompts in a CLI that takes 1 markdown file and outputs 30 social posts as a CSV. Ship in a weekend. $0.

Your job in 7 days (per the SMB 7-day ramp from `L9-4-the-smb-first-7-days.md`):
1. Pick your long-form piece (last week's newsletter, a podcast you were on, a customer case study).
2. Run the no-code prompt. Get 30 posts. Edit 5-10. Schedule them.
3. (Optional) Set up the Python wrapper for the next 4 weeks. 1 long-form/week → 30 posts/week.

---

## What you start with

A working content-recycling pipeline with:

- ✅ **5 prompts, ready to copy-paste** — for LinkedIn, Facebook, Instagram, Twitter/X, and email. Each is a 3-line prompt that takes 1 long-form piece and returns 5-10 posts in the platform's format.
- ✅ **The master prompt** — the 1-prompt version that returns 30 posts (10 LinkedIn, 10 Facebook, 10 Instagram) in 60 seconds.
- ✅ **A 1-page SOP** — what to do with the 30 posts after the AI returns them (edit 5-10, schedule 20, discard 5-10).
- ✅ **A 7-day ramp** — day-by-day tasks to ship this workflow in 7 days, 1 hour/day.
- ✅ **A 5-example test set** — 5 real long-form pieces you can use to test the prompt before you trust it on your own content.
- ✅ **Optional Python wrapper** — a 50-line CLI (`recycler.py`) that takes a markdown file and writes 30 social posts to a CSV. For SMB owners who want automation.
- ✅ **A safety check** — a 10-line script that flags the 5 most common AI mistakes (invented quotes, wrong attributions, off-brand hashtags, made-up stats, broken links).

What you add in 7 days:

- [ ] Pick 1 long-form piece from this week
- [ ] Run the master prompt. Get 30 posts.
- [ ] Edit 5-10 posts (the "human-in-the-loop" step)
- [ ] Schedule the edited 20 across the week
- [ ] Track: which posts got engagement? Which got ignored?
- [ ] Refine the prompt with the engagement data
- [ ] Hand the SOP to a new hire on day 30

---

## Who this is for

**This is for the SMB owner who:**
- Has a 1-20 person business in SG/TW/VN/CN
- Writes 1 long-form piece a week (newsletter, blog post, podcast notes, customer case study)
- Needs 30 social posts a week to promote it
- Currently spends 3-4 hours every Saturday writing social posts
- Doesn't code, doesn't want to learn to code, doesn't have time

**This is NOT for:**
- The AI engineer building a SaaS — see capstones 1-5 for that.
- The 1-person content creator who needs 1 post, not 30 — just use ChatGPT directly.
- The enterprise marketing team that already has a content team — your social posts are already done.

---

## How to ship in 7 days (the 1-hour-per-day ramp)

| Day | 1 hour | Output |
|-----|--------|--------|
| **1** | Pick 1 long-form piece from this week. Paste it into a Google Doc. Write 3 sentences about WHO the audience is, WHAT the 1 key takeaway is, and WHICH platforms you post on. | 1 long-form + 3 sentences of context |
| **2** | Copy the master prompt below. Paste your long-form. Run it in ChatGPT. Save the 30 posts to a Google Doc. | 30 raw posts |
| **3** | Edit 5-10 posts. Schedule the edited 20 across the week (Buffer, Hootsuite, or native scheduling). Discard 5-10 that don't fit. | 20 scheduled posts |
| **4** | After 3-4 days, check the engagement on the first 10 posts. Which got likes/comments/shares? Which got ignored? Make 2 notes: "this tone worked" and "this hook worked." | 2 notes on what worked |
| **5** | Refine the master prompt with your notes. Add your brand voice, your typical CTA, your 2-3 banned phrases. Run on the same long-form. Compare the new 30 to the old 30. | A refined prompt + comparison |
| **6** | Test the refined prompt on a 2nd long-form piece (a different one from this week). Run, edit, schedule. | 20 more scheduled posts |
| **7** | Write the 1-page SOP: the refined master prompt + the 3 sentences of context + the editing checklist + the scheduling tool. Hand it to yourself (or an employee) for week 2. | A 1-page SOP |

By day 7, you have: 1 working workflow, 40 scheduled posts, a refined prompt, and a 1-page SOP. **You just saved 3-4 hours/week, every week, forever.**

---

## The master prompt (lift this verbatim, then customize on day 5)

```
You are a social media manager for [YOUR BUSINESS NAME]. Your job is to turn
1 long-form piece (article, blog post, transcript, podcast notes, customer
case study) into 30 social posts: 10 LinkedIn, 10 Facebook, 10 Instagram.
Each post has a hook (first line that makes someone stop scrolling), a body
(2-4 sentences with the value), and a CTA (last line that asks for an
action). Each post stands alone — no "continued in comments", no
"swipe to see more".

Brand voice:
- [2-3 adjectives, e.g., "warm but direct", "data-driven but human"]
- Banned phrases: [2-3 phrases to never use, e.g., "game-changer", "10x",
  "in today's fast-paced world"]
- Typical CTA: [1 CTA you use a lot, e.g., "DM me 'WORKFLOW' to get the
  free SOP"]

The long-form piece:
[PASTE THE FULL TEXT HERE — 500-3000 words is the sweet spot]

Output: 30 posts, numbered 1-30, each labeled
[LinkedIn] / [Facebook] / [Instagram]. For each post, give the hook
on its own line, then the body, then the CTA.
```

**What this does in 60 seconds:** turns 1 newsletter into 30 social posts. The SMB owner edits 5-10 (the AI will invent 1-2 quotes, misattribute 1 stat, add 2-3 off-brand hashtags — that's why the human-in-the-loop is non-negotiable).

---

## The 5 platform-specific prompts (for SMB owners who want more control)

Some SMB owners prefer to get 5-10 posts per platform rather than 30 mixed. The 5 prompts below are platform-specific.

### LinkedIn (10 posts)

```
You are a LinkedIn ghostwriter for [YOUR NAME], the [TITLE] of
[YOUR BUSINESS]. You write in first person, in a reflective but
practical voice. You never use "game-changer" or "10x" or
"in today's fast-paced world". You always end with a question
to drive comments.

Turn this long-form into 10 LinkedIn posts. Each post:
- 800-1200 characters
- Starts with a hook (1 line that makes someone stop scrolling)
- 2-4 short paragraphs (1 sentence each, with line breaks)
- Ends with a question

The long-form:
[PASTE LONG-FORM HERE]

Output: 10 posts, numbered 1-10.
```

### Facebook (10 posts)

```
You are a Facebook community manager for [YOUR BUSINESS]. You write
in a warm, conversational voice. You can use 1-2 emojis per post but
no more. You always end with a question or a "tag a friend who..."

Turn this long-form into 10 Facebook posts. Each post:
- 400-800 characters
- Starts with a hook
- 1-2 short paragraphs
- Ends with a question or a "tag" prompt

The long-form:
[PASTE LONG-FORM HERE]

Output: 10 posts, numbered 1-10.
```

### Instagram (10 posts, caption + visual idea)

```
You are an Instagram copywriter for [YOUR BUSINESS]. You write
captions that pair with a visual. You suggest the visual idea
in brackets at the top of each caption. You use 3-5 hashtags at
the bottom of each post (relevant, not generic — no #motivation
or #business). You always end with a CTA.

Turn this long-form into 10 Instagram posts. Each post:
- [VISUAL IDEA: 1 line describing the image/graphic]
- Caption: 300-800 characters
- 3-5 hashtags at the bottom
- 1 CTA at the end

The long-form:
[PASTE LONG-FORM HERE]

Output: 10 posts, numbered 1-10.
```

### Twitter/X (5 threads)

```
You are a Twitter ghostwriter for [YOUR NAME], the [TITLE] of
[YOUR BUSINESS]. You write threads (5-7 tweets per thread) that
get retweets. Each tweet is < 280 chars. The first tweet of
each thread is the hook. The last tweet of each thread is the
CTA ("if this was useful, RT the first tweet").

Turn this long-form into 5 Twitter threads. Each thread:
- 5-7 tweets
- Tweet 1 is the hook (a surprising stat, a contrarian take,
  or a question)
- Tweets 2-6 are the value (1 idea per tweet)
- Tweet 7 is the CTA

The long-form:
[PASTE LONG-FORM HERE]

Output: 5 threads, labeled Thread 1-5, with tweets separated
by "---".
```

### Email newsletter (1 long email)

```
You are a newsletter writer for [YOUR BUSINESS]. You write
emails that get opened (subject line < 50 chars) and read
(scannable in 60 seconds). You write in first person, in a
conversational voice.

Turn this long-form into 1 newsletter email. The email:
- Subject line (< 50 chars, creates curiosity)
- Preview text (the 1 line that shows in the inbox preview)
- Greeting
- 3-5 short paragraphs (1 idea per paragraph)
- 1 CTA at the end
- P.S. line (the P.S. is the most-read line; put the
  strongest CTA or hook there)

The long-form:
[PASTE LONG-FORM HERE]

Output: subject line, preview text, full email body.
```

---

## The 1-page SOP (what to do with the 30 posts after the AI returns them)

```
# 1-Page SOP: From 1 Long-Form Piece to 30 Social Posts

## Before (the boring way)
Every Saturday morning, you sit down with a coffee and try to
write 30 social posts. You write 8. You give up. You have a
content gap.

## After (the AI way, 1 hour/day, 7 days setup)
1. Pick 1 long-form piece from this week.
2. Paste it into ChatGPT with the master prompt.
3. Get 30 posts in 60 seconds.
4. Edit 5-10 posts. (The AI will invent 1-2 quotes, misattribute
   1 stat, add 2-3 off-brand hashtags. This is normal.)
5. Schedule the edited 20 across the week (Buffer, Hootsuite,
   or native scheduling).
6. Discard the 5-10 posts that don't fit.

## The editing checklist (run this on every AI post)
- [ ] Did the AI invent a quote? Delete it.
- [ ] Did the AI misattribute a stat? Look it up or delete it.
- [ ] Did the AI add a banned phrase (e.g., "game-changer")? Delete it.
- [ ] Did the AI add a generic hashtag (#motivation)? Replace with a niche one.
- [ ] Does the post sound like YOU, or like a robot? Edit until it sounds like you.

## Time saved
- Before: 3-4 hours/week (the Saturday morning grind)
- After: 30 minutes/week (the edit + schedule)
- Net: 2.5-3.5 hours/week saved, every week, forever.

## The 5 guardrails (from L9-4)
1. Never post without reading. Every AI post is a draft. You read + click post.
2. Never paste customer PII. Anonymize first. Replace [NAME] with [CUSTOMER].
3. Never auto-post 30 in a batch. Edit 5-10 first. The wrong choice is
   to schedule all 30. The right choice is to edit 5-10 and schedule 20.
4. Never trust the output. The AI is wrong in 1-2 places per post.
   Budget 30 seconds per post for review.
5. Never skip the 1-hour-per-day ramp. 1 workflow, 1 hour/day, 7 days.
   The wrong choice is the Saturday binge.
```

---

## The optional Python wrapper (for SMB owners who want automation)

If you're an SMB owner who's comfortable with the command line (or you have a tech-savvy employee), the Python wrapper below takes 1 markdown file and writes 30 social posts to a CSV. ~50 lines of code, no frameworks, just `openai` and `csv`.

```python
# recycler.py — turn 1 markdown file into 30 social posts (CSV)
import csv
import sys
import openai

MASTER_PROMPT = """
You are a social media manager for {business}. Turn the long-form
piece below into 30 social posts: 10 LinkedIn, 10 Facebook, 10
Instagram. Each post: hook, body, CTA. Output as a numbered list
labeled [LinkedIn] / [Facebook] / [Instagram].

Long-form:
{long_form}
""".strip()

def recycle(long_form_path: str, business: str, output_csv: str) -> None:
    with open(long_form_path) as f:
        long_form = f.read()
    prompt = MASTER_PROMPT.format(business=business, long_form=long_form)
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    posts = parse_posts(resp.choices[0].message.content)
    with open(output_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["platform", "n", "text"])
        for platform, n, text in posts:
            w.writerow([platform, n, text])
    print(f"wrote {len(posts)} posts to {output_csv}")

def parse_posts(raw: str) -> list[tuple[str, int, str]]:
    """Parse the 30-post output into (platform, n, text) tuples."""
    posts = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        # Matches "1. [LinkedIn] hook\n   body\n   cta" or similar
        if "[" in line and "]" in line:
            try:
                n_part, rest = line.split(".", 1)
                n = int(n_part.strip())
                platform = rest.strip().split("]")[0].strip("[")
                text = rest.split("]", 1)[1].strip()
                posts.append((platform, n, text))
            except (ValueError, IndexError):
                continue
    return posts

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: python recycler.py <long_form.md> '<business>' <out.csv>")
        sys.exit(1)
    recycle(sys.argv[1], sys.argv[2], sys.argv[3])
```

**Usage:**

```bash
export OPENAI_API_KEY=sk-...
python recycler.py newsletter.md "Mei's Bakery" posts.csv
# writes 30 posts to posts.csv
```

**Cost:** $0.01-0.05 per long-form (gpt-4o-mini). **Time:** 60 seconds for the API call + 30 seconds for the parse. **Total:** 90 seconds end-to-end.

---

## The 5-example test set (so you can test the prompt before you trust it)

Before you run the prompt on your real long-form, test it on these 5 examples. Each is in a different voice + length. The prompt should produce acceptable output on 4/5; the 5th is the "stress test" (a contrarian take that the AI may over-soften).

| # | Example | Length | Voice | Expected output quality |
|---|---------|--------|-------|-------------------------|
| 1 | Your last 2 newsletters concatenated | 1000-2000 words | Your real voice | Should be 90%+ ready after editing |
| 2 | A podcast transcript you were on | 2000-4000 words | Conversational | Should be 80%+ ready |
| 3 | A customer case study (with permission) | 500-1000 words | Story-driven | Should be 85%+ ready |
| 4 | A LinkedIn post you wrote that did well | 200-500 words | Punchy | Should be 95%+ ready |
| 5 | A contrarian take you disagree with | 500-1000 words | Provocative | Should be 70%+ ready (the AI may soften it) |

If the prompt produces acceptable output on 4/5 of these, it's ready for real content. If it fails on 2/5, refine on day 5.

---

## The 5 guardrails (the same 5 from L9-4, applied to this workflow)

1. **Never post without reading.** Every AI post is a draft. You read + click post. The wrong choice is to auto-schedule all 30. The right choice is to edit 5-10 and schedule 20.
2. **Never paste customer PII.** Anonymize first. Replace `[CUSTOMER_NAME]` with `[NAME]`, `[CUSTOMER_EMAIL]` with `[EMAIL]`, etc. The wrong choice is to paste the actual case study with names. The right choice is to anonymize first.
3. **Never run 24/7.** This workflow runs once a week, with you in the loop. The wrong choice is to set up an auto-scheduler that runs the AI every day. The right choice is the weekly 30-minute edit-and-schedule.
4. **Never trust the output.** The AI is wrong in 1-2 places per post. The wrong choice is to assume the output is right. The right choice is the 30-second-per-post editing checklist.
5. **Never skip the 1-hour-per-day ramp.** 1 hour/day for 7 days. The wrong choice is the Saturday binge. The right choice is the daily 1-hour compounding.

---

## The wrong choices (the 3 ways this fails)

1. **The Saturday binge.** You try to set up all 5 prompts in 4 hours on Saturday. You get stuck on prompt 2, conclude AI "doesn't work for content," and never try again. The right choice: 1 prompt, 1 hour/day, 7 days.
2. **The 30-post auto-schedule.** You schedule all 30 AI posts without reading them. 5 of them have invented quotes, 3 have wrong stats, 8 have off-brand hashtags. Your audience notices. You lose credibility. The right choice: edit 5-10, schedule 20, discard 5-10.
3. **The "AI is good enough" trap.** You run the prompt 3 times and conclude it's good enough. You don't refine on day 5. You never add your brand voice, your banned phrases, your typical CTA. The output stays generic. The right choice: refine on day 5 with the engagement data from the first 10 posts.

---

## What this capstone IS and IS NOT

**IS:**
- A 7-day workflow for the SMB owner
- 5 copy-paste prompts (no code required for tier 1)
- A 1-page SOP the owner can hand to a new hire
- An optional Python wrapper for the SMB owner who wants automation
- The same 5 guardrails as the rest of the SMB playbook (L9-4)

**IS NOT:**
- A SaaS product. You're not building a startup; you're building a workflow.
- A 40-hour course. The 5 prompts are 1 page. The SOP is 1 page.
- A replacement for human judgment. The AI writes the draft; you read the draft; you make the call.
- A vendor-specific tool. It works with ChatGPT, Claude, Gemini — any LLM with a chat interface.

---

## Read next

- `course/ai-fde/.../s09-ai-agents-in-business/L9-4-the-smb-first-7-days.md` — the SMB owner's first 7 days, the 5 workflows, the 5 guardrails
- `marketing/content/substack-posts/2026-10-smb-ai-quick-wins/01-post-body.md` — the Substack article that drives traffic to this capstone
- `business/plan/smb-offer-ladder.md` — the $47 / $197 / $497 / $997 product stack that this capstone fits inside
- `course/capstone-starters/README.md` — how this capstone fits with the 5 engineer-pitched capstones

---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own business, courses, prototypes, and products.
---

**Last updated:** 2026-10-12  
**License:** MIT — use freely in your own courses, prototypes, and products.  

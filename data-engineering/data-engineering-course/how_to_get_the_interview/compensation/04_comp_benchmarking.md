# 04 — Comp Benchmarking

> **Lesson 4 of 4** · ~20 min

Where the numbers come from, the base-vs-RSU-vs-signing
framework, and the 6-month / 12-month / 4-year TC worksheet.

---

## 1. Where the numbers come from

There are 4 sources of comp data. Each has a different
reliability curve. Most candidates over-rely on (1) and ignore
(4), which is the most accurate for your specific situation.

| # | Source | Reliability | Caveat |
|---|---|---|---|
| 1 | levels.fyi | High for public companies, low for private | Self-reported, can be 1-2 years stale, doesn't separate DE from SWE |
| 2 | Glassdoor | Medium | Same self-report issue. Often under-counts RSU. |
| 3 | Blind / Teamblind | Medium-high for senior+ | Anonymous, but can be exaggerated (people post wins, not losses). Useful for ranges. |
| 4 | Recruiter conversations + internal networks | Highest for *your* specific role | Sensitive. The way you ask matters. |

The job: triangulate. Pull data from all 4 before you go on
loop. Then you'll have a defensible number to anchor on.

---

## 2. levels.fyi

**What it is:** Self-reported comp data, sortable by company,
level, role, location. Free to use.

**How to use it:**

1. Filter by **company** (e.g., Meta) and **role** (Data
   Engineer).
2. Filter by **level** (E5 / L5 / IC3). Don't confuse the
   levels — see Lesson 01.
3. Filter by **location** (Bay Area vs. remote vs. NYC). Big
   companies geo-adjust by 15-30%.
4. Look at the **75th percentile**, not the median. The 75th
   is the number you anchor on. The median is the number the
   recruiter will use.

**What it doesn't tell you:**

- **Stock price movement.** levels.fyi shows the grant value
  at the time, not the realized value. A 2021 grant at $300k
  is worth $300k on levels.fyi but the stock is now 50% lower
  and the realized value is $150k.
- **Refreshers.** Most public companies grant refreshers
  annually. A "$300k RSU" is really a "$300k RSU + $75k/yr
  refresher" if you stay. levels.fyi doesn't show refreshers.
- **The "this person failed negotiation" data.** The people
  who post on levels.fyi are disproportionately *good*
  negotiators. The median levels.fyi number is closer to the
  75th percentile of all offers.
- **The signing bonus clawback.** levels.fyi shows the
  headline signing number, not the after-clawback number.
- **Leveling differences across companies.** "E5" at Meta and
  "L5" at Google are close, but not identical. levels.fyi
  doesn't normalize for this.

**The discount:** Take the levels.fyi 75th percentile number
and discount by 10-15% to be conservative. If you see $400k
RSU for E5 at Meta, your real anchor is $340-360k.

---

## 3. Glassdoor / Blind

**Glassdoor:** More reliable for *base* than for *equity*.
The salary bands are often stale by 12-18 months. Use it for
the *range* (low to high), not the point estimate. The base
ranges are reasonable; the total comp is not.

**Blind (Teamblind):** Anonymous, employee-only. Useful for
three things:

1. **Recent comp data** for your target company at your target
   level. Search "[Company] E5 data engineer" and sort by
   recent.
2. **Negotiation scripts** that worked. Search "negotiation
   [Company]" and read the threads.
3. **Team-specific comp signals.** Some teams (ML platform,
   infra) pay above band. Some (legacy teams) pay below.
   Blind threads will mention this.

**Caveats:**

- Selection bias. People who post are either happy (and
  bragging) or angry (and ranting). The median negotiator
  isn't represented.
- The comp is often the *initial* offer, not the final
  negotiated one. The initial offer is always lower.
- Some posts are obviously fake (a $5M RSU for a Senior DE
  is not real). Discount the outliers.
- Reading Blind for an hour can make you *angrier*, not
  better-informed. Set a 30-minute timer.

---

## 4. Internal networks

The most accurate comp data is from people *in your network*
who work at the company or the team. This is sensitive and
must be handled carefully.

**How to ask without burning trust:**

The structure is **context + specific question + "no pressure"
out**.

> *"Hey [name] — quick one. I'm in process for a Senior DE
> role at [Company] at the E5 level. I'm trying to calibrate
> the comp range before I respond to the offer. If you're
> comfortable sharing, what was your E5 RSU grant when you
> joined? No pressure at all if you'd rather not — I know this
> stuff is sensitive. Either way, really appreciate it."*

The rules:

- **Ask for a specific number, not a range.** A range invites
  a non-answer. A specific number gets a specific answer.
- **Frame it as "calibrating before I respond."** This signals
  you're already in process, not just shopping.
- **Make the "no" path easy.** "No pressure at all if you'd
  rather not" gives them an exit. Most people will still say
  yes, because the path of least resistance is to give you a
  number.
- **Don't ask 10 people.** Ask 2-3 trusted peers. If you ask
  10, the question gets around.

**What to ask:**

- "What was your [level] RSU grant at [Company]?"
- "Did the RSU band have room to move during negotiation?"
- "Did they refresh you in the first 12 months?"
- "What's the team-specific comp philosophy — does [team X]
  pay above or below band?"

**What NOT to ask:**

- "What do you make?" — too direct, and includes base + bonus
  which they may not remember.
- "Should I take this offer?" — they don't have the context to
  answer, and the question puts them in an awkward position.

---

## 5. Recruiter conversations

Recruiters are a comp data source, not just a delivery vehicle
for the offer. The trick: extract the **band** without giving
away your number.

**The "range for the role" ask:**

> *"Before I respond, can you help me understand the comp
> philosophy for this role? Is the band anchored at the 50th
> percentile of the market, or higher? And within the band,
> what's the range for an L5 with my experience level?"*

Recruiters will often share the *band* (e.g., "L5 DE at this
location is $180-220k base, $300-400k RSU") even when they
won't share the *position in the band* (e.g., "you're at
$185k base, $300k RSU").

**The "what would it take" ask:**

> *"If I were to come back with a counter, what's the most
> important lever for the team — base, RSU, or signing?"*

This signals you're going to negotiate, and it tells you which
lever has room. The recruiter will sometimes answer directly:
*"We're flexible on RSU but base is at the top of the band."*

**The "is the team flexible on X" ask:**

> *"Is there any flexibility on the signing bonus? I'm leaving
> a sign-on at my current employer, and the bridge to year 1
> is a real consideration."*

This frames the signing ask as a *bridge*, not a *bump*. Most
recruiters will move on signing without escalating.

---

## 6. The "do I optimize base, RSU, or signing" framework

When the recruiter says "we can move one lever — pick one,"
or when you're deciding which to push on, the framework is:

| Your priority | Optimize | Why |
|---|---|---|
| Maximize 4-year TC | **RSU** | The RSU compounds over 4 years. $50k more in RSU = $50k more in 4-year TC, all else equal. |
| Maximize year-1 cash | **Signing** | The signing is the biggest year-1 lever if base and RSU are locked. |
| Maximize stable income | **Base** | Base compounds via 401k match, raises, and promo increases. |
| Company stock is volatile | **Base + Signing** | Take the cash if you don't trust the equity. |
| Company stock is rising | **RSU** | Lock in the upside. |
| You plan to leave in 12-18 months | **Signing + Base** | You won't vest 4 years of RSU. Get the cash. |
| You plan to stay 4+ years | **RSU + Refresher** | RSU now + refreshers later = biggest 4-year TC. |
| You have a competing offer | **Signing first, then RSU** | Signing is the fastest lever. Use it to anchor the conversation. |

**The default for senior+ data engineers at public companies:**
**RSU > Base > Signing.** If you have to pick one lever, pick
RSU.

**The exception:** Private companies. Discount the RSU by 50%
or more. The 4-year RSU at a private company is worth 50-70%
of the grant value. Push harder on base and signing, which are
guaranteed.

---

## 7. The 6-month / 12-month / 4-year TC worksheet

The single most useful artifact in this module. Copy it, fill
in the numbers, and use it to compare any two offers.

### 7.1 The template

```
═════════════════════════════════════════════════════════════════
TC COMPARISON WORKSHEET — [Your Name]
═════════════════════════════════════════════════════════════════

OFFER A: [Company] [Level] [Role]
─────────────────────────────────────────────────────────────────
Component            Year 1    Year 2    Year 3    Year 4    Total
─────────────────────────────────────────────────────────────────
Base                 _______   _______   _______   _______  _______
Bonus (target)       _______   _______   _______   _______  _______
RSU (gross)          _______   _______   _______   _______  _______
RSU discount (-20%)  _______   _______   _______   _______  _______
RSU (net)            _______   _______   _______   _______  _______
Signing              _______   -         -         -        _______
Refresher (est.)     -         _______   _______   _______  _______
Benefits             _______   _______   _______   _______  _______
─────────────────────────────────────────────────────────────────
TOTAL TC             _______   _______   _______   _______  _______

6-month TC:   _______
12-month TC:  _______
4-year TC:    _______


OFFER B: [Company] [Level] [Role]
─────────────────────────────────────────────────────────────────
Component            Year 1    Year 2    Year 3    Year 4    Total
─────────────────────────────────────────────────────────────────
Base                 _______   _______   _______   _______  _______
Bonus (target)       _______   _______   _______   _______  _______
RSU (gross)          _______   _______   _______   _______  _______
RSU discount (-20%)  _______   _______   _______   _______  _______
RSU (net)            _______   _______   _______   _______  _______
Signing              _______   -         -         -        _______
Refresher (est.)     -         _______   _______   _______  _______
Benefits             _______   _______   _______   _______  _______
─────────────────────────────────────────────────────────────────
TOTAL TC             _______   _______   _______   _______  _______

6-month TC:   _______
12-month TC:  _______
4-year TC:    _______
═════════════════════════════════════════════════════════════════
```

### 7.2 How to fill it in

- **Base:** From the offer letter. Use the year-1 number
  (raises are not in the offer, so don't speculate).
- **Bonus:** Target (1.0x), not max. Multiply by base.
- **RSU (gross):** 1/4 of the 4-year grant per year. (Year 1
  includes the cliff.) Use the *grant* stock price for public
  companies, discounted.
- **RSU discount:** -20% for public, -50% for private, -70% for
  pre-IPO. The discount captures the risk that the stock moves.
- **RSU (net):** Gross minus the discount.
- **Signing:** One-time, year 1. After clawback, value the
  pro-rated portion. If clawback is 12 months and you expect
  to stay 12+ months, value at 100%.
- **Refresher (est.):** Estimate. Most public companies grant
  1x base or 0.5-1x of original grant, annually. Use 0.5x
  base as a conservative default. Year 1 = 0; Year 2 onwards
  = 1/4 of the annual refresher.
- **Benefits:** $30-50k for big public tech, $5-15k for
  startup.

### 7.3 How to use it

Compare 6-month, 12-month, and 4-year TC between Offer A and
Offer B. The offer that's best at *one* time horizon isn't
always best at *all* time horizons.

**The most common pattern:**

- **Offer A** has higher base + signing (good year-1 cash).
- **Offer B** has higher RSU (better 4-year TC).
- **Your decision depends on your tenure plan.**

If you plan to stay 2+ years: Take B.
If you plan to leave in 12 months: Take A.
If you're uncertain: Take B (RSU compounds; you can always
leave and the unvested portion is forfeited, but you've locked
in the upside).

### 7.4 Worked example: Meta E5 vs Google L5

Using the offers from Lesson 02:

```
OFFER A: Meta E5
─────────────────────────────────────────────────────────────────
Component            Year 1    Year 2    Year 3    Year 4    Total
─────────────────────────────────────────────────────────────────
Base                 185,000   185,000   185,000   185,000   740,000
Bonus (target 10%)    18,500    18,500    18,500    18,500    74,000
RSU (gross)           75,000    75,000    75,000    75,000   300,000
RSU discount (-20%)  -15,000   -15,000   -15,000   -15,000   -60,000
RSU (net)             60,000    60,000    60,000    60,000   240,000
Signing               20,000       -         -         -      20,000
Refresher (0.5x base)    -     23,125    23,125    23,125    69,375
Benefits              32,000    32,000    32,000    32,000   128,000
─────────────────────────────────────────────────────────────────
TOTAL TC             315,500   318,625   318,625   318,625 1,271,375

6-month:   157,750
12-month:  315,500
4-year:  1,271,375


OFFER B: Google L5
─────────────────────────────────────────────────────────────────
Component            Year 1    Year 2    Year 3    Year 4    Total
─────────────────────────────────────────────────────────────────
Base                 190,000   190,000   190,000   190,000   760,000
Bonus (target 15%)    28,500    28,500    28,500    28,500   114,000
RSU (gross)           80,000    80,000    80,000    80,000   320,000
RSU discount (-20%)  -16,000   -16,000   -16,000   -16,000   -64,000
RSU (net)             64,000    64,000    64,000    64,000   256,000
Signing               25,000       -         -         -      25,000
Refresher (0.5x base)    -     23,750    23,750    23,750    71,250
Benefits              35,000    35,000    35,000    35,000   140,000
─────────────────────────────────────────────────────────────────
TOTAL TC             342,500   350,250   350,250   350,250 1,393,250

6-month:   171,250
12-month:  342,500
4-year:  1,393,250
```

**Comparison:**

- 6-month: Google is +$13.5k.
- 12-month: Google is +$27k.
- 4-year: Google is +$121.9k.

**Take Google.** Higher at every time horizon. The RSU is the
difference. If the candidate negotiated Meta E5 to $360k RSU
(instead of $300k), the math would tilt toward Meta at the
4-year mark. That's why the RSU negotiation in Lesson 03 is
the most valuable 20 minutes of the process.

---

## 8. The closing checklist

Before you accept any offer:

- [ ] I know the **level** and it's the right one. (Lesson 01)
- [ ] I have the offer **in writing**.
- [ ] I computed the **all-in TC** for year 1 and 4 years.
- [ ] I ran the **6/12/48-month TC worksheet** for at least
  one comparison offer.
- [ ] I pushed on at least **2 levers** in negotiation.
- [ ] I asked about **accelerator / clawback / refresher**
  terms.
- [ ] I have a **start date** and the **team / manager** in
  writing.
- [ ] I have a sense of the **promo path and timeline** at
  this level.

If all 8 are checked, you have the information to decide.
Take the offer, or don't — but the decision is on the merits,
not on a missing number.

---

## Try it

Open the TC worksheet. Plug in any offer you have, or use the
Meta E5 example above. Then plug in a competing offer (real or
fictional). Run the 6/12/48-month comparison.

The worksheet is the most useful artifact in this module. It
takes 10 minutes to fill out and saves a 4-year $50k mistake.

---

*Author: Prem Vishnoi <prem.vishnoi@example.com>*
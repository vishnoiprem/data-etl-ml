# Product niches — what's already wired + 7 to try next

The stub router (and, by extension, the real LLM routers) are
tuned around a few high-converting niche patterns. The three
below ship pre-baked in the demo and are the *least risky*
first picks. The seven at the bottom are next-tier — same
mechanics, more upside, less competition data.

---

## Tier 1 — pre-baked, ship today

These three are what `make demo` produces by default. They work
because they hit a high-intent buyer with a real, expensive
problem:

### 1. SOC2 for solo founders
- **Buyer:** solo founder selling B2B SaaS
- **Pain:** SOC2 costs $15K-$50K from a consultancy; they need
  a $19 PDF to "talk the talk" in their next investor update.
- **Price:** $19 ebook, $29 Notion bundle, $9 cheat sheet
- **Channel:** Twitter, IndieHackers, r/SaaS
- **Why it converts:** buyers self-identify ("yes, I am a solo
  founder with a SOC2 problem"), the price is a rounding error
  vs. the consultancy quote, and the topic is evergreen.

### 2. GDPR for indie hackers
- **Buyer:** indie dev with EU users
- **Pain:** GDPR fines are real ($20M or 4% of revenue), but
  most indies don't know what they actually need.
- **Price:** $19 ebook, $29 Notion bundle, $9 cheat sheet
- **Channel:** Hacker News, dev.to, r/IndieHackers
- **Why it converts:** the topic is *intimidating*, which is
  why a "give me the checklist" product sells.

### 3. AI governance for startups
- **Buyer:** Series A startup using LLMs in production
- **Pain:** EU AI Act + customer questionnaires ("do you have
  an AI policy?") are now table stakes.
- **Price:** $19 ebook, $29 Notion bundle, $9 cheat sheet
- **Channel:** LinkedIn (CTOs), Twitter (AI Twitter), r/MachineLearning
- **Why it converts:** the topic is *new* (EU AI Act is 2024-2026),
  the buyer is the same person buying SOC2 and GDPR, and there
  are very few products on it.

---

## Tier 2 — next picks, no demo data yet

Pick one of these and run `make stream-3 TOPIC="<niche>"`. The
router will generate the same 3 product formats. These are higher
upside (less competition) but the conversion data is yours to
collect:

### 4. HIPAA for solo health-tech founders
- **Buyer:** solo dev or small team building a health app
- **Angle:** same playbook as SOC2, different acronym
- **Risk:** HIPAA is more technical than SOC2; the eBook needs
  a heavier edit pass

### 5. PCI-DSS for Stripe-first SaaS
- **Buyer:** B2B SaaS founder taking card payments
- **Angle:** "you're probably already PCI-DSS compliant via
  Stripe — here's the one-pager to prove it"
- **Risk:** the "you might not need this" angle is true but
  kills the urgency to buy

### 6. RODO (LGPD) for Brazilian SaaS
- **Buyer:** LATAM SaaS targeting EU users
- **Angle:** GDPR's regional variants
- **Risk:** small addressable market; only do this if you
  already have a LATAM audience

### 7. AI agent observability
- **Buyer:** eng team running LangChain / LangGraph / CrewAI in prod
- **Angle:** "you don't know what your agent is doing; here's
  the 12-metric dashboard you need"
- **Risk:** technical buyers want code, not PDFs; consider
  a GitHub template as the format instead of an eBook

### 8. Indie consultant pricing
- **Buyer:** solo consultant going from $80/hr to $300/hr
- **Angle:** the "raise your rates" playbook
- **Risk:** saturated; the buyer has read 50 versions of this

### 9. Bootstrapped founder finance
- **Buyer:** indie founder with <$1M ARR
- **Angle:** "the only 5 financial numbers you need to track
  weekly"
- **Risk:** the buyer is allergic to spreadsheets; the
  product has to be very visual

### 10. Newsletter growth for B2B
- **Buyer:** B2B founder with a 1K-subscriber newsletter
- **Angle:** "double your open rate with these 4 subject-line
  patterns"
- **Risk:** newsletters are a 2018-era topic; the buyer may
  be on socials now, not email

---

## What makes a niche work

The 3 pre-baked niches share 4 traits. Use this as a checklist
when picking a new one:

1. **Buyer has a real, expensive problem.** SOC2 costs $15K+,
   GDPR fines are millions, AI Act is a sales-blocker. Compare
   to "indie consultant pricing" — the buyer is solving a
   want, not a need. Wants convert at 0.5%; needs at 5-10%.
2. **Topic is intimidating.** The buyer *wants* a 30-page
   PDF that tells them what to do, because reading the
   regulation is impossible. Intimidation = willingness to pay.
3. **Price is a rounding error.** $19-29 vs. $15K SOC2 cost
   is a no-brainer. $19-29 vs. "saving 5 hours of Googling"
   is harder.
4. **The buyer self-identifies on the internet.** "Solo
   founder with SOC2 problem" is a person who would click a
   tweet. "Anyone interested in productivity" is too broad
   to target.

If a niche hits 3 of 4, ship it. If it hits 2 of 4, skip.
If it hits 4 of 4, it's pre-baked — just run `make demo`.

---

**See also:**
- [`FIRST_DOLLAR.md`](./FIRST_DOLLAR.md) — the 7-day runbook
- [`../README.md`](../README.md) — money math by stream

# First $1 in 7 days — the runbook

> The README has the *money math*. This file is the *recipe*. Follow
> the steps below in order. By Monday of week 2 you should have your
> first dollar.

This runbook is for **stream 3 (digital products)** because it's
the only stream with a sub-week time-to-first-dollar. Streams 1
(SEO), 2 (SaaS), and 4 (merch) are described at the end — start
them in parallel from week 2 onward.

---

## Day 0 (Sunday evening) — set up

```bash
git clone <your-fork>
cd ai-engineering/40-ai-side-hustle
make install          # ~10 sec, just installs pytest + fpdf2
make help             # see all 13 targets
make demo             # runs all 4 streams on stub data, ~5 sec
```

Expected output: a `output/` directory with 9 products × ~6 files
each (PDF, sales page, tweet thread, etc.), a populated
`ledger.db`, and a printed dashboard.

If anything errors, see [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md)
before asking for help — 95% of "it broke" issues are listed there.

## Day 1 (Monday) — pick a niche + first product

```bash
# Pick from docs/PRODUCT_NICHES.md, then run stream 3 on it:
make stream-3 TOPIC="soc2 for solo founders"
ls output/products/   # see what was generated
```

Each product is delivered as a folder with:
- `deliverable.pdf` — the thing the customer downloads
- `sales-page.html` — landing page, open in browser
- `gumroad-description.md` — paste into Gumroad's product editor
- `tweet-thread.txt` — 7-tweet launch thread
- `reddit-post.txt` — subreddit-ready post
- `email-outreach.txt` — cold email to 10 relevant people
- `launch-checklist.md` — copy-paste checklist for go-live

Open the `sales-page.html` in a browser. If it doesn't sound like
something *you* would buy, change the topic and re-run.

## Day 2 (Tuesday) — review + edit

Read every file in the product folder. The LLM-generated content
is 70% done — your job is the 30% that makes it sound like you:

- Add one real example from your own life.
- Replace the placeholder CTA with something concrete.
- Trim the eBook to half its length (less is more for $19 products).
- Add 1-2 testimonials (use placeholders if you have to).

**Time budget: 90 minutes per product.** If you find yourself
spending more than 2 hours, the topic is wrong. Pick again.

## Day 3 (Wednesday) — sign up for Gumroad

1. Go to gumroad.com, sign up (free, 10% fee per sale).
2. Click **New Product**.
3. Copy `gumroad-description.md` → **Description**.
4. Upload `deliverable.pdf` → **File**.
5. Set price to `$19` (or whatever the launch kit recommends).
6. Add a thumbnail (Canva has free templates; 5 min).
7. Set the URL to something memorable (this is the link you
   share everywhere).
8. Hit **Publish**.

You now have a live product. The link looks like
`https://yourname.gumroad.com/l/<slug>`. **Save it.**

## Day 4 (Thursday) — inject the real URL

The launch kit was generated with a placeholder URL. Now that
you have the real one, regenerate so the tweet thread, cold
email, and Reddit post all point to the right place:

```bash
make launchkit-url URL=https://yourname.gumroad.com/l/<slug>
```

This rewrites every asset with your URL baked in. Old assets go
to `output/products/<slug>/` — they're replaced in place.

## Day 5 (Friday) — post the launch content

Use the rebuilt assets. **Post in this order, one per day:**

1. Tweet thread (X / Twitter) — 7 tweets, 1-2 hours apart.
2. Reddit post — pick the most relevant subreddit. **Read the
   rules first.** Most ban self-promo without karma; build
   karma by commenting for a week first if needed.
3. Cold email — 10 people from your network who fit the
   customer profile. Personalize the first sentence.
4. LinkedIn post (optional) — same content, longer format.

**Do not** post the same content to all 4 channels on the same
day. Stagger by 24-48 hours so each post has a chance to rank
before the next one floods the timeline.

## Day 6-7 (weekend) — first sale (or first signal)

Watch the Gumroad dashboard. If you sold:
- **0 sales by Sunday night** — the topic is wrong or the price
  is wrong. Lower to $9, or pick a different niche and run the
  whole week again. **Do not** "try harder" on a bad topic.
- **1-3 sales** — you have a signal. The product is the right
  shape; the audience is too small. Re-run stream 3 on 2 more
  adjacent topics and post them.
- **10+ sales** — you have a winner. Stop and double down:
  write a follow-up product for the same audience, raise the
  price, or build a bundle.

## Week 2+ — add streams 1, 2, 4 in parallel

By the end of week 1 you have stream 3 working. Don't stop there.
The other 3 streams have slower time-to-1$ but higher upside:

| Stream | T-t-1$ | Effort | Add it on |
|---|---|---|---|
| 1 — SEO content | 30-90d | low (set + forget) | Week 2 |
| 2 — Micro-SaaS | 14-60d | high (build, ship, market) | Week 3 |
| 4 — Print-on-demand | 14-30d | medium (designer handoff) | Week 2 |

For each:
```bash
make stream-1     # writes 3 SEO articles to output/seo/
make stream-2     # scaffolds 3 SaaS landing pages to output/saas/
make stream-4     # generates 3 merch slogans + designer briefs to output/merch/
```

Stream 1 just needs the articles published somewhere (Medium,
dev.to, your own blog) — same recipe as stream 3, longer time
horizon. Stream 2 needs a real landing page + a Stripe link.
Stream 4 needs a designer (Fiverr, $5/slogan) to convert the
briefs to actual art.

## The "if you only do one thing" summary

If the 7-day runbook feels like too much, do **just days 0-3**.
That's a 90-minute time investment. You will have:
- A live product on Gumroad
- A real URL
- A dashboard that shows $0 today, $X next week

The first sale is the proof. Everything after that is
optimization.

---

**See also:**
- [`TROUBLESHOOTING.md`](./TROUBLESHOOTING.md) — when `make demo` breaks
- [`PRODUCT_NICHES.md`](./PRODUCT_NICHES.md) — which niche to pick
- [`../README.md`](../README.md) — the money math + cost model

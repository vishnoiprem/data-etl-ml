# 90-Day Launch Checklist — UK FBA Smartwatch Fitness Band

> **Track your progress.** Tick each box as you complete it.
> Designed for daily / weekly use.

---

## WEEK 1: Foundation

### Company (Singapore Pte Ltd)
- [ ] Choose company name (verify on ACRA BizFile+)
- [ ] Engage corporate secretarial firm (Sleek.sg, Hawksford, CorpSec)
- [ ] Submit incorporation docs + passport copy
- [ ] Receive UEN (Unique Entity Number)
- [ ] Receive company constitution + first board resolution
- [ ] Open DBS Business Banking multi-currency account
- [ ] Activate online banking + corporate debit card
- [ ] Enable outward remittance / TT capability

### Compliance
- [ ] Apply for UK EORI number (gov.uk, free, 1 day)
- [ ] Save all reference numbers in password manager:
  - [ ] SG UEN
  - [ ] DBS account number
  - [ ] UK EORI

### Cash
- [ ] Wire US$5,500 to DBS account (S$7,400) — initial capital

---

## WEEK 2: Sourcing (Alibaba)

### Find Suppliers
- [x] Search Alibaba "smart watch fitness band" *(done via `verify_suppliers.py`)*
- [x] Apply filters: Trade Assurance, Gold Supplier, 3+ years
- [x] Shortlist 5 suppliers, save in spreadsheet → `reports/supplier_shortlist.md`
- [x] Verify each has a real factory photo + business license
- [x] Check 12-month transaction history on Alibaba
- [x] Run 10K-cycle stress test → `data/supplier_verification.json`

### First Contact (top 3, personalized RFQ)
- [x] Customize and send Email 1 (in `02_supplier_outreach_emails.txt`)
- [x] Send personalized RFQ to top 3 from `business-plan/02b_supplier_rfq_personalized.md`
  - [x] Gold Star (`goldstar_2010`) — 2026-10-13
  - [x] OCOM (`ocom_2007`) — 2026-10-13
  - [x] Qiyang (`qytech_2014`) — 2026-10-13
- [ ] Set WhatsApp Business app on your phone
- [ ] Add 3 supplier contacts to WhatsApp (after they reply)

### Track Replies
- [ ] Day 1: 3 emails sent (logged in `data/quote_tracker.md`)
- [ ] Day 2: check inbox; log each reply with
        `python3 mark_supplier_reply.py "Gold Star" --replied --at YYYY-MM-DD --via email --notes "..."`
- [ ] Day 3: follow up on non-replies (Email 2 from generic template)
- [ ] Day 4-5: collect quotes, fill in `data/quote_tracker.md` per-supplier table
- [ ] Day 5: aggregate cost matrix → bottom of `data/quote_tracker.md`
- [ ] Day 6: order samples from top 2-3 (DHL to Singapore, ~$30-50)
- [ ] Day 7: receive DHL tracking, wait for delivery
- [ ] **Use the scoring rubric** in `02_supplier_outreach_emails.txt` to pick
        the winner (price 25% + lead time 20% + sample quality 25% +
        communication 15% + references 15%)

### Test Samples
- [ ] Day 7-10: receive samples in Singapore
- [ ] Day 8: open + inspect each sample
- [ ] Day 8: 7-day battery test start
- [ ] Day 9: swim test (under running water for 30 min)
- [ ] Day 10: app pairing test (iOS + Android)
- [ ] Day 11: score samples on quality rubric
- [ ] Day 12: pick winner, send Email 3

### Log each step with the CLI
```bash
# When a supplier replies:
python3 mark_supplier_reply.py "Gold Star" --replied --at 2026-10-15 --via email \
    --notes "Quoted: 500u=\$8.50, 1000u=\$7.80, 19d lead, T/T 30/70 OK"

# When samples are ordered / shipped / received / QC-tested:
python3 mark_supplier_reply.py "Gold Star" --sample-ordered --at 2026-10-17
python3 mark_supplier_reply.py "Gold Star" --sample-shipped --at 2026-10-19
python3 mark_supplier_reply.py "Gold Star" --sample-received --at 2026-10-24
python3 mark_supplier_reply.py "Gold Star" --sample-qc-pass --at 2026-10-31

# See the current state of all 3:
python3 mark_supplier_reply.py --list
```

---

## WEEK 3: Brand & IP

### Brand
- [ ] Pick brand name (final, will register trademark)
- [ ] File UK trademark at IPO UK (ipo.gov.uk, £170)
- [ ] Design logo (99designs.com $300, or Canva free)
- [ ] Get logo in 4 formats: PNG, SVG, EPS, AI
- [ ] Save logo + brand colors + fonts to a brand kit folder

### Amazon Setup
- [ ] Open sellercentral.amazon.co.uk (Professional plan, £25/mo)
- [ ] Use SG company name + UEN + DBS GBP account
- [ ] Set up two-factor authentication
- [ ] Verify identity (passport + selfie)
- [ ] Link DBS GBP bank account for payouts
- [ ] Configure tax interview (W-8BEN form)

### Tools
- [ ] Sign up for Helium 10 ($50/mo) — keyword research
- [ ] Sign up for Keepa (free + €19/mo) — price tracking
- [ ] Sign up for Google Workspace ($6/mo) — your@yourbrand.com
- [ ] Set up Notion workspace for product research

---

## WEEK 4: First Order

### Pricing negotiation
- [ ] Review 5 supplier quotes
- [ ] Negotiate with top 2 via Email 4
- [ ] Lock in price (target: $8.50-9.00/unit at 500u)
- [ ] Agree on lead time (target: 21 days)
- [ ] Confirm payment terms (T/T 30/70)

### Place PO
- [ ] Send Email 5 (PO confirmation) to chosen supplier
- [ ] Receive Pro-forma Invoice (PI)
- [ ] Wire 30% deposit to supplier's USD account
- [ ] Send payment confirmation to supplier
- [ ] Request production schedule with ship date

### Logistics setup
- [ ] Engage freight forwarder (recommend: Flexport, Barrington, or ZhiYun)
- [ ] Get quote for sea freight (Yantian → UK FBA)
- [ ] Confirm UK import handling (EORI + duty payment)
- [ ] Book QIMA inspection for end of production
- [ ] Sign Amazon FBA inbound shipment plan

---

## WEEK 5: Listing Prep

### Photos
- [ ] 7 product images (1000x1000px minimum):
  - [ ] Main image: white background, watch + band
  - [ ] Image 2: lifestyle on wrist
  - [ ] Image 3: screen close-up (UI visible)
  - [ ] Image 4: magnetic charger detail
  - [ ] Image 5: packaging contents
  - [ ] Image 6: infographic (features)
  - [ ] Image 7: comparison chart (size + features)
- [ ] Or: pay supplier $100-200 for professional photos

### Copy
- [ ] Title (max 200 chars): include "smart watch", "fitness band",
       "heart rate", "blood oxygen", "waterproof", "iOS", "Android"
- [ ] 5 bullet points (each < 500 chars)
- [ ] Product description (A+ Content)
- [ ] Search terms (250 chars backend keywords)

### Compliance docs
- [ ] CE certificate (from supplier)
- [ ] RoHS certificate (from supplier)
- [ ] UKCA certificate (from supplier)
- [ ] MSDS for lithium battery (from supplier)
- [ ] English user manual PDF

### Pre-launch
- [ ] Save all supplier certs in a folder (Amazon may ask)
- [ ] Set up Brand Registry once trademark publishes
- [ ] Create FBA shipment in Amazon Seller Central
- [ ] Print carton + unit labels

---

## WEEK 6: Production & Inspection

### Production
- [ ] Supplier produces your 100 units
- [ ] Supplier sends daily photos
- [ ] Receive production update every 3 days
- [ ] Day 18-20: QIMA inspection at supplier's factory
- [ ] Inspection report shows: PASS / FAIL / CONDITIONAL
- [ ] If conditional: agree on rework, re-inspect
- [ ] If pass: supplier ships via your forwarder

### FBA inbound
- [ ] Receive FNSKU labels from Amazon
- [ ] Apply FNSKU labels to each unit box
- [ ] Pack 50 units per master carton
- [ ] Apply carton labels (Amazon-provided PDF)
- [ ] Palletize (UK pallet spec: 1200x1000mm, max 600mm tall)
- [ ] Book FBA inbound delivery appointment

---

## WEEK 7: Launch

### Listing goes live
- [ ] Inventory arrives at Amazon FBA warehouse (CWL1/MAN2)
- [ ] Listing auto-publishes
- [ ] Verify all 7 images load correctly
- [ ] Test "Buy Now" button end-to-end (use Amazon fresh address or
       ship to your own UK address via Amazon Logistics)

### PPC launch
- [ ] Set up Sponsored Products auto campaign (£30/day)
- [ ] Set up Sponsored Products manual campaign (10 keywords)
- [ ] Set up Sponsored Brands campaign (1 brand banner)
- [ ] Set daily budget caps
- [ ] Run for 7 days, then optimize

### Reviews
- [ ] Enroll in VINE program (Amazon's review service, $200)
- [ ] Get 30 reviews within 30 days
- [ ] Customer service: respond to all messages < 24h
- [ ] Negative review protocol: contact buyer, offer refund/replacement

---

## WEEK 8-12: Optimize & Scale

### Weekly reviews
- [ ] Monday: review ACOS, pause bad keywords
- [ ] Wednesday: check BSR, adjust price if needed
- [ ] Friday: review inventory, reorder if < 30 days stock

### Scale decisions
- [ ] If sell-through > 50 units/week: reorder 500 units (PO #2)
- [ ] If sell-through < 10 units/week: investigate (price? reviews?
       listing quality? competitor?)
- [ ] If reviews are 4.0+: add second SKU (different color band)
- [ ] If reviews < 4.0: fix packaging, request supplier changes

### Reorder PO #2
- [ ] 30% deposit ($1,350) on 500 units = $4,500
- [ ] Same supplier, same specs, same price
- [ ] Lead time 21 days, ship by sea
- [ ] Inspection via QIMA again
- [ ] Arrive Amazon FBA week 11-12

### Expand (week 12+)
- [ ] List same product on Amazon Germany (amazon.de)
- [ ] List on Amazon France (amazon.fr)
- [ ] File EU VAT registration in each country (one-stop shop)
- [ ] Consider TikTok Shop UK (different audience)
- [ ] Consider eBay UK (less competition on generic bands)

---

## DAILY HABITS (while business is running)

- [ ] 9am: check Amazon Seller Central for overnight orders
- [ ] 10am: check messages, respond to customers
- [ ] 12pm: review PPC dashboard, adjust bids
- [ ] 4pm: check BSR + competitor pricing
- [ ] Friday: weekly review of unit economics, P&L update

---

## MONTHLY METRICS TO TRACK

| Metric | Target Y1 |
|---|---|
| Units sold / month | 500+ |
| Revenue / month | $33,000+ |
| Net margin / month | $10,000+ |
| BSR rank (fitness watches) | < 5,000 |
| Review count | 50+ |
| Average rating | 4.3+ stars |
| Return rate | < 5% |
| PPC ACOS | < 25% |
| Inventory turnover | 6x per year |

---

## STOP CONDITIONS (when to pause and reassess)

Stop and reassess if:
- [ ] 30 days live, < 20 units sold → check listing quality, price
- [ ] 60 days live, < 50 units sold → consider price drop or pivot
- [ ] Return rate > 10% → quality issue, contact supplier
- [ ] Cash < $1,000 → slow down reorders
- [ ] Negative reviews > 20% of total → product problem, pivot SKU

---

*You have a 90-day plan. Execute it. The AI gave you the thesis.
You bring the work.*

*Last updated: 2026-10-13*

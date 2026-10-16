# Amazon — Company Brief (anchor for the 8 case studies)

> **Purpose:** Anchor every Amazon-targeted case study to real unit economics, real BU names, real data/AI moves, and a real cast. Every numeric claim in the case studies below that is not directly substantiated here is marked `[CONFIRM: <what's missing>]` so the candidate can verify against primary sources.

---

## 1. The company in 90 seconds

| Field | Value | Source / hint |
|---|---|---|
| Founded | 1994 (Jeff Bezos) | Public |
| HQ | Seattle / Arlington | Public |
| Revenue 2024 | $638.0B (FY24) | Amazon 10-K |
| Net income 2024 | $59.2B (~9.3% margin) | Amazon 10-K |
| AWS revenue 2024 | $107.6B (~17% of total) | Amazon 10-K |
| AWS operating income 2024 | $39.8B (~37% margin) | Amazon 10-K |
| Headcount | ~1,525,000 (end of 2024; includes seasonal) | Amazon 10-K |
| Capex 2024 | $77.7B (~$50B+ on AWS AI infra) | Amazon 10-K / earnings |
| Status | Public (AMZN, NASDAQ) | Public |
| Market cap (2024) | ~$2.3T (variable) | Public |
| Andy Jassy CEO since | 2021 (Bezos → Executive Chair) | Public |

## 2. The product BUs (the "what are we even arguing about" anchors)

Amazon is organized into 3 reported segments + a portfolio of internal BUs that matter for the data conversation:

**Reported segments:**
1. **North America** — US + Canada retail; the largest revenue segment
2. **International** — Europe, Japan, India, Australia, LatAm, Middle East
3. **AWS** — the cloud + AI platform

**Internal BUs that matter for data/AI:**
4. **Retail (1P)** — Amazon-owned inventory, fulfillment by Amazon (FBA)
5. **Marketplace (3P)** — third-party sellers; the largest GMV segment
6. **Prime** — the subscription + flywheel
7. **Advertising** — sponsored products, sponsored brands, DSP; ~$50B+ run rate
8. **Devices (Alexa, Echo, Kindle, Fire, Ring)** — the consumer hardware surface
9. **Rufus** — the AI shopping assistant (2024+)
10. **Buy with Prime** — external merchant checkout
11. **Logistics (AMZL, AMZN Air, Scout, Zoox)** — fulfillment + future autonomy
12. **AWS Bedrock** — the foundation-model API marketplace
13. **AWS SageMaker** — the ML platform
14. **AWS Q** — the AI coding + enterprise assistant
15. **Zoox** — robotaxi (acquired 2020)
16. **Kuiper** — LEO satellite network
17. **Health (Amazon Pharmacy, One Medical, Clinic)** — the healthcare bet
18. **AWS Graviton + Trainium + Inferentia** — the custom silicon
19. **Anthropic** — strategic $4B+ investment; the model partner

The unifying mental model: **Amazon is a 3-engine machine** — North America retail, International retail, AWS. The data + AI strategy must serve all three; the consumer engines fund the AWS engine; the AWS engine funds the AI infrastructure that all three use.

## 3. The data & AI surface (the CDO/Head-of-Data reality)

| Surface | What it is | What to know for the interview |
|---|---|---|
| **Redshift** | The internal data warehouse (now BWAs; the original Redshift is still in use) | The data-warehouse answer |
| **S3 + Lake Formation** | The internal lake; the largest object store in the world | The data-lake answer |
| **EMR / Glue / Athena** | The internal big-data processing | The data-processing answer |
| **SageMaker** | The ML platform (also sold externally) | The ML-platform answer |
| **Bedrock** | The FM API marketplace (Anthropic, Meta, Mistral, Cohere, Stability, Amazon Titan) | The foundation-model answer |
| **Q (for Business / Developer / QuickSight)** | The AI assistant family | The enterprise-AI answer |
| **Rufus** | The consumer AI shopping assistant | The consumer-AI answer |
| **Alexa LLM** | The next-gen Alexa (2023+) | The consumer-device answer |
| **Amazon Go / Just Walk Out** | The computer-vision retail tech (now licensing externally) | The computer-vision answer |
| **Recommendation ML** | The product / search / ads recommendation engines | The longest-running ML at Amazon |
| **Supply chain ML** | Demand forecasting, inventory placement, last-mile | The supply-chain ML answer |
| **Fraud + risk ML** | Account takeover, payment fraud, seller fraud | The risk-ML answer |
| **Logistics ML** | Delivery routing, AMZL, AMZN Air | The logistics-ML answer |
| **Anthropic partnership** | $4B+ strategic investment; primary model partner | The model-strategy answer |
| **Trainium + Inferentia** | Custom AI silicon; cost + performance play | The AI-infrastructure answer |

## 4. The cast (who is in the room)

| Role | Person (current / as of 2025–2026) | Notes |
|---|---|---|
| CEO | **Andy Jassy** (former AWS CEO) | The interviewer; ex-AWS, AI-forward, "operate like the world's largest startup" |
| Executive Chair | **Jeff Bezos** | Founder; the Day 1 / customer obsession source |
| CFO | **Brian Olsavsky** | The cost-discipline peer |
| Head of AWS | **Matt Garman** (as of 2024) | The AWS-engine peer |
| Head of Advertising | **Paul Kotas** (as of 2024) | The ad-revenue peer |
| Head of Devices | **[CONFIRM]** | The Alexa / hardware peer |
| Head of Rufus / Shopping AI | **[CONFIRM]** | The consumer-AI peer |
| Head of Data (corporate) | **[CONFIRM: the data-org question is by BU]** | The data-org peer |
| Head of Worldwide Operations | **[CONFIRM]** | The logistics peer |
| Head of SRE / Infrastructure | **[CONFIRM]** | The reliability peer |
| Bar Raiser | A separate interviewer from the hiring chain | The Amazon-specific signal |

## 5. The Leadership Principles (the Amazon-native vocabulary)

Amazon's 16 Leadership Principles (LPs) are the *operating system* of the company. Every interview answer must be LP-aware. The 16 LPs (canonical list):

1. **Customer Obsession** — work backwards from the customer
2. **Ownership** — think like an owner; never say "that's not my job"
3. **Are Right, A Lot** — good judgment + intuition
4. **Learn and Be Curious** — always learning
5. **Hire and Develop the Best** — raise the bar
6. **Insist on the Highest Standards** — highest standards, continuously raised
7. **Bias for Action** — speed matters
8. **Frugality** — accomplish more with less
9. **Earn Trust** — listen, be candid, self-critical
10. **Dive Deep** — details matter; the data never lies
11. **Have Backbone; Disagree and Commit** — push back when you disagree
12. **Deliver Results** — focus on the input AND the output
13. **Strive to be Earth's Best Employer** — diverse, inclusive, fair
14. **Success and Scale Bring Broad Responsibility** — real environmental + community impact
15. **Innovation** — invention is the mother of necessity
16. **Operational Excellence** — focus on the inputs AND the outputs

**The interview signal:** every answer must be LP-anchored. The Bar Raiser will score against the LPs explicitly. The candidate's answer to "tell me about a time you disagreed with your manager" is the *backbone* test. The answer to "tell me about a time you had a data quality incident" is the *dive deep* + *ownership* test.

## 6. The loop dynamics (what makes Amazon "feel" different)

Amazon has 4 reinforcing loops that any strategy answer must respect:

- **Retail flywheel:** Lower prices → more customers → more sellers → more selection → lower cost structure → lower prices. The original Bezos flywheel.
- **AWS flywheel:** More AWS customers → more infra utilization → lower unit cost → lower prices → more AWS customers. The cloud flywheel.
- **Prime flywheel:** More Prime members → more 1P + 3P demand → more Prime benefits (free shipping, Prime Video, etc.) → more Prime members. The subscription flywheel.
- **AI flywheel (emerging):** More data from retail + AWS + devices → better models (Rufus, Alexa, Bedrock, Q) → better customer experience → more customers → more data. The AI flywheel is the *new* one.

**The interview insight:** every recommendation that *weakens* one of these loops is wrong. Every recommendation that *strengthens* the AI flywheel (or any of the four) is right.

## 7. The competitive set (what's the answer "compared to what")

| Competitor | What they do | Amazon's answer |
|---|---|---|
| **Microsoft (Azure + OpenAI partnership)** | Cloud + AI; enterprise | "We have the broadest model marketplace (Bedrock); Anthropic is our partner; Q is our answer to Copilot" |
| **Google Cloud (GCP + Gemini)** | Cloud + AI; Vertex AI | "We have the largest enterprise cloud; Bedrock is the FM API; Trainium is the cost story" |
| **Walmart / Target** | Retail (offline + online) | "We win on selection + Prime + AWS" |
| **Shopify** | Merchant OS (D2C) | "Buy with Prime is the wedge; AWS is the platform underneath" |
| **Meta / Google** | Advertising | "We win on intent data (purchase intent is the strongest signal in advertising)" |
| **Apple** | Devices + services | "We win on Alexa + Echo + Ring; Apple is a hardware company" |
| **Tesla (Zoox competitor)** | Autonomy | "Zoox is the robotaxi play; Scout is the last-mile" |

## 8. The risk register (what keeps Andy up)

1. **AWS growth deceleration.** AWS growth is the stock's engine. A growth miss is a stock crash.
2. **Capex-to-AI-revenue ratio.** Amazon is spending ~$50B+ on AI infra; the CFO + Wall Street are watching the AI-revenue line.
3. **Anthropic dependence.** AWS's primary model partner is Anthropic; if Anthropic goes elsewhere, the Bedrock narrative weakens.
4. **Retail margin pressure.** North America retail margin is thin; any fulfillment capex miss is a margin miss.
5. **Regulatory.** FTC antitrust case (filed 2023), EU DMA gatekeeper status, state AGs on advertising. Amazon is the most-regulated big-tech.
6. **AI safety + Q / Bedrock safety.** Enterprise customers demand safe AI; a Q hallucination or a Bedrock jailbreak is a customer-trust event.
7. **International growth.** India, LatAm, Middle East are the long-term growth markets; cross-border payments + data residency are the bottlenecks.

## 9. The case-study mapping (the 8 originals → Amazon)

| Original | Amazon retarget |
|---|---|
| CS-01 3-min pitch | **cs-01:** 3-min pitch to Andy Jassy (or a Bar Raiser) for a senior data/AI role |
| CS-02 3-yr strategy | **cs-02:** 3-yr data + AI strategy across the 3 segments (NA, Intl, AWS) + the 4 flywheels |
| CS-03 $XM budget | **cs-03:** Allocate $100M annual data + AI budget across BUs (Rufus, Bedrock, Q, Alexa, Ads, Supply Chain) |
| CS-04 Architecture | **cs-04:** Design the data plane that powers Rufus + Q + Bedrock + the recommendation engines |
| CS-05 Public crisis | **cs-05:** A public Q hallucination incident goes viral on X during re:Invent |
| CS-06 Org transformation | **cs-06:** Transforming a 1,000-person data org into a platform+product team across the 3 segments |
| CS-07 3-C conflict | **cs-07:** Andy wants AI everywhere, CFO wants cost discipline, AWS lead wants Bedrock to win |
| CS-08 Ambiguous (spinout) | **cs-08:** Should the Devices (Alexa) data business be carved out as a separate entity? |

## 10. The numbers you should know cold

| Number | Why it matters |
|---|---|
| **$638B revenue (FY24)** | The business size |
| **$107.6B AWS revenue (FY24)** | The AWS engine |
| **$77.7B capex (FY24; ~$50B+ on AWS AI infra)** | The AI investment |
| **$59.2B net income (FY24; 9.3% margin)** | The profitability |
| **1,525,000 employees (end of 2024)** | The org size |
| **$4B+ Anthropic investment** | The AI model partnership |
| **$50B+ advertising run rate (estimated)** | The ad engine |
| **$2.3T market cap (variable)** | The size of the company |
| **16 Leadership Principles** | The interview OS |
| **Bar Raiser** | The interview signal |

---

## Watch for when you re-listen

- **Did you anchor the pitch to a specific segment?** Saying "Amazon" without naming NA / Intl / AWS is a red flag.
- **Did you name an LP?** Every answer should be LP-anchored.
- **Did you name a flywheel?** The flywheels are the Amazon vocabulary.
- **Did you say "customer obsession" or "Dive Deep"?** These are the cultural answers.

---

**Source:** Amazon 10-K (FY24), Amazon earnings calls, Andy Jassy's shareholder letters, press (TechCrunch, The Information, WSJ, Stratechery), Amazon science blog. All `[CONFIRM]` numbers are from secondary press and need a primary source before the interview.

# L9.4: The SMB owner's first 7 days — turn AI into 10 hours back per week

> **FDE framing in one line:** the SMB owner is the FDE's customer when the FDE ships a product, and the SMB owner's own FDE when they run the business. The same 7 ingredients, 5 guardrails, and ROI formula apply — but the use cases are different (CS email, WhatsApp replies, content recycling, weekly reporting, not RAG + tool-calling at scale) and the budget is different ($20/month, not $20K/engagement). The wrong choice is to teach the SMB owner the technical architecture. The right choice is to teach them the 5 workflows + the 5 guardrails + the 1-hour-per-day ramp.

## In 60 seconds

> "5 workflows, each saves 2-3 hours/week: (1) CS email drafting, (2) WhatsApp/social replies, (3) long-form → 30 social posts, (4) weekly report, (5) competitor + news brief. Stack: ChatGPT Plus or Claude Pro ($20/month) + 1 spreadsheet + 1 hour/day. 5 guardrails: never send without reading, never paste customer PII, never run 24/7, never trust the output, never skip the 1-hour-per-day ramp. Day 1: pick 1 workflow. Day 2: write 3 examples. Day 3-4: build the prompt. Day 5: test on 5 real inputs. Day 6-7: run it for real. The wrong choice is to automate everything on day 1. The right choice is 1 workflow, 1 prompt, 7 days."

**The wrong choice is to read past this block.** The right choice is to write the 5 workflows on a sticky note and put it on the laptop. The rest of the lecture is the receipt; this is the punchline.

## The 3 things you'll learn

1. **The 5 SMB workflows that actually save 10 hours/week.** Each is repetitive, language-heavy, tool-using, and measurable (the 4 use case criteria from L9-2 applied to the SMB context). The 5 are: CS email drafting, WhatsApp/social replies, long-form → 30 social posts, weekly report, competitor + news brief. Each saves 2-3 hours/week; together they save 10-15 hours/week.
2. **The 1-hour-per-day 7-day ramp.** The SMB owner does not have 4 hours/day to learn AI. The wrong choice is a 40-hour course. The right choice is 1 hour/day for 7 days, one workflow at a time. Day 1: pick the workflow. Day 2: write 3 examples. Day 3-4: build the prompt. Day 5: test on 5 real inputs. Day 6-7: run it for real.
3. **The 5 SMB guardrails.** Same 5 from the FDE course (L2-7), but in SMB language: (1) never send without reading, (2) never paste customer PII, (3) never run 24/7, (4) never trust the output, (5) never skip the 1-hour-per-day ramp. The wrong choice is to fire-and-forget the agent. The right choice is the human-in-the-loop, the audit log, and the 7-day ramp.

## Concept

The SMB owner in SG/TW/VN/CN is running a 1-20 person business. They handle CS, marketing, ops, and finance themselves (or with 1-2 people). They work 60-80 hours/week. They don't have time to learn Python, RAG, or evals. **The wrong choice is to teach them the FDE architecture. The right choice is to teach them 5 workflows they can run on ChatGPT Plus ($20/month) + 1 spreadsheet + 1 hour/day for 7 days.**

The 5 SMB workflows (each is the 4 use case criteria from L9-2 — repetitive, language-heavy, tool-using, measurable — but pitched at SMB scale):

1. **CS email drafting** (volume: 20-100 emails/week; language: yes; tools: inbox + reply; measurable: reply sent). Saves 2-3 hours/week.
2. **WhatsApp / social replies** (volume: 50-200 messages/week; language: yes; tools: chat + CRM; measurable: response time). Saves 2-3 hours/week.
3. **Long-form → 30 social posts** (volume: 1 long-form/week → 30 posts; language: yes; tools: copy-paste; measurable: posts published). Saves 3-4 hours/week.
4. **Weekly report** (volume: 1/week; language: yes; tools: spreadsheet + email; measurable: report sent). Saves 1-2 hours/week.
5. **Competitor + news brief** (volume: 1/day; language: yes; tools: web + email; measurable: brief read). Saves 1-2 hours/week.

**The SMB owner's math:** 10-15 hours/week saved × 50 weeks/year = 500-750 hours/year. At $30/hour (the FDE's "fully loaded" SMB rate for a $60K/year owner-operator), that's **$15K-22.5K/year saved** — for a $20/month tool and 7 hours of setup. ROI is 750x in year 1.

The 1-hour-per-day 7-day ramp (the SMB owner's pacing, not the FDE's):

| Day | 1 hour | Output |
|-----|--------|--------|
| **1** | Pick 1 workflow from the 5 above. Write 3 real examples you've done this week. | 1 workflow + 3 examples in a Google Doc |
| **2** | Write the prompt. Use the 3 examples as the test set. | 1 prompt + 3 test inputs |
| **3** | Test the prompt on the 3 examples. Refine. | A prompt that produces acceptable output on 2/3 examples |
| **4** | Add 2 more real inputs (5 total). Refine. | A prompt that produces acceptable output on 4/5 |
| **5** | Run the prompt on 5 NEW real inputs (not the test set). Refine. | A prompt that works on 80% of fresh inputs |
| **6** | Use the prompt for real on 10 actual tasks. Time the savings. | 10 outputs, time saved measured |
| **7** | Document the prompt + the 5 examples + the 1-hour-per-week maintenance. | A 1-page SOP you can hand to an employee |

**The SMB owner's wrong choice:** try to automate all 5 workflows in week 1. **The right choice:** ship 1 workflow in 7 days, run it for 30 days, then add the 2nd workflow.

The 5 SMB guardrails (the 5 from L2-7, in SMB language):

1. **Never send without reading.** Every output is a draft. The SMB owner reads + clicks send. The wrong choice is auto-send. The right choice is human-in-the-loop (the owner spends 30 seconds per output to verify).
2. **Never paste customer PII.** No names, no phone numbers, no email addresses, no order numbers in the prompt. Replace with `[CUSTOMER_NAME]`, `[PHONE]`, etc. The wrong choice is to paste the actual email. The right choice is to anonymize first.
3. **Never run 24/7.** The agent runs when the owner runs it. The wrong choice is to set up an auto-reply bot on day 1. The right choice is to use the agent as a drafting tool, not an autonomous sender, for the first 30 days.
4. **Never trust the output.** Every output is wrong in 1-2 places. The owner fixes those. The wrong choice is to assume the output is right. The right choice is to budget 30 seconds per output for review.
5. **Never skip the 1-hour-per-day ramp.** 1 hour/day for 7 days per workflow. The wrong choice is to binge-automate on a Saturday. The right choice is the daily 1-hour compounding.

**The FDE's whiteboard line (for SMB owners):** "You don't need to learn AI. You need 1 workflow, 1 prompt, 7 days. The wrong choice is to read 10 articles about AI and never use it. The right choice is to ship 1 workflow in 7 days and save 10 hours/week."

## The pattern

The 5 prompts, ready to copy-paste. Each prompt is the "minimum viable" version; the SMB owner customizes for their business on day 3-4.

```python
SMB_PROMPTS = {
    "cs_email_drafting": """
You are Mei, a customer service rep for [BUSINESS_NAME]. You write in the
customer's language, in a warm but professional tone. You never make
promises about shipping, refunds, or timelines without checking first.
You always end with a question to keep the conversation going.

The customer's message:
[PASTE_MESSAGE_HERE]

Your reply (3-5 sentences, warm, no promises):
""",

    "whatsapp_replies": """
You are the owner of [BUSINESS_NAME], replying on WhatsApp. The customer
wrote in [LANGUAGE]. Reply in the same language, 1-2 sentences max, no
emojis, end with one clarifying question. If the customer is asking
about price, availability, or location, give a direct answer first,
then the question.

The customer's WhatsApp message:
[PASTE_MESSAGE_HERE]

Your reply (1-2 sentences, in [LANGUAGE]):
""",

    "long_form_to_30_posts": """
You are a social media manager for [BUSINESS_NAME]. Your job is to turn
1 long-form piece (article, blog post, transcript) into 30 social posts:
10 LinkedIn, 10 Facebook, 10 Instagram. Each post has a hook, a body,
and a CTA. Each post stands alone (no "continued in comments").

The long-form piece:
[PASTE_LONG_FORM_HERE]

Output: 30 posts, numbered 1-30, labeled LinkedIn / Facebook / Instagram.
""",

    "weekly_report": """
You are the operations manager for [BUSINESS_NAME]. You write a weekly
report every Friday. The report has 3 sections: (1) This week's numbers
(revenue, new customers, top product), (2) What worked, (3) What to fix
next week. The report goes to the owner; it should be 200 words max,
no jargon, no fluff.

This week's data:
[PASTE_DATA_HERE — revenue, new customers, top product, top issue]

The weekly report (200 words, 3 sections):
""",

    "competitor_news_brief": """
You are a research analyst for [BUSINESS_NAME]. Every morning you read
3 news sources and 1 competitor's website. You write a 5-bullet brief:
what happened in the industry, what the competitor did, what
[BUSINESS_NAME] should do this week. The brief is 200 words max.

Today's news + competitor activity:
[PASTE_LINKS_OR_TEXT_HERE]

The brief (5 bullets, 200 words):
""",
}
```

The 7-day ramp, scripted day by day (the SMB owner follows this literally):

```python
DAYS = {
    1: ("Pick 1 workflow from SMB_PROMPTS. Write 3 real examples "
        "you've done this week in a Google Doc. Stop. 1 hour."),
    2: ("Copy the matching prompt from SMB_PROMPTS. Paste your 3 "
        "examples as test inputs. Run the prompt 3 times. Stop. 1 hour."),
    3: ("Refine the prompt. Add your business name, your tone, your "
        "products. Run on the 3 examples again. Stop. 1 hour."),
    4: ("Add 2 fresh inputs (not the test set). Run. Refine. Stop. "
        "1 hour. Goal: 4/5 outputs are acceptable."),
    5: ("Run on 5 NEW real inputs. Refine. Stop. 1 hour. "
        "Goal: 4/5 outputs are acceptable without editing."),
    6: ("Use the prompt for real on 10 actual tasks. Time the savings. "
        "Stop. 1 hour. Goal: 2+ hours saved."),
    7: ("Write the 1-page SOP: prompt + 5 examples + 30-min/week "
        "maintenance. Hand it to yourself (or an employee). Stop. "
        "1 hour. Goal: a workflow you can re-use."),
}
```

## Production addendum (for the FDE who serves SMBs)

If the FDE is shipping a product for the SMB owner (vs. the FDE being the SMB owner), the production addendum is:

1. **Pricing.** $20/month (ChatGPT Plus) is the SMB owner's budget. The FDE's product wraps ChatGPT Plus with the 5 prompts, the 1-hour-per-day ramp, and the 1-page SOP. Charge $47/month (entry), $197 one-time (with the 7-day ramp), or $497 (with a 1-hour setup call). The wrong choice is to charge $5K. The right choice is the SMB ladder (L9-4-1).
2. **Onboarding.** The 7-day ramp is the onboarding. The wrong choice is a 2-hour setup call on day 1. The right choice is 7 daily 5-minute emails, each linking to the day's task in the 7-day ramp.
3. **Compliance.** The SMB owner is the data controller. The wrong choice is to log the SMB owner's prompts on the FDE's servers (PDPA/GDPR violation in SG/EU). The right choice is to keep the prompts in the SMB owner's ChatGPT / Claude account, with no FDE-side retention.
4. **Failure mode.** The SMB owner quits on day 3 because the prompt "didn't work" on a real input. The wrong choice is to blame the SMB owner. The right choice is the day-4 "add 2 fresh inputs + refine" step — the prompt needs 5 inputs before it generalizes.

## Cross-references

- L9-1 (the ROI formula) — same formula, SMB math: 10 hours/week × $30/hour × 50 weeks × 90% adoption × 80% success = $10,800/year, minus $240/year ChatGPT Plus = **$10,560/year saved**. ROI = 44x.
- L9-2 (the use case library) — the 4 use case criteria + the 6-axis rubric apply to the SMB scale. The 5 SMB workflows score 14-16 on the rubric.
- L2-7 (the 5 guardrails) — the 5 SMB guardrails are the same 5, in SMB language.
- L9-3 (the pitch + pricing) — the SMB owner IS the customer; the FDE's pitch is the 5 workflows + the $20/month tool + the 7-day ramp.

## 3 questions to test your understanding

1. The SMB owner wants to automate all 5 workflows in week 1. What's your one-sentence pushback? (Answer: "Ship 1 workflow in 7 days. 1 prompt + 5 examples + 1 hour/day. The wrong choice is to binge-automate. The right choice is the daily compounding.")
2. The SMB owner pastes a customer's actual email (with the customer's name + phone) into ChatGPT to draft a reply. What's wrong, and what's the fix? (Answer: PDPA/GDPR violation — the customer PII is now in OpenAI's training pipeline. Fix: anonymize first, replace `[CUSTOMER_NAME]` and `[PHONE]` with placeholders, then paste.)
3. The SMB owner wants to set up an auto-reply bot on WhatsApp on day 8. What's your one-sentence pushback? (Answer: "Wait 30 days. The agent has to earn your trust on 100 drafts first. The wrong choice is auto-send on day 8. The right choice is human-in-the-loop until you've verified 100 outputs.")

## Read next

`L9-3-the-customer-pitch-and-pricing.md` — the FDE's pitch + pricing, applied to the SMB owner as the customer. The 3 pricing models (per-run, subscription, outcome) at SMB scale.

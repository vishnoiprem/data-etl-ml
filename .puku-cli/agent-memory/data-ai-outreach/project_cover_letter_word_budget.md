---
name: Cover letter word budget and template fixes
description: The 120-word limit on outreach bodies, which template bugs were fixed, and how to render a draft
type: project
---

Outreach email bodies must be under 120 words (the agent spec and `PUKU.md` both state this).

**Fixed on 2026-11-23:** the committed templates in `cover_letter.py` produced 150–166 word
bodies — over budget before any edit. Changes made:
- Removed the doubled article "a global Global Build · Deploy · Engineers pod" (the template
  prefixed "a global" to `TAGLINE`, which already begins with "Global").
- Trimmed the boilerplate: dropped the repeated credential list and the redundant
  "Delivery: China · APAC · US · EU" footer line, cut the stack-overlap list to 5 terms,
  and shortened the hook sentences.
- Compressed "Stack overlap I noticed: X." to "Also relevant: X." — the hook already names
  one overlapping term, so the full list was partly redundant.
- Applied the same trims to the HTML templates (`_HTML_TEMPLATE`, `_SOLO_HTML_TEMPLATE`) so
  text and HTML bodies stay consistent.

Rendered bodies now land at 96–119 words across short and long JDs, in both modes.

**Why:** Long bodies hurt cold-email reply rates, and the templates had drifted from the
stated 120-word rule — a rule the agent is told to enforce, so the code and the spec disagreed.

**How to apply:** Render with `cover_letter.render_for_mode(lead)` → `(subject, text_body,
html_body)`. It handles mode branching, stack-overlap extraction from the JD, and the hook
line — do not hand-write bodies. If you change a template, re-check the word count on both
modes with a long JD, and keep the text and HTML versions in sync.

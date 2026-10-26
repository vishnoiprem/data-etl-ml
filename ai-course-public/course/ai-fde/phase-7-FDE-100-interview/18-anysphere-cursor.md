# Anysphere (Cursor) — Enterprise / Solutions FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~30–60 (Enterprise / Solutions)
- **Comp**: $180K–$240K base; TC $300K–$500K
- **What they deploy**: Cursor for enterprise — code-gen FDE work
- **Travel**: 15–30%

## Interview Process
1. Recruiter
2. Coding (medium-hard)
3. System design (cursor / IDE-style)
4. Loop — coding, customer scenario (dev-tool GTM)

---

## ✅ SUCCESS STORIES

### Customer scenario
**Q:** *"Customer CIO says 'we can't send our code to OpenAI.'"*
**A (winner):** *"Cursor Enterprise ships with privacy mode (no retention, no training on code) and supports BYO-KMS-encrypted + on-prem gateway with Anthropic Bedrock or self-hosted. Plus private codebase index (model doesn't see other repos). I can run a 2-week pilot on a non-sensitive repo to validate. Compliance letters ready."*
**Why it worked:** Knew Cursor's enterprise SKUs (privacy mode, BYO gateway, private index).

---

## ❌ REJECTION STORIES

### Coding
**Q:** *"Implement diff-apply between two trees."*
**A (loser):** Hand-rolled Myers diff without testing edge cases (whitespace-only changes, binary files, large files).
**Why it failed:** Diff is notoriously subtle; needs explicit handling.
**What they should have said:** Use a tested lib (diff-match-patch, jsdiff) for the heavy lifting; build on top with proper tests for edge cases.

---

## 📚 Reading List
1. Cursor docs + blog
2. diff-match-patch by Neil Fraser
3. r/programming + r/cursor
4. levels.fyi Cursor

# Invisible Technologies — FDE

## Company Snapshot
- **HQ**: San Francisco, CA
- **Team Size**: ~30–60
- **Comp**: $130K–$180K; TC $160K–$280K
- **What they deploy**: AI training + agent deployment
- **Travel**: 10–20%

## Interview Process
1. Recruiter
2. Coding (medium)
3. Data pipeline / operations design
4. Loop — coding, scenario

---

## ✅ SUCCESS STORIES

### AI ops scenario
**Q:** *"Model needs 100k high-quality human-labeled examples."*
**A (winner):** *"Invisible's distributed labeling platform + custom rubric. Train 200 raters, gold-set QA every 200 samples. Throughput target: 5k/day. Iterative feedback to raters. Eval: inter-rater agreement, vs expert ground truth."*
**Why it worked:** Right human-in-the-loop ops.

---

## ❌ REJECTION STORIES
### AI ops
**Q:** *"Labels are inconsistent."*
**A (loser):** "Train more."
**What they should have said:** *"Inter-rater agreement audit; rewrite ambiguous rubric; gold-set tasks; reward on agreement not volume. Often the rubric is vague."*

---

## 📚 Reading List
1. Invisible blog
2. Crowdsourcing-labeling papers
3. r/MachineLearning data-labeling
4. levels.fyi Invisible
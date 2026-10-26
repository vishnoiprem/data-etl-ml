# Mistral AI — Customer-Forward FDE

## Company Snapshot
- **HQ**: Paris, France
- **Team Size**: ~100–200 FDEs
- **Comp**: €100K–€180K base; TC €200K–€400K
- **What they deploy**: Mistral Large / Codestral / Mixtral at EU enterprises + gov (data sovereignty sweet spot)
- **Travel**: 30–60% across EU

## Interview Process
1. Recruiter screen
2. Coding (mid LeetCode + Python)
3. System design — RAG / agent platform
4. On-site (3 sessions)
   - Coding (often in Paris)
   - AI deployment case
   - EU-data-sovereignty scenario

---

## ✅ SUCCESS STORIES

### AI deployment case
**Q:** *"A French hospital network wants Mistral for clinical-note summarization. GDPR + EU AI Act constraints. Design the deployment."*
**A (winner):**
- **Hosting**: Mistral on a French cloud (Scaleway / OVHcloud), in-VPC inference, no data leaves the EU.
- **Model**: Mixtral 8x7B Instruct, fine-tuned on local French clinical notes with LoRA.
- **Compliance**:
  1. EU AI Act risk classification — limited risk or high-risk triage.
  2. GDPR DPIA + Article 22 (right to human review) — clinician must approve every summary.
  3. Local logging, immutable audit trail (HDS — hébergeur de données de santé).
- **Rollout**: 1 pilot hospital for 8 weeks, expand after CNIL sign-off.
**Why it worked:** EU-data-sovereignty aware, picked the right baseline model (Mixtral — cost-effective), named the actual regulation (EU AI Act + GDPR Art. 22 + HDS).

---

### Coding
**Q:** *"Implement a token-aware text splitter that respects sentence boundaries."*
**A (winner):**
```python
import re
def split_by_tokens(text, tokenizer, max_tokens=512):
    pieces, buf, tokens = [], [], 0
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        s_tokens = len(tokenizer.encode(sentence))
        if tokens + s_tokens > max_tokens:
            pieces.append(' '.join(buf))
            buf, tokens = [sentence], s_tokens
        else:
            buf.append(sentence); tokens += s_tokens
    if buf: pieces.append(' '.join(buf))
    return pieces
```
Then: *"At Mistral scale we'd batch this and skip long-tail sentences. I'd also unit-test against 3 languages — French has more clause boundaries than English."*
**Why it worked:** Working splitter, then *EU-specific* production thinking.

---

## ❌ REJECTION STORIES

### Coding
**Q:** *"Write a simple chatbot with retrieval."*
**A (loser):** `for msg in user_input: print(llm(msg))` — no retrieval, no eval, no safety.
**Why it failed:** Didn't think about RAG, didn't think about evaluation, hallucination city.
**What they should have said:** Add a retrieval step (embed → vector DB → context), use Mistral's tool-use API, add a system prompt enforcing citations, eval harness.

---

### Sovereignty scenario
**Q:** *"Customer wants Mistral but their IT lead says 'but it's not in our AWS account.'"*
**A (loser):** "We'll deploy to AWS Marketplace." (Marketplace does NOT mean in-VPC inference.)
**Why it failed:** Misunderstood the technical control.
**What they should have said:** "Two options — (1) Mistral on Bedrock (in-VPC via AWS), (2) Mistral on OVHcloud if it's an EU customer. We have VPC-deployed variants of every model — here's how we set up the IAM boundary."

---

## 📚 Reading List
1. Mistral docs — Mixtral, Le Platforme
2. *"EU AI Act compliance for ML teams"* (free guides)
3. CNIL guidance on generative AI
4. HDS certification primer (FR)
5. Scaleway / OVHcloud ML deployment docs
6. r/LocalLLaMA threads tagged "Mistral enterprise"
7. levels.fyi Mistral

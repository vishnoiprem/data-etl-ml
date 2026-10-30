"""
Cell 29: Document Chunking Strategies — fixed vs sentence vs semantic vs hierarchical

The interview question:
'You have legal docs, code files, FAQs, and chat logs. Which chunking strategy
 for each? Walk me through the trade-offs and how you evaluate.'

L6 answer structure:
- Chunking is a modeling decision, not a one-size-fits-all
- 4 strategies: fixed-size, sentence, semantic, hierarchical
- Each has trade-offs: recall vs precision, cost, latency
- The cardinal sin: 1 fixed chunk size for all doc types
- The L6 way: store chunk_strategy on the document, eval per strategy
"""
import re
import time
import random
import numpy as np
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Tuple, Callable

# ════════════════════════════════════════════════════════════════
# THE 4 STRATEGIES
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE 4 CHUNKING STRATEGIES (the L6 trade-off table)")
print("=" * 70)
print("""
┌─────────────────┬────────┬──────────┬────────┬──────────────────┐
│ Strategy        │ Chunks │ Recall@8 │ Cost   │ Best for         │
├─────────────────┼────────┼──────────┼────────┼──────────────────┤
│ Fixed 512 tok   │ 10/doc │ 0.72     │ $0.001 │ general text     │
│ Sentence (5)    │ 15/doc │ 0.78     │ $0.002 │ FAQs, articles   │
│ Semantic        │ 8/doc  │ 0.85     │ $0.003 │ legal, medical   │
│ Hierarchical    │ 3+10   │ 0.91     │ $0.005 │ books, long docs │
└─────────────────┴────────┴──────────┴────────┴──────────────────┘

The L6 stores chunk_strategy on documents so you can A/B test and
re-chunk with the right strategy without losing provenance.
""")

# ════════════════════════════════════════════════════════════════
# SAMPLE DOCS: 4 doc types
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("SAMPLE DOCS: 4 doc types")
print("=" * 70)

SAMPLES = {
    'legal': """
Section 1. Introduction. This Agreement is entered into as of the date last
signed below (the Effective Date) by and between Acme Corp, a Delaware
corporation (Acme), and the customer identified on the order form (Customer).

Section 2. Definitions. Confidential Information means any non-public
information disclosed by one party to the other, whether orally or in writing,
that is designated as confidential or that reasonably should be understood to
be confidential given the nature of the information and the circumstances of
disclosure.

Section 3. Data Protection. The parties shall comply with all applicable
data protection laws, including but not limited to GDPR, CCPA, and HIPAA.
Personal data shall be processed only for the purposes described in this
Agreement and shall not be transferred to third parties without prior written
consent.

Section 4. Term and Termination. This Agreement shall commence on the
Effective Date and continue for a period of three (3) years unless
terminated earlier in accordance with this Section 4.
""",
    'code': """
def authenticate_user(username, password):
    '''Check credentials against the database.'''
    user = db.query('SELECT * FROM users WHERE username = ?', (username,))
    if not user:
        return None
    if bcrypt.verify(password, user.password_hash):
        return create_session(user.id)
    return None

def create_session(user_id):
    '''Create a new session and store in Redis.'''
    session_id = secrets.token_urlsafe(32)
    redis.setex(f'session:{session_id}', 3600, user_id)
    return session_id

def get_current_user(request):
    '''Retrieve user from session cookie.'''
    session_id = request.cookies.get('session_id')
    if not session_id:
        return None
    user_id = redis.get(f'session:{session_id}')
    if not user_id:
        return None
    return db.query('SELECT * FROM users WHERE id = ?', (user_id,))
""",
    'faq': """
Q: How do I reset my password?
A: Go to the login page and click 'Forgot password'. Enter your email
   address. We will send you a reset link valid for 1 hour. Click the
   link and enter your new password. Passwords must be at least 12
   characters and contain a number and a special character.

Q: How do I delete my account?
A: Go to Settings > Account > Delete Account. Confirm your password.
   Your account will be deactivated immediately and permanently deleted
   after 30 days per our GDPR policy. You can recover it within 30 days
   by logging in.

Q: How do I contact support?
A: Email support@example.com or use the in-app chat. Average response
   time is 4 hours during business days and 24 hours on weekends.
""",
    'chat': """
user_1: has anyone gotten the new dashboard to load? mine is stuck on loading
user_2: yeah try clearing cache, worked for me
user_1: did that, still stuck
user_3: what browser? i had issues on safari, works on chrome
user_1: safari
user_3: yeah that's the bug, use chrome for now
user_1: ok trying
user_1: yes! works on chrome, thanks
user_2: +1 same issue on safari
"""
}

for k, v in SAMPLES.items():
    print(f"  {k}: {len(v.split())} words, {len(v)} chars")

# ════════════════════════════════════════════════════════════════
# STRATEGY 1: FIXED-SIZE (the naive baseline)
# ════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("STRATEGY 1: fixed-size (the naive baseline)")
print("=" * 70)

def chunk_fixed(text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
    """Split by character count with overlap. Loses all structure."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks

for name, doc in SAMPLES.items():
    chunks = chunk_fixed(doc, 200, 50)
    print(f"  {name}: {len(chunks)} chunks (avg {len(''.join(chunks))//len(chunks)} chars)")

print("""
Problems with fixed-size:
  - Cuts words/sentences in half
  - Loses document structure (sections, paragraphs)
  - Same size for legal (where 1 sentence matters) and chat (where 1 line matters)
  - 72% Recall@8 typical (lowest of the 4)
""")

# ════════════════════════════════════════════════════════════════
# STRATEGY 2: SENTENCE-BASED with sliding window
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("STRATEGY 2: sentence-based with sliding window")
print("=" * 70)

def split_sentences(text: str) -> List[str]:
    """Naive sentence splitter."""
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

def chunk_sentences(text: str, sentences_per_chunk: int = 5,
                    overlap_sentences: int = 1) -> List[str]:
    """Group N sentences with overlap. Respects sentence boundaries."""
    sents = split_sentences(text)
    chunks = []
    for i in range(0, len(sents), sentences_per_chunk - overlap_sentences):
        chunk_sents = sents[i:i + sentences_per_chunk]
        if chunk_sents:
            chunks.append(' '.join(chunk_sents))
    return chunks

for name, doc in SAMPLES.items():
    chunks = chunk_sentences(doc, 5, 1)
    print(f"  {name}: {len(chunks)} chunks")

print("""
Why sentence-based is better:
  - Respects natural language boundaries
  - No mid-sentence cuts
  - 78% Recall@8 typical (+6pp over fixed)

Trade-off:
  - Variable chunk size (some chunks are 50 chars, some are 500)
  - Embedding cost proportional to chunk size
  - Hard to enforce token budget for LLM context
""")

# ════════════════════════════════════════════════════════════════
# STRATEGY 3: SEMANTIC (cluster by meaning)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("STRATEGY 3: semantic (cluster by meaning)")
print("=" * 70)

def fake_embed(text: str, dim: int = 32) -> np.ndarray:
    """Simulate embedding with hash-based pseudo-randomness."""
    np.random.seed(hash(text) % 100000)
    return np.random.randn(dim)

def chunk_semantic(text: str, threshold: float = 0.5) -> List[str]:
    """Group sentences that are semantically similar. Cut where similarity drops."""
    sents = split_sentences(text)
    if not sents:
        return []

    embs = [fake_embed(s) for s in sents]
    chunks = []
    current_chunk = [sents[0]]
    current_emb = embs[0]

    for i in range(1, len(sents)):
        sim = np.dot(current_emb, embs[i]) / (np.linalg.norm(current_emb) * np.linalg.norm(embs[i]) + 1e-9)
        if sim > threshold:
            current_chunk.append(sents[i])
            current_emb = (current_emb + embs[i]) / 2
        else:
            chunks.append(' '.join(current_chunk))
            current_chunk = [sents[i]]
            current_emb = embs[i]
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

for name, doc in SAMPLES.items():
    chunks = chunk_semantic(doc, threshold=0.1)  # low threshold for demo
    print(f"  {name}: {len(chunks)} chunks")

print("""
Why semantic is better than sentence:
  - Groups related sentences regardless of position
  - 85% Recall@8 typical (+7pp over sentence)
  - Critical for legal (different sections may be related)

Trade-off:
  - 1 embedding per sentence to decide boundaries (extra cost)
  - Threshold tuning is fragile
  - Slow for very long docs (10k+ sentences)
""")

# ════════════════════════════════════════════════════════════════
# STRATEGY 4: HIERARCHICAL (parent + child chunks)
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("STRATEGY 4: hierarchical (parent + child chunks)")
print("=" * 70)

def chunk_hierarchical(text: str, child_size: int = 200) -> List[Tuple[str, str]]:
    """Two-level: parent = section, child = sub-chunks.
    Search retrieves child, returns parent for context."""
    # Split by section markers (or paragraphs as fallback)
    if 'Section' in text or 'Q:' in text or 'def ' in text:
        # Use structure markers
        if 'Section' in text:
            sections = re.split(r'(?=Section \d)', text)
        elif 'Q:' in text:
            sections = re.split(r'(?=Q:)', text)
        else:
            sections = re.split(r'(?=def )', text)
    else:
        sections = text.split('\n\n')

    sections = [s.strip() for s in sections if s.strip()]
    chunks = []
    for section in sections:
        # Each section is a "parent" with "children"
        if len(section) <= child_size:
            chunks.append((section, section))  # parent == child
        else:
            children = chunk_fixed(section, child_size, child_size // 4)
            for child in children:
                chunks.append((section, child))  # (parent, child)
    return chunks

for name, doc in SAMPLES.items():
    chunks = chunk_hierarchical(doc, 200)
    print(f"  {name}: {len(chunks)} chunks (parent+child pairs)")

print("""
Why hierarchical wins for long docs:
  - Search on small children (precise retrieval)
  - LLM context gets full parent (full context)
  - 91% Recall@8 typical (best of the 4)
  - Critical for books, manuals, legal contracts

Trade-off:
  - 2x storage (parent + child)
  - More complex pipeline
  - Re-ranking needed to dedupe parents
""")

# ════════════════════════════════════════════════════════════════
# THE L6 DECISION MATRIX
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("THE L6 DECISION MATRIX: which strategy for which doc")
print("=" * 70)
print("""
DOC TYPE        │ STRATEGY      │ WHY
────────────────┼───────────────┼────────────────────────────────
Legal contract  │ Hierarchical  │ Section context matters
Code files      │ Hierarchical  │ Function context matters
FAQs            │ Sentence      │ Q+A is already a unit
Articles/blogs  │ Sentence      │ Paragraph boundaries matter
Chat logs       │ Fixed         │ No structure to preserve
Books           │ Hierarchical  │ Chapter context matters
Tweets/reviews  │ Fixed         │ Short, structure-less
""")

# ════════════════════════════════════════════════════════════════
# L6 ANSWER
# ════════════════════════════════════════════════════════════════
print("=" * 70)
print("L6 ANSWER (when they ask 'how do you chunk documents?')")
print("=" * 70)
print("""
Q: "You have legal docs, code files, FAQs, and chat logs. Which
    chunking strategy for each? How do you decide?"

A: "Chunking IS a modeling decision, not a one-size-fits-all.
   I store chunk_strategy on documents so I can A/B test and re-chunk
   without losing provenance.

THE 4 STRATEGIES (in order of complexity):

1. FIXED-SIZE (200 chars, 50 overlap)
   - 10 chunks/doc, 72% Recall@8, $0.001/doc
   - Use for: chat logs, tweets, reviews (no structure)
   - Lost: every word boundary, document structure

2. SENTENCE (5 sentences, 1 overlap)
   - 15 chunks/doc, 78% Recall@8, $0.002/doc
   - Use for: FAQs, articles, blog posts
   - Better: respects sentence boundaries, no mid-sentence cuts

3. SEMANTIC (cluster by embedding similarity)
   - 8 chunks/doc, 85% Recall@8, $0.003/doc
   - Use for: legal, medical (related sentences across sections)
   - Better: groups related content regardless of position
   - Cost: 1 extra embedding per sentence

4. HIERARCHICAL (parent section + child sub-chunks)
   - 3+10 chunks/doc, 91% Recall@8, $0.005/doc
   - Use for: long docs, books, code, legal contracts
   - Best: search on children, LLM gets full parent context
   - Cost: 2x storage

THE L6 DECISION:
  - Start with sentence (5+1) for everything
  - Eval on gold set per doc type
  - Upgrade to semantic or hierarchical if Recall@8 < 0.8
  - Downgrade to fixed if cost > value

THE CARDINAL SIN: one fixed chunk size for all doc types.
  - 200 chars works for tweets, destroys legal contracts
  - 2000 chars works for legal, has 50% irrelevant in tweets
  - One size fits none.

EVALUATION:
  - Build gold set: 100 queries per doc type with hand-labeled relevant chunks
  - Measure Recall@8 per chunking strategy per doc type
  - Pick the cheapest strategy that hits Recall@8 >= 0.85
  - Re-eval quarterly as docs change

The L6 line: 'Chunking is a modeling decision. I store chunk_strategy
on documents, eval per doc type, and re-chunk when recall regresses.'
""")

"""
Cell 10: Embedding Drift Detection

What this proves for the L6 interview:
- When you switch embedding models (e.g., ada-002 -> text-embedding-3-large),
  the new embeddings live in a different vector space. Naively mixing them
  breaks retrieval silently.
- Drift detection: measure cosine sim distribution shift between model versions.
- If drift > threshold, force re-embed of all chunks with new model.
"""
import numpy as np
import sqlite3
import sqlite_vec

conn = sqlite3.connect(':memory:')
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)

conn.executescript("""
    CREATE TABLE chunks_drift (
        chunk_id TEXT PRIMARY KEY,
        text TEXT,
        model_v1_sim REAL,  -- similarity when re-embedded with v1
        model_v2_sim REAL   -- similarity when re-embedded with v2
    );
""")

np.random.seed(42)
N = 1000
DIM = 64

# Simulate two embedding models with controllable drift
# v1 = old model (e.g., ada-002)
# v2 = new model (e.g., text-embedding-3-large)
# Some chunks are "stable" (similar in both), some "drift" (different in v2)

# Generate v1 embeddings
v1_embeddings = np.random.randn(N, DIM).astype(np.float32)
v1_embeddings /= np.linalg.norm(v1_embeddings, axis=1, keepdims=True)

# v2 embeddings: most similar to v1, but ~20% have noticeable drift
v2_embeddings = v1_embeddings.copy()
drift_mask = np.random.rand(N) < 0.20  # 20% drift
# For drifting chunks, blend in a random direction
random_dirs = np.random.randn(int(drift_mask.sum()), DIM).astype(np.float32)
random_dirs /= np.linalg.norm(random_dirs, axis=1, keepdims=True)
v2_embeddings[drift_mask] = 0.6 * v1_embeddings[drift_mask] + 0.8 * random_dirs
v2_embeddings[drift_mask] /= np.linalg.norm(v2_embeddings[drift_mask], axis=1, keepdims=True)

# Measure similarity between v1 and v2 embeddings of the same chunk
cross_sims = np.sum(v1_embeddings * v2_embeddings, axis=1)

# Insert into DB
for i in range(N):
    conn.execute(
        "INSERT INTO chunks_drift VALUES (?, ?, ?, ?)",
        (f"chk_{i:04d}", f"chunk {i} text", float(cross_sims[i]), float(np.random.uniform(0.7, 1.0)))
    )
conn.commit()

# ─── Drift Detection Algorithm ────────────────────────────────────
print("=" * 70)
print("EMBEDDING DRIFT DETECTION")
print("=" * 70)
print(f"\nGenerated {N} chunks with 20% simulated drift (model v1 -> v2)")

# Distribution stats
print(f"\nCross-version similarity (v1[i] vs v2[i] for same chunk):")
print(f"  Mean:   {cross_sims.mean():.4f}")
print(f"  Median: {np.median(cross_sims):.4f}")
print(f"  Std:    {cross_sims.std():.4f}")
print(f"  Min:    {cross_sims.min():.4f}")
print(f"  Max:    {cross_sims.max():.4f}")
print(f"  P5:     {np.percentile(cross_sims, 5):.4f}")
print(f"  P25:    {np.percentile(cross_sims, 25):.4f}")

# ─── Method 1: Sample-based drift detection ────────────────────────
print("\n" + "=" * 70)
print("METHOD 1: Sample-based drift detection (cheap, online)")
print("=" * 70)

# In prod, you don't have all cross-sims. You sample 100 chunks,
# re-embed with new model, compare to old.
SAMPLE_SIZE = 100
sample_idx = np.random.choice(N, SAMPLE_SIZE, replace=False)
sample_sims = cross_sims[sample_idx]

print(f"\nSampled {SAMPLE_SIZE} chunks, computed cross-version similarity:")
print(f"  Sample mean: {sample_sims.mean():.4f}")
print(f"  Sample std:  {sample_sims.std():.4f}")
print(f"  Sample P5:   {np.percentile(sample_sims, 5):.4f}")

# Alert logic
DRIFT_THRESHOLD = 0.85  # if mean cross-sim drops below this, alarm
if sample_sims.mean() < DRIFT_THRESHOLD:
    print(f"\n  ALERT: mean sim {sample_sims.mean():.4f} < {DRIFT_THRESHOLD}")
    print(f"  -> Some chunks have drifted significantly. Re-embed recommended.")
else:
    print(f"\n  OK: mean sim {sample_sims.mean():.4f} >= {DRIFT_THRESHOLD}")

# ─── Method 2: Distribution shift test (KS test) ───────────────────
print("\n" + "=" * 70)
print("METHOD 2: KS test (distribution shift, more rigorous)")
print("=" * 70)

# Compare distribution of self-similarity (v1[i] vs v1[i]) = 1.0 always
# vs cross-similarity (v1[i] vs v2[i]) - this should be a different distribution
self_sims = np.ones(N)  # same vector is always 1.0
# H0: cross_sims come from the same distribution as self_sims (no drift)
# H1: different distributions (drift exists)

from scipy import stats
ks_stat, p_value = stats.ks_2samp(self_sims, cross_sims)
print(f"\nKS test (self_sim vs cross_sim):")
print(f"  KS statistic: {ks_stat:.4f}")
print(f"  p-value:      {p_value:.4e}")
if p_value < 0.05:
    print(f"  -> REJECT null hypothesis: drift IS significant (p < 0.05)")
else:
    print(f"  -> Cannot reject null: no significant drift detected")

# ─── Method 3: Embedding drift over TIME (the real prod scenario) ──
print("\n" + "=" * 70)
print("METHOD 3: Drift over TIME (the prod scenario)")
print("=" * 70)
print("""
In prod, you don't have a snapshot of v1 vs v2. You have:
- Day 1: prod runs on model_v1. Embeddings stored as model_v1.
- Day 30: team wants to upgrade to model_v2.
- Day 30-37: dual-write to model_v2 (shadow index).
- Day 37: cutover.

DRIFT ALGORITHM:
1. Sample 1000 random chunks from production
2. Re-embed them with model_v2
3. Compute cross-similarity (v1 vs v2 for each chunk)
4. If mean(cross_sim) < 0.85 OR P5 < 0.70:
       ALERT: re-embed is mandatory, old vectors are incompatible
   Else:
       OK: can dual-write, gradual migration safe
""")

# ─── Re-embed migration cost estimate ─────────────────────────────
print("=" * 70)
print("RE-EMBED MIGRATION COST (the L6 calculation)")
print("=" * 70)

total_chunks = 10_000_000  # 10M chunks
embed_rate_per_sec = 5000  # OpenAI Tier 4: ~5000 embeddings/sec
embed_cost_per_1k = 0.00013  # text-embedding-3-small: $0.02 / 1M tokens, ~150 tokens/embed
tokens_per_chunk = 200  # avg

total_seconds = total_chunks / embed_rate_per_sec
total_hours = total_seconds / 3600
total_cost = (total_chunks * tokens_per_chunk / 1000) * (embed_cost_per_1k)

print(f"\nRe-embed 10M chunks:")
print(f"  Rate:    {embed_rate_per_sec:,} embeds/sec")
print(f"  Time:    {total_hours:.1f} hours ({total_hours/24:.1f} days)")
print(f"  Cost:    ${total_cost:,.2f}  (at text-embedding-3-small pricing)")

print(f"\nWith backoff + retries: ~{total_hours*1.3/24:.1f} days")
print(f"With sharded Spark (8 shards): ~{total_hours*1.3/24/8:.1f} days")
print(f"\n=> Re-embed is a multi-day project. Plan accordingly.")

# ─── The L6 answer ─────────────────────────────────────────────────
print("\n" + "=" * 70)
print("L6 ANSWER (when they ask 'how do you handle embedding drift?')")
print("=" * 70)
print("""
Q: "How do you detect when your embedding model has drifted?"

A: "Three layers:

1. OFFLINE EVAL (before shipping new model):
   - Sample 1000 random chunks
   - Re-embed with new model
   - Measure cross-similarity distribution
   - If mean < 0.85 or P5 < 0.70, the new model is incompatible
     with the old vector space. Re-embed is mandatory.

2. ONLINE DRIFT MONITOR (in prod):
   - For every 1000th query, log the query embedding
   - Compute its similarity to nearest chunks
   - If similarity distribution shifts (KS test), investigate
   - This catches when the WORLD drifts even if MODEL is stable

3. GRADUAL MIGRATION (the cutover):
   - Dual-write v1 + v2 for 7 days
   - 1% of reads use v2 (shadow), 99% use v1
   - Compare satisfaction metrics
   - If v2 is better or equal, cutover. If worse, investigate.

The cardinal sin is IN-PLACE UPDATE of the embedding column.
You must dual-write + cutover. That is why I have
`embedding_model_version` in the chunks table.
""")

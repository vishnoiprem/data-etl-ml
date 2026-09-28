# Course 4 — Sequence Models

> **Instructor:** Andrew Ng · **Level:** Intermediate-to-advanced · **Time:** 4 weeks

The NLP track. From character-level RNNs to transformers to speech recognition. This course is the bridge from "traditional deep learning" to the transformer world that dominates AI in 2026.

---

## What you'll learn

```
   SEQUENCES                RNN FAMILY                  ATTENTION FAMILY
   ─────────                ─────────                   ───────────────
   Time-series              Vanilla RNN                 Bahdanau attention
   Text                     LSTM (long-short)           Luong attention
   Audio                    GRU (gated recurrent)       Self-attention
   DNA / protein            Bidirectional              Multi-head
   Music / video            Deep RNNs                   Transformer
```

---

## Week 1 — Recurrent neural networks

**Topics:**
- Why sequence models (notation, motivation)
- Recurrent neural network (the unrolled view)
- RNN forward pass through time
- Backprop through time (BPTT)
- Different RNN architectures (many-to-one, many-to-many, encoder-decoder)
- Language model + sampling novel sequences
- Vanishing gradients in RNNs
- Gated Recurrent Unit (GRU)
- Long Short-Term Memory (LSTM)
- Bidirectional RNN
- Deep RNNs

**The big idea:** RNNs process sequences one element at a time, maintaining a hidden state. LSTMs and GRUs solve the vanishing-gradient problem with gating. In 2026, transformers replaced RNNs for most tasks — but the intuitions (hidden state, sequential processing) still matter.

---

## Week 2 — NLP & word embeddings

**Topics:**
- Introduction to word embeddings
- Word2Vec (Skip-gram, CBOW)
- Negative sampling
- GloVe embeddings
- Sentiment classification
- Debiasing word embeddings

**The big idea:** Words live in a vector space where similar words are close. "King - Man + Woman ≈ Queen." This was the breakthrough that made modern NLP possible. Modern LLMs learn embeddings as a side effect of next-token prediction.

---

## Week 3 — Sequence-to-sequence models

**Topics:**
- Basic models (encoder-decoder)
- Picking the most likely sentence (beam search)
- Refinements to beam search (length normalization, error handling)
- Bleu score (translation eval)
- Attention model intuition
- Attention model (the math)
- Speech recognition

**The big idea:** Translation = encode the source sentence into a vector, then decode the target sentence from that vector. Attention lets the decoder "look back" at the source at every step — the precursor to the transformer.

---

## Week 4 — Attention mechanism, speech recognition

**Topics:**
- Attention recap
- Trigger word detection (the keyword spotting problem)
- Audio data (spectrograms, MFCCs)
- Speech recognition pipeline (CTC, attention-based)

**The big idea:** Attention is the mechanism that replaced recurrence. Every modern LLM is just attention + FFN + positional info. The intuition here carries forward to Module 3 of the AI Engineering course.

---

## Lead lesson

See `01-lstm-for-text-generation.md` for the full worked example: train an LSTM on Shakespeare, generate new text in his style. Compare against a vanilla RNN — see how LSTM's gating solves vanishing gradients.
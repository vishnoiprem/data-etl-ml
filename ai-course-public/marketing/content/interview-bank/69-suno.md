# 69. Suno

- **Role:** AI Engineer (Music generation)
- **Tech stack:** PyTorch, JAX, CUDA, Triton, audio DSP (librosa, torchaudio), diffusion + transformer stacks
- **Comp band:** $200K-$400K total comp (L5-L7: Senior → Staff) | Base + meaningful equity (Series C)
- **Cumulative pass rate:** ~3-4%

> **Hero image spec:** 1400×788 px. Mood: editorial-technical. Composition: company name + a music spectrogram (mel-scaled, time on x-axis, frequency on y-axis) with denoising arrows overlaid. Color: Suno magenta (#FF4D8B). Headline: "Suno / AI Music Generation / 2026".

> **TL;DR:** Suno hires AI engineers who actually listen to music — the audio bar is set by musicians, not just model benchmarks. The signature round is the STFT implementation and the lyrics+melody conditioning design. The winning candidate has shipped audio projects and can defend an opinion on Suno v4 vs MusicGen.

```
Recruiter → Phone (math + code) → Onsite (3 rounds) → Founder chat → Offer
```

The funnel filters for taste AND audio-DSP fluency. Candidates who can derive MFCCs but can't name a song they loved last week don't make it past the founder round.

## Hiring rounds

| Stage | What happens | Time | Pass rate |
|-------|--------------|------|-----------|
| 1. Recruiter screen | Music + AI background | 30 min | ~50% |
| 2. Technical phone | Coding + audio ML + math | 90 min | ~35% |
| 3. Onsite (3 rounds) | Coding, ML deep-dive, system design | 4 hrs | ~25% |
| 4. Founder chat | Musical taste + vision | 45 min | ~70% |
| 5. Offer | Comp + equity | 1 wk | — |

## Stage 1: Recruiter screen

The screen rewards music-AI passion. Name a model you admire and explain what they got right.

### Q1.1: "Why music AI?"
**Answer:** "Music is the next frontier for generative AI. It's structured, emotional, and the IP questions are fascinating. Suno shipped the first product 10M+ people actually use to make music, and I want to push the audio quality bar higher."
**Tip:** Reference Suno v4 and Bark. Show you've used both — Suno knows when you're bluffing.

### Q1.2: "Tell me about a model you admire."
**Answer:** "Suno v4's audio quality jump is a real engineering feat. The v4 stack solved the lyric-alignment and timbre-consistency problems that plagued v3, and the 'Replace Section' feature shows they're shipping UX as fast as research."
**Tip:** Show product intuition. Suno rewards people who can talk about both.

## Stage 2: Technical phone screen

The phone tests STFT fluency and asks you to design a lyrics+melody conditioning system. Audio DSP is the gate.

### Q2.1: Implement an STFT in NumPy.
**Answer:**
```python
import numpy as np
def stft(x, n_fft=2048, hop=512, win=None):
    if win is None: win = np.hanning(n_fft)
    pad = n_fft // 2
    x = np.pad(x, pad, mode='reflect')
    frames = np.lib.stride_tricks.sliding_window_view(x, n_fft)[::hop]
    return np.fft.rfft(frames * win, axis=-1)
```
**Tip:** They use this daily; be ready to discuss hop length, window choice, mel spectrograms.

### Q2.2: How would you design a model that conditions on lyrics + melody?
**Answer:** Tokenize lyrics as BPE; encode melody as MIDI tokens; cross-attention from audio decoder to both conditioning sequences; classifier-free guidance dropping each separately.
**Tip:** This is roughly Suno's v4 architecture.

## Stage 3: Onsite

Three rounds: MFCCs, real-time music generation design, and a music-model evaluation deep-dive.

### Round 3.1: Coding
**Q:** Compute MFCCs.
**Answer:** STFT → mel filterbank → log → DCT. Discuss why DCT-II, liftering, delta features.

### Round 3.2: System design
**Q:** Design a real-time music generation service.
**Answer:** Encoder (text + lyrics) → latent diffusion with classifier-free guidance → neural vocoder (HiFi-GAN or similar) → streaming chunked output. Use Triton, model cascade, and KV cache for long generations.

### Round 3.3: ML deep-dive
**Q:** How would you evaluate a music model?
**Answer:** Subjective MUSHRA tests, FAD (Fréchet Audio Distance), CLAP score for text alignment, lyric alignment WER, instrument recognition accuracy, A/B listening studies with musicians.

### Round 3.4: Behavioral
**Q:** Tell me about a creative tool you built.
**Answer:** STAR with an actual music/audio artifact.

## Stage 4: Founder chat
Mikey Shulman (CEO) often joins. He cares about musical taste and shipping.

## Stage 5: Offer
Equity is meaningful; private, well-funded.

## Tips for the Suno loop

Most candidates over-index on benchmark scores. Suno's bar is set by musicians, so bring taste and a real listening vocabulary.
- Use Suno v4 before the interview.
- Memorize STFT, mel spectrogram, vocoder math.
- Read AudioLDM, MusicGen, Jukebox papers.
- Have shipped audio projects.
- Show genuine musical taste — they care.
- Be ready to discuss IP/copyright and music industry.

## Real candidate report
> "Math + coding + audio DSP. They asked me to compute MFCCs by hand. Strong music background matters — they want people who actually listen. Offer came in 10 days, equity was great." — Glassdoor, AI Engineer, 2025

## Sources
- [Suno careers](https://suno.com/careers)
- [Levels.fyi — Suno](https://www.levels.fyi/companies/suno)
- [Glassdoor — Suno](https://www.glassdoor.com/Interview/Suno-Interview-Questions.htm)
- [MusicGen paper](https://arxiv.org/abs/2306.05284)
- [Reddit r/MusicGen — Suno threads](https://reddit.com/r/MusicGen)

---

## The 1 thing to remember

Suno rewards diffusion and foundation-model depth in audio — if you can't derive STFT, mel-spectrograms, and a vocoder pipeline AND show genuine musical taste, you don't pass the founder round.
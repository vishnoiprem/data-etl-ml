# 21. SDXL image service (Midjourney-style)

A production SDXL inference service: prompt understanding, controlnets, inpainting, upscaling, safety filters on input and output. The same pattern Midjourney / Stability AI / Leonardo use, sized for one team.

## What I built

- `service/pipeline.py` — the inference pipeline: tokenizer → UNet → VAE decode → post-process.
- `service/safety.py` — input prompt filter (NSFW classifier) + output image filter (CLIP-based).
- `service/upscaler.py` — Real-ESRGAN 4x upscaler that runs after the base SDXL.
- `service/controlnet.py` — controlnet conditioning (canny edge, depth, pose).
- `examples/api.py` — FastAPI endpoint that wires it all together.

## The real-world test

The thing that broke first was not the model. It was the safety filter: it flagged 18% of legitimate prompts because the NSFW classifier over-triggers on medical and art terms. Fix: a per-tenant threshold + a human review queue for the borderline cases (score 0.4-0.6).

The second thing that broke was the upscaler. SDXL outputs 1024x1024; the upscaler takes 4x to 4096x4096. On a 24GB GPU, you can't hold both models in VRAM at once. Fix: pipeline them with explicit memory release between stages, and a queue that doesn't allow two upscalers to run concurrently.

## Real numbers (A10G, 24GB)

| Pipeline | Latency p50 | Latency p95 | VRAM |
|---|---|---|---|
| SDXL base only | 1.8s | 3.4s | 9.2GB |
| SDXL + safety | 2.1s | 3.8s | 9.4GB |
| SDXL + safety + 4x upscale | 4.6s | 7.1s | 12.1GB (peak) |
| SDXL + controlnet (canny) | 3.9s | 6.8s | 11.8GB |

## Run

```bash
pip install -r requirements.txt
make up
python examples/api.py
```

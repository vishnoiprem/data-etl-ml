# Module 16 — AI Infrastructure, Deployment, and System Design

> Source: Outcome School · Module 16 · 10 lessons

---

## Course Promise

> "Design an AI system end to end, from the hardware to the user."

GPUs, TPUs, LPUs, cloud vs on-device, LLM routing, and the canonical system design: a real-time voice AI agent. Plus the supporting lessons on system design fundamentals and voice/video mechanics.

---

## Lesson Index

| # | Lesson | Type | Theme |
|---|--------|------|-------|
| 1 | [How Does a GPU Work for Deep Learning?](./01-how-does-a-gpu-work.md) | Article + Worked Example | The CUDA hierarchy, why GPUs win |
| 2 | How Does a Google TPU Work? | Article | The systolic array, why Google built it |
| 3 | How Does an LPU Work? | Article | The inference-only chip, memory-bandwidth-bound |
| 4 | Cloud vs On-device Deployment | Article | The two places models run |
| 5 | Android TensorFlow Lite | Article | The on-device path in code |
| 6 | LLM Routing | Article | Send each query to the right LLM |
| 7 | Design a Real-Time Voice AI Agent | Article | The capstone system design |
| 8 | What is System Design? | Article | The fundamentals |
| 9 | HTTP Request vs Long-Polling vs WebSocket vs SSE | Article | The transport-layer primer |
| 10 | How Do Voice and Video Calls Work? | Article | Signaling, STUN, TURN, peer-to-peer |

---

## The Lead Lesson

> **Lesson 1 — [How Does a GPU Work for Deep Learning?](./01-how-does-a-gpu-work.md)** — the foundation. Worked example: take the same matrix-multiply kernel, run it on CPU vs GPU, measure the speedup and memory bandwidth, explain where the gap comes from.
# ADR-0001 — FastAPI over Flask

- **Status:** accepted
- **Date:** 2026-W3 (Phase 2, week 1)
- **Owner:** FDE
- **Stakeholders consulted:** Daniel (IT), Mei (CS)

## Context

We need an HTTP service that exposes the RAG-augmented drafter to Mei's terminal, the future CS team, and downstream tools. The two most credible options for a small Python service in 2026 are **Flask** and **FastAPI**.

## Decision

We use **FastAPI** with Pydantic request/response models and uvicorn as the ASGI server.

## Considered alternatives

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **FastAPI** | Async-native; Pydantic v2; auto-OpenAPI; type-checked handlers | Slightly newer; more import surface | ✅ chosen |
| Flask | Battle-tested; smaller surface | Sync-only; no built-in validation; manual OpenAPI | rejected — no async = a future bottleneck when we add streaming |
| LitServe | Built for ML serving | Over-engineered for 150 req/day | rejected — single VM, one route |
| Ray Serve | Multi-node, autoscaling | Operational overhead of a Ray cluster | rejected — 100x over-provisioned |

## Consequences

- All requests/responses are typed via Pydantic. The eval harness, the CLI, and the Swagger UI all use the same schema.
- We can add `/draft/stream` (SSE) without a separate framework.
- We add `fastapi`, `uvicorn`, `pydantic` to `requirements.txt` (3 small packages, no native deps).
- The Pydantic models double as the test surface: 13/13 pytest cases pin the schema.

## Why this is the right call

- Mei's CS lead pattern: **typed contracts age better than untyped ones.** The eval set won't drift; the API surface won't drift; the customer team can read the OpenAPI doc and start integrating on day 1.
- The operational cost is 3 packages; the operational benefit is 1 fewer class of bugs (no `KeyError` on missing fields, no `TypeError` on bad payloads).

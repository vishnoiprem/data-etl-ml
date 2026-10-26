"""AI-Powered Customer Support — Flask HTTP service (port 8033).

Thin wrapper around :class:`SupportService`. Exposes the RAG pipeline
end-to-end: ingest knowledge-base articles, open tickets, retrieve
relevant articles, and let the mock LLM auto-reply.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent))

from flask import Flask, jsonify, request  # noqa: E402

from common.metrics import MetricsRegistry  # noqa: E402
from common.storage import KeyValueStore  # noqa: E402

from service import SupportService  # noqa: E402


def create_app(service: SupportService | None = None) -> Flask:
    app = Flask("ai_support")
    svc = service or SupportService(
        store=KeyValueStore(
            "ai_support",
            persist_path=str(HERE / "var" / "ai_support.json"),
        ),
    )
    metrics = MetricsRegistry()
    ingest_hist = metrics.histogram("ingest_latency_ms", "POST /api/articles latency")
    ticket_hist = metrics.histogram("ticket_latency_ms", "POST /api/tickets latency")
    auto_hist = metrics.histogram("auto_reply_latency_ms", "auto-reply latency")
    ingest_count = metrics.counter("articles_ingested_total", "articles ingested")
    ticket_count = metrics.counter("tickets_opened_total", "tickets opened")
    auto_count = metrics.counter("auto_replies_total", "auto replies generated")
    reply_count = metrics.counter("replies_total", "follow-up replies posted")
    cache_hit = metrics.counter("cache_hits", "retrieve cache hits")
    cache_miss = metrics.counter("cache_misses", "retrieve cache misses")

    # ---- routes -------------------------------------------------------

    @app.get("/health")
    def health():
        return jsonify({"ok": True, "ts": time.time()})

    @app.post("/api/articles")
    def ingest():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            title = body.get("title")
            text = body.get("body")
            tags = body.get("tags") or []
            if not title or not text:
                return jsonify({"error": "title and body are required"}), 400
            art = svc.ingest_article(title, text, tags=tags)
            ingest_count.inc()
            return jsonify(art.to_dict()), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            ingest_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/articles")
    def list_articles():
        return jsonify([a.to_dict() for a in svc.list_articles()])

    @app.get("/api/articles/<int:article_id>")
    def get_article(article_id: int):
        art = svc.get_article(article_id)
        if not art:
            return jsonify({"error": "not found"}), 404
        return jsonify(art.to_dict())

    @app.post("/api/retrieve")
    def retrieve():
        """Debug endpoint: directly test the retriever."""
        body = request.get_json(force=True, silent=True) or {}
        q = body.get("query", "")
        k = int(body.get("top_k", svc.top_k))
        scored = svc.retrieve(q, top_k=k)
        # Track cache effectiveness.
        if scored and svc.cache.get(f"retrieve:{hash(q)}:{k}") is not None:
            cache_hit.inc()
        else:
            cache_miss.inc()
        return jsonify({
            "query": q,
            "results": [
                {"article": a.to_dict(), "score": s} for a, s in scored
            ],
        })

    @app.post("/api/tickets")
    def open_ticket():
        start = time.perf_counter()
        try:
            body = request.get_json(force=True, silent=True) or {}
            user_id = body.get("user_id")
            subject = body.get("subject")
            text = body.get("body")
            if not user_id or not subject or not text:
                return jsonify({"error": "user_id, subject, body required"}), 400
            t = svc.open_ticket(user_id, subject, text)
            ticket_count.inc()
            return jsonify(t.to_dict()), 201
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            ticket_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/api/tickets")
    def list_tickets():
        return jsonify([t.to_dict() for t in svc.list_tickets()])

    @app.get("/api/tickets/<int:ticket_id>")
    def get_ticket(ticket_id: int):
        t = svc.get_ticket(ticket_id)
        if not t:
            return jsonify({"error": "not found"}), 404
        return jsonify(t.to_dict())

    @app.post("/api/tickets/<int:ticket_id>/reply")
    def reply(ticket_id: int):
        """Auto-reply via RAG, or a follow-up reply if `body` is given.

        - Without ``body``: trigger the auto-reply flow.
        - With ``role`` in {"agent", "user"}: post a follow-up message.
        """
        body = request.get_json(force=True, silent=True) or {}
        start = time.perf_counter()
        try:
            if "body" not in body:
                # Auto-reply path.
                m = svc.auto_reply(ticket_id)
                if m is None:
                    return jsonify({"error": "ticket not found or no user message"}), 404
                auto_count.inc()
                return jsonify({
                    "ticket_id": ticket_id,
                    "reply": m.to_dict(),
                })
            role = body.get("role", "user")
            text = body["body"]
            if role == "agent":
                m = svc.agent_reply(ticket_id, text)
            else:
                m = svc.user_reply(ticket_id, text)
            reply_count.inc()
            return jsonify({
                "ticket_id": ticket_id,
                "reply": m.to_dict(),
            })
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        finally:
            auto_hist.observe_ms((time.perf_counter() - start) * 1000)

    @app.get("/metrics")
    def metrics_endpoint():
        return metrics.render(), 200, {"Content-Type": "text/plain; version=0.0.4"}

    @app.get("/")
    def index():
        return jsonify({
            "service": "ai_support",
            "endpoints": [
                "POST /api/articles",
                "GET  /api/articles",
                "GET  /api/articles/<id>",
                "POST /api/retrieve",
                "POST /api/tickets",
                "GET  /api/tickets",
                "GET  /api/tickets/<id>",
                "POST /api/tickets/<id>/reply",
                "GET  /metrics",
                "GET  /health",
            ],
            "stats": svc.stats(),
        })

    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8033"))
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)

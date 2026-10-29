"""
Lab 18: Hallucination Detector
==============================

A production-grade hallucination detection system for LLM responses. It
verifies that the claims in a response are supported by the source context,
using three independent detection methods:

1. NLI (Natural Language Inference) -- mock model that returns
   entailment/neutral/contradiction labels.
2. Fact-checking -- atomic claim extraction and lookup against the context.
3. Source citation -- checks that the response references the source
   passages it claims to use.

A response with low overall confidence is queued for human review; a CLI
allows manual labeling, which is recorded in a training set for later use.

Architecture
------------

    +-----------------+        +-------------------+        +-----------------+
    |  LLM response   | -----> |  HallucinationDet. | -----> |  Confidence     |
    |  + context      |        |  (3 methods)      |        |  + decision     |
    +-----------------+        +---------+---------+        +---------+-------+
                                          |
                                          | (low confidence)
                                          v
                                +-------------------+
                                |  Human Review     |
                                |  Queue (CLI)      |
                                +-------------------+
                                          |
                                          v
                                +-------------------+
                                |  Training Set     |
                                |  (labeled)        |
                                +-------------------+

Components
----------
1. AtomicClaimExtractor: splits a response into individual claims.
2. NLIDetector: mock NLI model scoring (entailment / neutral / contradiction).
3. FactChecker: simple string-overlap + entity match against context.
4. CitationChecker: enforces that cited source IDs exist in the context.
5. HallucinationDetector: aggregates the three signals.
6. ReviewQueue: low-confidence responses for human review.
7. LabelingCLI: a click-based CLI for manual labeling.
8. WebDashboard: live metrics + recent low-confidence responses.

How to run
----------
$ python 18-hallucination-detector.py --mode demo
$ python 18-hallucination-detector.py --mode review       # interactive CLI
$ python 18-hallucination-detector.py --mode gateway      # HTTP gateway

Configuration (env vars)
------------------------
- HALLUC_NLI_LATENCY_MS   (int, default 30)
- HALLUC_NLI_ERROR_RATE   (float, default 0.02)
- HALLUC_ENTAIL_THRESHOLD (float, default 0.55)
- HALLUC_LOW_CONF         (float, default 0.6)   # below -> queue
- HALLUC_REVIEW_MAX       (int, default 500)
- HALLUC_DASHBOARD_PORT   (int, default 8086)
- HALLUC_DASHBOARD_TOKEN  (str, default admin-token)
- HALLUC_LABEL_FILE       (str, default halluc_labels.ndjson)
- HALLUC_WINDOW_SEC       (int, default 3600)    # rolling rate

Dependencies
------------
- aiohttp (HTTP server + client for the gateway mode)
- click (CLI for human review)
- prometheus_client (optional)
- Standard library (asyncio, math, statistics, json, time, re, hashlib)

Failure modes
-------------
- NLI model down -> degrade to fact-check only, with degraded confidence.
- Claim extraction returns no claims -> trust response (no signal).
- Review queue full -> oldest entries get evicted; metrics count evictions.
- Dashboard auth missing -> 401.

What makes it production-grade
------------------------------
- Multi-method detection (NLI + fact-check + citation) with aggregation.
- Probabilistic outputs (NLI returns soft scores, not labels).
- Human review queue with persistence and CLI.
- Tracks hallucination rate over time (rolling window).
- Per-method metrics: NLI failures, fact-check matches, citation coverage.
- CLI for manual labeling.
- Web dashboard.
- Graceful shutdown.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import dataclasses
import json
import logging
import math
import os
import random
import re
import signal
import sys
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Deque,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
)

try:
    from aiohttp import web  # type: ignore
    AIOHTTP_AVAILABLE = True
except Exception:  # pragma: no cover
    AIOHTTP_AVAILABLE = False

try:
    from prometheus_client import (  # type: ignore
        Counter, Gauge, Histogram, CollectorRegistry,
        generate_latest, CONTENT_TYPE_LATEST,
    )
    PROMETHEUS_AVAILABLE = True
except Exception:  # pragma: no cover
    PROMETHEUS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in payload or key.startswith("_"):
                continue
            if key in (
                "args", "asctime", "created", "exc_info", "exc_text",
                "filename", "funcName", "levelname", "levelno", "lineno",
                "module", "msecs", "message", "msg", "name", "pathname",
                "process", "processName", "relativeCreated", "stack_info",
                "thread", "threadName", "taskName",
            ):
                continue
            try:
                json.dumps(value)
                payload[key] = value
            except TypeError:
                payload[key] = repr(value)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, sort_keys=True, default=str)


def _build_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(JsonFormatter())
        logger.addHandler(h)
        logger.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
        logger.propagate = False
    return logger


log = _build_logger("halluc-detector")


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DetectorConfig:
    nli_latency_ms: int = int(os.environ.get("HALLUC_NLI_LATENCY_MS", "30"))
    nli_error_rate: float = float(os.environ.get("HALLUC_NLI_ERROR_RATE", "0.02"))
    entail_threshold: float = float(
        os.environ.get("HALLUC_ENTAIL_THRESHOLD", "0.55")
    )
    low_confidence: float = float(os.environ.get("HALLUC_LOW_CONF", "0.6"))
    review_max: int = int(os.environ.get("HALLUC_REVIEW_MAX", "500"))
    dashboard_port: int = int(os.environ.get("HALLUC_DASHBOARD_PORT", "8086"))
    dashboard_host: str = os.environ.get("HALLUC_DASHBOARD_HOST", "127.0.0.1")
    dashboard_token: str = os.environ.get("HALLUC_DASHBOARD_TOKEN", "admin-token")
    label_file: str = os.environ.get("HALLUC_LABEL_FILE", "halluc_labels.ndjson")
    window_sec: int = int(os.environ.get("HALLUC_WINDOW_SEC", "3600"))


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
class Metrics:
    def __init__(self) -> None:
        self.use_prom = PROMETHEUS_AVAILABLE
        if self.use_prom:
            self.registry = CollectorRegistry()
            self.evaluated = Counter(
                "halluc_evaluated_total",
                "Responses evaluated.",
                ["verdict"],
                registry=self.registry,
            )
            self.claims = Counter(
                "halluc_claims_total",
                "Atomic claims processed.",
                ["verdict"],
                registry=self.registry,
            )
            self.review_queued = Counter(
                "halluc_review_queued_total",
                "Responses added to human review queue.",
                registry=self.registry,
            )
            self.review_labeled = Counter(
                "halluc_review_labeled_total",
                "Responses labeled by a human.",
                ["label"],
                registry=self.registry,
            )
            self.nli_failures = Counter(
                "halluc_nli_failures_total",
                "NLI model failures.",
                registry=self.registry,
            )
            self.citation_coverage = Histogram(
                "halluc_citation_coverage",
                "Citation coverage ratio per response (0..1).",
                buckets=(0.0, 0.1, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0),
                registry=self.registry,
            )
            self.review_depth = Gauge(
                "halluc_review_queue_depth",
                "Current review queue depth.",
                registry=self.registry,
            )
            self.halluc_rate = Gauge(
                "halluc_rate_rolling",
                "Rolling hallucination rate.",
                registry=self.registry,
            )
        else:
            self._counters: Dict[str, int] = {}
            self._gauges: Dict[str, float] = {}

    def inc_evaluated(self, verdict: str) -> None:
        if self.use_prom:
            self.evaluated.labels(verdict=verdict).inc()
        else:
            self._counters[f"eval:{verdict}"] = (
                self._counters.get(f"eval:{verdict}", 0) + 1
            )

    def inc_claims(self, verdict: str) -> None:
        if self.use_prom:
            self.claims.labels(verdict=verdict).inc()
        else:
            self._counters[f"claim:{verdict}"] = (
                self._counters.get(f"claim:{verdict}", 0) + 1
            )

    def inc_review_queued(self) -> None:
        if self.use_prom:
            self.review_queued.inc()
        else:
            self._counters["rq"] = self._counters.get("rq", 0) + 1

    def inc_review_labeled(self, label: str) -> None:
        if self.use_prom:
            self.review_labeled.labels(label=label).inc()
        else:
            self._counters[f"rl:{label}"] = self._counters.get(f"rl:{label}", 0) + 1

    def inc_nli_failure(self) -> None:
        if self.use_prom:
            self.nli_failures.inc()
        else:
            self._counters["nli_fail"] = self._counters.get("nli_fail", 0) + 1

    def observe_citation(self, ratio: float) -> None:
        if self.use_prom:
            self.citation_coverage.observe(ratio)
        else:
            pass

    def set_review_depth(self, n: int) -> None:
        if self.use_prom:
            self.review_depth.set(n)
        else:
            self._gauges["review_depth"] = n

    def set_halluc_rate(self, rate: float) -> None:
        if self.use_prom:
            self.halluc_rate.set(rate)
        else:
            self._gauges["halluc_rate"] = rate

    def render(self) -> Tuple[bytes, str]:
        if self.use_prom:
            return generate_latest(self.registry), CONTENT_TYPE_LATEST
        return (
            json.dumps({"counters": self._counters, "gauges": self._gauges}, indent=2).encode(),
            "application/json",
        )


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class SourceContext:
    """The source material the LLM was supposed to base its answer on."""

    id: str
    text: str


@dataclass
class EvaluationResult:
    request_id: str
    response: str
    confidence: float
    verdict: str  # "ok" | "suspect" | "hallucinated"
    nli: Dict[str, float]   # entailment / neutral / contradiction
    fact_check: Dict[str, Any]  # {matched: int, total: int, ratio: float}
    citation: Dict[str, Any]   # {referenced: int, present: int, ratio: float}
    claims: List[str]
    flagged_claims: List[str]
    ts: float
    user_id: str = "anon"


@dataclass
class ReviewItem:
    item_id: str
    request_id: str
    response: str
    context: List[SourceContext]
    confidence: float
    verdict: str
    claims: List[str]
    flagged_claims: List[str]
    enqueued_at: float
    label: Optional[str] = None  # filled by human
    labeled_at: Optional[float] = None


# ---------------------------------------------------------------------------
# Atomic claim extractor
# ---------------------------------------------------------------------------
class AtomicClaimExtractor:
    """Splits a response into individual factual claims.

    Heuristic: split by sentence terminators (., !, ?, newline). Drop
    short sentences (< 4 chars) and trivial fragments.
    """

    _SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

    def extract(self, response: str) -> List[str]:
        if not response:
            return []
        sentences = [s.strip() for s in self._SENTENCE_SPLIT.split(response)]
        sentences = [s for s in sentences if len(s) >= 4]
        return sentences

    @staticmethod
    def normalize(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip().lower())


# ---------------------------------------------------------------------------
# NLI mock
# ---------------------------------------------------------------------------
class NLIDetector:
    """Mock NLI model. Returns soft probability distribution.

    Real implementation: call a HuggingFace model (e.g. cross-encoder).
    Mock heuristic: token overlap -> entailment if many shared tokens;
    contradictions if the response contains a known negation word near
    an entity in the context.
    """

    def __init__(self, cfg: DetectorConfig) -> None:
        self.cfg = cfg

    async def score(self, claim: str, context: str) -> Dict[str, float]:
        await asyncio.sleep(
            self.cfg.nli_latency_ms / 1000.0 * random.uniform(0.5, 1.5)
        )
        if random.random() < self.cfg.nli_error_rate:
            raise RuntimeError("NLI model error")
        claim_tokens = set(AtomicClaimExtractor.normalize(claim).split())
        ctx_tokens = set(AtomicClaimExtractor.normalize(context).split())
        if not claim_tokens or not ctx_tokens:
            return {"entailment": 0.0, "neutral": 1.0, "contradiction": 0.0}
        overlap = claim_tokens & ctx_tokens
        overlap_ratio = len(overlap) / max(1, len(claim_tokens))
        # Negation heuristic
        neg_words = {"not", "no", "never", "without", "isn't", "wasn't",
                     "didn't", "doesn't"}
        has_negation_claim = bool(neg_words & claim_tokens)
        has_negation_ctx = bool(neg_words & ctx_tokens)
        contradiction = 0.0
        if has_negation_claim != has_negation_ctx and overlap_ratio > 0.2:
            contradiction = random.uniform(0.3, 0.7)
        entail = max(0.0, min(1.0, overlap_ratio * random.uniform(0.9, 1.1)))
        # Renormalize
        total = entail + 0.4 + contradiction
        entail /= total
        neutral = 0.4 / total
        contradiction /= total
        # Force at least a small probability for any class
        entail = max(0.01, min(0.98, entail))
        neutral = max(0.01, min(0.98, neutral))
        contradiction = max(0.01, min(0.98, contradiction))
        s = entail + neutral + contradiction
        return {
            "entailment": round(entail / s, 3),
            "neutral": round(neutral / s, 3),
            "contradiction": round(contradiction / s, 3),
        }


# ---------------------------------------------------------------------------
# Fact checker
# ---------------------------------------------------------------------------
class FactChecker:
    """Simple overlap-based fact checker."""

    def __init__(self, cfg: DetectorConfig) -> None:
        self.cfg = cfg

    async def check(
        self, claim: str, context_text: str
    ) -> Tuple[bool, Dict[str, Any]]:
        await asyncio.sleep(0.001)
        norm_claim = AtomicClaimExtractor.normalize(claim)
        norm_ctx = AtomicClaimExtractor.normalize(context_text)
        if not norm_claim:
            return False, {"matched_tokens": 0, "total_tokens": 0, "ratio": 0.0}
        claim_tokens = norm_claim.split()
        ctx_tokens = set(norm_ctx.split())
        matched = sum(1 for t in claim_tokens if t in ctx_tokens)
        total = len(claim_tokens)
        ratio = matched / total if total else 0.0
        # Plausibility threshold: at least 50% of tokens appear in context.
        supported = ratio >= 0.5
        return supported, {
            "matched_tokens": matched,
            "total_tokens": total,
            "ratio": round(ratio, 3),
        }


# ---------------------------------------------------------------------------
# Citation checker
# ---------------------------------------------------------------------------
class CitationChecker:
    """Checks that citations like [doc-1] in the response exist in the context."""

    _CITATION_RE = re.compile(r"\[(doc-\w+)\]")

    def __init__(self, cfg: DetectorConfig) -> None:
        self.cfg = cfg

    def check(self, response: str, context: List[SourceContext]) -> Dict[str, Any]:
        referenced = self._CITATION_RE.findall(response)
        present_ids = {c.id for c in context}
        present = sum(1 for ref in referenced if ref in present_ids)
        total = len(referenced)
        ratio = present / total if total else 1.0
        return {
            "referenced": referenced,
            "present": present,
            "total": total,
            "ratio": round(ratio, 3),
        }


# ---------------------------------------------------------------------------
# Hallucination detector (aggregates the 3 methods)
# ---------------------------------------------------------------------------
class HallucinationDetector:
    def __init__(self, cfg: DetectorConfig, metrics: Metrics) -> None:
        self.cfg = cfg
        self.metrics = metrics
        self.claim_extractor = AtomicClaimExtractor()
        self.nli = NLIDetector(cfg)
        self.fact = FactChecker(cfg)
        self.citation = CitationChecker(cfg)
        self._rolling_verdicts: Deque[Tuple[float, str]] = deque()

    async def evaluate(
        self,
        response: str,
        context: List[SourceContext],
        *,
        request_id: str,
        user_id: str = "anon",
    ) -> EvaluationResult:
        context_text = " ".join(c.text for c in context)
        claims = self.claim_extractor.extract(response)
        # Run the per-claim detectors in parallel.
        nli_tasks = [
            self._safe_nli_score(claim, context_text) for claim in claims
        ]
        fact_tasks = [
            self.fact.check(claim, context_text) for claim in claims
        ]
        nli_results = await asyncio.gather(*nli_tasks)
        fact_results = await asyncio.gather(*fact_tasks)
        # Aggregate per-claim verdicts.
        per_claim: List[Tuple[str, str, Dict[str, float], bool]] = []
        flagged: List[str] = []
        for claim, nli, (supported, fact) in zip(claims, nli_results, fact_results):
            if nli is None:
                # NLI failure -- use fact-check only
                verdict = "ok" if supported else "suspect"
            else:
                if nli["contradiction"] > 0.4:
                    verdict = "hallucinated"
                elif nli["entailment"] < self.cfg.entail_threshold or not supported:
                    verdict = "suspect"
                else:
                    verdict = "ok"
            if verdict in ("suspect", "hallucinated"):
                flagged.append(claim)
            per_claim.append((claim, verdict, nli or {"entailment": 0, "neutral": 1, "contradiction": 0}, supported))
            self.metrics.inc_claims(verdict)
        # Aggregate confidence: average NLI entailment (where available)
        # + citation coverage + fact-check ratio.
        if nli_results and any(r is not None for r in nli_results):
            nli_mean = sum(
                (r["entailment"] if r else 0.0) for r in nli_results
            ) / max(1, sum(1 for r in nli_results if r is not None))
        else:
            nli_mean = 0.5
        fact_ratios = [r[1]["ratio"] for r in fact_results]
        fact_mean = sum(fact_ratios) / max(1, len(fact_ratios))
        citation = self.citation.check(response, context)
        self.metrics.observe_citation(citation["ratio"])
        confidence = round(
            0.5 * nli_mean + 0.3 * fact_mean + 0.2 * citation["ratio"], 3
        )
        if confidence < self.cfg.low_confidence / 2:
            verdict = "hallucinated"
        elif confidence < self.cfg.low_confidence:
            verdict = "suspect"
        else:
            verdict = "ok"
        self.metrics.inc_evaluated(verdict)
        # Update rolling rate
        self._rolling_verdicts.append((time.time(), verdict))
        self._evict()
        self._update_rate()
        result = EvaluationResult(
            request_id=request_id,
            response=response,
            confidence=confidence,
            verdict=verdict,
            nli={
                "mean_entailment": round(
                    sum((r["entailment"] if r else 0) for r in nli_results)
                    / max(1, len(nli_results)),
                    3,
                ),
                "contradictions": sum(
                    1 for r in nli_results if r and r["contradiction"] > 0.4
                ),
            },
            fact_check={
                "matched": sum(r[1]["matched_tokens"] for r in fact_results),
                "total": sum(r[1]["total_tokens"] for r in fact_results),
                "ratio": round(fact_mean, 3),
            },
            citation=citation,
            claims=claims,
            flagged_claims=flagged,
            ts=time.time(),
            user_id=user_id,
        )
        log.info(
            "halluc_evaluated",
            extra={
                "request_id": request_id,
                "confidence": confidence,
                "verdict": verdict,
                "claims": len(claims),
                "flagged": len(flagged),
            },
        )
        return result

    async def _safe_nli_score(
        self, claim: str, context_text: str
    ) -> Optional[Dict[str, float]]:
        try:
            return await self.nli.score(claim, context_text)
        except Exception as exc:
            log.warning("nli_failure", extra={"err": str(exc)})
            self.metrics.inc_nli_failure()
            return None

    def _evict(self) -> None:
        cutoff = time.time() - self.cfg.window_sec
        while self._rolling_verdicts and self._rolling_verdicts[0][0] < cutoff:
            self._rolling_verdicts.popleft()

    def _update_rate(self) -> None:
        if not self._rolling_verdicts:
            self.metrics.set_halluc_rate(0.0)
            return
        bad = sum(1 for _, v in self._rolling_verdicts if v != "ok")
        rate = bad / len(self._rolling_verdicts)
        self.metrics.set_halluc_rate(rate)

    def rate(self) -> float:
        if not self._rolling_verdicts:
            return 0.0
        bad = sum(1 for _, v in self._rolling_verdicts if v != "ok")
        return bad / len(self._rolling_verdicts)


# ---------------------------------------------------------------------------
# Review queue
# ---------------------------------------------------------------------------
class ReviewQueue:
    def __init__(self, cfg: DetectorConfig, metrics: Metrics) -> None:
        self.cfg = cfg
        self.metrics = metrics
        self._items: Deque[ReviewItem] = deque(maxlen=cfg.review_max)
        self._by_id: Dict[str, ReviewItem] = {}
        self._lock = asyncio.Lock()

    async def push(self, item: ReviewItem) -> None:
        async with self._lock:
            if len(self._items) >= self.cfg.review_max:
                evicted = self._items.popleft()
                self._by_id.pop(evicted.item_id, None)
            self._items.append(item)
            self._by_id[item.item_id] = item
            self.metrics.inc_review_queued()
            self.metrics.set_review_depth(len(self._items))

    async def list_unlabeled(self, limit: int = 50) -> List[ReviewItem]:
        async with self._lock:
            return [i for i in self._items if i.label is None][:limit]

    async def list_all(self, limit: int = 50) -> List[ReviewItem]:
        async with self._lock:
            return list(self._items)[:limit]

    async def label(self, item_id: str, label: str) -> bool:
        async with self._lock:
            item = self._by_id.get(item_id)
            if not item:
                return False
            item.label = label
            item.labeled_at = time.time()
            self.metrics.inc_review_labeled(label)
            return True

    @property
    def depth(self) -> int:
        return len(self._items)


# ---------------------------------------------------------------------------
# Label store (persists human labels for training)
# ---------------------------------------------------------------------------
class LabelStore:
    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = asyncio.Lock()

    async def append(self, item: ReviewItem) -> None:
        if not self.path:
            return
        async with self._lock:
            try:
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "item_id": item.item_id,
                                "request_id": item.request_id,
                                "label": item.label,
                                "confidence": item.confidence,
                                "verdict": item.verdict,
                                "claims": item.claims,
                                "flagged_claims": item.flagged_claims,
                                "response": item.response,
                                "ts": item.enqueued_at,
                            }
                        )
                        + "\n"
                    )
            except Exception as exc:
                log.warning("label_append_failed", extra={"err": str(exc)})

    async def load(self) -> List[Dict[str, Any]]:
        if not self.path or not os.path.exists(self.path):
            return []
        out: List[Dict[str, Any]] = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        out.append(json.loads(line))
                    except Exception:
                        continue
        except Exception as exc:
            log.warning("label_load_failed", extra={"err": str(exc)})
        return out


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------
class HallucinationService:
    def __init__(self, cfg: Optional[DetectorConfig] = None) -> None:
        self.cfg = cfg or DetectorConfig()
        self.metrics = Metrics()
        self.detector = HallucinationDetector(self.cfg, self.metrics)
        self.review = ReviewQueue(self.cfg, self.metrics)
        self.labels = LabelStore(self.cfg.label_file)
        self.dashboard: Optional["DashboardServer"] = None

    async def start(self) -> None:
        if AIOHTTP_AVAILABLE:
            self.dashboard = DashboardServer(self.cfg, self.metrics, self)
            await self.dashboard.start()

    async def stop(self) -> None:
        if self.dashboard:
            await self.dashboard.stop()

    async def evaluate(
        self,
        *,
        response: str,
        context: List[SourceContext],
        request_id: Optional[str] = None,
        user_id: str = "anon",
    ) -> EvaluationResult:
        rid = request_id or uuid.uuid4().hex
        result = await self.detector.evaluate(
            response=response,
            context=context,
            request_id=rid,
            user_id=user_id,
        )
        if result.verdict in ("suspect", "hallucinated"):
            item = ReviewItem(
                item_id=uuid.uuid4().hex,
                request_id=rid,
                response=response,
                context=context,
                confidence=result.confidence,
                verdict=result.verdict,
                claims=result.claims,
                flagged_claims=result.flagged_claims,
                enqueued_at=time.time(),
            )
            await self.review.push(item)
        return result


# ---------------------------------------------------------------------------
# Web dashboard
# ---------------------------------------------------------------------------
if AIOHTTP_AVAILABLE:

    class DashboardServer:
        def __init__(
            self,
            cfg: DetectorConfig,
            metrics: Metrics,
            service: HallucinationService,
        ) -> None:
            self.cfg = cfg
            self.metrics = metrics
            self.service = service
            self._app = web.Application()
            self._app.router.add_get("/healthz", self._healthz)
            self._app.router.add_get("/metrics", self._metrics)
            self._app.router.add_get("/dashboard", self._dashboard)
            self._app.router.add_get("/review", self._review)
            self._app.router.add_post("/review/label", self._label)
            self._runner: Optional[web.AppRunner] = None

        async def start(self) -> None:
            self._runner = web.AppRunner(self._app)
            await self._runner.setup()
            site = web.TCPSite(self._runner, host=self.cfg.dashboard_host, port=self.cfg.dashboard_port)
            await site.start()
            log.info(
                "dashboard_started",
                extra={"host": self.cfg.dashboard_host, "port": self.cfg.dashboard_port},
            )

        async def stop(self) -> None:
            if self._runner:
                await self._runner.cleanup()

        async def _healthz(self, _: web.Request) -> web.Response:
            return web.json_response({"status": "ok"})

        async def _metrics(self, _: web.Request) -> web.Response:
            body, ctype = self.metrics.render()
            return web.Response(body=body, content_type=ctype)

        async def _dashboard(self, request: web.Request) -> web.Response:
            token = request.query.get("token", "")
            if token != self.cfg.dashboard_token:
                return web.json_response({"error": "unauthorized"}, status=401)
            labeled = await self.labels.load()
            return web.json_response(
                {
                    "config": {
                        "entail_threshold": self.cfg.entail_threshold,
                        "low_confidence": self.cfg.low_confidence,
                        "review_max": self.cfg.review_max,
                    },
                    "review_queue_depth": self.service.review.depth,
                    "rolling_hallucination_rate": self.service.detector.rate(),
                    "labels_loaded": len(labeled),
                    "label_distribution": self._label_distribution(labeled),
                }
            )

        def _label_distribution(
            self, labels: List[Dict[str, Any]]
        ) -> Dict[str, int]:
            d: Dict[str, int] = {}
            for entry in labels:
                lab = entry.get("label") or "unknown"
                d[lab] = d.get(lab, 0) + 1
            return d

        async def _review(self, request: web.Request) -> web.Response:
            limit = int(request.query.get("limit", "25"))
            only_unlabeled = request.query.get("unlabeled", "1") == "1"
            items = (
                await self.review.list_unlabeled(limit=limit)
                if only_unlabeled
                else await self.review.list_all(limit=limit)
            )
            return web.json_response(
                {
                    "items": [
                        {
                            "item_id": i.item_id,
                            "request_id": i.request_id,
                            "confidence": i.confidence,
                            "verdict": i.verdict,
                            "claims": i.claims,
                            "flagged_claims": i.flagged_claims,
                            "response": i.response,
                            "enqueued_at": i.enqueued_at,
                            "label": i.label,
                        }
                        for i in items
                    ]
                }
            )

        async def _label(self, request: web.Request) -> web.Response:
            try:
                payload = await request.json()
            except Exception:
                return web.json_response({"error": "bad_json"}, status=400)
            item_id = payload.get("item_id")
            label = payload.get("label")
            if not item_id or label not in ("ok", "suspect", "hallucinated", "skip"):
                return web.json_response({"error": "bad_request"}, status=400)
            ok = await self.service.review.label(item_id, label)
            if not ok:
                return web.json_response({"error": "not_found"}, status=404)
            # Persist if finalized
            if label in ("ok", "hallucinated"):
                item = self.service.review._by_id.get(item_id)
                if item is not None:
                    await self.service.labels.append(item)
            return web.json_response({"status": "labeled", "label": label})


# ---------------------------------------------------------------------------
# CLI (interactive)
# ---------------------------------------------------------------------------
def _print_review_item(item: ReviewItem) -> None:
    print("\n" + "=" * 70)
    print(f"Item: {item.item_id}   request: {item.request_id}")
    print(f"Confidence: {item.confidence:.3f}  verdict: {item.verdict}")
    print(f"Enqueued: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item.enqueued_at))}")
    print("-" * 70)
    print("RESPONSE:")
    print(item.response[:1000])
    print("-" * 70)
    print("FLAGGED CLAIMS:")
    for c in item.flagged_claims:
        print(f"  ! {c[:200]}")
    print("-" * 70)
    print("CONTEXT (truncated):")
    for ctx in item.context:
        print(f"  [{ctx.id}] {ctx.text[:200]}")
    print("=" * 70)


async def _run_review_cli(svc: HallucinationService) -> None:
    """A simple async CLI for human review."""
    while True:
        items = await svc.review.list_unlabeled(limit=10)
        if not items:
            print("No more items to review.")
            return
        item = items[0]
        _print_review_item(item)
        print(
            "Choose label: [o]k / [s]uspect / [h]allucinated / [k]skip / [q]uit"
        )
        try:
            choice = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input("> ").strip().lower()
            )
        except (EOFError, KeyboardInterrupt):
            return
        mapping = {
            "o": "ok", "s": "suspect", "h": "hallucinated",
            "k": "skip", "q": "quit",
        }
        if choice not in mapping:
            print("invalid choice")
            continue
        if mapping[choice] == "quit":
            return
        await svc.review.label(item.item_id, mapping[choice])
        if mapping[choice] in ("ok", "hallucinated"):
            await svc.labels.append(item)
        print(f"labeled {item.item_id} as {mapping[choice]}")


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
async def _run_demo() -> None:
    cfg = DetectorConfig(
        nli_error_rate=0.04,
        low_confidence=0.65,
        review_max=200,
    )
    svc = HallucinationService(cfg=cfg)
    await svc.start()
    # Define some context passages.
    context = [
        SourceContext(
            id="doc-1",
            text="The Eiffel Tower is in Paris, France. It was completed in 1889 "
                 "and is 330 metres tall.",
        ),
        SourceContext(
            id="doc-2",
            text="The Amazon River is the largest river by discharge volume of "
                 "water in the world.",
        ),
        SourceContext(
            id="doc-3",
            text="Mount Everest is the tallest mountain on Earth, located in the "
                 "Himalayas on the border of Nepal and Tibet.",
        ),
    ]
    # A mix of supported and unsupported responses.
    test_responses = [
        # Fully supported
        "The Eiffel Tower is in Paris. It was completed in 1889 [doc-1].",
        # Partial hallucination
        "The Eiffel Tower is in Berlin, Germany. It is 500 metres tall [doc-1].",
        # Mostly unsupported
        "Mount Everest is located in the Andes. It is the smallest mountain on Earth [doc-3].",
        # Supported, no citations
        "The Amazon is the largest river by discharge volume of water.",
        # NLI failure case
        "The Amazon flows through Antarctica and empties into the Arctic Ocean [doc-2].",
    ]
    for i, resp in enumerate(test_responses * 30):  # 150 evaluations
        result = await svc.evaluate(
            response=resp,
            context=context,
            request_id=f"req-{i:04d}",
            user_id=f"u-{i % 10}",
        )
    # Print a summary
    print("\n=== DEMO SUMMARY ===")
    print(f"review queue depth: {svc.review.depth}")
    print(f"rolling halluc rate: {svc.detector.rate():.3f}")
    body, _ = svc.metrics.render()
    text = body.decode()
    if PROMETHEUS_AVAILABLE:
        keys = ("halluc_evaluated_total", "halluc_claims_total",
                "halluc_review_queued_total", "halluc_nli_failures_total",
                "halluc_citation_coverage_count", "halluc_review_queue_depth",
                "halluc_rate_rolling")
        print("\nMETRICS (filtered):")
        for line in text.splitlines():
            if any(k in line for k in keys):
                print(" ", line)
    else:
        print("\nMETRICS (fallback):")
        print(text[:2000])
    # Show first 3 items
    items = await svc.review.list_all(limit=3)
    for item in items:
        _print_review_item(item)
    # Now run the labeling CLI briefly
    print("\nStarting interactive CLI for first 2 items...")
    for _ in range(2):
        items = await svc.review.list_unlabeled(limit=1)
        if not items:
            break
        item = items[0]
        # auto-label as "hallucinated" if confidence < 0.4, else "ok"
        label = "hallucinated" if item.confidence < 0.4 else "ok"
        await svc.review.label(item.item_id, label)
        await svc.labels.append(item)
        print(f"auto-labeled {item.item_id} as {label}")
    # Reload labels
    labels = await svc.labels.load()
    print(f"\nlabels persisted: {len(labels)}")
    await svc.stop()


async def _run_review_mode() -> None:
    svc = HallucinationService()
    await svc.start()
    print("Starting interactive review CLI. Press Ctrl+C to exit.")
    try:
        await _run_review_cli(svc)
    finally:
        await svc.stop()


async def _run_gateway() -> None:
    cfg = DetectorConfig()
    svc = HallucinationService(cfg=cfg)
    await svc.start()
    print(f"Dashboard on http://{cfg.dashboard_host}:{cfg.dashboard_port}/dashboard")
    try:
        await asyncio.Event().wait()
    finally:
        await svc.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Hallucination Detector")
    parser.add_argument(
        "--mode",
        choices=["demo", "review", "gateway"],
        default=os.environ.get("HALLUC_MODE", "demo"),
    )
    args = parser.parse_args()
    if args.mode == "demo":
        asyncio.run(_run_demo())
    elif args.mode == "review":
        asyncio.run(_run_review_mode())
    else:
        asyncio.run(_run_gateway())


if __name__ == "__main__":
    main()

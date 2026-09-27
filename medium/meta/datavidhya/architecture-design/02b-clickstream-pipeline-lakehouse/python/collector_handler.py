"""
Reference Event Collector handler (FastAPI / Flask).

Production would be Envoy + Lua or a custom C++/Rust handler to keep p99 < 5ms.
This Python implementation is for tests + dev.

Responsibilities:
  1. Validate schema (reject fast)
  2. Check consent (GDPR / cookie)
  3. Enrich with edge info (geo, ASN)
  4. Hash PII (user_id, ip)
  5. Push to Kafka (async, fire-and-forget for the client)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Optional

from aiohttp import web

from bot_filter import _ua_matches_blocklist
from schema_validator import EVENT_JSON_SCHEMA
import jsonschema


# --------------------------------------------------------------------- #
# Mock Kafka producer (real prod: aiokafka)
# --------------------------------------------------------------------- #

@dataclass
class MockKafkaProducer:
    topic: str = "events.raw"
    sent: int = 0
    rejected: int = 0

    async def send(self, payload: bytes):
        self.sent += 1

    async def send_quarantine(self, payload: bytes, reason: str):
        self.rejected += 1


# --------------------------------------------------------------------- #
# Geo / ASN (mock; real: MaxMind GeoLite2)
# --------------------------------------------------------------------- #

def geo_lookup(ip: str) -> dict:
    return {"country": "US", "asn": "AS15169 GOOGLE"}   # placeholder


def hash_value(v: str, salt: str = "collector-salt-v1") -> str:
    return hashlib.sha256(f"{salt}:{v}".encode()).hexdigest()[:32]


# --------------------------------------------------------------------- #
# Handler
# --------------------------------------------------------------------- #

async def collect(request: web.Request) -> web.Response:
    producer: MockKafkaProducer = request.app["producer"]

    # 1. Body parsing
    try:
        payload = await request.json()
    except Exception:
        return web.json_response({"error": "invalid_json"}, status=400)

    # If batch
    if isinstance(payload, list):
        events = payload
    else:
        events = [payload]

    accepted, rejected = 0, 0
    for ev in events:
        # 2. Consent check (header from client SDK)
        if request.headers.get("X-Consent", "unknown") != "granted":
            rejected += 1
            continue

        # 3. Schema validation
        try:
            jsonschema.validate(ev, EVENT_JSON_SCHEMA)
        except jsonschema.ValidationError as e:
            await producer.send_quarantine(json.dumps(ev).encode(), f"schema:{e.message[:80]}")
            rejected += 1
            continue

        # 4. Enrichment
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        geo = geo_lookup(ip)
        ev["country"] = geo["country"]
        ev["ip_hash"] = hash_value(ip) if ip else None
        ev["received_ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # 5. Hash user_id (already hashed at SDK, but double-hash at edge)
        ev["user_id"] = hash_value(ev["user_id"])

        # 6. Push to Kafka
        await producer.send(json.dumps(ev).encode())
        accepted += 1

    return web.json_response({"accepted": accepted, "rejected": rejected}, status=202)


# --------------------------------------------------------------------- #
# App factory
# --------------------------------------------------------------------- #

def make_app(producer: Optional[MockKafkaProducer] = None) -> web.Application:
    app = web.Application()
    app["producer"] = producer or MockKafkaProducer()
    app.router.add_post("/v1/events", collect)
    return app


if __name__ == "__main__":
    web.run_app(make_app(), port=8080)

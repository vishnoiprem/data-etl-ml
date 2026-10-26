"""HTTP tests for the webhook delivery Flask app.

The app is created with ``start_loop=False`` so the background
delivery thread doesn't interfere with tests. Instead, the service's
``dispatch_pending_now`` is called directly via a test endpoint or by
piggy-backing on the test client.

Run with:
    cd system_design
    python -m unittest 08_webhook_delivery.tests.test_app -v
"""

from __future__ import annotations

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.app import create_app  # noqa: E402
from code.service import SimulatedTransport, WebhookService  # noqa: E402


def _flush(svc: WebhookService, delivery_id: str) -> None:
    """Force-dispatch a delivery across retries (no waiting)."""
    while True:
        d = svc.get_delivery(delivery_id)
        if d is None or d.status != "pending":
            return
        d.next_attempt_at = 0
        svc.store.set(svc._k_del(delivery_id), d.to_dict())
        svc.dispatch_pending_now()


class WebhookAppTest(unittest.TestCase):
    def setUp(self):
        self.transport = SimulatedTransport()
        self.svc = WebhookService(
            transport=self.transport, max_attempts=3, base_delay_s=0.001
        )
        self.app = create_app(service=self.svc, start_loop=False)
        self.client = self.app.test_client()

    # ---- subscriptions --------------------------------------------------

    def test_create_and_get_subscription(self):
        rv = self.client.post(
            "/api/subscriptions",
            data=json.dumps(
                {
                    "url": "https://example.com/h",
                    "secret": "longenoughsecret",
                    "event_types": ["order.placed"],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 201)
        sub = rv.get_json()
        self.assertTrue(sub["subscription_id"])
        # Get by id.
        rv = self.client.get(f"/api/subscriptions/{sub['subscription_id']}")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["url"], "https://example.com/h")

    def test_invalid_url_rejected(self):
        rv = self.client.post(
            "/api/subscriptions",
            data=json.dumps({"url": "ftp://x", "secret": "longenough"}),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 400)

    def test_list_subscriptions(self):
        self.client.post(
            "/api/subscriptions",
            data=json.dumps(
                {"url": "https://a.com/h", "secret": "longenougha"}
            ),
            content_type="application/json",
        )
        self.client.post(
            "/api/subscriptions",
            data=json.dumps(
                {"url": "https://b.com/h", "secret": "longenoughb"}
            ),
            content_type="application/json",
        )
        rv = self.client.get("/api/subscriptions")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(rv.get_json()["subscriptions"]), 2)

    # ---- deliveries -----------------------------------------------------

    def test_deliver_returns_202(self):
        # Create sub.
        sub = self.client.post(
            "/api/subscriptions",
            data=json.dumps(
                {
                    "url": "https://x.com/h",
                    "secret": "longenoughevent",
                    "event_types": ["order.placed"],
                }
            ),
            content_type="application/json",
        ).get_json()
        rv = self.client.post(
            f"/api/subscriptions/{sub['subscription_id']}/deliver",
            data=json.dumps(
                {"event": "order.placed", "payload": {"order_id": 1}}
            ),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 202)
        d = rv.get_json()
        self.assertEqual(d["status"], "pending")

    def test_deliver_to_unknown_sub_returns_404(self):
        rv = self.client.post(
            "/api/subscriptions/nope/deliver",
            data=json.dumps({"event": "x", "payload": {}}),
            content_type="application/json",
        )
        self.assertEqual(rv.status_code, 404)

    def test_successful_delivery_flow(self):
        # Create subscription.
        sub = self.client.post(
            "/api/subscriptions",
            data=json.dumps(
                {
                    "url": "https://x.com/h",
                    "secret": "longenoughevent",
                    "event_types": ["order.placed"],
                }
            ),
            content_type="application/json",
        ).get_json()
        self.transport.queue_outcome(200)
        d = self.client.post(
            f"/api/subscriptions/{sub['subscription_id']}/deliver",
            data=json.dumps(
                {"event": "order.placed", "payload": {"order_id": 1}}
            ),
            content_type="application/json",
        ).get_json()
        _flush(self.svc, d["delivery_id"])
        rv = self.client.get(f"/api/deliveries/{d['delivery_id']}")
        self.assertEqual(rv.status_code, 200)
        d = rv.get_json()
        self.assertEqual(d["status"], "delivered")
        self.assertEqual(len(d["attempts_detail"]), 1)

    def test_retry_and_dlq_via_http(self):
        sub = self.client.post(
            "/api/subscriptions",
            data=json.dumps(
                {
                    "url": "https://x.com/h",
                    "secret": "longenoughevent",
                }
            ),
            content_type="application/json",
        ).get_json()
        # Make max_attempts low so we go to DLQ quickly.
        # Queue all failures.
        for _ in range(10):
            self.transport.queue_outcome(500)
        d = self.client.post(
            f"/api/subscriptions/{sub['subscription_id']}/deliver",
            data=json.dumps(
                {
                    "event": "x",
                    "payload": {},
                    "max_attempts": 2,  # short for testing
                }
            ),
            content_type="application/json",
        ).get_json()
        for _ in range(5):
            _flush(self.svc, d["delivery_id"])
        rv = self.client.get(f"/api/deliveries/{d['delivery_id']}")
        d = rv.get_json()
        self.assertEqual(d["status"], "dead")
        # DLQ endpoint sees it.
        rv = self.client.get("/api/dlq")
        ids = [x["delivery_id"] for x in rv.get_json()["dlq"]]
        self.assertIn(d["delivery_id"], ids)
        # Replay.
        self.transport.reset()
        self.transport.queue_outcome(200)
        rv = self.client.post(
            f"/api/subscriptions/{sub['subscription_id']}/replay/{d['delivery_id']}"
        )
        self.assertEqual(rv.status_code, 200)
        _flush(self.svc, d["delivery_id"])
        rv = self.client.get(f"/api/deliveries/{d['delivery_id']}")
        self.assertEqual(rv.get_json()["status"], "delivered")

    def test_list_deliveries_per_subscription(self):
        sub = self.client.post(
            "/api/subscriptions",
            data=json.dumps(
                {
                    "url": "https://x.com/h",
                    "secret": "longenoughevent",
                }
            ),
            content_type="application/json",
        ).get_json()
        for i in range(3):
            self.client.post(
                f"/api/subscriptions/{sub['subscription_id']}/deliver",
                data=json.dumps({"event": "x", "payload": {"i": i}}),
                content_type="application/json",
            )
        rv = self.client.get(
            f"/api/subscriptions/{sub['subscription_id']}/deliveries"
        )
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(len(rv.get_json()["deliveries"]), 3)

    # ---- health & metrics ----------------------------------------------

    def test_health(self):
        rv = self.client.get("/health")
        self.assertEqual(rv.status_code, 200)
        self.assertTrue(rv.get_json()["ok"])

    def test_metrics_text(self):
        rv = self.client.get("/metrics")
        self.assertEqual(rv.status_code, 200)
        body = rv.get_data(as_text=True)
        self.assertIn("deliveries_total", body)
        self.assertIn("replays_total", body)

    def test_index(self):
        rv = self.client.get("/")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.get_json()["service"], "webhook_delivery")


if __name__ == "__main__":
    unittest.main()

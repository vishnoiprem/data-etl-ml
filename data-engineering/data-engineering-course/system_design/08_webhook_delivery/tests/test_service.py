"""Unit tests for WebhookService.

Run with:
    cd system_design
    python -m unittest 08_webhook_delivery.tests.test_service -v
"""

from __future__ import annotations

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "..")))

from code.service import (  # noqa: E402
    SimulatedTransport,
    WebhookService,
    DEFAULT_MAX_ATTEMPTS,
)


class TestSubscriptions(unittest.TestCase):
    def setUp(self):
        self.svc = WebhookService(transport=SimulatedTransport())

    def test_create_and_get(self):
        s = self.svc.create_subscription(
            url="https://example.com/hook",
            secret="supersecret",
            event_types=["order.placed"],
        )
        self.assertTrue(s.subscription_id)
        self.assertEqual(s.url, "https://example.com/hook")
        self.assertEqual(s.event_types, ["order.placed"])
        loaded = self.svc.get_subscription(s.subscription_id)
        self.assertEqual(loaded.url, "https://example.com/hook")

    def test_url_must_be_http(self):
        with self.assertRaises(ValueError):
            self.svc.create_subscription(
                url="ftp://example.com", secret="supersecret"
            )

    def test_secret_too_short(self):
        with self.assertRaises(ValueError):
            self.svc.create_subscription(
                url="https://x.com", secret="short"
            )

    def test_list_subscriptions(self):
        self.svc.create_subscription("https://a.com/h", "aaaaaaaa")
        self.svc.create_subscription("https://b.com/h", "bbbbbbbb")
        self.assertEqual(len(self.svc.list_subscriptions()), 2)


class TestSignature(unittest.TestCase):
    def test_sign_is_deterministic_and_format_correct(self):
        s = WebhookService.sign("secret", '{"x":1}', ts=1700000000)
        self.assertTrue(s.startswith("t=1700000000,v1="))
        # Same inputs -> same signature.
        s2 = WebhookService.sign("secret", '{"x":1}', ts=1700000000)
        self.assertEqual(s, s2)
        # Different body -> different signature.
        s3 = WebhookService.sign("secret", '{"x":2}', ts=1700000000)
        self.assertNotEqual(s, s3)
        # Different secret -> different signature.
        s4 = WebhookService.sign("othersecret", '{"x":1}', ts=1700000000)
        self.assertNotEqual(s, s4)


class TestDelivery(unittest.TestCase):
    def setUp(self):
        self.transport = SimulatedTransport()
        self.svc = WebhookService(
            transport=self.transport, max_attempts=3, base_delay_s=0.001
        )
        self.sub = self.svc.create_subscription(
            url="https://example.com/hook",
            secret="supersecret",
            event_types=["order.placed", "order.shipped"],
        )

    def test_deliver_to_unknown_subscription_raises(self):
        with self.assertRaises(ValueError):
            self.svc.deliver(
                subscription_id="nope",
                event="order.placed",
                payload={"x": 1},
            )

    def test_deliver_with_unknown_event_filtered(self):
        with self.assertRaises(ValueError):
            self.svc.deliver(
                subscription_id=self.sub.subscription_id,
                event="user.deleted",  # not in filter
                payload={"x": 1},
            )

    def test_happy_path_one_attempt(self):
        self.transport.queue_outcome(200)
        d = self.svc.deliver(
            self.sub.subscription_id,
            event="order.placed",
            payload={"order_id": 1},
        )
        self.assertEqual(d.status, "pending")
        n = self.svc.dispatch_pending_now()
        self.assertEqual(n, 1)
        d2 = self.svc.get_delivery(d.delivery_id)
        self.assertEqual(d2.status, "delivered")
        self.assertEqual(d2.attempts, 1)
        self.assertEqual(d2.last_status_code, 200)
        attempts = self.svc.attempts_for(d.delivery_id)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].status_code, 200)

    def test_signature_header_sent(self):
        self.transport.queue_outcome(200)
        d = self.svc.deliver(
            self.sub.subscription_id,
            event="order.placed",
            payload={"x": 1},
        )
        self.svc.dispatch_pending_now()
        # Inspect what the transport saw.
        self.assertEqual(len(self.transport.calls), 1)
        headers = self.transport.calls[0]["headers"]
        self.assertIn("X-Signature", headers)
        self.assertTrue(headers["X-Signature"].startswith("t="))
        self.assertIn("v1=", headers["X-Signature"])
        self.assertEqual(headers["X-Event"], "order.placed")
        self.assertEqual(headers["X-Delivery-Id"], d.delivery_id)

    def test_retry_then_succeed(self):
        # Fail twice, succeed on the third attempt.
        self.transport.queue_outcome(503)
        self.transport.queue_outcome(503)
        self.transport.queue_outcome(200)
        d = self.svc.deliver(
            self.sub.subscription_id,
            event="order.placed",
            payload={"x": 1},
        )
        # First attempt: 503 -> schedule retry.
        self.svc.dispatch_pending_now()
        d = self.svc.get_delivery(d.delivery_id)
        self.assertEqual(d.status, "pending")
        self.assertEqual(d.attempts, 1)
        # Force the next_attempt_at to "now" so we don't have to wait.
        d.next_attempt_at = 0
        self.svc.store.set(self.svc._k_del(d.delivery_id), d.to_dict())
        # Second attempt: 503 -> schedule retry.
        self.svc.dispatch_pending_now()
        d = self.svc.get_delivery(d.delivery_id)
        self.assertEqual(d.status, "pending")
        self.assertEqual(d.attempts, 2)
        d.next_attempt_at = 0
        self.svc.store.set(self.svc._k_del(d.delivery_id), d.to_dict())
        # Third attempt: 200 -> delivered.
        self.svc.dispatch_pending_now()
        d = self.svc.get_delivery(d.delivery_id)
        self.assertEqual(d.status, "delivered")
        self.assertEqual(d.attempts, 3)
        attempts = self.svc.attempts_for(d.delivery_id)
        self.assertEqual(len(attempts), 3)
        self.assertEqual([a.status_code for a in attempts], [503, 503, 200])

    def test_dlq_after_max_attempts(self):
        # All attempts fail.
        for _ in range(10):
            self.transport.queue_outcome(500)
        d = self.svc.deliver(
            self.sub.subscription_id,
            event="order.placed",
            payload={"x": 1},
        )
        for _ in range(DEFAULT_MAX_ATTEMPTS + 1):
            d.next_attempt_at = 0
            self.svc.store.set(self.svc._k_del(d.delivery_id), d.to_dict())
            self.svc.dispatch_pending_now()
            d = self.svc.get_delivery(d.delivery_id)
            if d.status == "dead":
                break
        self.assertEqual(d.status, "dead")
        self.assertEqual(d.attempts, self.svc.max_attempts)
        # DLQ should list it.
        self.assertIn(d.delivery_id, {x.delivery_id for x in self.svc.list_dlq()})

    def test_4xx_immediately_dead(self):
        # No retry on client errors.
        self.transport.queue_outcome(404)
        self.transport.queue_outcome(200)  # would succeed but should not run
        d = self.svc.deliver(
            self.sub.subscription_id,
            event="order.placed",
            payload={"x": 1},
        )
        self.svc.dispatch_pending_now()
        d = self.svc.get_delivery(d.delivery_id)
        self.assertEqual(d.status, "dead")
        self.assertEqual(d.attempts, 1)
        # Only one transport call was made.
        self.assertEqual(len(self.transport.calls), 1)

    def test_replay_resets_attempt_counter(self):
        # First, fail to DLQ.
        for _ in range(10):
            self.transport.queue_outcome(500)
        d = self.svc.deliver(
            self.sub.subscription_id,
            event="order.placed",
            payload={"x": 1},
        )
        for _ in range(self.svc.max_attempts + 1):
            d.next_attempt_at = 0
            self.svc.store.set(self.svc._k_del(d.delivery_id), d.to_dict())
            self.svc.dispatch_pending_now()
            d = self.svc.get_delivery(d.delivery_id)
            if d.status == "dead":
                break
        self.assertEqual(d.status, "dead")
        # Now "fix" the endpoint and replay.
        self.transport.reset()
        self.transport.queue_outcome(200)
        replayed = self.svc.replay(self.sub.subscription_id, d.delivery_id)
        self.assertEqual(replayed.status, "pending")
        self.assertEqual(replayed.attempts, 0)
        self.svc.dispatch_pending_now()
        d = self.svc.get_delivery(d.delivery_id)
        self.assertEqual(d.status, "delivered")
        self.assertEqual(d.attempts, 1)

    def test_subscription_lost_after_enqueue_goes_to_dlq(self):
        # Hard case: enqueue, delete the subscription, dispatch.
        d = self.svc.deliver(
            self.sub.subscription_id,
            event="order.placed",
            payload={"x": 1},
        )
        self.svc.store.delete(self.svc._k_sub(self.sub.subscription_id))
        self.svc.dispatch_pending_now()
        d = self.svc.get_delivery(d.delivery_id)
        self.assertEqual(d.status, "dead")
        self.assertEqual(d.last_error, "subscription not found")

    def test_stats(self):
        self.transport.queue_outcome(200)
        d = self.svc.deliver(
            self.sub.subscription_id,
            event="order.placed",
            payload={"x": 1},
        )
        self.svc.dispatch_pending_now()
        s = self.svc.stats()
        self.assertEqual(s["subscriptions"], 1)
        self.assertEqual(s["delivered"], 1)
        self.assertEqual(s["dlq"], 0)
        self.assertEqual(s["pending"], 0)


class TestBackoff(unittest.TestCase):
    def test_backoff_grows_exponentially(self):
        svc = WebhookService(transport=SimulatedTransport(), base_delay_s=1.0)
        b1 = svc._backoff(1)
        b2 = svc._backoff(2)
        b3 = svc._backoff(3)
        # Approximate — jitter is +/-25%, so check the *central* value.
        self.assertGreater(b2, 1.0)
        self.assertGreater(b3, b2)


if __name__ == "__main__":
    unittest.main()

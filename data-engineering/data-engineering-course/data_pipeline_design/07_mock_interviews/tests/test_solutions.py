"""Unit tests for the three mock-interview pipeline solutions.

Verifies that each of the three end-to-end solutions
(Netflix clickstream, document processing, banking CDC)
runs correctly and produces the expected artifacts.

Run with::

    python3 scripts/run_all_tests.py data_pipeline_design/07_mock_interviews

Author: Prem Vishnoi <prem.vishnoi@example.com>
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
COURSE_ROOT = HERE.parents[2]
sys.path.insert(0, str(COURSE_ROOT.parent))


def _load(name: str, file_name: str):
    path = HERE.parent / "code" / file_name
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


sols = _load("data_pipeline_design_07_solutions", "full_solutions.py")


# ============================================================================
# Solution 1 — Netflix clickstream
# ============================================================================


class NetflixClickstreamTests(unittest.TestCase):
    def setUp(self) -> None:
        self.events = [
            {"event_id": "e1", "user_id": "u1", "title_id": "t1", "ts_ms": 1000},
            {"event_id": "e2", "user_id": "u1", "title_id": "t1", "ts_ms": 2000},
            {"event_id": "e3", "user_id": "u2", "title_id": "t2", "ts_ms": 3000},
            {"event_id": "e4", "user_id": "u2", "title_id": "t2", "ts_ms": 4000,
             "event_type": "pause"},
        ]

    def test_build_creates_components(self) -> None:
        sol = sols.build_netflix_clickstream_pipeline(num_partitions=4)
        self.assertEqual(len(sol.broker._topics), 1)
        self.assertIn("events.plays", sol.broker._topics)
        self.assertEqual(sol.events_published, 0)
        self.assertEqual(sol.events_processed, 0)

    def test_publish_increments_counter(self) -> None:
        sol = sols.build_netflix_clickstream_pipeline()
        sols.netflix_publish_event(
            sol, event_id="e1", user_id="u1", title_id="t1", ts_ms=1
        )
        self.assertEqual(sol.events_published, 1)

    def test_run_pipeline_publishes_all(self) -> None:
        sol = sols.run_netflix_clickstream_pipeline(self.events)
        self.assertEqual(sol.events_published, 4)
        self.assertEqual(sol.events_processed, 4)

    def test_run_pipeline_user_play_counts(self) -> None:
        sol = sols.run_netflix_clickstream_pipeline(self.events)
        # u1 has 2 plays, u2 has 1 play (one event is "pause").
        self.assertEqual(sol.user_play_counts["u1"], 2)
        self.assertEqual(sol.user_play_counts["u2"], 1)

    def test_run_pipeline_feature_store(self) -> None:
        sol = sols.run_netflix_clickstream_pipeline(self.events)
        self.assertEqual(
            sol.feature_store["u1"]["rolling_1h_play_count"], 2
        )
        self.assertEqual(
            sol.feature_store["u2"]["rolling_1h_play_count"], 1
        )
        # last_play_ts_ms is from the play events, not pauses.
        self.assertEqual(sol.feature_store["u1"]["last_play_ts_ms"], 2000)
        self.assertEqual(sol.feature_store["u2"]["last_play_ts_ms"], 3000)

    def test_warehouse_loads_events(self) -> None:
        sol = sols.run_netflix_clickstream_pipeline(self.events)
        rows = sol.warehouse.query_all(
            "SELECT event_id, user_id FROM fact_events ORDER BY event_id"
        )
        self.assertEqual(len(rows), 4)
        self.assertEqual({r["user_id"] for r in rows}, {"u1", "u2"})

    def test_summary(self) -> None:
        sol = sols.run_netflix_clickstream_pipeline(self.events)
        summary = sols.get_solution_summary(sol)
        self.assertEqual(summary["events_published"], 4)
        self.assertEqual(summary["events_processed"], 4)
        self.assertEqual(summary["unique_users"], 2)
        self.assertEqual(summary["warehouse_rows"], 4)


# ============================================================================
# Solution 2 — Document processing
# ============================================================================


class DocumentProcessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.messages = [
            {
                "doc_id": "d1",
                "text": "INV-1234 Total: $1,234.56 2024-01-15",
                "doc_type": "invoice",
                "title": "Invoice 1",
            },
            {
                "doc_id": "d2",
                "text": "This is a contract between ACME and ...",
                "doc_type": "contract",
                "title": "Contract",
            },
            {
                "doc_id": "d3",
                "text": "INV-5678 Total: $999.99 2024-01-16",
                "doc_type": "invoice",
                "title": "Invoice 2",
            },
        ]

    def test_invoice_field_extraction(self) -> None:
        sol = sols.run_document_processing_pipeline(self.messages)
        # Three docs all process successfully.
        self.assertEqual(sol.processed, 3)
        self.assertEqual(len(sol.dlq), 0)

    def test_invoice_number_extracted(self) -> None:
        sol = sols.run_document_processing_pipeline(self.messages)
        rows = sol.warehouse.query_all(
            "SELECT doc_id, invoice_number, total, event_date"
            " FROM extracted_fields WHERE doc_id = 'd1'"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["invoice_number"], "INV-1234")
        self.assertEqual(rows[0]["total"], 1234.56)
        self.assertEqual(rows[0]["event_date"], "2024-01-15")

    def test_contract_has_no_fields(self) -> None:
        sol = sols.run_document_processing_pipeline(self.messages)
        rows = sol.warehouse.query_all(
            "SELECT invoice_number, total, event_date"
            " FROM extracted_fields WHERE doc_id = 'd2'"
        )
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["invoice_number"])
        self.assertIsNone(rows[0]["total"])
        self.assertIsNone(rows[0]["event_date"])

    def test_search_index_built(self) -> None:
        sol = sols.run_document_processing_pipeline(self.messages)
        self.assertEqual(len(sol.search_index), 3)
        self.assertIn("d1", sol.search_index)
        self.assertEqual(sol.search_index["d1"]["doc_type"], "invoice")
        self.assertIn("INV-1234", sol.search_index["d1"]["body_text"])

    def test_empty_text_goes_to_dlq(self) -> None:
        msgs = [
            {
                "doc_id": "d1",
                "text": "INV-1234 Total: $1,234.56 2024-01-15",
                "doc_type": "invoice",
                "title": "Invoice 1",
            },
            {
                "doc_id": "d2",
                "text": "",
                "doc_type": "invoice",
                "title": "Empty",
            },
        ]
        sol = sols.run_document_processing_pipeline(msgs)
        self.assertEqual(sol.processed, 1)
        self.assertEqual(len(sol.dlq), 1)
        self.assertEqual(sol.dlq[0]["doc_id"], "d2")

    def test_summary(self) -> None:
        sol = sols.run_document_processing_pipeline(self.messages)
        summary = sols.get_solution_summary(sol)
        self.assertEqual(summary["processed"], 3)
        self.assertEqual(summary["search_index_size"], 3)
        self.assertEqual(summary["dlq_size"], 0)
        self.assertEqual(summary["warehouse_rows"], 3)


# ============================================================================
# Solution 3 — Banking CDC
# ============================================================================


class BankingCDCTests(unittest.TestCase):
    def setUp(self) -> None:
        self.initial_rows = [
            {"txn_id": 1, "account_id": 100, "amount": 10.0, "ts_ms": 1000},
            {"txn_id": 2, "account_id": 100, "amount": 20.0, "ts_ms": 2000},
            {"txn_id": 3, "account_id": 200, "amount": 50.0, "ts_ms": 3000},
        ]
        self.updates = [
            # Txn 1: amount spikes 10x -> fraud alert.
            {"txn_id": 1, "account_id": 100, "amount": 10000.0, "ts_ms": 4000},
            # Txn 2: deleted.
            # Txn 3: unchanged.
            {"txn_id": 3, "account_id": 200, "amount": 50.0, "ts_ms": 5000},
            # Txn 4: new row.
            {"txn_id": 4, "account_id": 200, "amount": 60.0, "ts_ms": 6000},
        ]

    def test_build_creates_components(self) -> None:
        sol = sols.build_banking_cdc_pipeline()
        # Source has accounts + transactions tables.
        tables = sol.source.query_all(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        names = {t["name"] for t in tables}
        self.assertIn("accounts", names)
        self.assertIn("transactions", names)
        # Broker has the two topics.
        self.assertIn("cdc.transactions", sol.broker._topics)
        self.assertIn("fraud.alerts", sol.broker._topics)
        # Warehouse has the bronze table.
        rows = sol.warehouse.query_all(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='bronze_transactions'"
        )
        self.assertEqual(len(rows), 1)

    def test_initial_snapshot_emits_creates(self) -> None:
        sol = sols.run_banking_cdc_pipeline(
            initial_rows=self.initial_rows, updates=[]
        )
        # 3 events from initial snapshot.
        self.assertGreaterEqual(sol.events_emitted, 3)
        # All initial rows are creates.
        op_rows = sol.warehouse.query_all(
            "SELECT DISTINCT op FROM bronze_transactions"
        )
        ops = {r["op"] for r in op_rows}
        # The updates pass with an empty list also emits 3 deletes
        # (since the source is wiped and the new snapshot is empty).
        # So we can see 'c' here at minimum.
        self.assertIn("c", ops)

    def test_full_run_emits_cu_d(self) -> None:
        sol = sols.run_banking_cdc_pipeline(
            initial_rows=self.initial_rows, updates=self.updates
        )
        # We should see c (initial), u (txn1 spike), u (txn3 unchanged is
        # NOT emitted by the CDC because it's identical; we also get
        # d (txn 2 deleted) and c (txn 4 new).
        op_rows = sol.warehouse.query_all(
            "SELECT op, COUNT(*) AS n FROM bronze_transactions GROUP BY op"
        )
        ops = {r["op"]: r["n"] for r in op_rows}
        # At minimum: 3 creates from initial, 1 create for txn4, 1 delete
        # for txn2. Unchanged rows do not generate events.
        self.assertGreaterEqual(ops.get("c", 0), 4)
        self.assertGreaterEqual(ops.get("d", 0), 1)
        # 1 update for txn1.
        self.assertGreaterEqual(ops.get("u", 0), 1)

    def test_fraud_alert_on_spike(self) -> None:
        sol = sols.run_banking_cdc_pipeline(
            initial_rows=self.initial_rows, updates=self.updates
        )
        # Txn 1 amount is 10x the mean of (10, 20) = 15 -> z = 9985/7.07 ≈ 1412
        # Way above 4σ -> fraud alert.
        self.assertGreaterEqual(len(sol.fraud_alerts), 1)
        first = sol.fraud_alerts[0]
        self.assertEqual(first["txn_id"], 1)
        self.assertGreaterEqual(first["score"], 0.9)

    def test_no_fraud_on_unchanged(self) -> None:
        # Updates that don't change anything relative to history don't
        # produce a fraud alert.
        no_change_updates = [
            {"txn_id": 1, "account_id": 100, "amount": 10.0, "ts_ms": 4000},
            {"txn_id": 2, "account_id": 100, "amount": 20.0, "ts_ms": 5000},
            {"txn_id": 3, "account_id": 200, "amount": 50.0, "ts_ms": 6000},
        ]
        sol = sols.run_banking_cdc_pipeline(
            initial_rows=self.initial_rows, updates=no_change_updates
        )
        # No spikes -> no fraud alerts.
        self.assertEqual(len(sol.fraud_alerts), 0)

    def test_summary(self) -> None:
        sol = sols.run_banking_cdc_pipeline(
            initial_rows=self.initial_rows, updates=self.updates
        )
        summary = sols.get_solution_summary(sol)
        self.assertGreater(summary["events_emitted"], 0)
        self.assertGreaterEqual(summary["fraud_alerts"], 1)
        self.assertGreater(summary["bronze_rows"], 0)


if __name__ == "__main__":
    unittest.main()

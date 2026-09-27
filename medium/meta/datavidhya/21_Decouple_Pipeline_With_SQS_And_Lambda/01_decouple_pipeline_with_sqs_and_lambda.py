"""Q21: Decouple a Pipeline with SQS and Lambda    [AWS | SQS, Lambda, DLQ, ESM]

A runnable, **offline-first** mirror of the AWS Skill Builder lab
"Decouple a Pipeline with SQS and Lambda." Seven stages, eight shell
scripts that map exactly to the lab's "click in the console" steps,
plus a pytest suite that drives the same in-memory SQS simulator. No
AWS credentials needed for verification.

How to think:
    Producers (web/API) write orders to SQS and forget. A Lambda event
    source mapping polls the queue in batches and invokes the consumer
    function. Bad messages keep failing; SQS retries them up to
    ``maxReceiveCount``, then the redrive policy parks them in the DLQ
    for human inspection. The producer and consumer never share state;
    the queue is the only contract between them.

The trap:
    Raising an exception inside ``lambda_handler`` is the *correct*
    poison-message signal. If you swallow it (try/except around the
    handler body and return success) you silently lose the bad payload.
    Conversely, if you call ``delete_message`` from inside the handler
    after a partial failure you can ack a message whose downstream
    effects never landed. The handler raises; SQS owns the retry policy.

AWS note:
    In production, SQS deletes on the Lambda event source mapping's
    "Successful messages deleted" metric. A handler that returns
    successfully means "all messages in this batch are processed" --
    SQS deletes them all. A handler that raises means "leave the batch
    in the queue" -- SQS retries the batch, ReceiveCount++ on each.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "lambda_function"))

from sqs_stub import SqsSimulator          # noqa: E402
from app import lambda_handler             # noqa: E402


# ============================================================ test harness
PASS, FAIL = "\u2713", "\u2717"
_results: List[Tuple[bool, str]] = []


def expect(title: str, ok: bool, detail: str = "") -> None:
    """Stage-style assertion -- mirrors slot 12's ``expect()`` helper."""
    tag = PASS if ok else FAIL
    line = f"  [{tag}] {title}" + (f" -- {detail}" if detail else "")
    print(line)
    _results.append((ok, title))


def section(title: str) -> None:
    print(f"\n--- {title} ---")


# ============================================================ load fixtures
def _load_orders(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


# ============================================================ main
def run() -> int:
    sample = os.path.join(HERE, "sample_data", "orders.json")
    all_orders = _load_orders(sample)
    good_orders = [o for o in all_orders
                   if not str(o.get("order_id", "")).startswith("POISON")]
    poison_orders = [o for o in all_orders
                     if str(o.get("order_id", "")).startswith("POISON")]

    sim = SqsSimulator()
    processed_batches: List[List[Dict[str, Any]]] = []

    # ---------------------------------------------------------- stage 1
    section("Stage 1 -- create the main SQS queue")
    main = sim.create_queue("orders-main-queue")
    expect("main queue created", main.name == "orders-main-queue")
    expect("main queue ARN is SQS-shaped",
           main.arn.startswith("arn:aws:sqs:") and main.name in main.arn)
    expect("main queue starts empty", main.size() == 0)

    # ---------------------------------------------------------- stage 2
    section("Stage 2 -- create the dead-letter queue")
    dlq = sim.create_queue("orders-dlq")
    expect("DLQ created", dlq.name == "orders-dlq")
    expect("DLQ starts empty", dlq.size() == 0)

    # ---------------------------------------------------------- stage 3
    section("Stage 3 -- attach the redrive policy (maxReceiveCount=3)")
    sim.attach_redrive("orders-main-queue", "orders-dlq",
                       max_receive_count=3)
    expect("main queue redrive points at DLQ",
           main.redrive_to is dlq)
    expect("main queue max_receive_count = 3",
           main.max_receive_count == 3)

    # ---------------------------------------------------------- stage 4
    section("Stage 4 -- wire the queue to Lambda via event source mapping")

    # Wrap the handler so we can record which batches were "processed",
    # including the ones that raised (poison-message retries).
    def recording_handler(event: Dict[str, Any], context: Any) -> Dict[str, int]:
        bodies = [json.loads(r["body"]) for r in event["Records"]]
        processed_batches.append(bodies)
        return lambda_handler(event, context)

    sim.install_event_source("orders-main-queue", recording_handler,
                              batch_size=5)
    expect("event source mapping installed",
           "orders-main-queue" in sim.event_source_mappings)
    expect("batch size captured as 5", sim.batch_size == 5)

    # ---------------------------------------------------------- stage 5
    section("Stage 5 -- send 8 good messages; observe batched processing")
    for order in good_orders:
        main.enqueue(json.dumps(order))
    expect("8 good messages enqueued", main.size() == 8)

    # Drive 2 polls: poll 1 grabs 5 (the maxReceiveCount=3 policy
    # doesn't gate the main queue while messages are healthy).
    sim.poll("orders-main-queue")
    sim.poll("orders-main-queue")
    expect("main queue drained of good messages", main.size() == 0)
    expect("DLQ still empty", dlq.size() == 0)
    expect("Lambda invoked exactly twice for good messages",
           len(processed_batches) == 2,
           f"got {len(processed_batches)} invocations")
    expect("first batch had 5 messages", len(processed_batches[0]) == 5)
    expect("second batch had 3 messages", len(processed_batches[1]) == 3)
    all_good_bodies = [b for batch in processed_batches for b in batch]
    expect("all 8 good messages reached the handler",
           len(all_good_bodies) == 8)
    expect("handler saw order_id 2001..2008",
           {b["order_id"] for b in all_good_bodies}
           == {str(i) for i in range(2001, 2009)})

    # ---------------------------------------------------------- stage 6
    section("Stage 6 -- send poison messages; trace retries -> DLQ")
    for poison in poison_orders:
        main.enqueue(json.dumps(poison))
    expect("2 poison messages enqueued", main.size() == 2)

    # Four rounds: ReceiveCount climbs past max_receive_count=3,
    # then redrive_poison() moves them to the DLQ. Both poisons arrive
    # in the same batch (batch_size=5 >> 2), so each round = 1 invocation.
    invocations_after_good = len(processed_batches)
    for round_num in range(1, 5):
        sim.poll("orders-main-queue")
        # After each poll, if redrive conditions are met, move them.
        main.redrive_poison()
        expected = invocations_after_good + round_num
        expect(f"round {round_num}: poison batch retried",
               len(processed_batches) == expected,
               f"got {len(processed_batches) - invocations_after_good} "
               f"extra invocations")

    expect("main queue drained of poison (no orphan messages)",
           main.size() == 0)
    expect("DLQ contains both poison messages", dlq.size() == 2,
           f"DLQ has {dlq.size()}")

    # DLQ receives them with ReceiveCount reset to 1.
    dlq_receive_counts = sorted(m.receive_count for m in dlq.messages)
    expect("DLQ messages have reset ReceiveCount = 1",
           dlq_receive_counts == [1, 1],
           f"got {dlq_receive_counts}")

    dlq_ids = sorted(m.attributes.get("order_id", "")
                      or json.loads(m.body)["order_id"]
                      for m in dlq.messages)
    expect("DLQ contains exactly the two POISON order_ids",
           dlq_ids == ["POISON_BAD_CURRENCY", "POISON_MISSING_AMOUNT"],
           f"got {dlq_ids}")

    # ---------------------------------------------------------- stage 7
    section("Stage 7 -- teardown")
    sim.event_source_mappings.clear()
    sim.queues.clear()
    expect("event source mappings cleared",
           sim.event_source_mappings == {})
    expect("queues dropped", sim.queues == {})
    expect("processed_batches history preserved for inspection",
           len(processed_batches) == 6,
           f"total Lambda invocations = {len(processed_batches)}")

    # ---------------------------------------------------------- summary
    total = len(_results)
    passed = sum(1 for ok, _ in _results if ok)
    print(f"\n=== {passed}/{total} checks passed ===")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(run())

"""Lambda handler: EventBridge wrapper around the L16 EC2 lifecycle handler.

Companion to L17.

# --- What this Lambda is and how it is invoked -------------------------
#
# This Lambda is invoked by two EventBridge scheduled rules:
#
#   1. StartRule  (cron 0 8 ? * MON-FRI *)  ->  Input: {"action":"start", "instance_id":"i-..."}
#   2. StopRule   (cron 0 20 ? * MON-FRI *) ->  Input: {"action":"stop",  "instance_id":"i-..."}
#
# EventBridge wraps the rule's Input in a standard envelope:
#
#   {
#     "version":     "0",
#     "id":          "...",
#     "detail-type": "Scheduled Event",
#     "source":      "aws.events",
#     "time":        "2026-10-10T08:00:00Z",
#     "region":      "us-east-1",
#     "resources":   ["arn:aws:events:...:rule/StartRule"],
#     "detail":      {"action": "start", "instance_id": "i-..."}
#   }
#
# The L16 handler expects a flat shape ({"action", "instance_id"}).
# This wrapper normalizes the two shapes — wrapped and flat — and
# delegates to the L16 handler.
#
# --- IAM ---------------------------------------------------------------
#
# Lambda execution role needs (real AWS):
#   ec2:DescribeInstances
#   ec2:StartInstances
#   ec2:StopInstances
#   logs:CreateLogGroup, logs:CreateLogStream, logs:PutLogEvents
#
# Lambda resource-based policy (real AWS) — one per rule:
#   {
#     "Effect": "Allow",
#     "Principal": { "Service": "events.amazonaws.com" },
#     "Action":   "lambda:InvokeFunction",
#     "Resource": "<this-lambda-arn>",
#     "Condition": { "ArnLike": { "AWS:SourceArn": "<rule-arn>" } }
#   }
#
# The full CloudFormation is in README.md of this directory.
"""

import json
import logging
import os
import sys

# The L16 handler lives in the sibling directory `ec2_lifecycle/`.
# Add it to sys.path so the wrapper can be deployed as a single Lambda
# package alongside start_stop_ec2.py.
_SIBLING = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "ec2_lifecycle",
)
sys.path.insert(0, os.path.abspath(_SIBLING))

from start_stop_ec2 import handler as ec2_lifecycle_handler  # noqa: E402

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)


def handler(event, context):
    """Normalize the EventBridge event shape and delegate to L16.

    Returns the result from the L16 handler unchanged.
    """
    LOG.info("eventbridge event: %s", json.dumps(event))

    payload = (event or {}).get("detail") or event or {}

    action = payload.get("action")
    if not action:
        raise ValueError("event is missing required 'action' key")

    return ec2_lifecycle_handler(payload, context)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    sample = {
        "version": "0",
        "id": "demo-event-id",
        "detail-type": "Scheduled Event",
        "source": "aws.events",
        "time": "2026-10-10T08:00:00Z",
        "region": "us-east-1",
        "resources": ["arn:aws:events:us-east-1:123456789012:rule/StartRule"],
        "detail": {"action": "start", "instance_id": "i-0123456789abcdef0"},
    }
    print(handler(sample, None))

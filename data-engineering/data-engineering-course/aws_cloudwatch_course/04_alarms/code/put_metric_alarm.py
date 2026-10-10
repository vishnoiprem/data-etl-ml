"""put_metric_alarm.py — create an SNS topic + a metric alarm on EC2 CPU.

Companion to L17/L19. Idempotent: existing topic / alarm are not
duplicated.

Required IAM permissions (real AWS):
    cloudwatch:PutMetricAlarm
    cloudwatch:DescribeAlarms
    sns:CreateTopic
    sns:Subscribe
    sns:SetTopicAttributes
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

import boto3
from botocore.config import Config

LOG = logging.getLogger("put_metric_alarm")
LOG.setLevel(logging.INFO)

TOPIC_NAME = "cw-demo-pager"
ALARM_NAME = "ec2-cpu-high-70"
ALARM_DESCRIPTION = "Page on-call when EC2 CPU > 70% for 3 of 3 min"
SUBSCRIPTION_EMAIL = "oncall@example.com"

ALARM_PARAMS = dict(
    AlarmName=ALARM_NAME,
    AlarmDescription=ALARM_DESCRIPTION,
    Namespace="AWS/EC2",
    MetricName="CPUUtilization",
    Statistic="Average",
    Dimensions=[{"Name": "InstanceId", "Value": "i-0deadbeefcafe"}],
    Period=60,
    EvaluationPeriods=3,
    DatapointsToAlarm=3,
    Threshold=70.0,
    ComparisonOperator="GreaterThanThreshold",
    TreatMissingData="notBreaching",
    ActionsEnabled=True,
)


def _client(service: str, region: str = "us-east-1"):
    return boto3.client(
        service,
        region_name=region,
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )


def ensure_topic(sns, *, dry_run: bool = False) -> str:
    if dry_run:
        LOG.info("[DRY-RUN] create_topic Name=%s", TOPIC_NAME)
        return f"arn:aws:sns:us-east-1:111122223333:{TOPIC_NAME}"
    resp = sns.create_topic(Name=TOPIC_NAME)
    arn = resp["TopicArn"]
    LOG.info("topic %s = %s", TOPIC_NAME, arn)
    return arn


def allow_cw_to_publish(sns, topic_arn: str, *, dry_run: bool = False) -> None:
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowCloudWatchAlarmsToPublish",
            "Effect": "Allow",
            "Principal": {"Service": "cloudwatch.amazonaws.com"},
            "Action": "SNS:Publish",
            "Resource": topic_arn,
        }],
    }
    if dry_run:
        LOG.info("[DRY-RUN] set_topic_attributes Policy=%s", json.dumps(policy))
        return
    sns.set_topic_attributes(
        TopicArn=topic_arn,
        AttributeName="Policy",
        AttributeValue=json.dumps(policy),
    )


def subscribe_email(sns, topic_arn: str, email: str, *, dry_run: bool = False) -> None:
    if dry_run:
        LOG.info("[DRY-RUN] subscribe %s to %s", email, topic_arn)
        return
    try:
        sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email,
        )
        LOG.info("subscribed %s to %s (confirmation email sent)", email, topic_arn)
    except Exception as exc:  # pragma: no cover - real AWS path
        LOG.warning("subscribe failed (probably already exists): %s", exc)


def ensure_alarm(cw, topic_arn: str, *, dry_run: bool = False) -> None:
    params = dict(ALARM_PARAMS)
    params["AlarmActions"] = [topic_arn]
    if dry_run:
        LOG.info("[DRY-RUN] put_metric_alarm:\n%s", json.dumps(params, indent=2))
        return
    cw.put_metric_alarm(**params)
    LOG.info("created alarm %s", ALARM_NAME)


def describe_alarm(cw, *, dry_run: bool = False) -> dict | None:
    if dry_run:
        LOG.info("[DRY-RUN] describe_alarms AlarmNamePrefix=%s", ALARM_NAME)
        return None
    resp = cw.describe_alarms(AlarmNamePrefix=ALARM_NAME)
    alarms = resp.get("MetricAlarms", [])
    return alarms[0] if alarms else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    sns = _client("sns", args.region)
    cw = _client("cloudwatch", args.region)

    print(f"[1/4] ensure_topic ({TOPIC_NAME})")
    topic_arn = ensure_topic(sns, dry_run=args.dry_run)
    print(f"      arn = {topic_arn}")
    print("[2/4] allow_cw_to_publish")
    allow_cw_to_publish(sns, topic_arn, dry_run=args.dry_run)
    print(f"[3/4] subscribe_email ({SUBSCRIPTION_EMAIL})")
    subscribe_email(sns, topic_arn, SUBSCRIPTION_EMAIL, dry_run=args.dry_run)
    print(f"[4/4] ensure_alarm ({ALARM_NAME})")
    ensure_alarm(cw, topic_arn, dry_run=args.dry_run)
    desc = describe_alarm(cw, dry_run=args.dry_run)
    if desc:
        print(f"      state   = {desc.get('StateValue')}")
        print(f"      actions = {desc.get('AlarmActions')}")
        print(f"      threshold = {desc.get('Threshold')} {desc.get('ComparisonOperator')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

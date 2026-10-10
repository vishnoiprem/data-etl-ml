"""
test_alb_create.py — pytest tests for ``alb_create.create_alb_and_rules``.

> **Author:** Prem Vishnoi <prem.vishnoi@example.com>
> **Section:** 7 — Application Load Balancer

Four tests, all backed by ``moto>=5`` via ``@mock_aws``. The fixture
provisions a VPC and two subnets in two AZs, then calls the function
under test. The four tests assert the four properties listed in the
section README:

* ``test_alb_type_is_application`` — the load balancer is an ALB.
* ``test_default_listener_exists`` — a listener on port 80.
* ``test_path_rule_forwards_to_target_group`` — priority-10 rule with
  path-pattern ``/api/*`` and a forward action.
* ``test_default_action_is_fixed_404`` — the default listener action
  is a fixed-response with status code 404.

Run with::

    python -m pytest -v

Expected: 4 passed.
"""

from __future__ import annotations

import os
from typing import Any, Dict

import boto3
import pytest
from moto import mock_aws

from alb_create import create_alb_and_rules


# ---------------------------------------------------------------------------
# Fixtures — build a VPC with two subnets in two AZs and a security group,
# then call the function under test. All four tests share this state.
# ---------------------------------------------------------------------------
@pytest.fixture
def aws_env() -> Dict[str, Any]:
    """Provision VPC + 2 subnets + SG inside moto and call the function."""
    with mock_aws():
        ec2 = boto3.client("ec2", region_name="us-east-1")
        elbv2 = boto3.client("elbv2", region_name="us-east-1")

        # ----- VPC -----
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")["Vpc"]
        vpc_id = vpc["VpcId"]

        # ----- Two subnets in two AZs (ALB hard requirement) -----
        subnet_a = ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone="us-east-1a"
        )["Subnet"]
        subnet_b = ec2.create_subnet(
            VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone="us-east-1b"
        )["Subnet"]
        subnet_ids = [subnet_a["SubnetId"], subnet_b["SubnetId"]]

        # ----- Security group allowing inbound HTTP 80 -----
        sg = ec2.create_security_group(
            GroupName="alb-sg",
            Description="ALB SG",
            VpcId=vpc_id,
        )
        ec2.authorize_security_group_ingress(
            GroupId=sg["GroupId"],
            IpPermissions=[
                {
                    "IpProtocol": "TCP",
                    "FromPort": 80,
                    "ToPort": 80,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                }
            ],
        )

        # ----- Call the function under test -----
        result = create_alb_and_rules(
            vpc_id=vpc_id,
            subnet_ids=subnet_ids,
            security_group_id=sg["GroupId"],
            alb_name="alb-demo-test",
            tg_name="tg-alb-demo-test",
            region_name="us-east-1",
            client=elbv2,
        )

        yield {
            "ec2": ec2,
            "elbv2": elbv2,
            "vpc_id": vpc_id,
            "subnet_ids": subnet_ids,
            "sg_id": sg["GroupId"],
            "result": result,
        }


# ---------------------------------------------------------------------------
# Tests — the four assertions from the section README.
# ---------------------------------------------------------------------------
def test_alb_type_is_application(aws_env: Dict[str, Any]) -> None:
    """The load balancer is an ALB (``Type == 'application'``)."""
    elbv2 = aws_env["elbv2"]
    arn = aws_env["result"]["alb_arn"]

    resp = elbv2.describe_load_balancers(LoadBalancerArns=[arn])
    lb = resp["LoadBalancers"][0]
    assert lb["Type"] == "application"
    assert lb["Scheme"] == "internet-facing"
    az_names = {az["ZoneName"] for az in lb["AvailabilityZones"]}
    assert {"us-east-1a", "us-east-1b"} <= az_names


def test_default_listener_exists(aws_env: Dict[str, Any]) -> None:
    """A listener on port 80 exists for the ALB."""
    elbv2 = aws_env["elbv2"]
    arn = aws_env["result"]["listener_arn"]

    resp = elbv2.describe_listeners(ListenerArns=[arn])
    listener = resp["Listeners"][0]
    assert listener["Protocol"] == "HTTP"
    assert listener["Port"] == 80
    assert listener["LoadBalancerArn"] == aws_env["result"]["alb_arn"]


def test_path_rule_forwards_to_target_group(aws_env: Dict[str, Any]) -> None:
    """Priority-10 rule with path-pattern ``/api/*`` forwards to the TG."""
    elbv2 = aws_env["elbv2"]
    listener_arn = aws_env["result"]["listener_arn"]
    tg_arn = aws_env["result"]["target_group_arn"]

    resp = elbv2.describe_rules(ListenerArn=listener_arn)
    api_rules = [
        r for r in resp["Rules"] if r.get("Priority") == "10"
    ]
    assert len(api_rules) == 1, "expected exactly one rule at priority 10"
    rule = api_rules[0]

    # Condition: path-pattern = /api/*
    conds = rule["Conditions"]
    path_conds = [c for c in conds if c["Field"] == "path-pattern"]
    assert path_conds, "expected a path-pattern condition"
    assert path_conds[0]["Values"] == ["/api/*"]

    # Action: forward to the target group
    actions = rule["Actions"]
    assert len(actions) == 1
    assert actions[0]["Type"] == "forward"
    assert actions[0]["TargetGroupArn"] == tg_arn


def test_default_action_is_fixed_404(aws_env: Dict[str, Any]) -> None:
    """The default action is a fixed-response 404."""
    elbv2 = aws_env["elbv2"]
    listener_arn = aws_env["result"]["listener_arn"]

    resp = elbv2.describe_rules(ListenerArn=listener_arn)

    # The default action is on the rule whose Priority is "default".
    default_rules = [
        r for r in resp["Rules"] if r.get("Priority") == "default"
    ]
    assert len(default_rules) == 1, "expected exactly one default rule"
    default_rule = default_rules[0]

    actions = default_rule["Actions"]
    assert len(actions) == 1
    assert actions[0]["Type"] == "fixed-response"
    assert actions[0]["FixedResponseConfig"]["StatusCode"] == "404"
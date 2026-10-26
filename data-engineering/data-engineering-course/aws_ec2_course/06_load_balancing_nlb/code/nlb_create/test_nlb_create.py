"""Tests for the nlb_create.py NLB setup script.

Every test uses @mock_aws from moto to stub the elbv2 client, so the
suite is fully offline and runs in <1 second.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

HERE = Path(__file__).resolve().parent
SCRIPT_PATH = HERE / "nlb_create.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("nlb_create", SCRIPT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def script(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-east-1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    if "nlb_create" in sys.modules:
        del sys.modules["nlb_create"]
    return _load_script()


# ── tests ──────────────────────────────────────────────────────────────
def test_create_target_group_returns_arn(script):
    """create_target_group must return an ARN in the expected format."""
    with mock_aws():
        client = boto3.client("elbv2", region_name="us-east-1")
        # moto requires a VPC for target group creation
        ec2 = boto3.client("ec2", region_name="us-east-1")
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        tg_arn = script.create_target_group(
            client,
            name="demo-tg",
            vpc_id=vpc_id,
        )

    assert isinstance(tg_arn, str)
    assert tg_arn.startswith("arn:aws:elasticloadbalancing:")
    assert ":targetgroup/demo-tg/" in tg_arn


def test_create_nlb_returns_dns(script):
    """create_nlb + describe_load_balancers must return a DNS name
    that ends with .elb.<region>.amazonaws.com."""
    with mock_aws():
        client = boto3.client("elbv2", region_name="us-east-1")
        ec2 = boto3.client("ec2", region_name="us-east-1")
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        # moto requires two subnets in different AZs to create an NLB
        az1 = "us-east-1a"
        az2 = "us-east-1b"
        sn1 = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone=az1)
        sn2 = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone=az2)

        nlb_arn = script.create_nlb(
            client,
            name="demo-nlb",
            subnet_ids=[sn1["Subnet"]["SubnetId"], sn2["Subnet"]["SubnetId"]],
        )

        described = client.describe_load_balancers(LoadBalancerArns=[nlb_arn])
        dns_name = described["LoadBalancers"][0]["DNSName"]

    assert isinstance(dns_name, str)
    assert dns_name.endswith(".elb.amazonaws.com")
    assert "us-east-1" in dns_name


def test_listener_forward_to_target_group(script):
    """create_listener must register exactly 1 default action that
    forwards to the supplied target group ARN."""
    with mock_aws():
        client = boto3.client("elbv2", region_name="us-east-1")
        ec2 = boto3.client("ec2", region_name="us-east-1")
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        tg_arn = script.create_target_group(
            client, name="demo-tg", vpc_id=vpc_id,
        )

        az1 = "us-east-1a"
        az2 = "us-east-1b"
        sn1 = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone=az1)
        sn2 = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone=az2)
        nlb_arn = script.create_nlb(
            client,
            name="demo-nlb",
            subnet_ids=[sn1["Subnet"]["SubnetId"], sn2["Subnet"]["SubnetId"]],
        )

        listener_arn = script.create_listener(
            client,
            load_balancer_arn=nlb_arn,
            target_group_arn=tg_arn,
        )

        described = client.describe_listeners(ListenerArns=[listener_arn])
        listener = described["Listeners"][0]

    assert len(listener["DefaultActions"]) == 1
    action = listener["DefaultActions"][0]
    assert action["Type"] == "forward"
    assert action["TargetGroupArn"] == tg_arn


def test_nlb_type_is_network(script):
    """The created NLB must have Type='network' (and not 'application' or 'gateway')."""
    with mock_aws():
        client = boto3.client("elbv2", region_name="us-east-1")
        ec2 = boto3.client("ec2", region_name="us-east-1")
        vpc = ec2.create_vpc(CidrBlock="10.0.0.0/16")
        vpc_id = vpc["Vpc"]["VpcId"]

        az1 = "us-east-1a"
        az2 = "us-east-1b"
        sn1 = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.1.0/24", AvailabilityZone=az1)
        sn2 = ec2.create_subnet(VpcId=vpc_id, CidrBlock="10.0.2.0/24", AvailabilityZone=az2)

        nlb_arn = script.create_nlb(
            client,
            name="demo-nlb",
            subnet_ids=[sn1["Subnet"]["SubnetId"], sn2["Subnet"]["SubnetId"]],
        )

        described = client.describe_load_balancers(LoadBalancerArns=[nlb_arn])
        nlb = described["LoadBalancers"][0]

    assert nlb["Type"] == "network"
    assert nlb["Scheme"] == "internet-facing"

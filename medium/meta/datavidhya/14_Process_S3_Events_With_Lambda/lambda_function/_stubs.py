"""Offline S3 stub + tiny CSV helpers shared by the driver and pytest suite.

Packaged alongside the Lambda handler so it ships with the deployment.
Tests import the classes/functions; the one-shot driver imports them
plus ``install()`` to monkey-patch boto3 in-place.
"""
from __future__ import annotations

import csv
import io
from typing import Any, Dict, Optional

import boto3


class StubBucket:
    """Minimal in-memory S3 replacement: dict[Key -> Body (bytes)]."""

    def __init__(self) -> None:
        self.objects: Dict[str, bytes] = {}

    def put(self, key: str, body: str) -> None:
        self.objects[key] = body.encode("utf-8")

    def get(self, key: str) -> str:
        return self.objects[key].decode("utf-8")

    def has(self, key: str) -> bool:
        return key in self.objects


class _StubS3Client:
    """Boto3-shaped subset (get_object / put_object) bound to a StubBucket."""

    def __init__(self, stub: StubBucket) -> None:
        self._stub = stub

    def get_object(self, Bucket, Key):
        if Key not in self._stub.objects:
            raise KeyError(Key)
        return {"Body": io.BytesIO(self._stub.objects[Key])}

    def put_object(self, Bucket, Key, Body, ContentType=None):
        if isinstance(Body, str):
            Body = Body.encode("utf-8")
        self._stub.objects[Key] = Body


def make_client(stub: StubBucket) -> _StubS3Client:
    """Return an object with .get_object/.put_object matching the boto3 API."""
    return _StubS3Client(stub)


def install(stub: StubBucket, monkeypatch: Optional[Any] = None) -> None:
    """Replace ``boto3.client('s3')`` with a stub.

    When called from pytest, pass the ``monkeypatch`` fixture so the original
    is restored after the test. The one-shot driver omits it because the
    process exits shortly after.
    """
    replacement = lambda *a, **kw: make_client(stub)
    if monkeypatch is not None:
        monkeypatch.setattr(boto3, "client", replacement)
    else:
        boto3.client = replacement


def load_csv(path: str):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def parse_csv(body: str):
    return list(csv.DictReader(io.StringIO(body)))

"""
oop/aws_wrapper.py — Shared Library AWS Wrapper (OOP style)
============================================================
Each AWS service is a class. AWSClientFactory composes them.
Mock stubs replace boto3 — no credentials needed for this demo.

Key contrast with Functional:
  - Multi-region = multiple AWSClientFactory instances (no config clash)
  - Each service is a namespaced object: aws.s3.upload(), aws.sqs.send()
  - Adding a service = adding one new class (not a new flat function set)
  - Context manager on factory logs entry/exit and enables teardown hooks
  - Thread-safe lazy client init via per-instance lock
"""

import json
import threading
from contextlib import contextmanager
from typing import Any, Optional
from unittest.mock import MagicMock

from .logger import Logger


# --- mock factories (same stubs as functional — same contrast, same data) ----

def _mock_s3() -> MagicMock:
    store: dict = {}
    m = MagicMock()
    m.put_object.side_effect     = lambda Bucket, Key, Body, **_: store.setdefault(Bucket, {}).__setitem__(Key, Body) or {}
    m.get_object.side_effect     = lambda Bucket, Key, **_: {"Body": type("B", (), {"read": lambda s: store[Bucket][Key]})()}
    m.list_objects_v2.side_effect = lambda Bucket, Prefix="", **_: {"Contents": [{"Key": k} for k in store.get(Bucket, {}) if k.startswith(Prefix)], "IsTruncated": False}
    m.delete_object.side_effect  = lambda Bucket, Key, **_: store.get(Bucket, {}).pop(Key, None)
    return m


def _mock_sqs() -> MagicMock:
    queues: dict = {}
    m = MagicMock()
    m.send_message.side_effect    = lambda QueueUrl, MessageBody, **_: queues.setdefault(QueueUrl, []).append({"Body": MessageBody, "ReceiptHandle": "rh-0", "MessageId": "id-0"}) or {"MessageId": "mock-id"}
    m.receive_message.side_effect = lambda QueueUrl, MaxNumberOfMessages=1, **_: {"Messages": (queues.get(QueueUrl) or [])[:MaxNumberOfMessages]}
    m.delete_message.side_effect  = lambda **_: {}
    return m


def _mock_ssm() -> MagicMock:
    store = {"/app/db/host": "localhost", "/app/db/port": "5432"}
    m = MagicMock()
    m.get_parameter.side_effect = lambda Name, **_: {"Parameter": {"Value": store[Name]}} if Name in store else (_ for _ in ()).throw(KeyError(Name))
    m.put_parameter.side_effect = lambda Name, Value, **_: store.__setitem__(Name, Value) or {}
    return m


_MOCK_FACTORIES = {"s3": _mock_s3, "sqs": _mock_sqs, "ssm": _mock_ssm}


# --- base class ----------------------------------------------------------

class AWSClient:
    """Lazy, thread-safe boto3 client wrapper."""
    _service: str = ""

    def __init__(self, region: str, mock: bool, logger: Logger) -> None:
        self._region  = region
        self._mock    = mock
        self._logger  = logger
        self._client  = None
        self._lock    = threading.Lock()

    @property
    def client(self) -> Any:
        if self._client is None:
            with self._lock:
                if self._client is None:
                    if self._mock:
                        self._client = _MOCK_FACTORIES[self._service]()
                        self._logger.info(f"[AWS-OOP] mock client: {self._service}")
                    else:
                        import boto3
                        self._client = boto3.client(self._service, region_name=self._region)
        return self._client


# --- service classes -----------------------------------------------------

class S3Client(AWSClient):
    _service = "s3"

    def upload(self, bucket: str, key: str, body: Any) -> None:
        self._logger.info(f"[S3-OOP] upload s3://{bucket}/{key}")
        self.client.put_object(Bucket=bucket, Key=key, Body=body)

    def download(self, bucket: str, key: str) -> bytes:
        self._logger.info(f"[S3-OOP] download s3://{bucket}/{key}")
        return self.client.get_object(Bucket=bucket, Key=key)["Body"].read()

    def list_objects(self, bucket: str, prefix: str = "") -> list:
        return [o["Key"] for o in self.client.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", [])]

    def delete(self, bucket: str, key: str) -> None:
        self.client.delete_object(Bucket=bucket, Key=key)


class SQSClient(AWSClient):
    _service = "sqs"

    def send(self, queue: str, message: Any) -> str:
        body = message if isinstance(message, str) else json.dumps(message)
        self._logger.info(f"[SQS-OOP] send -> {queue}")
        return self.client.send_message(QueueUrl=queue, MessageBody=body)["MessageId"]

    def receive(self, queue: str, max_msgs: int = 1) -> list:
        return self.client.receive_message(QueueUrl=queue, MaxNumberOfMessages=max_msgs).get("Messages", [])


class SSMClient(AWSClient):
    _service = "ssm"

    def get(self, name: str) -> str:
        self._logger.info(f"[SSM-OOP] get {name}")
        return self.client.get_parameter(Name=name)["Parameter"]["Value"]

    def put(self, name: str, value: str) -> None:
        self._logger.info(f"[SSM-OOP] put {name}")
        self.client.put_parameter(Name=name, Value=value)


# --- factory (composition) -----------------------------------------------

class AWSClientFactory:
    """
    Single entry point for all AWS clients.
    Use as a context manager for clean lifecycle logging.

        with AWSClientFactory() as aws:
            aws.s3.upload("bucket", "key", data)
            aws.sqs.send(queue_url, payload)
            value = aws.ssm.get("/app/db/host")
    """

    def __init__(self, region: str = "us-east-1", mock: bool = True,
                 logger: Optional[Logger] = None) -> None:
        lg = logger or Logger.get_instance()
        kw = dict(region=region, mock=mock, logger=lg)
        self.s3  = S3Client(**kw)
        self.sqs = SQSClient(**kw)
        self.ssm = SSMClient(**kw)
        self._logger = lg
        lg.info(f"[AWS-OOP] factory ready: region={region} mock={mock}")

    def __enter__(self) -> "AWSClientFactory":
        return self

    def __exit__(self, *_) -> None:
        self._logger.info("[AWS-OOP] factory context exited")

    def __repr__(self) -> str:
        return f"AWSClientFactory(region={self.s3._region!r}, mock={self.s3._mock})"

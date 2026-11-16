"""
functional/aws_wrapper.py — Shared Library AWS Wrapper (Functional style)
==========================================================================
Clients stored in a module-level dict.
All operations are prefixed free functions (s3_*, sqs_*, ssm_*).
Mock stubs replace boto3 so no AWS credentials are needed.

Key contrast with OOP:
  - One global config (region/mock) — multi-region needs workarounds
  - Each service is a flat set of functions (s3_upload, sqs_send, …)
  - Adding a new service adds more top-level functions to this module
  - No context manager for lifecycle — callers manage cleanup themselves
"""

import json
from typing import Any
from unittest.mock import MagicMock

from . import logger as log

# Module-level state
_config: dict = {"region": "us-east-1", "mock": True}
_clients: dict[str, Any] = {}


def configure(region: str = "us-east-1", mock: bool = True) -> None:
    _config.update(region=region, mock=mock)
    _clients.clear()
    log.info(f"[AWS-FN] configured: region={region} mock={mock}")


# --- mock factories (replace with boto3.client() for real AWS) -----------

def _mock_s3() -> MagicMock:
    store: dict = {}
    m = MagicMock()
    m.put_object.side_effect    = lambda Bucket, Key, Body, **_: store.setdefault(Bucket, {}).__setitem__(Key, Body) or {}
    m.get_object.side_effect    = lambda Bucket, Key, **_: {"Body": type("B", (), {"read": lambda s: store[Bucket][Key]})()}
    m.list_objects_v2.side_effect = lambda Bucket, Prefix="", **_: {"Contents": [{"Key": k} for k in store.get(Bucket, {}) if k.startswith(Prefix)], "IsTruncated": False}
    m.delete_object.side_effect = lambda Bucket, Key, **_: store.get(Bucket, {}).pop(Key, None)
    return m


def _mock_sqs() -> MagicMock:
    queues: dict = {}
    m = MagicMock()
    m.send_message.side_effect    = lambda QueueUrl, MessageBody, **_: queues.setdefault(QueueUrl, []).append({"Body": MessageBody, "ReceiptHandle": f"rh-{len(queues)}", "MessageId": f"id-{len(queues)}"}) or {"MessageId": "mock-id"}
    m.receive_message.side_effect = lambda QueueUrl, MaxNumberOfMessages=1, **_: {"Messages": (queues.get(QueueUrl) or [])[:MaxNumberOfMessages]}
    m.delete_message.side_effect  = lambda **_: {}
    return m


def _mock_ssm() -> MagicMock:
    store = {"/app/db/host": "localhost", "/app/db/port": "5432"}
    m = MagicMock()
    m.get_parameter.side_effect = lambda Name, **_: {"Parameter": {"Value": store[Name]}} if Name in store else (_ for _ in ()).throw(KeyError(Name))
    m.put_parameter.side_effect = lambda Name, Value, **_: store.__setitem__(Name, Value) or {}
    return m


def _client(service: str) -> Any:
    if service not in _clients:
        _clients[service] = {"s3": _mock_s3, "sqs": _mock_sqs, "ssm": _mock_ssm}[service]() if _config["mock"] else __import__("boto3").client(service, region_name=_config["region"])
    return _clients[service]


# --- S3 ------------------------------------------------------------------
def s3_upload(bucket: str, key: str, body: Any) -> None:
    log.info(f"[S3-FN] upload s3://{bucket}/{key}")
    _client("s3").put_object(Bucket=bucket, Key=key, Body=body)

def s3_download(bucket: str, key: str) -> bytes:
    log.info(f"[S3-FN] download s3://{bucket}/{key}")
    return _client("s3").get_object(Bucket=bucket, Key=key)["Body"].read()

def s3_list(bucket: str, prefix: str = "") -> list:
    return [o["Key"] for o in _client("s3").list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", [])]

def s3_delete(bucket: str, key: str) -> None:
    _client("s3").delete_object(Bucket=bucket, Key=key)


# --- SQS -----------------------------------------------------------------
def sqs_send(queue: str, message: Any) -> str:
    body = message if isinstance(message, str) else json.dumps(message)
    log.info(f"[SQS-FN] send -> {queue}")
    return _client("sqs").send_message(QueueUrl=queue, MessageBody=body)["MessageId"]

def sqs_receive(queue: str, max_msgs: int = 1) -> list:
    return _client("sqs").receive_message(QueueUrl=queue, MaxNumberOfMessages=max_msgs).get("Messages", [])


# --- SSM -----------------------------------------------------------------
def ssm_get(name: str) -> str:
    log.info(f"[SSM-FN] get {name}")
    return _client("ssm").get_parameter(Name=name)["Parameter"]["Value"]

def ssm_put(name: str, value: str) -> None:
    log.info(f"[SSM-FN] put {name}")
    _client("ssm").put_parameter(Name=name, Value=value)

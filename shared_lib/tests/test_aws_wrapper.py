"""Tests — AWS Wrapper: functional vs OOP produce same results, different structure."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import json
import pytest
import shared_lib.functional.aws_wrapper as fn_aws
from shared_lib.oop.aws_wrapper import AWSClientFactory
from shared_lib.oop.logger import Logger

BUCKET = "test-bucket"
QUEUE  = "https://sqs.us-east-1.amazonaws.com/123/test-queue"


# ── Functional ────────────────────────────────────────────────────────────

def setup_function():
    fn_aws.configure(region="us-east-1", mock=True)


def test_fn_s3_upload_and_download():
    fn_aws.s3_upload(BUCKET, "file.txt", b"hello")
    assert fn_aws.s3_download(BUCKET, "file.txt") == b"hello"


def test_fn_s3_list():
    fn_aws.s3_upload(BUCKET, "a/1.txt", b"1")
    fn_aws.s3_upload(BUCKET, "a/2.txt", b"2")
    fn_aws.s3_upload(BUCKET, "b/3.txt", b"3")
    keys = fn_aws.s3_list(BUCKET, prefix="a/")
    assert "a/1.txt" in keys
    assert "b/3.txt" not in keys


def test_fn_s3_delete():
    fn_aws.s3_upload(BUCKET, "del.txt", b"x")
    fn_aws.s3_delete(BUCKET, "del.txt")
    assert "del.txt" not in fn_aws.s3_list(BUCKET, prefix="del")


def test_fn_sqs_send_and_receive():
    fn_aws.sqs_send(QUEUE, {"event": "test"})
    msgs = fn_aws.sqs_receive(QUEUE, max_msgs=1)
    assert len(msgs) == 1
    assert json.loads(msgs[0]["Body"]) == {"event": "test"}


def test_fn_sqs_send_string():
    fn_aws.sqs_send(QUEUE, "plain string")
    msgs = fn_aws.sqs_receive(QUEUE, max_msgs=1)
    assert msgs[0]["Body"] == "plain string"


def test_fn_ssm_get_existing_param():
    assert fn_aws.ssm_get("/app/db/host") == "localhost"


def test_fn_ssm_put_and_get():
    fn_aws.ssm_put("/app/new-key", "new-value")
    assert fn_aws.ssm_get("/app/new-key") == "new-value"


def test_fn_ssm_missing_param_raises():
    with pytest.raises(KeyError):
        fn_aws.ssm_get("/does/not/exist")


def test_fn_configure_clears_clients():
    fn_aws.s3_upload(BUCKET, "probe.txt", b"x")
    fn_aws.configure(mock=True)
    assert fn_aws._clients == {}


# ── OOP ───────────────────────────────────────────────────────────────────

def test_oop_s3_upload_and_download():
    Logger.reset()
    with AWSClientFactory(mock=True) as aws:
        aws.s3.upload(BUCKET, "file.txt", b"hello")
        assert aws.s3.download(BUCKET, "file.txt") == b"hello"


def test_oop_s3_list():
    Logger.reset()
    with AWSClientFactory(mock=True) as aws:
        aws.s3.upload(BUCKET, "a/1.txt", b"1")
        aws.s3.upload(BUCKET, "a/2.txt", b"2")
        aws.s3.upload(BUCKET, "b/3.txt", b"3")
        keys = aws.s3.list_objects(BUCKET, prefix="a/")
        assert "a/1.txt" in keys
        assert "b/3.txt" not in keys


def test_oop_s3_delete():
    Logger.reset()
    with AWSClientFactory(mock=True) as aws:
        aws.s3.upload(BUCKET, "del.txt", b"x")
        aws.s3.delete(BUCKET, "del.txt")
        assert "del.txt" not in aws.s3.list_objects(BUCKET, prefix="del")


def test_oop_sqs_send_and_receive():
    Logger.reset()
    with AWSClientFactory(mock=True) as aws:
        aws.sqs.send(QUEUE, {"event": "test"})
        msgs = aws.sqs.receive(QUEUE, max_msgs=1)
        assert len(msgs) == 1
        assert json.loads(msgs[0]["Body"]) == {"event": "test"}


def test_oop_ssm_get_existing_param():
    Logger.reset()
    with AWSClientFactory(mock=True) as aws:
        assert aws.ssm.get("/app/db/host") == "localhost"


def test_oop_ssm_put_and_get():
    Logger.reset()
    with AWSClientFactory(mock=True) as aws:
        aws.ssm.put("/app/new-key", "new-value")
        assert aws.ssm.get("/app/new-key") == "new-value"


def test_oop_ssm_missing_param_raises():
    Logger.reset()
    with AWSClientFactory(mock=True) as aws:
        with pytest.raises(KeyError):
            aws.ssm.get("/does/not/exist")


def test_oop_multi_region_independent():
    Logger.reset()
    us = AWSClientFactory(region="us-east-1", mock=True)
    eu = AWSClientFactory(region="eu-west-1",  mock=True)
    us.s3.upload(BUCKET, "us.txt", b"us data")
    eu.s3.upload(BUCKET, "eu.txt", b"eu data")
    assert us.s3.list_objects(BUCKET) != eu.s3.list_objects(BUCKET)


def test_oop_client_lazy_init():
    Logger.reset()
    factory = AWSClientFactory(mock=True)
    assert factory.s3._client is None
    _ = factory.s3.client
    assert factory.s3._client is not None


# ── Comparison ────────────────────────────────────────────────────────────

def test_both_s3_round_trip_match():
    Logger.reset()
    fn_aws.configure(mock=True)
    fn_aws.s3_upload(BUCKET, "cmp.txt", b"compare me")
    fn_data = fn_aws.s3_download(BUCKET, "cmp.txt")

    with AWSClientFactory(mock=True) as aws:
        aws.s3.upload(BUCKET, "cmp.txt", b"compare me")
        oop_data = aws.s3.download(BUCKET, "cmp.txt")

    assert fn_data == oop_data == b"compare me"


def test_both_ssm_get_same_default_values():
    Logger.reset()
    fn_aws.configure(mock=True)
    fn_host = fn_aws.ssm_get("/app/db/host")
    fn_port = fn_aws.ssm_get("/app/db/port")

    with AWSClientFactory(mock=True) as aws:
        oop_host = aws.ssm.get("/app/db/host")
        oop_port = aws.ssm.get("/app/db/port")

    assert fn_host == oop_host == "localhost"
    assert fn_port == oop_port == "5432"

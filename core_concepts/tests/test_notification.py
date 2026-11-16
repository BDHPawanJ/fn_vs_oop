"""Tests — Notification (functional vs OOP produce identical results)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from functional.notification import email_sender, sms_sender, notify
from oop.notification import EmailChannel, SMSChannel, NotificationService


def test_functional_notify_returns_results():
    results = notify("a@b.com", "Hello", [email_sender, sms_sender])
    assert results == {"email_sender": True, "sms_sender": True}


def test_oop_notify_returns_results():
    svc = NotificationService([EmailChannel(), SMSChannel()])
    results = svc.notify("a@b.com", "Hello")
    assert results == {"EmailChannel": True, "SMSChannel": True}


def test_empty_channels_returns_empty():
    assert notify("a@b.com", "Hello", []) == {}
    assert NotificationService([]).notify("a@b.com", "Hello") == {}


def test_single_channel():
    assert notify("a@b.com", "Hi", [email_sender]) == {"email_sender": True}
    svc = NotificationService([EmailChannel()])
    assert svc.notify("a@b.com", "Hi") == {"EmailChannel": True}

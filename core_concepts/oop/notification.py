"""
OOP — Notification
==================
Each channel is a class with a send() method.
NotificationService owns a list of channels and broadcasts to all.
Adding a channel = adding a new class and passing it to the service.
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class NotificationChannel(ABC):
    @abstractmethod
    def send(self, recipient: str, message: str) -> bool: ...


class EmailChannel(NotificationChannel):
    def send(self, recipient: str, message: str) -> bool:
        print(f"  [EMAIL] To: {recipient} | {message}")
        return True


class SMSChannel(NotificationChannel):
    def send(self, recipient: str, message: str) -> bool:
        print(f"  [SMS]   To: {recipient} | {message[:40]}")
        return True


class PushChannel(NotificationChannel):
    def send(self, recipient: str, message: str) -> bool:
        print(f"  [PUSH]  To: {recipient} | {message[:40]}")
        return True


class NotificationService:
    """Broadcasts a message across all registered channels."""

    def __init__(self, channels: "List[NotificationChannel]") -> None:
        self._channels = channels

    def notify(self, recipient: str, message: str) -> "Dict[str, bool]":
        return {
            ch.__class__.__name__: ch.send(recipient, message)
            for ch in self._channels
        }

    def notify_all(self, recipients: "List[str]", message: str) -> None:
        for r in recipients:
            self.notify(r, message)


# --- demo ---------------------------------------------------------------
if __name__ == "__main__":
    service = NotificationService([EmailChannel(), SMSChannel(), PushChannel()])
    results = service.notify("alice@example.com", "Your order has shipped!")
    print(f"  Results: {results}")

    print()
    service.notify_all(
        ["bob@example.com", "carol@example.com"],
        "Flash sale — 20% off today!",
    )

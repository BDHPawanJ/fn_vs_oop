"""
Functional — Notification
==========================
A "sender" is just a function: (recipient, message) -> bool.
Routing is done by composing a list of sender functions.
Swapping channels at runtime = swapping functions in a list.
No class, no state.
"""

from typing import Callable, List, Dict

Sender = Callable[[str, str], bool]


# --- channel implementations (pure functions) ---------------------------

def email_sender(recipient: str, message: str) -> bool:
    print(f"  [EMAIL] To: {recipient} | {message}")
    return True


def sms_sender(recipient: str, message: str) -> bool:
    print(f"  [SMS]   To: {recipient} | {message[:40]}")
    return True


def push_sender(recipient: str, message: str) -> bool:
    print(f"  [PUSH]  To: {recipient} | {message[:40]}")
    return True


# --- composition --------------------------------------------------------

def notify(recipient: str, message: str, senders: "List[Sender]") -> "Dict[str, bool]":
    """Send via every channel in senders; return a results dict."""
    return {fn.__name__: fn(recipient, message) for fn in senders}


def notify_all(recipients: "List[str]", message: str, senders: "List[Sender]") -> None:
    """Broadcast to multiple recipients."""
    for r in recipients:
        notify(r, message, senders)


# --- demo ---------------------------------------------------------------
if __name__ == "__main__":
    channels = [email_sender, sms_sender, push_sender]
    results = notify("alice@example.com", "Your order has shipped!", channels)
    print(f"  Results: {results}")

    print()
    notify_all(
        ["bob@example.com", "carol@example.com"],
        "Flash sale — 20% off today!",
        [email_sender, sms_sender],
    )

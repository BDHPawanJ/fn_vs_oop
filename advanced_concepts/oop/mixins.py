"""
OOP — Mixins
=============
CONCEPT
  A mixin is a class that provides reusable behaviour meant to be
  *mixed into* another class via multiple inheritance — not used
  standalone. Mixins solve the problem of sharing behaviour across
  unrelated class hierarchies without deep inheritance chains.

  Mixin vs Inheritance:
    Inheritance   = "is-a" relationship  (Dog is-a Animal)
    Mixin         = "can-do" capability  (Report can-do JSONSerializable)

  Mixin vs Decorator:
    Decorator wraps a function.  Mixin augments a class.

TYPES COVERED
  1. Single capability mixin    — JSONMixin, ReprMixin
  2. Stacking mixins            — combine independently
  3. Mixin with hook method     — mixin calls self.validate() that
                                  the host class defines (cooperative)
  4. Mixin ordering (MRO)       — Python resolves left-to-right

WHEN TO USE
  - You have 10 model classes that all need .to_json() and .from_json()
  - You want audit logging on selected service classes, not all
  - You need to bolt on behaviour to third-party classes you don't own

INSIGHT
  Keep mixins stateless where possible — they should add methods,
  not __init__ state. If a mixin needs state, document it clearly and
  use cooperative __init__ with super(). Never put business logic in a
  mixin; they should be pure infrastructure concerns.
"""

import json
from datetime import datetime


# ── 1. Pure capability mixins ─────────────────────────────────────────────

class JSONMixin:
    """Adds .to_json() / .from_dict() to any dataclass-like class."""
    def to_json(self) -> str:
        return json.dumps(self.__dict__, default=str)

    @classmethod
    def from_dict(cls, data: dict):
        # NOTE: bypasses __init__ — only safe for classes with no __init__ state.
        # Classes that stack mixins with __init__ (e.g. TimestampMixin) should
        # reconstruct via their own constructor instead.
        obj = cls.__new__(cls)
        obj.__dict__.update(data)
        return obj


class ReprMixin:
    """Adds a consistent __repr__ showing class name + all attributes."""
    def __repr__(self) -> str:
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"


class TimestampMixin:
    """Adds created_at / updated_at tracking."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_at: str = datetime.utcnow().isoformat()
        self.updated_at: str = self.created_at

    def touch(self) -> None:
        self.updated_at = datetime.utcnow().isoformat()


# ── 2. Mixin with hook — relies on host class implementing validate() ─────

class ValidateMixin:
    """
    Calls self.validate() before save(). The host class must define
    validate() — this is the Template Method pattern via mixins.
    """
    def save(self) -> str:
        errors = self.validate()           # hook — implemented by host
        if errors:
            raise ValueError(f"Validation failed: {errors}")
        return f"{self.__class__.__name__} saved."


# ── 3. Composing mixins — MRO resolved left to right ─────────────────────

class User(TimestampMixin, JSONMixin, ReprMixin, ValidateMixin):
    def __init__(self, name: str, email: str) -> None:
        super().__init__()
        self.name  = name
        self.email = email

    def validate(self) -> list:
        errors = []
        if not self.name:
            errors.append("name is required")
        if "@" not in self.email:
            errors.append("invalid email")
        return errors


class Product(JSONMixin, ReprMixin):
    def __init__(self, sku: str, price: float) -> None:
        self.sku   = sku
        self.price = price


# ── demo ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    u = User("Alice", "alice@example.com")
    print(repr(u))
    print(u.to_json())
    print(u.save())

    u.touch()
    print(f"updated_at changed: {u.updated_at != u.created_at}")

    p = Product("SKU-001", 29.99)
    print(repr(p))
    print(p.to_json())

    # Validation failure
    try:
        bad = User("", "not-an-email")
        bad.save()
    except ValueError as e:
        print(f"Caught: {e}")

    # MRO inspection
    print(f"\nUser MRO: {[c.__name__ for c in User.__mro__]}")

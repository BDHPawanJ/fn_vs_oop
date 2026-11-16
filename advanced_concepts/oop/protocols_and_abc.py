"""
OOP — Protocols vs Abstract Base Classes (ABC)
================================================
CONCEPT
  Both define a contract — a set of methods a class must implement.
  They differ in *how* the contract is enforced:

  ABC (Abstract Base Class)
    - Nominal typing: a class must explicitly inherit from the ABC
    - Python raises TypeError at *instantiation* if abstract methods
      are missing — catches errors early, before the object is used
    - Use when you own the class hierarchy and want hard enforcement

  Protocol (PEP 544 — structural subtyping / duck typing)
    - Structural typing: any class with the right methods qualifies —
      no inheritance required (third-party classes work automatically)
    - Checked by type checkers (mypy/pyright) at *type-check time*,
      not at runtime
    - Use when you don't own the classes, or want looser coupling

  Summary: ABC = "must inherit"   Protocol = "must have the methods"

WHEN TO USE
  ABC:      Defining a plugin interface you control; ensuring all concrete
            implementations are registered; using isinstance() checks
  Protocol: Accepting any object that "acts like" a file / event / message;
            writing library code consumed by third parties

INSIGHT
  Protocol is superior for library boundaries — it lets callers pass
  any conformant object without coupling to your class hierarchy.
  ABC is superior for enforcing internal architecture contracts — it
  makes missing implementations a hard error, not a type-hint warning.
  In production, combine both: Protocol for public APIs, ABC for internal
  plugin systems that need runtime isinstance() checks.
"""

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable


# ── 1. ABC — nominal, inheritance-based contract ─────────────────────────

class Exporter(ABC):
    """Every exporter must implement export() and content_type."""

    @abstractmethod
    def export(self, data: dict) -> str: ...

    @property
    @abstractmethod
    def content_type(self) -> str: ...


class JSONExporter(Exporter):
    import json as _json
    def export(self, data: dict) -> str:
        import json
        return json.dumps(data)

    @property
    def content_type(self) -> str:
        return "application/json"


class CSVExporter(Exporter):
    def export(self, data: dict) -> str:
        header = ",".join(data.keys())
        values = ",".join(str(v) for v in data.values())
        return f"{header}\n{values}"

    @property
    def content_type(self) -> str:
        return "text/csv"


# Trying to instantiate without all abstract methods → TypeError at runtime
class BrokenExporter(Exporter):
    pass   # missing export() and content_type


# ── 2. Protocol — structural, no inheritance required ────────────────────

@runtime_checkable          # enables isinstance() checks at runtime
class Serializable(Protocol):
    """Any object with .serialize() -> str qualifies — no inheritance."""
    def serialize(self) -> str: ...


# These classes know nothing about Serializable — zero coupling
class Invoice:
    def __init__(self, id: str, amount: float) -> None:
        self.id, self.amount = id, amount

    def serialize(self) -> str:
        return f"Invoice(id={self.id}, amount={self.amount})"


class LogEntry:
    def __init__(self, msg: str) -> None:
        self.msg = msg

    def serialize(self) -> str:
        return f"LogEntry({self.msg!r})"


def archive(item: Serializable) -> None:
    """Accepts ANY object that has .serialize() — no ABC required."""
    print(f"  archiving: {item.serialize()}")


# ── 3. Combining: ABC for plugin base, Protocol for public API ────────────

class StorageBackend(ABC):
    """Internal plugin base — hard enforcement via ABC."""
    @abstractmethod
    def write(self, key: str, value: bytes) -> None: ...

    @abstractmethod
    def read(self, key: str) -> bytes: ...


class MemoryBackend(StorageBackend):
    def __init__(self): self._store: dict = {}
    def write(self, key, value): self._store[key] = value
    def read(self, key): return self._store[key]


# ── demo ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    record = {"id": 1, "name": "Alice", "score": 98.5}

    for exp in [JSONExporter(), CSVExporter()]:
        print(f"  [{exp.content_type}]\n  {exp.export(record)}\n")

    # ABC enforcement
    try:
        BrokenExporter()
    except TypeError as e:
        print(f"  ABC caught missing impl: {e}\n")

    # Protocol — isinstance() works at runtime
    for obj in [Invoice("INV-001", 250.0), LogEntry("server started")]:
        print(f"  is Serializable: {isinstance(obj, Serializable)}")
        archive(obj)

    # Storage backend
    backend = MemoryBackend()
    backend.write("config", b'{"env": "prod"}')
    print(f"\n  read back: {backend.read('config')}")

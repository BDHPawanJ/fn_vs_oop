"""
mixed.py — Hybrid Scenario: Order Processing Pipeline
=======================================================
SCENARIO
  An order processing system that validates, enriches, and routes orders.

  This scenario deliberately shows WHERE each paradigm wins:
    OOP  → models with identity and lifecycle (Order, PricingRule)
    OOP  → plugin registry for route handlers (__init_subclass__)
    OOP  → descriptors for validated Order fields
    FN   → validation pipeline (compose + Result monad — railway)
    FN   → decorators for cross-cutting concerns (timing, logging)
    FN   → partial application to specialise generic rules

KEY TAKEAWAY
  Real systems are hybrid. The mistake is forcing one paradigm everywhere:
  - Pure OOP: validation becomes a tangle of Visitor/Strategy classes
  - Pure Functional: resource lifecycle (DB, connections) has no clean home
  
  The rule of thumb:
    DATA with LIFECYCLE    → class (owns state, has __enter__/__exit__)
    BEHAVIOUR / TRANSFORM → function (pure, composable, testable in one line)
    CROSS-CUTTING CONCERN  → decorator (timing, auth, retry, logging)
    SHARED CAPABILITY      → mixin (serialisation, repr, timestamps)
    INTERFACE CONTRACT     → Protocol (loose) or ABC (strict)
    CLASS FACTORY / REGISTRY → __init_subclass__ or metaclass
"""

from __future__ import annotations
import time
import functools
from dataclasses import dataclass, field
from typing import Callable, Union


# ═══════════════════════════════════════════════════════════════════════════
# FUNCTIONAL LAYER — validation pipeline (Result monad + compose)
# ═══════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Ok:
    # Local re-definition for self-containedness — same concept as composition_pipeline.py
    value: object
    def bind(self, fn): return fn(self.value)
    def __repr__(self): return f"Ok({self.value!r})"

@dataclass(frozen=True)
class Err:
    error: str
    def bind(self, fn): return self          # short-circuit
    def __repr__(self): return f"Err({self.error!r})"

Result = Union[Ok, Err]


def railway(*steps: Callable) -> Callable[[Result], Result]:
    def run(result):
        for step in steps:
            result = result.bind(step)
        return result
    return run


# validation steps — pure functions, independently testable
def check_items_not_empty(order: dict) -> Result:
    return Ok(order) if order.get("items") else Err("order has no items")

def check_total_positive(order: dict) -> Result:
    total = sum(i["qty"] * i["price"] for i in order["items"])
    return Ok({**order, "total": total}) if total > 0 else Err("total must be positive")

def apply_discount(rate: float) -> Callable[[dict], Result]:
    """Partial application — specialise for a discount rate."""
    def step(order: dict) -> Result:
        discounted = round(order["total"] * (1 - rate), 2)
        return Ok({**order, "total": discounted, "discount_rate": rate})
    return step

def tag_priority(order: dict) -> Result:
    priority = "high" if order["total"] > 500 else "normal"
    return Ok({**order, "priority": priority})


# ═══════════════════════════════════════════════════════════════════════════
# FUNCTIONAL LAYER — decorator for timing (cross-cutting concern)
# ═══════════════════════════════════════════════════════════════════════════

def timed(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        ms = (time.perf_counter() - t0) * 1000
        print(f"  [TIMED] {fn.__name__} took {ms:.2f} ms")
        return result
    return wrapper


# ═══════════════════════════════════════════════════════════════════════════
# OOP LAYER — Order model with descriptor-validated fields
# ═══════════════════════════════════════════════════════════════════════════

class PositiveFloat:
    """Descriptor: ensures attribute is always a positive float."""
    def __set_name__(self, owner, name): self._name = name
    def __get__(self, obj, _=None): return obj.__dict__.get(self._name) if obj else self
    def __set__(self, obj, value):
        value = float(value)
        if value <= 0:
            raise ValueError(f"{self._name} must be positive, got {value}")
        obj.__dict__[self._name] = value


@dataclass
class OrderItem:
    sku:   str
    qty:   int
    price: float

    def to_dict(self) -> dict:
        return {"sku": self.sku, "qty": self.qty, "price": self.price}


class Order:
    """OOP: owns identity, lifecycle, and mutable state."""
    minimum_amount = PositiveFloat()   # descriptor-validated

    def __init__(self, order_id: str, customer: str, items: list[OrderItem]) -> None:
        self.order_id  = order_id
        self.customer  = customer
        self.items     = items
        self.status    = "pending"
        self.minimum_amount = 1.0      # descriptor enforces > 0

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "customer": self.customer,
            "items":    [i.to_dict() for i in self.items],
        }

    def __repr__(self) -> str:
        return f"Order({self.order_id!r}, status={self.status!r})"


# ═══════════════════════════════════════════════════════════════════════════
# OOP LAYER — Route handlers via __init_subclass__ registry
# ═══════════════════════════════════════════════════════════════════════════

class RouteHandler:
    """OOP: __init_subclass__ auto-registers handlers by priority."""
    _registry: dict[str, "RouteHandler"] = {}

    def __init_subclass__(cls, priority: str = "", **kwargs):
        super().__init_subclass__(**kwargs)
        if priority:
            RouteHandler._registry[priority] = cls

    def handle(self, order: dict) -> str: ...


class HighPriorityHandler(RouteHandler, priority="high"):
    def handle(self, order: dict) -> str:
        return f"[FAST-LANE] Order {order['order_id']} → express fulfilment (${order['total']})"


class NormalPriorityHandler(RouteHandler, priority="normal"):
    def handle(self, order: dict) -> str:
        return f"[STANDARD]  Order {order['order_id']} → standard fulfilment (${order['total']})"


# ═══════════════════════════════════════════════════════════════════════════
# ORCHESTRATION — ties OOP model + functional pipeline + OOP routing
# ═══════════════════════════════════════════════════════════════════════════

@timed   # functional decorator on a method-like function
def process_order(order: Order, discount_rate: float = 0.10) -> str:
    """
    Hybrid entry point:
      1. OOP Order object  → serialised to plain dict (FN-friendly)
      2. Functional pipeline validates + enriches the dict
      3. OOP handler routes the enriched result
    """
    validate_and_enrich = railway(
        check_items_not_empty,
        check_total_positive,
        apply_discount(discount_rate),   # partial application
        tag_priority,
    )

    result = validate_and_enrich(Ok({**order.to_dict(), "order_id": order.order_id}))

    if isinstance(result, Err):
        order.status = "rejected"
        return f"REJECTED: {result.error}"

    enriched = result.value
    order.status = "routed"

    handler_cls = RouteHandler._registry.get(enriched["priority"], NormalPriorityHandler)
    return handler_cls().handle(enriched)


# ── demo ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    orders = [
        Order("ORD-001", "Alice", [
            OrderItem("SKU-A", 3, 200.0),
            OrderItem("SKU-B", 1,  50.0),
        ]),
        Order("ORD-002", "Bob", [
            OrderItem("SKU-C", 1,   9.99),
        ]),
        Order("ORD-003", "Carol", []),   # empty — will be rejected
    ]

    for order in orders:
        result = process_order(order, discount_rate=0.10)
        print(f"  {order} -> {result}")

    print(f"\n  Registered handlers: {list(RouteHandler._registry.keys())}")
    print("""
  PARADIGM SPLIT IN THIS FILE:
    OOP  : Order (identity + lifecycle), OrderItem (value object)
           PositiveFloat descriptor (validated field)
           RouteHandler + __init_subclass__ (auto plugin registry)
    FN   : railway() pipeline (Result monad, short-circuit on error)
           apply_discount(rate) partial application
           @timed decorator (cross-cutting, zero coupling to Order)
    """)

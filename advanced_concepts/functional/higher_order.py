"""
Functional — Higher-Order Functions & Currying
===============================================
CONCEPT
  A higher-order function (HOF) either takes a function as an argument
  or returns one. map/filter/reduce are the canonical examples.
  Currying transforms f(a, b, c) into f(a)(b)(c) — each call binds
  one argument and returns a new function.

TYPES COVERED
  1. map / filter / reduce     — data pipeline without loops
  2. Manual currying           — step-by-step argument binding
  3. Function as strategy      — pass behaviour, not data
  4. Lazy evaluation with generators — HOFs over infinite sequences

WHEN TO USE
  - Data transformation pipelines (ETL, event processing)
  - Injecting pluggable behaviour: sort key, filter predicate, reducer
  - Building domain-specific combinators from small generic pieces

INSIGHT
  HOFs are the foundation of every functional pipeline framework
  (pandas .pipe(), toolz, PySpark map/filter/reduce).
  Currying shines when you generate many specialised functions from
  one generic one — but Python's syntax makes it less natural than
  Haskell/Scala; functools.partial is usually preferred in practice.
"""

from functools import reduce
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
U = TypeVar("U")


# ── 1. map / filter / reduce ──────────────────────────────────────────────

def pipeline_demo():
    orders = [
        {"id": 1, "amount": 120, "status": "paid"},
        {"id": 2, "amount":  45, "status": "pending"},
        {"id": 3, "amount": 300, "status": "paid"},
        {"id": 4, "amount":  10, "status": "paid"},
    ]
    total = reduce(
        lambda acc, x: acc + x,
        map(lambda o: o["amount"],
            filter(lambda o: o["status"] == "paid", orders))
    )
    return total   # 120 + 300 + 10 = 430


# ── 2. Manual currying ────────────────────────────────────────────────────

def curry_add(a: int) -> Callable[[int], Callable[[int], int]]:
    """add(1)(2)(3) == 6  — each call returns a new function."""
    def step2(b: int):
        def step3(c: int):
            return a + b + c
        return step3
    return step2


def make_multiplier(factor: int) -> Callable[[int], int]:
    """Curried single-arg specialisation — cleaner than a lambda."""
    return lambda x: x * factor

double = make_multiplier(2)
triple = make_multiplier(3)


# ── 3. Function as strategy (pluggable behaviour) ─────────────────────────

def process_items(
    items: list,
    transform: Callable,
    predicate: Callable[[any], bool] = lambda _: True,
) -> list:
    """
    Generic processor: apply transform, then filter.
    Callers inject their own strategy — no subclassing required.
    """
    return [transform(i) for i in items if predicate(i)]


# ── 4. Lazy HOFs with generators ──────────────────────────────────────────

def take(n: int, iterable: Iterable[T]) -> list[T]:
    result = []
    for item in iterable:
        if len(result) >= n:
            break
        result.append(item)
    return result


def imap(fn: Callable[[T], U], iterable: Iterable[T]) -> Iterable[U]:
    """Lazy map — does not materialise the whole sequence."""
    return (fn(x) for x in iterable)


def naturals(start: int = 0):
    """Infinite sequence of natural numbers."""
    n = start
    while True:
        yield n
        n += 1


# ── demo ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"pipeline total paid: {pipeline_demo()}")     # 430

    print(f"curry_add(1)(2)(3) = {curry_add(1)(2)(3)}")  # 6
    print(f"double(7) = {double(7)}  triple(7) = {triple(7)}")

    items = [1, 2, 3, 4, 5, 6]
    result = process_items(items, transform=double, predicate=lambda x: x % 2 == 0)
    print(f"double evens: {result}")                      # [4, 8, 12]

    # First 8 squares from an infinite sequence
    squares = imap(lambda n: n ** 2, naturals(1))
    print(f"first 8 squares: {take(8, squares)}")         # [1,4,9,16,25,36,49,64]

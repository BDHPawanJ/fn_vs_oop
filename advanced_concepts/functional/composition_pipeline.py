"""
Functional — Function Composition & Result/Railway Pattern
===========================================================
CONCEPT
  compose(f, g)(x) == f(g(x))  — pipe data through a chain of functions.
  The Railway / Result pattern wraps a value in Ok/Err so the pipeline
  short-circuits on the first failure without exceptions or if-chains.
  This is the functional equivalent of the OOP Chain-of-Responsibility
  pattern — but purely data-driven and without shared mutable state.

TYPES COVERED
  1. compose / pipe            — left-to-right vs right-to-left composition
  2. Result[T] monad           — Ok / Err propagation (railway pattern)
  3. Transducer-style compose  — compose transformations, not data
  4. tap()                     — inject side-effects (logging) without
                                 breaking the pipeline

WHEN TO USE
  - Validation chains: each step returns Ok(value) or Err(reason)
  - ETL pipelines where any stage can fail cleanly
  - Replacing nested if/else ladders with composable steps

INSIGHT
  The Result type eliminates exception-driven control flow.
  Every step is independently testable: fn(Ok(x)) -> Ok(y) or Err(msg).
  Compare with OOP: each step would be a class with a process() method —
  possible, but more verbose and harder to reorder.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")


# ── 1. compose / pipe ─────────────────────────────────────────────────────

def compose(*fns: Callable) -> Callable:
    """Right-to-left: compose(f, g, h)(x) == f(g(h(x)))"""
    from functools import reduce
    return reduce(lambda f, g: lambda x: f(g(x)), fns)


def pipe(*fns: Callable) -> Callable:
    """Left-to-right: pipe(f, g, h)(x) == h(g(f(x)))"""
    from functools import reduce
    return reduce(lambda f, g: lambda x: g(f(x)), fns)


# ── 2. Result monad (Railway pattern) ─────────────────────────────────────

@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T
    def bind(self, fn: Callable[[T], "Result"]) -> "Result": return fn(self.value)
    def __repr__(self): return f"Ok({self.value!r})"


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E
    def bind(self, fn: Callable) -> "Err": return self   # short-circuit
    def __repr__(self): return f"Err({self.error!r})"


Result = Union[Ok, Err]


def railway(*steps: Callable) -> Callable[[Result], Result]:
    """
    Thread a Result through a sequence of steps.
    Any step returning Err short-circuits the remaining steps.
    """
    def run(result: Result) -> Result:
        for step in steps:
            result = result.bind(step)
        return result
    return run


# ── 3. tap — side-effects without breaking the chain ──────────────────────

def tap(fn: Callable[[T], None]) -> Callable[[T], Result]:
    """Call fn(value) for its side-effect, then pass Ok(value) through."""
    def _tap(value: T) -> Result:
        fn(value)
        return Ok(value)
    return _tap


# ── concrete validation pipeline ─────────────────────────────────────────

def parse_int(s: str) -> Result:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"'{s}' is not a valid integer")


def validate_positive(n: int) -> Result:
    return Ok(n) if n > 0 else Err(f"{n} must be positive")


def validate_max(limit: int) -> Callable[[int], Result]:
    return lambda n: Ok(n) if n <= limit else Err(f"{n} exceeds max {limit}")


def to_percentage(n: int) -> Result:
    return Ok(n / 100)


# ── demo ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Basic compose / pipe
    normalize = pipe(str.strip, str.lower, lambda s: s.replace(" ", "_"))
    print(normalize("  Hello World  "))   # hello_world

    add1    = lambda x: x + 1
    double  = lambda x: x * 2
    square  = lambda x: x ** 2
    transform = compose(square, double, add1)  # square(double(add1(x)))
    print(transform(3))   # square(double(4)) = square(8) = 64

    # Railway pipeline
    validate_score = railway(
        validate_positive,
        validate_max(100),
        tap(lambda n: print(f"  [TAP] score accepted: {n}")),
        to_percentage,
    )

    for raw in ["85", "-5", "120", "abc"]:
        result = parse_int(raw)
        print(f"  input={raw!r:6}  -> {validate_score(result)}")

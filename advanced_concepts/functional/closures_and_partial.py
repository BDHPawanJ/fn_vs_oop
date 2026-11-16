"""
Functional — Closures & Partial Application
============================================
CONCEPT
  A closure is a function that *captures* variables from its enclosing
  scope. Those captured variables become private state — no class needed.

  Partial application fixes some arguments of a function, returning a
  new function with fewer parameters. functools.partial is the stdlib
  tool; manual closures give more control.

WHEN TO USE
  - You need lightweight stateful callables without the overhead of a class
  - You want to specialise a generic function for a specific context
    (e.g. a logger pre-bound to a module name)
  - Building configurable factories: make_validator(), make_formatter()

INSIGHT
  Closures are the functional equivalent of __init__ + self._value.
  The key difference: a closure cannot be inspected or mutated by callers
  the way an object's attributes can — which is both a safety feature
  and an occasional debugging challenge.
"""

from functools import partial
from typing import Callable


# ── 1. Closure as private state ──────────────────────────────────────────

def make_counter(start: int = 0, step: int = 1) -> Callable[[], int]:
    """
    Returns a counter function. `count` is captured private state.
    Compare with OOP: class Counter: def __init__(self): self.count = 0
    """
    count = start

    def increment() -> int:
        nonlocal count
        count += step
        return count

    return increment


# ── 2. Closure as a configurable validator ────────────────────────────────

def make_range_validator(lo: float, hi: float) -> Callable[[float], bool]:
    """
    Closes over lo/hi — no class, no dataclass, just a function.
    Usage: validate_age = make_range_validator(0, 150)
    """
    def validate(value: float) -> bool:
        return lo <= value <= hi
    return validate


# ── 3. Partial application — fix some args, specialise later ─────────────

def send_message(channel: str, priority: str, text: str) -> str:
    return f"[{channel.upper()}:{priority}] {text}"


# Specialised callables via partial — no subclass required
send_email  = partial(send_message, "email",  "normal")
send_urgent = partial(send_message, "email",  "urgent")
send_sms    = partial(send_message, "sms",    "normal")


# ── 4. Closure-based memoisation (manual, transparent) ───────────────────

def make_memoised(fn: Callable) -> Callable:
    """
    Wraps any single-arg pure function with a cache.
    The cache dict is captured in the closure — invisible to callers.
    """
    _cache: dict = {}

    def wrapper(arg):
        if arg not in _cache:
            _cache[arg] = fn(arg)
        return _cache[arg]

    wrapper.cache = _cache          # expose cache for inspection/testing
    return wrapper


# ── demo ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Counter
    counter = make_counter(start=10, step=5)
    print([counter() for _ in range(4)])   # [15, 20, 25, 30]

    # Range validator
    valid_age = make_range_validator(0, 150)
    print(valid_age(25), valid_age(200))   # True False

    # Partial
    print(send_email("Meeting at 10am"))
    print(send_urgent("Server is down!"))
    print(send_sms("Your OTP is 4821"))

    # Memoised fibonacci
    fib = make_memoised(lambda n: n if n < 2 else fib(n-1) + fib(n-2))
    print([fib(i) for i in range(8)])      # [0,1,1,2,3,5,8,13]

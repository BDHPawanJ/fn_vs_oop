"""
Functional — Decorators
========================
CONCEPT
  A decorator is a higher-order function that wraps another function,
  adding behaviour before/after without modifying the original.
  It is the functional answer to the OOP Proxy and Chain-of-Responsibility
  patterns — but applied at function definition time.

TYPES COVERED
  1. Simple decorator          — no arguments
  2. Parametrised decorator    — decorator factory (most common in production)
  3. Class-based decorator     — when the decorator itself needs state
  4. Stacking decorators       — order matters (outermost applied last)

WHEN TO USE
  - Cross-cutting concerns: logging, timing, retry, auth, caching
  - You want to annotate intent at the call site (@retry, @require_auth)
  - Avoid repeating the same boilerplate in every function

INSIGHT
  Always use @functools.wraps — without it, the wrapped function loses
  its __name__, __doc__, and signature, breaking introspection tools,
  debuggers, and documentation generators.
"""

import functools
import time
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


# ── 1. Simple decorator ───────────────────────────────────────────────────

def log_call(fn: F) -> F:
    """Prints function name and args on every call."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        print(f"  [LOG] calling {fn.__name__}({args}, {kwargs})")
        result = fn(*args, **kwargs)
        print(f"  [LOG] {fn.__name__} returned {result!r}")
        return result
    return wrapper  # type: ignore


# ── 2. Parametrised decorator (decorator factory) ─────────────────────────

def retry(times: int = 3, exceptions: tuple = (Exception,)):
    """
    @retry(times=3, exceptions=(IOError,))
    Retries the wrapped function up to `times` attempts on given exceptions.
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, times + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    print(f"  [RETRY] {fn.__name__} attempt {attempt}/{times} failed: {e}")
            raise last_exc
        return wrapper  # type: ignore
    return decorator


def timeit(fn: F) -> F:
    """Measures and prints execution time."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        ms = (time.perf_counter() - t0) * 1000
        print(f"  [TIME] {fn.__name__} took {ms:.2f} ms")
        return result
    return wrapper  # type: ignore


# ── 3. Class-based decorator (stateful — tracks call count) ───────────────

class CountCalls:
    """Decorator that records how many times a function was called."""
    def __init__(self, fn: Callable) -> None:
        functools.update_wrapper(self, fn)
        self._fn  = fn
        self.calls = 0

    def __call__(self, *args, **kwargs):
        self.calls += 1
        return self._fn(*args, **kwargs)


# ── 4. Stacking — order is outermost-first at application, inner-first at call

@timeit          # applied second → outermost wrapper → runs first
@retry(times=2)  # applied first  → inner wrapper
@log_call        # applied zeroth → innermost
def fetch_data(url: str) -> str:
    return f"data from {url}"


# ── demo ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Stacked decorators
    print("-- stacked decorators --")
    fetch_data("https://api.example.com/items")

    # Class-based stateful decorator
    print("\n-- stateful class-based decorator --")

    @CountCalls
    def add(a, b): return a + b

    add(1, 2); add(3, 4); add(5, 6)
    print(f"  add called {add.calls} times")  # 3

    # Parametrised retry on a flaky function
    print("\n-- retry on flaky function --")
    _attempt = [0]

    @retry(times=3, exceptions=(ValueError,))
    def flaky():
        _attempt[0] += 1
        if _attempt[0] < 3:
            raise ValueError("not ready yet")
        return "success"

    print(f"  result: {flaky()}")

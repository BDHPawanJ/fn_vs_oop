"""Tests — Decorators"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from advanced_concepts.functional.decorators import retry, CountCalls


def test_retry_succeeds_on_first_attempt():
    @retry(times=3, exceptions=(IOError,))
    def ok(): return "done"
    assert ok() == "done"


def test_retry_succeeds_after_failures():
    attempts = [0]

    @retry(times=3, exceptions=(ValueError,))
    def flaky():
        attempts[0] += 1
        if attempts[0] < 3:
            raise ValueError("not yet")
        return "ok"

    assert flaky() == "ok"
    assert attempts[0] == 3


def test_retry_raises_after_exhaustion():
    @retry(times=2, exceptions=(ValueError,))
    def always_fails():
        raise ValueError("nope")

    with pytest.raises(ValueError):
        always_fails()


def test_retry_does_not_catch_unlisted_exception():
    @retry(times=5, exceptions=(IOError,))
    def raises_type_error():
        raise TypeError("wrong type")

    with pytest.raises(TypeError):
        raises_type_error()


def test_count_calls_tracks_invocations():
    @CountCalls
    def add(a, b): return a + b

    add(1, 2); add(3, 4)
    assert add.calls == 2


def test_count_calls_returns_correct_value():
    @CountCalls
    def multiply(a, b): return a * b

    assert multiply(3, 4) == 12


def test_retry_preserves_function_name():
    @retry(times=2)
    def my_func(): pass
    assert my_func.__name__ == "my_func"

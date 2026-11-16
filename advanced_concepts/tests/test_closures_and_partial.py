"""Tests — Closures & Partial Application"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from advanced_concepts.functional.closures_and_partial import (
    make_counter, make_range_validator,
    send_email, send_urgent, send_sms, make_memoised,
)


def test_counter_increments_by_step():
    c = make_counter(start=0, step=5)
    assert c() == 5
    assert c() == 10
    assert c() == 15


def test_counters_are_independent():
    a = make_counter(start=0, step=1)
    b = make_counter(start=100, step=10)
    a(); a()
    assert a() == 3
    assert b() == 110   # b is unaffected by a


def test_range_validator_in_bounds():
    valid = make_range_validator(0, 100)
    assert valid(0) is True
    assert valid(50) is True
    assert valid(100) is True


def test_range_validator_out_of_bounds():
    valid = make_range_validator(0, 100)
    assert valid(-1) is False
    assert valid(101) is False


def test_partial_email():
    result = send_email("Hello")
    assert result == "[EMAIL:normal] Hello"


def test_partial_urgent():
    result = send_urgent("ALERT")
    assert result == "[EMAIL:urgent] ALERT"


def test_partial_sms():
    result = send_sms("OTP: 1234")
    assert result == "[SMS:normal] OTP: 1234"


def test_memoised_called_once():
    call_count = [0]

    def expensive(n):
        call_count[0] += 1
        return n * 2

    mem = make_memoised(expensive)
    assert mem(5) == 10
    assert mem(5) == 10   # cached
    assert call_count[0] == 1


def test_memoised_cache_exposed():
    mem = make_memoised(lambda x: x + 1)
    mem(10)
    assert mem.cache == {10: 11}

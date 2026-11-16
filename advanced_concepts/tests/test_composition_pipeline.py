"""Tests — Function Composition & Railway Pattern"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from advanced_concepts.functional.composition_pipeline import (
    compose, pipe, Ok, Err, railway,
    parse_int, validate_positive, validate_max, to_percentage, tap,
)


# ── compose / pipe ────────────────────────────────────────────────────────

def test_pipe_left_to_right():
    fn = pipe(lambda x: x + 1, lambda x: x * 2)
    assert fn(3) == 8     # (3+1)*2


def test_compose_right_to_left():
    fn = compose(lambda x: x * 2, lambda x: x + 1)
    assert fn(3) == 8     # (3+1)*2  — same math, different reading order


def test_pipe_single_function():
    fn = pipe(lambda x: x + 10)
    assert fn(5) == 15


# ── Ok / Err ──────────────────────────────────────────────────────────────

def test_ok_bind_propagates():
    result = Ok(5).bind(lambda x: Ok(x * 2))
    assert result == Ok(10)


def test_err_bind_short_circuits():
    called = [False]

    def should_not_run(x):
        called[0] = True
        return Ok(x)

    result = Err("fail").bind(should_not_run)
    assert result == Err("fail")
    assert called[0] is False


# ── parse_int ─────────────────────────────────────────────────────────────

def test_parse_int_valid():
    assert parse_int("42") == Ok(42)


def test_parse_int_invalid():
    result = parse_int("abc")
    assert isinstance(result, Err)


# ── validate_positive ─────────────────────────────────────────────────────

def test_validate_positive_passes():
    assert validate_positive(1) == Ok(1)


def test_validate_positive_fails_on_zero():
    assert isinstance(validate_positive(0), Err)


def test_validate_positive_fails_on_negative():
    assert isinstance(validate_positive(-5), Err)


# ── validate_max ─────────────────────────────────────────────────────────

def test_validate_max_within_limit():
    assert validate_max(100)(80) == Ok(80)


def test_validate_max_at_limit():
    assert validate_max(100)(100) == Ok(100)


def test_validate_max_exceeds():
    assert isinstance(validate_max(100)(101), Err)


# ── to_percentage ─────────────────────────────────────────────────────────

def test_to_percentage():
    result = to_percentage(75)
    assert result == Ok(0.75)


# ── tap ───────────────────────────────────────────────────────────────────

def test_tap_passes_value_through():
    side_effect = []
    fn = tap(lambda x: side_effect.append(x))
    result = fn(42)
    assert result == Ok(42)
    assert side_effect == [42]


# ── full railway pipeline ─────────────────────────────────────────────────

def test_railway_happy_path():
    validate = railway(validate_positive, validate_max(100), to_percentage)
    result = validate(Ok(80))
    assert result == Ok(0.80)


def test_railway_short_circuits_on_err():
    validate = railway(validate_positive, validate_max(100), to_percentage)
    result = validate(Ok(-5))
    assert isinstance(result, Err)


def test_railway_full_flow_via_parse():
    validate = railway(validate_positive, validate_max(100), to_percentage)
    assert isinstance(validate(parse_int("75")), Ok)
    assert isinstance(validate(parse_int("-1")), Err)
    assert isinstance(validate(parse_int("abc")), Err)
    assert isinstance(validate(parse_int("150")), Err)

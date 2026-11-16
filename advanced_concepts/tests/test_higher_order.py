"""Tests — Higher-Order Functions & Currying"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from advanced_concepts.functional.higher_order import (
    pipeline_demo, curry_add, double, triple,
    process_items, take, imap, naturals,
)


def test_pipeline_total():
    assert pipeline_demo() == 430


def test_curry_add():
    assert curry_add(1)(2)(3) == 6
    assert curry_add(0)(0)(0) == 0


def test_double():
    assert double(7) == 14
    assert double(0) == 0


def test_triple():
    assert triple(7) == 21


def test_process_items_transform_only():
    result = process_items([1, 2, 3], transform=double)
    assert result == [2, 4, 6]


def test_process_items_with_predicate():
    result = process_items(
        [1, 2, 3, 4, 5, 6],
        transform=double,
        predicate=lambda x: x % 2 == 0,
    )
    assert result == [4, 8, 12]


def test_process_items_empty_after_filter():
    result = process_items([1, 3, 5], transform=double, predicate=lambda x: x % 2 == 0)
    assert result == []


def test_take():
    assert take(3, [10, 20, 30, 40, 50]) == [10, 20, 30]
    assert take(0, [1, 2, 3]) == []


def test_imap_lazy():
    gen = imap(lambda x: x * 2, [1, 2, 3])
    assert list(gen) == [2, 4, 6]


def test_naturals_start():
    assert take(5, naturals(0)) == [0, 1, 2, 3, 4]
    assert take(3, naturals(10)) == [10, 11, 12]


def test_first_8_squares():
    squares = imap(lambda n: n ** 2, naturals(1))
    assert take(8, squares) == [1, 4, 9, 16, 25, 36, 49, 64]

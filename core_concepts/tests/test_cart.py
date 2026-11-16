"""Tests — Cart (functional vs OOP produce identical results)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from functional.cart import EMPTY_CART, add_item, remove_item, total, item_count
from oop.cart import Cart


def _build_fn_cart():
    c = EMPTY_CART
    c = add_item(c, "Apple", 0.50, qty=4)
    c = add_item(c, "Milk",  1.49, qty=2)
    return c


def _build_oop_cart():
    c = Cart()
    c.add("Apple", 0.50, qty=4)
    c.add("Milk",  1.49, qty=2)
    return c


def test_total_matches():
    assert total(_build_fn_cart()) == _build_oop_cart().total()


def test_item_count():
    assert item_count(_build_fn_cart()) == _build_oop_cart().item_count() == 6


def test_remove_item():
    fn_c  = remove_item(_build_fn_cart(), "Milk")
    oop_c = _build_oop_cart()
    oop_c.remove("Milk")
    assert total(fn_c) == oop_c.total() == 2.0


def test_functional_immutability():
    """Original cart must not change when add_item is called."""
    original = add_item(EMPTY_CART, "Apple", 0.50)
    _new = add_item(original, "Milk", 1.49)
    assert len(original) == 1   # original unchanged

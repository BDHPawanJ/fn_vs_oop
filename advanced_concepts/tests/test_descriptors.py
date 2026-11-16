"""Tests — Descriptors"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from advanced_concepts.oop.descriptors import Product


def test_valid_product_creation():
    p = Product("Widget", 9.99, 4.5)
    assert p.name == "Widget"
    assert p.price == 9.99
    assert p.rating == 4.5


def test_price_coerces_int_to_float():
    p = Product("Widget", 9, 3.0)
    assert isinstance(p.price, float)
    assert p.price == 9.0


def test_price_below_range_raises():
    with pytest.raises(ValueError, match="price"):
        Product("Widget", 0.0, 3.0)


def test_price_above_range_raises():
    with pytest.raises(ValueError, match="price"):
        Product("Widget", 100_000.0, 3.0)


def test_rating_above_range_raises():
    with pytest.raises(ValueError, match="rating"):
        Product("Widget", 9.99, 5.1)


def test_rating_below_range_raises():
    with pytest.raises(ValueError, match="rating"):
        Product("Widget", 9.99, -0.1)


def test_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        Product("   ", 9.99, 3.0)


def test_lazy_property_computed_once():
    p = Product("Widget", 9.99, 4.0)
    label1 = p.label
    label2 = p.label
    assert label1 == label2
    assert "Widget" in label1
    # After first access the value lives in instance __dict__, not on class
    assert "label" in p.__dict__


def test_descriptor_set_name_works_on_multiple_fields():
    p = Product("Gadget", 24.99, 3.5)
    p.price = 19.99
    p.rating = 2.0
    assert p.price == 19.99
    assert p.rating == 2.0

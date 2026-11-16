"""Tests — Mixins"""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from advanced_concepts.oop.mixins import User, Product


def test_user_repr_contains_name():
    u = User("Alice", "alice@example.com")
    assert "Alice" in repr(u)
    assert "User(" in repr(u)


def test_user_to_json_is_valid():
    u = User("Alice", "alice@example.com")
    data = json.loads(u.to_json())
    assert data["name"] == "Alice"
    assert data["email"] == "alice@example.com"


def test_user_save_valid():
    u = User("Alice", "alice@example.com")
    assert "saved" in u.save().lower()


def test_user_save_invalid_name():
    u = User("", "alice@example.com")
    with pytest.raises(ValueError, match="name is required"):
        u.save()


def test_user_save_invalid_email():
    u = User("Alice", "not-an-email")
    with pytest.raises(ValueError, match="invalid email"):
        u.save()


def test_timestamp_mixin_sets_created_at():
    u = User("Alice", "alice@example.com")
    assert u.created_at is not None
    assert u.updated_at == u.created_at


def test_touch_updates_timestamp():
    import time
    u = User("Alice", "alice@example.com")
    original = u.updated_at
    time.sleep(0.002)
    u.touch()
    assert u.updated_at != original


def test_product_to_json():
    p = Product("SKU-001", 29.99)
    data = json.loads(p.to_json())
    assert data["sku"] == "SKU-001"
    assert data["price"] == 29.99


def test_user_mro_includes_all_mixins():
    mro_names = [c.__name__ for c in User.__mro__]
    for name in ["TimestampMixin", "JSONMixin", "ReprMixin", "ValidateMixin"]:
        assert name in mro_names

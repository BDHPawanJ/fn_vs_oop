"""Tests — Hybrid Order Processing Pipeline"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
from advanced_concepts.mixed import (
    Ok, Err, railway,
    check_items_not_empty, check_total_positive,
    apply_discount, tag_priority,
    Order, OrderItem, process_order, RouteHandler,
)


# ── Railway steps ─────────────────────────────────────────────────────────

def test_check_items_not_empty_passes():
    result = check_items_not_empty({"items": [{"qty": 1, "price": 10.0}]})
    assert isinstance(result, Ok)


def test_check_items_not_empty_fails():
    result = check_items_not_empty({"items": []})
    assert isinstance(result, Err)


def test_check_total_positive_passes():
    order = {"items": [{"qty": 2, "price": 50.0}]}
    result = check_total_positive(order)
    assert isinstance(result, Ok)
    assert result.value["total"] == 100.0


def test_apply_discount():
    order = {"items": [], "total": 100.0}
    result = apply_discount(0.10)(order)
    assert isinstance(result, Ok)
    assert result.value["total"] == 90.0


def test_tag_priority_high():
    result = tag_priority({"total": 600.0})
    assert isinstance(result, Ok)
    assert result.value["priority"] == "high"


def test_tag_priority_normal():
    result = tag_priority({"total": 100.0})
    assert result.value["priority"] == "normal"


# ── Order model ───────────────────────────────────────────────────────────

def test_order_to_dict():
    order = Order("ORD-1", "Alice", [OrderItem("SKU-A", 2, 10.0)])
    d = order.to_dict()
    assert d["order_id"] == "ORD-1"
    assert len(d["items"]) == 1


def test_order_descriptor_rejects_zero():
    order = Order("ORD-1", "Alice", [])
    with pytest.raises(ValueError):
        order.minimum_amount = 0.0


def test_order_descriptor_rejects_negative():
    order = Order("ORD-1", "Alice", [])
    with pytest.raises(ValueError):
        order.minimum_amount = -5.0


# ── Full process_order integration ───────────────────────────────────────

def test_process_order_high_priority():
    order = Order("ORD-H", "Alice", [
        OrderItem("SKU-A", 3, 200.0),
        OrderItem("SKU-B", 1,  50.0),
    ])
    result = process_order(order, discount_rate=0.10)
    assert "FAST-LANE" in result or "express" in result.lower()
    assert order.status == "routed"


def test_process_order_normal_priority():
    order = Order("ORD-N", "Bob", [OrderItem("SKU-C", 1, 9.99)])
    result = process_order(order, discount_rate=0.0)
    assert "STANDARD" in result or "standard" in result.lower()
    assert order.status == "routed"


def test_process_order_empty_items_rejected():
    order = Order("ORD-E", "Carol", [])
    result = process_order(order)
    assert "REJECTED" in result
    assert order.status == "rejected"


# ── Handler registry ─────────────────────────────────────────────────────

def test_both_priority_handlers_registered():
    assert "high"   in RouteHandler._registry
    assert "normal" in RouteHandler._registry

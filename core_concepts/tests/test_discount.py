"""Tests — Discount (functional vs OOP produce identical results)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from functional.discount import apply_discounts, seasonal_discount, loyalty_discount, bulk_discount
from oop.discount import DiscountEngine, SeasonalDiscount, LoyaltyDiscount, BulkDiscount


CTX  = {"is_sale": True, "is_member": True, "quantity": 12}
FN_RULES = [seasonal_discount, loyalty_discount, bulk_discount]
OOP_RULES = [SeasonalDiscount(True), LoyaltyDiscount(True), BulkDiscount(12)]


def test_functional_full_discount():
    assert apply_discounts(100.0, CTX, FN_RULES) == 72.67


def test_oop_full_discount():
    assert DiscountEngine(OOP_RULES).calculate(100.0) == 72.67


def test_both_produce_same_result():
    fn  = apply_discounts(100.0, CTX, FN_RULES)
    oop = DiscountEngine(OOP_RULES).calculate(100.0)
    assert fn == oop


def test_no_discount_applied():
    no_ctx = {"is_sale": False, "is_member": False, "quantity": 1}
    assert apply_discounts(100.0, no_ctx, FN_RULES) == 100.0
    assert DiscountEngine([SeasonalDiscount(False), LoyaltyDiscount(False),
                           BulkDiscount(1)]).calculate(100.0) == 100.0

"""
Functional — Discount
=====================
Rules are plain functions. apply_discount() composes them via a list.
Adding a new rule = adding a new function. No class needed.
"""

from typing import Callable, List

DiscountRule = Callable[[float, dict], float]


def seasonal_discount(price: float, context: dict) -> float:
    """10 % off during sale season."""
    return price * 0.90 if context.get("is_sale") else price


def loyalty_discount(price: float, context: dict) -> float:
    """5 % off for loyalty members."""
    return price * 0.95 if context.get("is_member") else price


def bulk_discount(price: float, context: dict) -> float:
    """15 % off when quantity >= 10."""
    return price * 0.85 if context.get("quantity", 0) >= 10 else price


def apply_discounts(price: float, context: dict, rules: "List[DiscountRule]") -> float:
    """Compose any list of discount rules left-to-right."""
    for rule in rules:
        price = rule(price, context)
    return round(price, 2)


# --- demo ---------------------------------------------------------------
if __name__ == "__main__":
    ctx = {"is_sale": True, "is_member": True, "quantity": 12}
    rules = [seasonal_discount, loyalty_discount, bulk_discount]
    final = apply_discounts(100.0, ctx, rules)
    print(f"Final price: ${final}")   # 100 → 90 → 85.5 → 72.67

"""
OOP — Discount
==============
Each rule is a class with an apply() method.
DiscountEngine composes rules via a list and applies them in order.
Adding a new rule = adding a new class (open/closed principle).
"""

from abc import ABC, abstractmethod
from typing import List


class DiscountRule(ABC):
    @abstractmethod
    def apply(self, price: float) -> float: ...


class SeasonalDiscount(DiscountRule):
    """10 % off — enabled by a flag passed at construction time."""
    def __init__(self, active: bool) -> None:
        self._active = active

    def apply(self, price: float) -> float:
        return price * 0.90 if self._active else price


class LoyaltyDiscount(DiscountRule):
    """5 % off for loyalty members."""
    def __init__(self, is_member: bool) -> None:
        self._is_member = is_member

    def apply(self, price: float) -> float:
        return price * 0.95 if self._is_member else price


class BulkDiscount(DiscountRule):
    """15 % off when quantity reaches the threshold."""
    def __init__(self, quantity: int, threshold: int = 10) -> None:
        self._quantity = quantity
        self._threshold = threshold

    def apply(self, price: float) -> float:
        return price * 0.85 if self._quantity >= self._threshold else price


class DiscountEngine:
    """Composes multiple DiscountRule objects and applies them in order."""

    def __init__(self, rules: "List[DiscountRule]") -> None:
        self._rules = rules

    def calculate(self, price: float) -> float:
        for rule in self._rules:
            price = rule.apply(price)
        return round(price, 2)


# --- demo ---------------------------------------------------------------
if __name__ == "__main__":
    engine = DiscountEngine([
        SeasonalDiscount(active=True),
        LoyaltyDiscount(is_member=True),
        BulkDiscount(quantity=12),
    ])
    print(f"Final price: ${engine.calculate(100.0)}")  # 72.67

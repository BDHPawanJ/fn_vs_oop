"""
OOP — Shopping Cart
====================
Cart owns its item list as internal state.
Methods mutate self — the caller never manages raw data directly.
Encapsulation: internal list is hidden behind the Cart interface.
"""

from dataclasses import dataclass, field


@dataclass
class Item:
    name:  str
    price: float
    qty:   int = 1


class Cart:
    def __init__(self) -> None:
        self._items: list[Item] = []

    def add(self, name: str, price: float, qty: int = 1) -> None:
        """Add item or increment quantity if it already exists."""
        for item in self._items:
            if item.name == name:
                item.qty += qty
                return
        self._items.append(Item(name, price, qty))

    def remove(self, name: str) -> None:
        self._items = [i for i in self._items if i.name != name]

    def total(self) -> float:
        return round(sum(i.price * i.qty for i in self._items), 2)

    def item_count(self) -> int:
        return sum(i.qty for i in self._items)

    def summary(self) -> str:
        lines = [f"  {i.name:15} x{i.qty}  ${i.price * i.qty:.2f}"
                 for i in self._items]
        return "\n".join(lines) + f"\n  {'TOTAL':15}      ${self.total():.2f}"

    def __repr__(self) -> str:
        return f"Cart(items={len(self._items)}, total=${self.total()})"


# --- demo ---------------------------------------------------------------
if __name__ == "__main__":
    cart = Cart()
    cart.add("Apple",  0.50, qty=4)
    cart.add("Bread",  2.99)
    cart.add("Milk",   1.49, qty=2)
    cart.add("Apple",  0.50, qty=2)   # increments qty → 6
    cart.remove("Bread")
    print(cart.summary())

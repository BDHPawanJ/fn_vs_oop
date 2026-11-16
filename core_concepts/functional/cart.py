"""
Functional — Shopping Cart
===========================
Cart is an immutable tuple of item dicts. Every operation returns a
NEW cart — the original is never mutated (pure functions).
State lives in the caller, not in a shared object.
"""

from typing import Callable, Dict, Any, Tuple

Item  = Dict[str, Any]   # {"name": str, "price": float, "qty": int}
Cart  = Tuple            # Tuple[Item, ...]


EMPTY_CART: Cart = ()


def add_item(cart: Cart, name: str, price: float, qty: int = 1) -> Cart:
    """Return a new cart with the item added (or quantity incremented)."""
    for item in cart:
        if item["name"] == name:
            updated = {**item, "qty": item["qty"] + qty}
            return tuple(i if i["name"] != name else updated for i in cart)
    return cart + ({"name": name, "price": price, "qty": qty},)


def remove_item(cart: Cart, name: str) -> Cart:
    """Return a new cart with the named item removed."""
    return tuple(i for i in cart if i["name"] != name)


def total(cart: Cart) -> float:
    """Sum of price * qty for all items."""
    return round(sum(i["price"] * i["qty"] for i in cart), 2)


def item_count(cart: Cart) -> int:
    return sum(i["qty"] for i in cart)


def summary(cart: Cart) -> str:
    lines = [f"  {i['name']:15} x{i['qty']}  ${i['price'] * i['qty']:.2f}"
             for i in cart]
    return "\n".join(lines) + f"\n  {'TOTAL':15}      ${total(cart):.2f}"


# --- demo ---------------------------------------------------------------
if __name__ == "__main__":
    cart = EMPTY_CART
    cart = add_item(cart, "Apple",  0.50, qty=4)
    cart = add_item(cart, "Bread",  2.99)
    cart = add_item(cart, "Milk",   1.49, qty=2)
    cart = add_item(cart, "Apple",  0.50, qty=2)   # increments qty
    cart = remove_item(cart, "Bread")
    print(summary(cart))

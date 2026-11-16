"""
Functional — Shapes
====================
Shape data is a plain dict. area() and perimeter() dispatch on "type".
Adding a new shape = adding an elif branch (or a dispatch dict entry).
No inheritance, no state.
"""

import math
from typing import Callable, Dict, Any

Shape = Dict[str, Any]   # {"type": "circle"|"rectangle"|"triangle", ...}


def area(shape: Shape) -> float:
    t = shape["type"]
    if t == "circle":
        return round(math.pi * shape["radius"] ** 2, 4)
    elif t == "rectangle":
        return shape["width"] * shape["height"]
    elif t == "triangle":
        return 0.5 * shape["base"] * shape["height"]
    raise ValueError(f"Unknown shape: {t}")


def perimeter(shape: Shape) -> float:
    t = shape["type"]
    if t == "circle":
        return round(2 * math.pi * shape["radius"], 4)
    elif t == "rectangle":
        return 2 * (shape["width"] + shape["height"])
    elif t == "triangle":
        a, b, c = shape["a"], shape["b"], shape["c"]
        return a + b + c
    raise ValueError(f"Unknown shape: {t}")


def describe(shape: Shape) -> str:
    return (f"{shape['type'].title()}: "
            f"area={area(shape)}, perimeter={perimeter(shape)}")


# --- demo ---------------------------------------------------------------
if __name__ == "__main__":
    shapes = [
        {"type": "circle",    "radius": 5},
        {"type": "rectangle", "width": 4, "height": 6},
        {"type": "triangle",  "base": 3, "height": 4, "a": 3, "b": 4, "c": 5},
    ]
    for s in shapes:
        print(describe(s))

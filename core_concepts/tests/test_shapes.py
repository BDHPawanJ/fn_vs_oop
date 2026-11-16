"""Tests — Shapes (functional vs OOP produce identical results)."""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import functional.shapes as fn
from oop.shapes import Circle, Rectangle, Triangle


def test_circle_area():
    assert fn.area({"type": "circle", "radius": 5}) == Circle(5).area()


def test_circle_perimeter():
    assert fn.perimeter({"type": "circle", "radius": 5}) == Circle(5).perimeter()


def test_rectangle_area():
    s = {"type": "rectangle", "width": 4, "height": 6}
    assert fn.area(s) == Rectangle(4, 6).area() == 24


def test_rectangle_perimeter():
    s = {"type": "rectangle", "width": 4, "height": 6}
    assert fn.perimeter(s) == Rectangle(4, 6).perimeter() == 20


def test_triangle_area():
    s = {"type": "triangle", "base": 3, "height": 4, "a": 3, "b": 4, "c": 5}
    assert fn.area(s) == Triangle(3, 4, 3, 4, 5).area() == 6.0


def test_unknown_shape_raises():
    import pytest
    with pytest.raises(ValueError):
        fn.area({"type": "hexagon"})

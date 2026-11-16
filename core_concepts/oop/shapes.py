"""
OOP — Shapes
=============
Each shape is a class. area() and perimeter() are methods.
Adding a new shape = adding a new subclass; no existing code changes.
Polymorphism: any Shape works wherever a Shape is expected.
"""

import math
from abc import ABC, abstractmethod
from typing import List


class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

    @abstractmethod
    def perimeter(self) -> float: ...

    def describe(self) -> str:
        return (f"{self.__class__.__name__}: "
                f"area={self.area()}, perimeter={self.perimeter()}")


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return round(math.pi * self.radius ** 2, 4)

    def perimeter(self) -> float:
        return round(2 * math.pi * self.radius, 4)


class Rectangle(Shape):
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height

    def perimeter(self) -> float:
        return 2 * (self.width + self.height)


class Triangle(Shape):
    def __init__(self, base: float, height: float, a: float, b: float, c: float) -> None:
        self.base = base
        self.height = height
        self._sides = (a, b, c)

    def area(self) -> float:
        return 0.5 * self.base * self.height

    def perimeter(self) -> float:
        return sum(self._sides)


# --- demo ---------------------------------------------------------------
if __name__ == "__main__":
    shapes: "List[Shape]" = [
        Circle(5),
        Rectangle(4, 6),
        Triangle(3, 4, 3, 4, 5),
    ]
    for s in shapes:
        print(s.describe())

"""
OOP — Descriptors
==================
CONCEPT
  A descriptor is any object that defines __get__, __set__, or __delete__.
  When assigned as a *class attribute*, Python calls these methods instead
  of doing a plain dict lookup — giving you computed properties, validation,
  lazy loading, and type enforcement with zero boilerplate at the call site.

  This is the mechanism behind @property, @classmethod, @staticmethod,
  and every ORM field (Django's CharField, SQLAlchemy's Column).

TYPES COVERED
  1. Data descriptor       — defines __get__ AND __set__ (e.g. validated field)
  2. Non-data descriptor   — defines only __get__ (e.g. cached_property)
  3. @property shorthand   — built-in descriptor for simple cases
  4. Reusable typed field  — one descriptor class used on many models

WHEN TO USE
  - Attribute-level validation without repeating it in every setter
  - Lazy computation cached on first access (expensive DB / API call)
  - Type coercion: always store as float even if int is passed
  - Building a mini-ORM or config system

INSIGHT
  Properties are single-use descriptors — they can't be reused across
  classes. A proper descriptor class can be declared once and used as a
  field on 50 different model classes. This is exactly how Django's model
  fields work. The __set_name__ hook (Python 3.6+) lets the descriptor
  know which attribute name it was assigned to — no manual naming needed.
"""


# ── 1. Reusable data descriptor — typed + range-validated field ───────────

class RangedFloat:
    """
    Descriptor: validates that the value is a float within [lo, hi].
    Declare as a class attribute; __set_name__ captures the field name.
    """
    def __init__(self, lo: float, hi: float) -> None:
        self.lo = lo
        self.hi = hi
        self._name = ""

    def __set_name__(self, owner, name: str) -> None:
        self._name = name                     # e.g. "price", "rating"

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self                       # accessed on the class itself
        return obj.__dict__.get(self._name)

    def __set__(self, obj, value) -> None:
        value = float(value)                  # coerce int -> float
        if not (self.lo <= value <= self.hi):
            raise ValueError(
                f"{self._name} must be in [{self.lo}, {self.hi}], got {value}"
            )
        obj.__dict__[self._name] = value


class NonEmpty:
    """Descriptor: ensures a string attribute is never empty."""
    def __set_name__(self, owner, name): self._name = name
    def __get__(self, obj, _=None): return obj.__dict__.get(self._name) if obj else self
    def __set__(self, obj, value):
        if not str(value).strip():
            raise ValueError(f"{self._name} cannot be empty")
        obj.__dict__[self._name] = str(value).strip()


# ── 2. Non-data descriptor — lazy cached property ─────────────────────────

class lazy_property:
    """
    Non-data descriptor: computes value on first access, then caches it
    in the instance __dict__ (which shadows the class descriptor on
    subsequent lookups — that's the caching trick).
    """
    def __init__(self, fn):
        self._fn = fn
        self.__doc__ = fn.__doc__

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        value = self._fn(obj)
        obj.__dict__[self._fn.__name__] = value  # cache in instance dict
        return value


# ── 3. Models using the descriptors ───────────────────────────────────────

class Product:
    name   = NonEmpty()
    price  = RangedFloat(0.01, 99_999.99)
    rating = RangedFloat(0.0, 5.0)

    def __init__(self, name: str, price: float, rating: float) -> None:
        self.name   = name
        self.price  = price
        self.rating = rating

    @lazy_property
    def label(self) -> str:
        """Computed once, cached forever: expensive formatting."""
        print("    [lazy_property] computing label...")
        return f"{self.name} — ${self.price:.2f} ({self.rating}/5)"

    def __repr__(self) -> str:
        return f"Product({self.name!r}, {self.price}, {self.rating})"


# ── demo ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = Product("Widget", 29.99, 4.5)
    print(repr(p))

    print(p.label)   # triggers computation
    print(p.label)   # from cache — "[lazy_property]" NOT printed again

    # Validation via descriptor
    try:
        p.price = 150_000
    except ValueError as e:
        print(f"Caught: {e}")

    try:
        p.name = "   "
    except ValueError as e:
        print(f"Caught: {e}")

    # Int coercion
    p.price = 10          # int passed
    print(type(p.price), p.price)   # <class 'float'> 10.0

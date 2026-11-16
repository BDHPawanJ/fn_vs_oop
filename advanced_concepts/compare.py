"""
advanced_concepts/compare.py — Advanced Concepts Runner
========================================================
Run:  python3 advanced_concepts/compare.py   (from fn_vs_oop/)

Exercises every advanced concept file and prints the key insight
from each one.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BOLD  = "\033[1m";  CYAN  = "\033[96m";  GREEN = "\033[92m"
YEL   = "\033[93m"; DIM   = "\033[2m";   RESET = "\033[0m"

def title(t):   print(f"\n{BOLD}{CYAN}{'='*62}\n  {t}\n{'='*62}{RESET}")
def head(t):    print(f"\n{BOLD}{YEL}  -- {t} --{RESET}")
def show(k, v): print(f"  {DIM}{k:<26}{RESET} {v}")
def ok(msg):    print(f"  {GREEN}[OK]{RESET}  {msg}")
def sep():      print(f"  {DIM}{'-'*58}{RESET}")
def insight(t): print(f"\n  {GREEN}>> {t}{RESET}")


# ═══════════════════════════════════════════════════════════════════════════
# FUNCTIONAL
# ═══════════════════════════════════════════════════════════════════════════

def demo_closures():
    title("FN-1: CLOSURES & PARTIAL APPLICATION")
    from functional.closures_and_partial import (
        make_counter, make_range_validator,
        send_email, send_urgent, send_sms, make_memoised,
    )

    head("Closure as private state")
    counter = make_counter(start=0, step=10)
    ok(f"counter() x4: {[counter() for _ in range(4)]}")
    show("OOP equivalent", "class Counter:  def __init__(self): self.n = 0")

    head("Closure as configurable validator")
    valid_pct  = make_range_validator(0, 100)
    valid_age  = make_range_validator(0, 150)
    ok(f"valid_pct(85)={valid_pct(85)}  valid_pct(110)={valid_pct(110)}")
    ok(f"valid_age(30)={valid_age(30)}  valid_age(200)={valid_age(200)}")

    head("Partial application — specialised functions from one generic")
    ok(send_email("Weekly digest ready"))
    ok(send_urgent("Payment gateway down!"))
    ok(send_sms("Your OTP: 7291"))

    head("Closure-based memoisation")
    fib = make_memoised(lambda n: n if n < 2 else fib(n-1) + fib(n-2))
    ok(f"fib(0..7): {[fib(i) for i in range(8)]}")

    insight("Closure = lightweight stateful callable. "
            "Use when a class would be overkill for a single captured value.")


def demo_decorators():
    title("FN-2: DECORATORS")
    import functional.decorators as dec

    head("Parametrised decorator — @retry")
    attempts = [0]

    @dec.retry(times=3, exceptions=(ValueError,))
    def unstable():
        attempts[0] += 1
        if attempts[0] < 3:
            raise ValueError("not ready")
        return f"succeeded on attempt {attempts[0]}"

    ok(f"retry result: {unstable()}")

    head("Class-based stateful decorator — CountCalls")

    @dec.CountCalls
    def greet(name): return f"Hello, {name}"

    greet("Alice"); greet("Bob"); greet("Carol")
    ok(f"greet called {greet.calls} times")

    head("Stacking — @timeit wraps @retry wraps @log_call (outermost runs first)")
    import functional.decorators as _dec_mod
    _dec_mod.fetch_data("https://api.example.com/items")
    ok("fetch_data() ran: timeit measured, retry stood by, log_call traced")

    insight("Decorator = cross-cutting concern (timing, auth, retry) "
            "applied declaratively. OOP equivalent = Proxy pattern — "
            "more verbose, requires a wrapper class per function.")


def demo_higher_order():
    title("FN-3: HIGHER-ORDER FUNCTIONS & CURRYING")
    from functional.higher_order import (
        pipeline_demo, curry_add, double, triple,
        process_items, take, imap, naturals,
    )

    head("map / filter / reduce pipeline")
    ok(f"total paid orders: {pipeline_demo()}")   # 430

    head("Currying — f(a)(b)(c)")
    ok(f"curry_add(1)(2)(3) = {curry_add(1)(2)(3)}")
    ok(f"double(7) = {double(7)}    triple(7) = {triple(7)}")

    head("Function as strategy — pluggable transform + predicate")
    items = list(range(1, 9))
    result = process_items(items, transform=double, predicate=lambda x: x % 2 == 0)
    ok(f"double(evens of {items}) = {result}")

    head("Lazy HOFs — infinite sequence")
    squares = imap(lambda n: n**2, naturals(1))
    ok(f"first 8 squares: {take(8, squares)}")

    insight("HOFs are the foundation of every data pipeline "
            "(pandas .pipe, PySpark map/filter). "
            "Currying is cleaner with functools.partial in Python "
            "but explicit curry shows the concept clearly.")


def demo_pipeline():
    title("FN-4: FUNCTION COMPOSITION & RAILWAY PATTERN")
    from functional.composition_pipeline import (
        pipe, compose, railway, Ok, Err,
        parse_int, validate_positive, validate_max, to_percentage, tap,
    )

    head("compose / pipe")
    normalize = pipe(str.strip, str.lower, lambda s: s.replace(" ", "_"))
    ok(f"normalize('  Hello World  ') = {normalize('  Hello World  ')!r}")

    transform = compose(lambda x: x**2, lambda x: x*2, lambda x: x+1)
    ok(f"compose(square, double, add1)(3) = {transform(3)}")  # 64

    head("Railway pattern — Ok/Err short-circuit")
    validate = railway(
        validate_positive,
        validate_max(100),
        tap(lambda n: print(f"    [tap] accepted: {n}")),
        to_percentage,
    )
    for raw in ["75", "-5", "150", "abc"]:
        result = validate(parse_int(raw))
        ok(f"input={raw!r:<6} -> {result}")

    insight("Railway replaces nested if/else or exception-driven control flow. "
            "Each step is independently unit-testable with Ok/Err inputs. "
            "OOP equivalent: a list of validator objects each with validate(value) — "
            "both are reorderable; the functional version needs no classes at all.")


# ═══════════════════════════════════════════════════════════════════════════
# OOP
# ═══════════════════════════════════════════════════════════════════════════

def demo_mixins():
    title("OOP-1: MIXINS")
    from oop.mixins import User, Product

    head("Stacking 4 mixins on User")
    u = User("Alice", "alice@example.com")
    ok(f"repr:    {repr(u)}")
    ok(f"to_json: {u.to_json()}")
    ok(f"save:    {u.save()}")

    head("TimestampMixin — created_at / updated_at")
    import time; time.sleep(0.001)
    u.touch()
    ok(f"updated_at changed: {u.updated_at != u.created_at}")

    head("MRO — Python resolves method lookup left to right")
    ok(f"User MRO: {[c.__name__ for c in User.__mro__]}")

    head("Validation failure via ValidateMixin hook")
    try:
        User("", "not-an-email").save()
    except ValueError as e:
        ok(f"caught: {e}")

    insight("Mixin = horizontal reuse across unrelated hierarchies. "
            "Functional equivalent = a class decorator or a function that accepts the object. "
            "Mixins win when the added behaviour needs to access and mutate instance state (self).")


def demo_descriptors():
    title("OOP-2: DESCRIPTORS")
    from oop.descriptors import Product

    head("Reusable typed + validated fields")
    p = Product("Widget", 29.99, 4.5)
    ok(repr(p))

    head("lazy_property — computed once, cached")
    ok(f"first access  (computes): {p.label}")
    ok(f"second access (cached):   {p.label}")

    head("Type coercion — int stored as float")
    p.price = 10
    ok(f"p.price = 10 (int) stored as {type(p.price).__name__}: {p.price}")

    head("Validation at assignment time")
    for bad_val, field in [(-1, "price"), ("   ", "name"), (6.0, "rating")]:
        try:
            setattr(p, field, bad_val)
        except (ValueError, TypeError) as e:
            ok(f"blocked {field}={bad_val!r}: {e}")

    insight("Descriptors eliminate per-setter boilerplate. "
            "Declare once, reuse across any number of model classes. "
            "Django ORM fields are built on the same descriptor protocol — "
            "CharField, IntegerField etc. all use __get__/__set__/__set_name__.")


def demo_protocols_abc():
    title("OOP-3: PROTOCOLS vs ABC")
    from oop.protocols_and_abc import (
        JSONExporter, CSVExporter, BrokenExporter,
        Serializable, Invoice, LogEntry, archive, MemoryBackend,
    )

    head("ABC — nominal typing, enforced at instantiation")
    record = {"id": 1, "name": "Alice"}
    for exp in [JSONExporter(), CSVExporter()]:
        ok(f"[{exp.content_type}] {exp.export(record)[:40]}")

    try:
        BrokenExporter()
    except TypeError as e:
        ok(f"BrokenExporter blocked: {str(e)[:60]}")

    head("Protocol — structural typing, no inheritance needed")
    for obj in [Invoice("INV-001", 250.0), LogEntry("boot complete")]:
        ok(f"isinstance(Serializable)={isinstance(obj, Serializable)} | {type(obj).__name__}")
        archive(obj)

    head("StorageBackend — ABC for internal plugin contracts")
    b = MemoryBackend()
    b.write("key", b"value")
    ok(f"read back: {b.read('key')}")

    insight("Protocol = public API surface (loose coupling, any conformant object).\n"
            "  ABC    = internal architecture contract (hard enforcement, isinstance checks).\n"
            "  Rule: Protocol at boundaries, ABC inside the system.")


def demo_metaclass():
    title("OOP-4: METACLASSES & CLASS FACTORIES")
    from oop.metaclass import PluginMeta, Command, _handlers

    head("Metaclass plugin registry — auto-register on class definition")
    for name in ["csvplugin", "jsonplugin", "xmlplugin"]:
        plugin = PluginMeta.get(name)()
        ok(f"{name}: {plugin.run()}")

    head("__init_subclass__ — lighter alternative (preferred)")
    for name, cls in Command._registry.items():
        ok(f"command '{name}': {cls().execute()}")

    head("Class decorator — simplest option")
    for event, cls in _handlers.items():
        ok(f"event '{event}' -> {cls.__name__}")

    head("Validation metaclass — error at class definition time (fires on subclasses)")
    from oop.metaclass import StrictMeta

    class WellDocumented(metaclass=StrictMeta):
        """This class has a docstring — passes StrictMeta validation."""

    try:
        class MissingDocs(WellDocumented):
            pass   # subclass with no docstring → StrictMeta raises immediately
    except TypeError as e:
        ok(f"caught at class definition: {e}")

    insight("Prefer __init_subclass__ over metaclass for 80% of use cases.\n"
            "  Reserve metaclass for ORM-level framework code.\n"
            "  Class decorator is the simplest; metaclass is the most powerful.")


# ═══════════════════════════════════════════════════════════════════════════
# HYBRID
# ═══════════════════════════════════════════════════════════════════════════

def demo_mixed():
    title("HYBRID: Order Processing Pipeline")
    from mixed import Order, OrderItem, process_order, RouteHandler

    orders = [
        Order("ORD-001", "Alice", [OrderItem("SKU-A", 3, 200.0), OrderItem("SKU-B", 1, 50.0)]),
        Order("ORD-002", "Bob",   [OrderItem("SKU-C", 1, 9.99)]),
        Order("ORD-003", "Carol", []),
    ]
    for order in orders:
        result = process_order(order, discount_rate=0.10)
        ok(f"{order} -> {result}")

    ok(f"handlers: {list(RouteHandler._registry.keys())}")

    insight(
        "OOP owns the DATA with lifecycle (Order, handlers registry).\n"
        "  FN  owns the TRANSFORM (railway pipeline, partial discount, @timed).\n"
        "  Rule: data with identity/lifecycle -> class. "
        "Transform/validate -> function."
    )


# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════

def print_summary():
    title("ADVANCED CONCEPTS DECISION GUIDE")
    print(f"""
  {BOLD}FUNCTIONAL{RESET}
  Closures       Use when you need a lightweight stateful callable.
                 Prefer over a class when only ONE value is captured.
  Partial        Use to fix some arguments of a function and get a specialised one back.
                 Cleaner than a wrapper function or lambda that only fixes one arg.
  Decorators     Cross-cutting concerns: @retry, @timed, @require_auth.
                 Compose multiple decorators; outermost runs first.
  HOFs           Data pipelines, pluggable strategies, lazy sequences.
                 For simple transforms prefer list comprehensions for readability;
                 use map/filter/reduce when composing pipelines programmatically.
  Railway        Replace exception-driven control flow in validation chains.
                 Every step testable independently with Ok/Err inputs.

  {BOLD}OOP{RESET}
  Mixins         Add behaviour to unrelated class hierarchies (horizontal reuse).
                 Functional equivalent: class decorator or standalone function taking self.
                 Mixins win when the added behaviour needs to mutate instance state.
  Descriptors    Per-attribute validation, coercion, and lazy loading reused across models.
                 Django ORM fields (CharField, IntegerField) are built on this protocol.
  Protocol       Public API contracts — any conformant object qualifies.
                 Preferred at library boundaries; checked by mypy.
  ABC            Internal contracts with hard enforcement at instantiation.
                 Use when isinstance() checks are needed at runtime.
  __init_subclass__ Auto-register plugins without metaclass complexity.
                 Covers 80% of metaclass use cases; far more readable.
  Metaclass      ORM field definitions, class-body transformations.
                 Most powerful but hardest to debug — prefer __init_subclass__ first.

  {BOLD}HYBRID RULE OF THUMB{RESET}
  Data with identity / lifecycle        ->  class
  Pure transform / validation           ->  function
  Cross-cutting concern                 ->  decorator
  Shared capability across hierarchies  ->  mixin
  Loose interface contract              ->  Protocol
  Hard enforcement / plugin system      ->  ABC / __init_subclass__
    """)


# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    demo_closures()
    demo_decorators()
    demo_higher_order()
    demo_pipeline()
    demo_mixins()
    demo_descriptors()
    demo_protocols_abc()
    demo_metaclass()
    demo_mixed()
    print_summary()
    print(f"\n{BOLD}{GREEN}  All advanced concept demos completed.{RESET}\n")

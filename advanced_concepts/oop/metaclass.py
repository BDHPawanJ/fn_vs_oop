"""
OOP — Metaclasses
==================
CONCEPT
  In Python, classes are themselves objects — instances of their metaclass.
  The default metaclass is `type`. By subclassing `type` you intercept
  class *creation* itself: you can validate class bodies, auto-register
  subclasses, inject methods, enforce naming conventions, and more.

  Hierarchy:
    instance  <-- created by --> class
    class     <-- created by --> metaclass (type by default)

TYPES COVERED
  1. Registry metaclass    — auto-registers every subclass by name
  2. Validation metaclass  — enforces naming / interface rules at class
                             definition time (before any instance exists)
  3. __init_subclass__     — lighter alternative to metaclass for many
                             common use cases (Python 3.6+)
  4. Class decorator       — even lighter alternative for simple cases

WHEN TO USE (metaclass)
  - Plugin registries: auto-discover all Command / Handler subclasses
  - ORMs: Django Model, SQLAlchemy declarative base
  - Enforcing team conventions at class definition time, not runtime
  - Framework code where you need to transform class structure

WHEN NOT TO USE
  - Business logic (use regular classes or functions)
  - Simple validation (prefer __init_subclass__ or ABC)
  - Anywhere readability matters more than magic

INSIGHT
  Metaclasses are powerful but opaque. Prefer __init_subclass__ for
  simple registration/validation — it covers 80 % of metaclass use
  cases with zero metaclass complexity. Reserve metaclasses for true
  framework-level code (ORMs, serialisation libraries, plugin systems).
"""


# ── 1. Registry metaclass — auto-register every subclass ─────────────────

class PluginMeta(type):
    """
    Every class with metaclass=PluginMeta is auto-registered in
    _registry by its lowercase class name. No manual registration needed.
    """
    _registry: dict = {}

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)
        if bases:                           # skip the base class itself
            mcs._registry[name.lower()] = cls
        return cls

    @classmethod
    def get(mcs, name: str):
        cls = mcs._registry.get(name.lower())
        if not cls:
            raise KeyError(f"No plugin registered: {name!r}")
        return cls


class Plugin(metaclass=PluginMeta):
    def run(self) -> str: ...


class CSVPlugin(Plugin):
    def run(self) -> str: return "processing CSV"


class JSONPlugin(Plugin):
    def run(self) -> str: return "processing JSON"


class XMLPlugin(Plugin):
    def run(self) -> str: return "processing XML"


# ── 2. Validation metaclass — enforce rules at class creation time ─────────

class StrictMeta(type):
    """
    Rejects class definitions that:
      - don't define a docstring
      - contain methods without type annotations
    Errors surface at import time, not at instantiation.
    """
    def __new__(mcs, name, bases, namespace):
        if bases and not namespace.get("__doc__"):
            raise TypeError(f"Class '{name}' must have a docstring")
        for attr, val in namespace.items():
            if callable(val) and not attr.startswith("_"):
                ann = getattr(val, "__annotations__", {})
                if "return" not in ann:
                    raise TypeError(
                        f"Method '{name}.{attr}' missing return type annotation"
                    )
        return super().__new__(mcs, name, bases, namespace)


# ── 3. __init_subclass__ — lightweight alternative (preferred) ────────────

class Command:
    """
    __init_subclass__ fires when a subclass is defined.
    Lighter than a metaclass; achieves the same auto-registration.
    """
    _registry: dict = {}

    def __init_subclass__(cls, command_name: str = "", **kwargs):
        super().__init_subclass__(**kwargs)
        name = command_name or cls.__name__.lower()
        Command._registry[name] = cls

    def execute(self) -> str: ...


class StartCommand(Command, command_name="start"):
    def execute(self) -> str: return "starting service"


class StopCommand(Command, command_name="stop"):
    def execute(self) -> str: return "stopping service"


class ReloadCommand(Command, command_name="reload"):
    def execute(self) -> str: return "reloading config"


# ── 4. Class decorator — simplest option for annotation/registration ──────

_handlers: dict = {}

def handler(event: str):
    """Decorator that registers a class as a handler for an event type."""
    def decorator(cls):
        _handlers[event] = cls
        return cls
    return decorator


@handler("user.created")
class UserCreatedHandler:
    def handle(self, payload: dict) -> str:
        return f"welcome email sent to {payload['email']}"


@handler("order.placed")
class OrderPlacedHandler:
    def handle(self, payload: dict) -> str:
        return f"order {payload['id']} queued for fulfilment"


# ── demo ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Metaclass registry
    print("-- metaclass plugin registry --")
    for name in ["csvplugin", "jsonplugin", "xmlplugin"]:
        plugin = PluginMeta.get(name)()
        print(f"  {name}: {plugin.run()}")

    # __init_subclass__ registry
    print("\n-- __init_subclass__ command registry --")
    for name, cmd_cls in Command._registry.items():
        print(f"  {name}: {cmd_cls().execute()}")

    # Class decorator registry
    print("\n-- class decorator event handler registry --")
    for event, handler_cls in _handlers.items():
        print(f"  {event}: registered -> {handler_cls.__name__}")

    # Validation metaclass
    print("\n-- validation metaclass --")
    try:
        class BadService(metaclass=StrictMeta):
            pass   # no docstring
    except TypeError as e:
        print(f"  Caught at class definition: {e}")

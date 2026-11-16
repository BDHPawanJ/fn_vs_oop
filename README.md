# Functional vs OOP — Python POC

Side-by-side comparison of Functional and OOP design in Python,
organized into three progressive levels.

---

## Project Layout

```
fn_vs_oop/
│
├── core_concepts/          # Part 1 — foundational patterns, no dependencies
│   ├── functional/
│   │   ├── discount.py     # Rules as composable functions
│   │   ├── shapes.py       # Shape as dict, area/perimeter as free functions
│   │   ├── cart.py         # Immutable tuple cart
│   │   └── notification.py # Channel as a function
│   ├── oop/
│   │   ├── discount.py     # Rules as subclasses + DiscountEngine
│   │   ├── shapes.py       # Shape ABC + Circle / Rectangle / Triangle
│   │   ├── cart.py         # Cart class with encapsulated item list
│   │   └── notification.py # NotificationChannel ABC + NotificationService
│   ├── tests/              # 18 tests covering both approaches
│   └── compare.py          # Side-by-side demo runner
│
├── shared_lib/             # Part 2 — real shared library patterns
│   ├── functional/
│   │   ├── logger.py       # Module-level state, free functions, bind()
│   │   ├── db.py           # Connection registry, free query functions
│   │   └── aws_wrapper.py  # s3_*/sqs_*/ssm_* prefixed functions
│   ├── oop/
│   │   ├── logger.py       # Logger class, singleton, BoundLogger, get_child()
│   │   ├── db.py           # DatabaseConnection, ReadOnlyConnection, ConnectionPool
│   │   └── aws_wrapper.py  # AWSClient base, S3/SQS/SSMClient, AWSClientFactory
│   ├── tests/              # 54 tests covering both approaches
│   └── compare.py          # Side-by-side demo runner
│
├── advanced_concepts/      # Part 3 — advanced patterns & hybrid design
│   ├── functional/
│   │   ├── closures_and_partial.py   # Closure as state, partial application, memoisation
│   │   ├── decorators.py             # Simple / parametrised / class-based / stacked
│   │   ├── higher_order.py           # map/filter/reduce, currying, strategy, lazy HOFs
│   │   └── composition_pipeline.py  # compose/pipe, Result monad (railway), tap
│   ├── oop/
│   │   ├── mixins.py                 # JSONMixin, TimestampMixin, ValidateMixin stacking
│   │   ├── descriptors.py            # Data descriptor, lazy_property, __set_name__
│   │   ├── protocols_and_abc.py      # Protocol (structural) vs ABC (nominal)
│   │   └── metaclass.py              # PluginMeta, __init_subclass__, class decorator
│   ├── mixed.py                      # Hybrid order pipeline — OOP model + FN pipeline
│   ├── tests/                        # 103 tests covering all concepts
│   └── compare.py                    # Full walkthrough runner with decision guide
│
├── conftest.py
├── pyproject.toml
└── README.md
```

---

## Run the demos

```bash
# Part 1 — core concepts
python3 core_concepts/compare.py

# Part 2 — shared library patterns
python3 shared_lib/compare.py

# Part 3 — advanced concepts
python3 advanced_concepts/compare.py
```

## Run the tests

```bash
# All tests (174 total)
python3 -m pytest

# Per suite
python3 -m pytest core_concepts/tests/ -v      # 18 tests
python3 -m pytest shared_lib/tests/ -v         # 54 tests
python3 -m pytest advanced_concepts/tests/ -v  # 103 tests
```

---

## Part 1 — Core Concepts

Four everyday examples. No frameworks, no external libraries.

| Example | Functional | OOP |
|---|---|---|
| Discount | Rules are functions in a list | Rules are subclasses of `DiscountRule` |
| Shapes | Shape is a `dict`, central `area()` dispatches on type | Each shape class owns its own formulas |
| Cart | Immutable `tuple` — every op returns a new cart | `Cart` owns a mutable list; methods mutate `self` |
| Notification | Channel is a function; routing via `list[fn]` | Channel is a class; contract enforced via ABC |

---

## Part 2 — Shared Library

Real-world infrastructure patterns: Logger, Database, AWS wrapper.
AWS runs against in-process mock stubs by default (`mock=True`). Set `mock=False`
and configure credentials via the standard boto3 credential chain to use real AWS.

### Logger

| | Functional | OOP |
|---|---|---|
| State | Module-level `_state` dict | Instance variables |
| Singleton | Module import (implicit) | Double-checked lock (explicit) |
| `bind()` | Mutates `_state['extra']` — global effect | Returns a new `BoundLogger` — isolated |
| Child logger | Returns raw `stdlib Logger` | Returns a `Logger` wrapper |

### Database

| | Functional | OOP |
|---|---|---|
| Connection | Dict keyed by `name=` string | `DatabaseConnection` object |
| Lifecycle | `connect()` / `disconnect_all()` | `with DatabaseConnection(...) as db:` |
| Multiple DBs | Multiple `name=` strings | Multiple objects |
| Read-only | No built-in guard — opt-in per call | `ReadOnlyConnection` subclass blocks all writes |
| Pool | Not provided | `ConnectionPool` with `queue.Queue` — thread-safe |

### AWS Wrapper

| | Functional | OOP |
|---|---|---|
| Config | One global `_config` dict | Per-instance `region` / `mock` |
| Call style | `s3_upload()`, `sqs_send()`, `ssm_get()` | `aws.s3.upload()`, `aws.sqs.send()` |
| Multi-region | `configure()` resets global — only one region | One `AWSClientFactory` per region |
| Add service | New set of `xyz_*()` functions | New class extending `AWSClient` |
| Lifecycle | No context manager | `with AWSClientFactory() as aws:` |

---

## Part 3 — Advanced Concepts

Advanced patterns. Each file is self-contained with concept, types, when-to-use,
and key insight documented in the module docstring.

### Functional

| File | Concepts |
|---|---|
| `closures_and_partial.py` | Closure as private state, partial application, memoisation |
| `decorators.py` | Simple / parametrised / class-based / stacked, `@functools.wraps` |
| `higher_order.py` | `map`/`filter`/`reduce`, currying, function-as-strategy, lazy generators |
| `composition_pipeline.py` | `compose`/`pipe`, Result monad (Ok/Err), railway pattern, `tap` |

### OOP

| File | Concepts |
|---|---|
| `mixins.py` | Stacking mixins, MRO, hook methods |
| `descriptors.py` | Data descriptor, `lazy_property`, `__set_name__`, type coercion |
| `protocols_and_abc.py` | Protocol (structural) vs ABC (nominal), `@runtime_checkable` |
| `metaclass.py` | Registry metaclass, `__init_subclass__`, class decorator |

### Hybrid

| File | What it shows |
|---|---|
| `mixed.py` | Order pipeline — OOP owns the model/registry, FN owns the validation/transform |

---

## When to Use Which

| Need | Reach for |
|---|---|
| Lightweight stateful callable | Closure |
| Specialise a function for a context | `functools.partial` |
| Cross-cutting concern (timing, retry, auth) | Decorator |
| Data transformation / validation chain | `compose` / `pipe` / Railway pattern |
| Share behaviour across unrelated hierarchies | Mixin |
| Validated / computed / lazy attribute | Descriptor |
| Loose interface at a library boundary | `Protocol` |
| Hard enforcement / `isinstance()` needed | `ABC` |
| Auto-register subclasses | `__init_subclass__` |
| ORM-level class transformation | Metaclass |
| Data with identity and lifecycle | Class |
| Pure transform — data in, data out | Function |

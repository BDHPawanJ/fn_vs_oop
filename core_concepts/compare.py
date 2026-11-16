"""
compare.py — Functional vs OOP side-by-side runner
====================================================
Run:  python3 compare.py

Each section shows the SAME result produced two ways, then
prints a one-line summary of the key design difference.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── terminal helpers ──────────────────────────────────────────────────────
BOLD  = "\033[1m"
CYAN  = "\033[96m"
GREEN = "\033[92m"
DIM   = "\033[2m"
RESET = "\033[0m"

def title(text):  print(f"\n{BOLD}{CYAN}{'='*60}\n  {text}\n{'='*60}{RESET}")
def head(text):   print(f"\n{BOLD}  {text}{RESET}")
def row(k, v):    print(f"  {DIM}{k:<18}{RESET} {v}")
def rule():       print(f"  {DIM}{'-'*58}{RESET}")
def insight(text):print(f"\n  {GREEN}>> {text}{RESET}")


# =========================================================================
# 1. DISCOUNT
# =========================================================================
def demo_discount():
    title("1. DISCOUNT — applying pricing rules")

    from functional.discount import (
        apply_discounts, seasonal_discount, loyalty_discount, bulk_discount)
    from oop.discount import (
        DiscountEngine, SeasonalDiscount, LoyaltyDiscount, BulkDiscount)

    ctx   = {"is_sale": True, "is_member": True, "quantity": 12}
    price = 100.0

    head("Functional")
    row("approach", "functions in a list, composed by apply_discounts()")
    rules = [seasonal_discount, loyalty_discount, bulk_discount]
    fn_result = apply_discounts(price, ctx, rules)
    row("rules", [f.__name__ for f in rules])
    row("result", f"${fn_result}")

    rule()

    head("OOP")
    row("approach", "DiscountRule subclasses composed by DiscountEngine")
    engine = DiscountEngine([
        SeasonalDiscount(active=True),
        LoyaltyDiscount(is_member=True),
        BulkDiscount(quantity=12),
    ])
    oop_result = engine.calculate(price)
    row("rules", [type(r).__name__ for r in engine._rules])
    row("result", f"${oop_result}")

    insight("Functional: add a rule = add a function.  "
            "OOP: add a rule = add a subclass (open/closed principle).")


# =========================================================================
# 2. SHAPES
# =========================================================================
def demo_shapes():
    title("2. SHAPES — area & perimeter calculation")

    import functional.shapes as fn
    from oop.shapes import Circle, Rectangle, Triangle

    fn_shapes  = [
        {"type": "circle",    "radius": 5},
        {"type": "rectangle", "width": 4, "height": 6},
        {"type": "triangle",  "base": 3, "height": 4, "a": 3, "b": 4, "c": 5},
    ]
    oop_shapes = [Circle(5), Rectangle(4, 6), Triangle(3, 4, 3, 4, 5)]

    head("Functional  (shape = plain dict, dispatch inside area() / perimeter())")
    for s in fn_shapes:
        row(s["type"], fn.describe(s))

    rule()

    head("OOP  (shape = class instance, each class owns its own formulas)")
    for s in oop_shapes:
        row(type(s).__name__, s.describe())

    insight("Functional: one function handles all shapes via match/elif.  "
            "OOP: each shape class is self-contained — no central dispatch needed.")


# =========================================================================
# 3. CART
# =========================================================================
def demo_cart():
    title("3. SHOPPING CART — managing items")

    from functional.cart import EMPTY_CART, add_item, remove_item, summary
    from oop.cart import Cart

    head("Functional  (cart = immutable tuple; every op returns a NEW cart)")
    fn_cart = EMPTY_CART
    fn_cart = add_item(fn_cart, "Apple", 0.50, qty=4)
    fn_cart = add_item(fn_cart, "Bread", 2.99)
    fn_cart = add_item(fn_cart, "Milk",  1.49, qty=2)
    fn_cart = add_item(fn_cart, "Apple", 0.50, qty=2)  # increments qty
    fn_cart = remove_item(fn_cart, "Bread")
    print(summary(fn_cart))

    rule()

    head("OOP  (Cart owns its list; methods mutate internal state)")
    oop_cart = Cart()
    oop_cart.add("Apple", 0.50, qty=4)
    oop_cart.add("Bread", 2.99)
    oop_cart.add("Milk",  1.49, qty=2)
    oop_cart.add("Apple", 0.50, qty=2)  # increments qty
    oop_cart.remove("Bread")
    print(oop_cart.summary())

    insight("Functional: immutable data — safe to share, easy to test, no side-effects.  "
            "OOP: encapsulated state — caller never touches raw data directly.")


# =========================================================================
# 4. NOTIFICATION
# =========================================================================
def demo_notification():
    title("4. NOTIFICATION — sending via multiple channels")

    from functional.notification import email_sender, sms_sender, push_sender, notify
    from oop.notification import (
        EmailChannel, SMSChannel, PushChannel, NotificationService)

    recipient = "alice@example.com"
    message   = "Your order has shipped!"

    head("Functional  (channel = function, channels = list of functions)")
    fn_result = notify(recipient, message, [email_sender, sms_sender, push_sender])
    row("sent via", list(fn_result.keys()))

    rule()

    head("OOP  (channel = class, service composes channel objects)")
    svc = NotificationService([EmailChannel(), SMSChannel(), PushChannel()])
    oop_result = svc.notify(recipient, message)
    row("sent via", list(oop_result.keys()))

    insight("Functional: swap a channel = swap a function in a list.  "
            "OOP: swap a channel = swap a class instance; interface enforced by ABC.")


# =========================================================================
# SUMMARY TABLE
# =========================================================================
def summary_table():
    title("SUMMARY — When to use which")
    print(f"""
  {'Aspect':<24} {'Functional':<32} {'OOP'}
  {'-'*24} {'-'*32} {'-'*28}
  {'State':<24} {'Caller owns it':<32} {'Object owns it'}
  {'Data shape':<24} {'dict / tuple / plain value':<32} {'class instance'}
  {'Add behaviour':<24} {'Add a function or dispatch entry':<32} {'Add a subclass'}
  {'Immutability':<24} {'Natural (return new value)':<32} {'Requires discipline'}
  {'Polymorphism':<24} {'if/elif, dispatch dict,':<32} {'method override'}
  {'':<24} {'functools.singledispatch':<32} {'(inheriting class)'}
  {'Thread sharing':<24} {'Safe only if data is immutable':<32} {'Needs care (mutable state)'}
  {'Test isolation':<24} {'Pure fns: pass different args':<32} {'Inject a different object'}
  {'':<24} {'Module state: patch globals':<32} {''}
  {'Best for':<24} {'Transforms, pipelines':<32} {'Lifecycle, resources, state'}
    """)


# =========================================================================
if __name__ == "__main__":
    demo_discount()
    demo_shapes()
    demo_cart()
    demo_notification()
    summary_table()
    print(f"{BOLD}{GREEN}  All examples ran successfully.{RESET}\n")

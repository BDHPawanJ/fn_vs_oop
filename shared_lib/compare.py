"""
shared_lib/compare.py — Shared Library Functional vs OOP runner
================================================================
Run:  python3 shared_lib/compare.py   (from fn_vs_oop/)
  or  cd shared_lib && python3 compare.py

Three sections mirror a real shared library:
  1. Logger   — configuration, bind(), child loggers
  2. Database — connect/query/transaction, read-only guard, pool
  3. AWS      — S3, SQS, SSM via functional functions vs OOP objects
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── terminal helpers ──────────────────────────────────────────────────────
BOLD  = "\033[1m";  CYAN = "\033[96m";  GREEN = "\033[92m"
DIM   = "\033[2m";  YEL  = "\033[93m";  RESET = "\033[0m"

def title(t):   print(f"\n{BOLD}{CYAN}{'='*62}\n  {t}\n{'='*62}{RESET}")
def head(t):    print(f"\n{BOLD}{YEL}  -- {t} --{RESET}")
def row(k, v):  print(f"  {DIM}{k:<22}{RESET} {v}")
def ok(msg):    print(f"  {GREEN}[OK]{RESET}  {msg}")
def sep():      print(f"  {DIM}{'-'*58}{RESET}")
def insight(t): print(f"\n  {GREEN}>> {t}{RESET}")


# =========================================================================
# 1. LOGGER
# =========================================================================
def demo_logger():
    title("1. LOGGER")

    # -- Functional --------------------------------------------------------
    head("Functional  (module-level state, free functions)")
    import functional.logger as fn_log

    fn_log.configure(name="fn-app", level="DEBUG")
    fn_log.info("app started")
    fn_log.debug("loading config")

    row("bind()", "mutates global _state['extra'] — all callers share it")
    fn_log.bind(request_id="req-001")
    fn_log.info("request received")           # request_id visible here

    row("get_child()", "returns a raw stdlib Logger — caller gets logging.Logger, not a wrapper")
    child = fn_log.get_child("db")
    child.info("child log from db module")
    row("type of child", str(type(child)))

    sep()

    # -- OOP ---------------------------------------------------------------
    head("OOP  (class instance, double-checked singleton)")
    from oop.logger import Logger

    Logger.reset()
    logger = Logger.get_instance(name="oop-app", level="DEBUG")
    logger.info("app started")
    logger.debug("loading config")

    row("bind()", "returns a NEW BoundLogger — does NOT touch global state")
    req_log = logger.bind(request_id="req-001")
    req_log.info("request received")          # request_id only on req_log

    row("get_child()", "returns a Logger wrapper — caller gets the same API, not raw stdlib")
    db_log = logger.get_child("db")
    db_log.info("child log from db module")
    row("type of child", str(type(db_log)))

    row("singleton safety", "10 threads, all get the same instance")
    import threading
    instances = []
    def _get(): instances.append(Logger.get_instance())
    ts = [threading.Thread(target=_get) for _ in range(10)]
    for t in ts: t.start()
    for t in ts: t.join()
    ok(f"all 10 threads got same instance: {len(set(id(i) for i in instances)) == 1}")

    insight(
        "Functional bind() changes state for the entire module.\n"
        "  OOP bind() returns an isolated BoundLogger — safe for per-request context."
    )


# =========================================================================
# 2. DATABASE
# =========================================================================
def demo_db():
    title("2. DATABASE")

    DDL  = "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL)"
    SEED = "INSERT INTO products (name, price) VALUES (?, ?)"
    ROWS = [("Widget", 9.99), ("Gadget", 24.99), ("Doohickey", 4.99)]

    # -- Functional --------------------------------------------------------
    head("Functional  (module-level registry, free functions)")
    import functional.db as fn_db

    fn_db.connect(dsn=":memory:", name="main")
    fn_db.execute(DDL, name="main")
    fn_db.execute_many(SEED, ROWS, name="main")

    rows = fn_db.query("SELECT * FROM products ORDER BY price", name="main")
    ok(f"query returned {len(rows)} rows: {[r['name'] for r in rows]}")
    ok(f"health_check: {fn_db.health_check('main')}")

    row("transaction", "contextmanager — commit on success, rollback on error")
    with fn_db.transaction("main") as conn:
        conn.execute("INSERT INTO products (name, price) VALUES (?, ?)", ("Thingamajig", 1.99))
    rows = fn_db.query("SELECT COUNT(*) AS n FROM products", name="main")
    ok(f"after transaction insert, total rows: {rows[0]['n']}")

    row("read-only", "no built-in guard — caller must opt in manually")
    fn_db.disconnect_all()

    sep()

    # -- OOP ---------------------------------------------------------------
    head("OOP  (DatabaseConnection object, context manager, pool)")
    from oop.db import DatabaseConnection, ReadOnlyConnection, ConnectionPool
    from oop.logger import Logger

    with DatabaseConnection(dsn=":memory:", name="main") as db:
        db.execute(DDL)
        db.execute_many(SEED, ROWS)
        rows = db.query("SELECT * FROM products ORDER BY price")
        ok(f"query returned {len(rows)} rows: {[r['name'] for r in rows]}")
        ok(f"health_check: {db.health_check()}")

        row("transaction", "method on the object — use raw conn.execute() to stay inside the transaction boundary")
        with db.transaction() as conn:
            conn.execute("INSERT INTO products (name, price) VALUES (?, ?)", ("Thingamajig", 1.99))
        rows = db.query("SELECT COUNT(*) AS n FROM products")
        ok(f"after transaction insert, total rows: {rows[0]['n']}")
    ok("context manager auto-closed the connection")

    row("read-only", "ReadOnlyConnection subclass blocks writes at the object level")
    with ReadOnlyConnection(dsn=":memory:", name="ro") as ro:
        try:
            ro.execute("INSERT INTO products (name, price) VALUES (?, ?)", ("X", 0))
        except PermissionError as e:
            ok(f"PermissionError raised: {e}")

    row("pool", "ConnectionPool — queue.Queue backed, thread-safe acquire")
    pool = ConnectionPool(dsn=":memory:", size=3)
    pool.initialise()
    with pool.acquire() as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
        conn.execute("INSERT INTO t VALUES (?)", (42,))
        ok(f"pool query: {conn.query('SELECT * FROM t')}")
    pool.close_all()
    ok(f"pool repr: {pool}")

    insight(
        "Functional: multiple DBs = multiple conn_name strings (easy to mix up).\n"
        "  OOP: multiple DBs = multiple objects — each self-contained and injectable."
    )


# =========================================================================
# 3. AWS
# =========================================================================
def demo_aws():
    title("3. AWS (S3 / SQS / SSM)")

    BUCKET = "demo-bucket"
    QUEUE  = "https://sqs.us-east-1.amazonaws.com/123/demo-queue"

    # -- Functional --------------------------------------------------------
    head("Functional  (module-level config, prefixed free functions)")
    import functional.aws_wrapper as fn_aws

    fn_aws.configure(region="us-east-1", mock=True)

    fn_aws.s3_upload(BUCKET, "data/hello.txt", b"hello from functional")
    data = fn_aws.s3_download(BUCKET, "data/hello.txt")
    ok(f"s3 round-trip: {data}")
    ok(f"s3 list: {fn_aws.s3_list(BUCKET, prefix='data/')}")
    fn_aws.s3_delete(BUCKET, "data/hello.txt")
    ok(f"after delete: {fn_aws.s3_list(BUCKET, prefix='data/')}")

    msg_id = fn_aws.sqs_send(QUEUE, {"event": "order.placed", "id": 42})
    msgs   = fn_aws.sqs_receive(QUEUE)
    ok(f"sqs send -> receive: {msgs[0]['Body']}")

    fn_aws.ssm_put("/app/db/host", "prod-db.example.com")
    ok(f"ssm get /app/db/host: {fn_aws.ssm_get('/app/db/host')!r}")

    row("multi-region", "fn_aws.configure() resets global — only ONE region at a time")

    sep()

    # -- OOP ---------------------------------------------------------------
    head("OOP  (AWSClientFactory, service objects, context manager)")
    from oop.aws_wrapper import AWSClientFactory
    from oop.logger import Logger

    with AWSClientFactory(region="us-east-1", mock=True) as aws:
        aws.s3.upload(BUCKET, "data/hello.txt", b"hello from OOP")
        data = aws.s3.download(BUCKET, "data/hello.txt")
        ok(f"s3 round-trip: {data}")
        ok(f"s3 list: {aws.s3.list_objects(BUCKET, prefix='data/')}")
        aws.s3.delete(BUCKET, "data/hello.txt")
        ok(f"after delete: {aws.s3.list_objects(BUCKET, prefix='data/')}")

        aws.sqs.send(QUEUE, {"event": "order.placed", "id": 42})
        msgs = aws.sqs.receive(QUEUE)
        ok(f"sqs send -> receive: {msgs[0]['Body']}")

        aws.ssm.put("/app/db/host", "prod-db.example.com")
        ok(f"ssm get /app/db/host: {aws.ssm.get('/app/db/host')!r}")

    row("multi-region", "create two factories — no config clash")
    us = AWSClientFactory(region="us-east-1", mock=True)
    eu = AWSClientFactory(region="eu-west-1",  mock=True)
    ok(f"us={us}  eu={eu}")

    insight(
        "Functional: s3_upload(), sqs_send() — flat namespace, one global config.\n"
        "  OOP: aws.s3.upload(), aws.sqs.send() — namespaced, multi-region safe."
    )


# =========================================================================
# SUMMARY
# =========================================================================
def summary():
    title("SHARED LIBRARY COMPARISON SUMMARY")
    print(f"""
  {'Aspect':<26} {'Functional':<34} {'OOP'}
  {'-'*26} {'-'*34} {'-'*32}
  {'Config storage':<26} {'Module-level dict':<34} {'Constructor / instance vars'}
  {'Multiple instances':<26} {'name= string key (typo-prone)':<34} {'Multiple objects'}
  {'Singleton guarantee':<26} {'Module import cached per process':<34} {'Double-checked lock (explicit)'}
  {'bind() / context fields':<26} {'Mutates global _state (all callers)':<34} {'Returns isolated BoundLogger'}
  {'Connection lifecycle':<26} {'connect() / disconnect_all()':<34} {'with DatabaseConnection() as db:'}
  {'Read-only DB':<26} {'Opt-in per call site':<34} {'ReadOnlyConnection subclass'}
  {'Connection pool':<26} {'Not natural to express as state':<34} {'ConnectionPool (queue.Queue)'}
  {'AWS multi-region':<26} {'configure() resets global config':<34} {'One factory per region'}
  {'Add a new AWS service':<26} {'New set of fn_aws.xyz_*()':<34} {'New class extending AWSClient'}
  {'Test isolation':<26} {'Patch module globals':<34} {'Inject a different object'}
  {'':<26} {'(state leaks between tests)':<34} {'(fully isolated)'}
    """)


# =========================================================================
if __name__ == "__main__":
    demo_logger()
    demo_db()
    demo_aws()
    summary()
    print(f"{BOLD}{GREEN}  All shared_lib demos completed successfully.{RESET}\n")

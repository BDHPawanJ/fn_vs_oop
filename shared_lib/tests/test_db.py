"""Tests — Database: functional vs OOP produce same results, different ownership."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

import pytest
import shared_lib.functional.db as fn_db
from shared_lib.oop.db import DatabaseConnection, ReadOnlyConnection, ConnectionPool
from shared_lib.oop.logger import Logger

DDL  = "CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT, qty INTEGER)"
SEED = "INSERT INTO items (name, qty) VALUES (?, ?)"
ROWS = [("Apple", 10), ("Bread", 5), ("Milk", 8)]


# ── Functional ────────────────────────────────────────────────────────────

def setup_function():
    fn_db.disconnect_all()


def test_fn_connect_and_health_check():
    fn_db.connect(dsn=":memory:", name="t")
    assert fn_db.health_check("t") is True
    fn_db.disconnect("t")


def test_fn_missing_connection_raises():
    with pytest.raises(RuntimeError, match="no connection"):
        fn_db.query("SELECT 1", name="missing")


def test_fn_execute_and_query():
    fn_db.connect(dsn=":memory:", name="t")
    fn_db.execute(DDL, name="t")
    fn_db.execute_many(SEED, ROWS, name="t")
    rows = fn_db.query("SELECT * FROM items ORDER BY name", name="t")
    assert len(rows) == 3
    assert rows[0]["name"] == "Apple"


def test_fn_execute_returns_rowcount():
    fn_db.connect(dsn=":memory:", name="t")
    fn_db.execute(DDL, name="t")
    count = fn_db.execute(SEED, ("Widget", 3), name="t")
    assert count == 1


def test_fn_transaction_commits():
    fn_db.connect(dsn=":memory:", name="t")
    fn_db.execute(DDL, name="t")
    with fn_db.transaction("t") as conn:
        conn.execute(SEED, ("Cherry", 20))
    rows = fn_db.query("SELECT COUNT(*) AS n FROM items", name="t")
    assert rows[0]["n"] == 1


def test_fn_transaction_rolls_back_on_error():
    fn_db.connect(dsn=":memory:", name="t")
    fn_db.execute(DDL, name="t")
    fn_db.execute(SEED, ("Cherry", 20), name="t")
    try:
        with fn_db.transaction("t") as conn:
            conn.execute(SEED, ("Grape", 5))
            raise RuntimeError("abort")
    except RuntimeError:
        pass
    rows = fn_db.query("SELECT COUNT(*) AS n FROM items", name="t")
    assert rows[0]["n"] == 1


def test_fn_disconnect_all():
    fn_db.connect(dsn=":memory:", name="a")
    fn_db.connect(dsn=":memory:", name="b")
    fn_db.disconnect_all()
    assert fn_db._connections == {}


# ── OOP ───────────────────────────────────────────────────────────────────

def test_oop_connect_and_health_check():
    Logger.reset()
    with DatabaseConnection(dsn=":memory:", name="t") as db:
        assert db.health_check() is True


def test_oop_context_manager_closes():
    Logger.reset()
    db = DatabaseConnection(dsn=":memory:", name="t")
    db.connect()
    assert db._conn is not None
    db.close()
    assert db._conn is None


def test_oop_query_not_connected_raises():
    Logger.reset()
    db = DatabaseConnection(dsn=":memory:", name="t")
    with pytest.raises(RuntimeError):
        db.query("SELECT 1")


def test_oop_execute_and_query():
    Logger.reset()
    with DatabaseConnection(dsn=":memory:", name="t") as db:
        db.execute(DDL)
        db.execute_many(SEED, ROWS)
        rows = db.query("SELECT * FROM items ORDER BY name")
        assert len(rows) == 3
        assert rows[0]["name"] == "Apple"


def test_oop_transaction_commits():
    Logger.reset()
    with DatabaseConnection(dsn=":memory:", name="t") as db:
        db.execute(DDL)
        with db.transaction():
            db.execute(SEED, ("Cherry", 20))
        rows = db.query("SELECT COUNT(*) AS n FROM items")
        assert rows[0]["n"] == 1


def test_oop_transaction_rolls_back():
    Logger.reset()
    with DatabaseConnection(dsn=":memory:", name="t") as db:
        db.execute(DDL)
        db.execute(SEED, ("Cherry", 20))
        try:
            with db.transaction() as conn:
                conn.execute(SEED, ("Grape", 5))
                raise RuntimeError("abort")
        except RuntimeError:
            pass
        rows = db.query("SELECT COUNT(*) AS n FROM items")
        assert rows[0]["n"] == 1


def test_oop_read_only_blocks_insert():
    Logger.reset()
    with ReadOnlyConnection(dsn=":memory:", name="ro") as ro:
        with pytest.raises(PermissionError, match="INSERT"):
            ro.execute("INSERT INTO items (name, qty) VALUES (?, ?)", ("X", 1))


def test_oop_read_only_blocks_delete():
    Logger.reset()
    with ReadOnlyConnection(dsn=":memory:", name="ro") as ro:
        with pytest.raises(PermissionError, match="DELETE"):
            ro.execute("DELETE FROM items WHERE id = 1")


def test_oop_pool_acquire_and_release():
    Logger.reset()
    pool = ConnectionPool(dsn=":memory:", size=2)
    pool.initialise()
    with pool.acquire() as conn:
        conn.execute("CREATE TABLE t (x INTEGER)")
        conn.execute("INSERT INTO t VALUES (?)", (99,))
        rows = conn.query("SELECT * FROM t")
        assert rows[0]["x"] == 99
    assert pool._pool.qsize() == 2
    pool.close_all()


def test_oop_pool_timeout_raises():
    Logger.reset()
    pool = ConnectionPool(dsn=":memory:", size=1)
    pool.initialise()
    with pool.acquire():
        with pytest.raises(RuntimeError, match="no connection"):
            with pool.acquire(timeout=0.1):
                pass
    pool.close_all()


# ── Comparison ────────────────────────────────────────────────────────────

def test_both_produce_same_query_results():
    Logger.reset()
    fn_db.disconnect_all()

    fn_db.connect(dsn=":memory:", name="cmp")
    fn_db.execute(DDL, name="cmp")
    fn_db.execute_many(SEED, ROWS, name="cmp")
    fn_rows = fn_db.query("SELECT name FROM items ORDER BY name", name="cmp")

    with DatabaseConnection(dsn=":memory:", name="cmp") as db:
        db.execute(DDL)
        db.execute_many(SEED, ROWS)
        oop_rows = db.query("SELECT name FROM items ORDER BY name")

    assert [r["name"] for r in fn_rows] == [r["name"] for r in oop_rows]

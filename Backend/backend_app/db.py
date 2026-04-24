from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import resolve_db_path
from .seed import CARD_PRODUCTS, DEFAULT_HISTORY_RENTALS, DEFAULT_USERS, USER_PRICE_CONFIGS, build_cabinets


_db_path: Path = resolve_db_path()


def dict_factory(cursor: sqlite3.Cursor, row: tuple) -> dict:
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def configure_database(db_path: str | Path | None = None) -> None:
    global _db_path
    _db_path = Path(db_path) if db_path else resolve_db_path()


def get_database_path() -> Path:
    return _db_path


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_database_path(), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connection_scope() -> sqlite3.Connection:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaction() -> sqlite3.Connection:
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connection_scope() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS card_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_type TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                cabinet_desc TEXT NOT NULL,
                vram TEXT NOT NULL,
                cpu TEXT NOT NULL,
                memory TEXT NOT NULL,
                display_price TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS user_price_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_type TEXT NOT NULL,
                cabinet_type TEXT NOT NULL,
                hourly_user_price REAL NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(card_type, cabinet_type)
            );

            CREATE TABLE IF NOT EXISTS cabinets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cabinet_code TEXT NOT NULL UNIQUE,
                location TEXT NOT NULL,
                card_type TEXT NOT NULL,
                cabinet_type TEXT NOT NULL,
                capacity_cards INTEGER NOT NULL,
                day_hourly_power_cost REAL NOT NULL,
                night_hourly_power_cost REAL NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('available', 'rented', 'offline'))
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                phone TEXT,
                nickname TEXT NOT NULL,
                avatar_url TEXT,
                balance REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'disabled')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS user_balance_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                balance_after REAL NOT NULL,
                reference_type TEXT,
                reference_id INTEGER,
                remark TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'revoked')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_used_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS rentals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                card_type TEXT NOT NULL,
                cabinet_type TEXT NOT NULL,
                cabinet_count INTEGER NOT NULL,
                timeslot TEXT NOT NULL CHECK(timeslot IN ('day', 'night')),
                started_at TEXT NOT NULL,
                ended_at TEXT,
                duration_seconds INTEGER,
                hourly_user_price_total REAL NOT NULL,
                hourly_power_cost_total REAL NOT NULL,
                user_total_amount REAL,
                power_cost_total REAL,
                status TEXT NOT NULL CHECK(status IN ('active', 'cancelled')),
                ip TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rental_allocations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rental_id INTEGER NOT NULL,
                cabinet_id INTEGER NOT NULL,
                hourly_user_price REAL NOT NULL,
                hourly_power_cost REAL NOT NULL,
                FOREIGN KEY(rental_id) REFERENCES rentals(id) ON DELETE CASCADE,
                FOREIGN KEY(cabinet_id) REFERENCES cabinets(id) ON DELETE CASCADE
            );
            """
        )
        _migrate_schema(conn)
        _seed_if_empty(conn)
        conn.commit()


def _migrate_schema(conn: sqlite3.Connection) -> None:
    _ensure_column(conn, "rentals", "user_id", "INTEGER")


def _ensure_column(conn: sqlite3.Connection, table_name: str, column_name: str, column_sql: str) -> None:
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name in columns:
        return
    conn.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    table_records = {
        "card_products": CARD_PRODUCTS,
        "user_price_configs": USER_PRICE_CONFIGS,
        "cabinets": build_cabinets(),
    }
    for table_name, records in table_records.items():
        if _table_count(conn, table_name):
            continue
        if table_name == "card_products":
            conn.executemany(
                """
                INSERT INTO card_products (
                    card_type, title, cabinet_desc, vram, cpu, memory, display_price
                ) VALUES (
                    :card_type, :title, :cabinet_desc, :vram, :cpu, :memory, :display_price
                )
                """,
                records,
            )
        elif table_name == "user_price_configs":
            conn.executemany(
                """
                INSERT INTO user_price_configs (
                    card_type, cabinet_type, hourly_user_price, enabled
                ) VALUES (
                    :card_type, :cabinet_type, :hourly_user_price, :enabled
                )
                """,
                records,
            )
        else:
            conn.executemany(
                """
                INSERT INTO cabinets (
                    cabinet_code, location, card_type, cabinet_type, capacity_cards,
                    day_hourly_power_cost, night_hourly_power_cost, status
                ) VALUES (
                    :cabinet_code, :location, :card_type, :cabinet_type, :capacity_cards,
                    :day_hourly_power_cost, :night_hourly_power_cost, :status
                )
                """,
                records,
            )

    _seed_users(conn)
    _seed_history_rentals(conn)


def _table_count(conn: sqlite3.Connection, table_name: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()["count"])


def _seed_users(conn: sqlite3.Connection) -> None:
    if _table_count(conn, "users"):
        return

    conn.executemany(
        """
        INSERT INTO users (
            username, password_hash, phone, nickname, avatar_url, balance, status
        ) VALUES (
            :username, :password_hash, :phone, :nickname, :avatar_url, :balance, :status
        )
        """,
        DEFAULT_USERS,
    )

    default_user = conn.execute(
        "SELECT id, balance FROM users WHERE username = ?",
        (DEFAULT_USERS[0]["username"],),
    ).fetchone()
    if not default_user:
        return

    conn.execute(
        """
        INSERT INTO user_balance_transactions (
            user_id, type, amount, balance_after, reference_type, reference_id, remark
        ) VALUES (?, 'recharge', ?, ?, 'seed', NULL, ?)
        """,
        (
            default_user["id"],
            float(default_user["balance"]),
            float(default_user["balance"]),
            "初始化演示余额",
        ),
    )


def _seed_history_rentals(conn: sqlite3.Connection) -> None:
    default_user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (DEFAULT_USERS[0]["username"],),
    ).fetchone()
    if not default_user:
        return

    existing = conn.execute(
        "SELECT COUNT(*) AS count FROM rentals WHERE user_id = ? AND status = 'cancelled'",
        (default_user["id"],),
    ).fetchone()["count"]
    if existing:
        return

    conn.executemany(
        """
        INSERT INTO rentals (
            user_id,
            card_type,
            cabinet_type,
            cabinet_count,
            timeslot,
            started_at,
            ended_at,
            duration_seconds,
            hourly_user_price_total,
            hourly_power_cost_total,
            user_total_amount,
            power_cost_total,
            status,
            ip,
            password
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                default_user["id"],
                item["card_type"],
                item["cabinet_type"],
                item["cabinet_count"],
                item["timeslot"],
                item["started_at"],
                item["ended_at"],
                item["duration_seconds"],
                item["hourly_user_price_total"],
                item["hourly_power_cost_total"],
                item["user_total_amount"],
                item["power_cost_total"],
                item["status"],
                item["ip"],
                item["password"],
            )
            for item in DEFAULT_HISTORY_RENTALS
        ],
    )

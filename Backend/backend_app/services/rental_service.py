from __future__ import annotations

from ..config import FIXED_CONNECTION
from ..db import connection_scope, transaction
from ..errors import AppError
from ..utils import card_label, now_iso, parse_iso, round2


def _get_user_price(conn, card_type: str, cabinet_type: str) -> float:
    row = conn.execute(
        """
        SELECT hourly_user_price
        FROM user_price_configs
        WHERE card_type = ? AND cabinet_type = ? AND enabled = 1
        """,
        (card_type, cabinet_type),
    ).fetchone()
    if not row:
        raise AppError("USER_PRICE_CONFIG_NOT_FOUND", "未找到对应的用户租赁价格配置", 400)
    return float(row["hourly_user_price"])


def _serialize_allocation(row: dict) -> dict:
    return {
        "cabinet_code": row["cabinet_code"],
        "location": row["location"],
        "cabinet_type": row["cabinet_type"],
        "capacity_cards": row["capacity_cards"],
        "hourly_user_price": round2(row["hourly_user_price"]),
        "hourly_power_cost": round2(row["hourly_power_cost"]),
    }


def fetch_rental_detail(conn, rental_id: int, user_id: int | None = None) -> dict | None:
    if user_id is None:
        rental = conn.execute("SELECT * FROM rentals WHERE id = ?", (rental_id,)).fetchone()
    else:
        rental = conn.execute(
            "SELECT * FROM rentals WHERE id = ? AND user_id = ?",
            (rental_id, user_id),
        ).fetchone()
    if not rental:
        return None

    allocations = conn.execute(
        """
        SELECT
            ra.hourly_user_price,
            ra.hourly_power_cost,
            c.cabinet_code,
            c.location,
            c.cabinet_type,
            c.capacity_cards
        FROM rental_allocations ra
        JOIN cabinets c ON c.id = ra.cabinet_id
        WHERE ra.rental_id = ?
        ORDER BY c.cabinet_code ASC
        """,
        (rental_id,),
    ).fetchall()
    return {
        "success": True,
        "rental_id": rental["id"],
        "user_id": rental["user_id"],
        "card_type": rental["card_type"],
        "card_label": card_label(rental["card_type"], rental["cabinet_type"]),
        "cabinet_type": rental["cabinet_type"],
        "cabinet_count": rental["cabinet_count"],
        "timeslot": rental["timeslot"],
        "status": rental["status"],
        "started_at": rental["started_at"],
        "ended_at": rental["ended_at"],
        "duration_seconds": rental["duration_seconds"],
        "hourly_user_price_total": round2(rental["hourly_user_price_total"]),
        "hourly_power_cost_total": round2(rental["hourly_power_cost_total"]),
        "user_total_amount": round2(rental["user_total_amount"]),
        "power_cost_total": round2(rental["power_cost_total"]),
        "allocations": [_serialize_allocation(row) for row in allocations],
        "connection": FIXED_CONNECTION,
    }


def get_rental(rental_id: int, user_id: int) -> dict:
    with connection_scope() as conn:
        detail = fetch_rental_detail(conn, rental_id, user_id=user_id)
        if detail is None:
            raise AppError("RENTAL_NOT_FOUND", "租单不存在", 404)
        return detail


def create_rental(
    user_id: int,
    card_type: str,
    cabinet_type: str,
    cabinet_count: int,
    timeslot: str,
) -> dict:
    if timeslot not in {"day", "night"}:
        raise AppError("INVALID_TIMESLOT", "timeslot 只能为 day 或 night", 400)

    cost_column = "day_hourly_power_cost" if timeslot == "day" else "night_hourly_power_cost"
    started_at = now_iso()

    with transaction() as conn:
        hourly_user_price = _get_user_price(conn, card_type, cabinet_type)
        candidate_rows = conn.execute(
            f"""
            SELECT *
            FROM cabinets
            WHERE card_type = ? AND cabinet_type = ? AND status = 'available'
            ORDER BY {cost_column} ASC, cabinet_code ASC
            """,
            (card_type, cabinet_type),
        ).fetchall()

        if len(candidate_rows) < cabinet_count:
            raise AppError("NO_AVAILABLE_CABINETS", "当前时段该卡型可租机柜数量不足", 409)

        selected = candidate_rows[:cabinet_count]
        hourly_power_cost_total = sum(float(row[cost_column]) for row in selected)
        hourly_user_price_total = hourly_user_price * cabinet_count

        cursor = conn.execute(
            """
            INSERT INTO rentals (
                user_id, card_type, cabinet_type, cabinet_count, timeslot,
                started_at, ended_at, duration_seconds,
                hourly_user_price_total, hourly_power_cost_total,
                user_total_amount, power_cost_total,
                status, ip, password
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, NULL, NULL, 'active', ?, ?)
            """,
            (
                user_id,
                card_type,
                cabinet_type,
                cabinet_count,
                timeslot,
                started_at,
                hourly_user_price_total,
                hourly_power_cost_total,
                FIXED_CONNECTION["ip"],
                FIXED_CONNECTION["password"],
            ),
        )
        rental_id = cursor.lastrowid

        for row in selected:
            conn.execute(
                """
                INSERT INTO rental_allocations (
                    rental_id, cabinet_id, hourly_user_price, hourly_power_cost
                ) VALUES (?, ?, ?, ?)
                """,
                (rental_id, row["id"], hourly_user_price, float(row[cost_column])),
            )
            conn.execute("UPDATE cabinets SET status = 'rented' WHERE id = ?", (row["id"],))

        detail = fetch_rental_detail(conn, rental_id, user_id=user_id)
        if detail is None:
            raise AppError("RENTAL_CREATE_FAILED", "租单创建失败", 500)
        return detail


def cancel_rental(rental_id: int, user_id: int) -> dict:
    with transaction() as conn:
        rental = conn.execute(
            "SELECT * FROM rentals WHERE id = ? AND user_id = ?",
            (rental_id, user_id),
        ).fetchone()
        if not rental:
            raise AppError("RENTAL_NOT_FOUND", "租单不存在", 404)

        if rental["status"] == "cancelled":
            return {
                "success": True,
                "rental_id": rental["id"],
                "status": "cancelled",
                "started_at": rental["started_at"],
                "ended_at": rental["ended_at"],
                "duration_seconds": rental["duration_seconds"],
                "hourly_user_price_total": round2(rental["hourly_user_price_total"]),
                "hourly_power_cost_total": round2(rental["hourly_power_cost_total"]),
                "user_total_amount": round2(rental["user_total_amount"]),
                "power_cost_total": round2(rental["power_cost_total"]),
            }

        ended_at = now_iso()
        started_dt = parse_iso(rental["started_at"])
        ended_dt = parse_iso(ended_at)
        if started_dt is None or ended_dt is None:
            raise AppError("INVALID_RENTAL_TIMESTAMPS", "租单时间戳无效", 500)

        duration_seconds = max(0, int((ended_dt - started_dt).total_seconds()))
        user_total_amount = float(rental["hourly_user_price_total"]) * duration_seconds / 3600
        power_cost_total = float(rental["hourly_power_cost_total"]) * duration_seconds / 3600

        conn.execute(
            """
            UPDATE rentals
            SET ended_at = ?, duration_seconds = ?, user_total_amount = ?, power_cost_total = ?, status = 'cancelled'
            WHERE id = ?
            """,
            (ended_at, duration_seconds, round2(user_total_amount), round2(power_cost_total), rental_id),
        )
        conn.execute(
            """
            UPDATE cabinets
            SET status = 'available'
            WHERE id IN (SELECT cabinet_id FROM rental_allocations WHERE rental_id = ?)
            """,
            (rental_id,),
        )
        updated = conn.execute("SELECT * FROM rentals WHERE id = ?", (rental_id,)).fetchone()
        return {
            "success": True,
            "rental_id": updated["id"],
            "status": "cancelled",
            "started_at": updated["started_at"],
            "ended_at": updated["ended_at"],
            "duration_seconds": updated["duration_seconds"],
            "hourly_user_price_total": round2(updated["hourly_user_price_total"]),
            "hourly_power_cost_total": round2(updated["hourly_power_cost_total"]),
            "user_total_amount": round2(updated["user_total_amount"]),
            "power_cost_total": round2(updated["power_cost_total"]),
        }

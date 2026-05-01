from __future__ import annotations

from ..config import FIXED_CONNECTION
from ..db import connection_scope, transaction
from ..errors import AppError
from ..seed import get_hourly_user_price_total
from ..utils import card_label, cabinet_status_from_active_cards, now_iso, parse_iso, resolve_timeslot, round2


def _serialize_allocation(row: dict) -> dict:
    return {
        "cabinet_code": row["cabinet_code"],
        "location": row["location"],
        "cabinet_type": row["cabinet_type"],
        "capacity_cards": row["capacity_cards"],
        "allocated_cards": row["allocated_cards"],
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
            ra.allocated_cards,
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
        "card_count": rental["card_count"],
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
    card_count: int,
) -> dict:
    started_at = now_iso()
    current_pricing_period = resolve_timeslot(parse_iso(started_at))
    cost_column = "day_hourly_power_cost" if current_pricing_period == "day" else "night_hourly_power_cost"

    with transaction() as conn:
        try:
            hourly_user_price_total = get_hourly_user_price_total(card_type, cabinet_type, card_count)
        except ValueError as exc:
            raise AppError("USER_PRICE_CONFIG_NOT_FOUND", str(exc), 400) from exc

        lock_clause = " FOR UPDATE SKIP LOCKED" if conn.backend == "postgres" else ""
        candidate_rows = conn.execute(
            f"""
            SELECT *,
                ({cost_column} * 1.0 / capacity_cards) AS unit_power_cost,
                (capacity_cards - active_card_count) AS available_cards
            FROM cabinets
            WHERE card_type = ? AND cabinet_type = ? AND status IN ('available', 'offline')
              AND active_card_count < capacity_cards
            ORDER BY
                ({cost_column} * 1.0 / capacity_cards) ASC,
                CASE status WHEN 'available' THEN 1 WHEN 'offline' THEN 2 ELSE 3 END,
                active_card_count DESC,
                cabinet_code ASC
            {lock_clause}
            """,
            (card_type, cabinet_type),
        ).fetchall()

        if sum(int(row["available_cards"]) for row in candidate_rows) < card_count:
            raise AppError("NO_AVAILABLE_CARDS", "当前时段该卡型可租卡数不足", 409)

        remaining_cards = card_count
        selected: list[dict] = []
        hourly_power_cost_total = 0.0
        for row in candidate_rows:
            if remaining_cards <= 0:
                break
            allocated_cards = min(remaining_cards, int(row["available_cards"]))
            if allocated_cards <= 0:
                continue
            allocation_power_cost = float(row["unit_power_cost"]) * allocated_cards
            selected.append(
                {
                    **row,
                    "allocated_cards": allocated_cards,
                    "allocation_power_cost": allocation_power_cost,
                }
            )
            hourly_power_cost_total += allocation_power_cost
            remaining_cards -= allocated_cards

        unit_user_price = hourly_user_price_total / card_count

        rental_id = conn.execute_insert(
            """
            INSERT INTO rentals (
                user_id, card_type, cabinet_type, cabinet_count, card_count,
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
                len(selected),
                card_count,
                started_at,
                hourly_user_price_total,
                hourly_power_cost_total,
                FIXED_CONNECTION["ip"],
                FIXED_CONNECTION["password"],
            ),
        )

        remaining_user_price = hourly_user_price_total
        for index, row in enumerate(selected):
            allocation_user_price = (
                remaining_user_price
                if index == len(selected) - 1
                else round2(unit_user_price * row["allocated_cards"])
            )
            remaining_user_price -= allocation_user_price
            conn.execute(
                """
                INSERT INTO rental_allocations (
                    rental_id, cabinet_id, allocated_cards, hourly_user_price, hourly_power_cost
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    rental_id,
                    row["id"],
                    row["allocated_cards"],
                    round2(allocation_user_price),
                    round2(row["allocation_power_cost"]),
                ),
            )
            updated_active_card_count = int(row["active_card_count"]) + int(row["allocated_cards"])
            conn.execute(
                "UPDATE cabinets SET active_card_count = ?, status = ?, last_idle_at = NULL WHERE id = ?",
                (
                    updated_active_card_count,
                    cabinet_status_from_active_cards(updated_active_card_count, int(row["capacity_cards"])),
                    row["id"],
                ),
            )

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
            SET
                active_card_count = CASE
                    WHEN active_card_count - COALESCE(
                        (
                            SELECT allocated_cards
                            FROM rental_allocations
                            WHERE rental_id = ? AND cabinet_id = cabinets.id
                        ),
                        0
                    ) < 0 THEN 0
                    ELSE active_card_count - COALESCE(
                        (
                            SELECT allocated_cards
                            FROM rental_allocations
                            WHERE rental_id = ? AND cabinet_id = cabinets.id
                        ),
                        0
                    )
                END
            WHERE id IN (SELECT cabinet_id FROM rental_allocations WHERE rental_id = ?)
            """,
            (rental_id, rental_id, rental_id),
        )
        rows = conn.execute(
            """
            SELECT id, active_card_count, capacity_cards
            FROM cabinets
            WHERE id IN (SELECT cabinet_id FROM rental_allocations WHERE rental_id = ?)
            """,
            (rental_id,),
        ).fetchall()
        for row in rows:
            conn.execute(
                "UPDATE cabinets SET status = ?, last_idle_at = NULL WHERE id = ?",
                (
                    cabinet_status_from_active_cards(int(row["active_card_count"]), int(row["capacity_cards"])),
                    row["id"],
                ),
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

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend_app.db import configure_database, init_db, transaction
from backend_app.seed import build_cabinets


STATIC_COLUMNS = [
    "location",
    "card_type",
    "cabinet_type",
    "capacity_cards",
    "day_hourly_power_cost",
    "night_hourly_power_cost",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync the cabinets table with backend_app.seed.build_cabinets()."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to the database. Without this flag the script only prints a dry run.",
    )
    parser.add_argument(
        "--sync-status",
        action="store_true",
        help="Also update statuses for existing cabinets. By default existing statuses are preserved.",
    )
    return parser.parse_args()


def load_existing_cabinets(conn) -> dict[str, dict]:
    rows = conn.execute(
        """
        SELECT
            cabinet_code,
            location,
            card_type,
            cabinet_type,
            capacity_cards,
            day_hourly_power_cost,
            night_hourly_power_cost,
            status
        FROM cabinets
        """
    ).fetchall()
    return {row["cabinet_code"]: row for row in rows}


def changed_static_fields(existing: dict, seeded: dict) -> list[str]:
    return [
        column
        for column in STATIC_COLUMNS
        if existing[column] != seeded[column]
    ]


def sync_cabinets(apply: bool, sync_status: bool) -> None:
    configure_database()
    init_db()

    seeded_cabinets = build_cabinets()

    with transaction() as conn:
        existing_by_code = load_existing_cabinets(conn)

        to_insert = [
            cabinet
            for cabinet in seeded_cabinets
            if cabinet["cabinet_code"] not in existing_by_code
        ]
        to_update = [
            cabinet
            for cabinet in seeded_cabinets
            if cabinet["cabinet_code"] in existing_by_code
            and (
                changed_static_fields(existing_by_code[cabinet["cabinet_code"]], cabinet)
                or (
                    sync_status
                    and existing_by_code[cabinet["cabinet_code"]]["status"] != cabinet["status"]
                )
            )
        ]

        print(f"Seed cabinets: {len(seeded_cabinets)}")
        print(f"Existing cabinets: {len(existing_by_code)}")
        print(f"Will insert: {len(to_insert)}")
        print(f"Will update existing rows: {len(to_update)}")
        if to_insert:
            print("Insert cabinet codes:")
            for cabinet in to_insert:
                print(f"  - {cabinet['cabinet_code']} ({cabinet['location']}, {cabinet['status']})")

        if not apply:
            print("Dry run only. Re-run with --apply to write changes.")
            conn.rollback()
            return

        for cabinet in to_insert:
            conn.execute(
                """
                INSERT INTO cabinets (
                    cabinet_code, location, card_type, cabinet_type, capacity_cards,
                    day_hourly_power_cost, night_hourly_power_cost, status
                ) VALUES (
                    :cabinet_code, :location, :card_type, :cabinet_type, :capacity_cards,
                    :day_hourly_power_cost, :night_hourly_power_cost, :status
                )
                """,
                cabinet,
            )

        for cabinet in to_update:
            status_sql = ", status = :status" if sync_status else ""
            conn.execute(
                f"""
                UPDATE cabinets
                SET
                    location = :location,
                    card_type = :card_type,
                    cabinet_type = :cabinet_type,
                    capacity_cards = :capacity_cards,
                    day_hourly_power_cost = :day_hourly_power_cost,
                    night_hourly_power_cost = :night_hourly_power_cost
                    {status_sql}
                WHERE cabinet_code = :cabinet_code
                """,
                cabinet,
            )

        print("Cabinet sync applied successfully.")


if __name__ == "__main__":
    args = parse_args()
    sync_cabinets(apply=args.apply, sync_status=args.sync_status)

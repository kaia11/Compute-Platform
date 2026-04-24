from __future__ import annotations

from ..db import connection_scope
from ..seed import LOCATION_EDGES, LOCATION_LAYOUTS


def get_locations_summary() -> dict:
    with connection_scope() as conn:
        location_rows = conn.execute(
            """
            SELECT
                location,
                COUNT(*) AS total_cabinets,
                SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) AS available_cabinets,
                SUM(CASE WHEN status = 'rented' THEN 1 ELSE 0 END) AS rented_cabinets,
                SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) AS offline_cabinets
            FROM cabinets
            GROUP BY location
            ORDER BY location ASC
            """
        ).fetchall()
        breakdown_rows = conn.execute(
            """
            SELECT
                location,
                card_type,
                cabinet_type,
                capacity_cards,
                COUNT(*) AS total_cabinets,
                SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) AS available_cabinets,
                SUM(CASE WHEN status = 'rented' THEN 1 ELSE 0 END) AS rented_cabinets,
                SUM(CASE WHEN status = 'offline' THEN 1 ELSE 0 END) AS offline_cabinets
            FROM cabinets
            GROUP BY location, card_type, cabinet_type, capacity_cards
            ORDER BY
                location ASC,
                CASE card_type WHEN '4090' THEN 1 WHEN '910B' THEN 2 WHEN '910C' THEN 3 ELSE 99 END,
                CASE cabinet_type WHEN '单卡机柜' THEN 1 WHEN '双卡机柜' THEN 2 WHEN '8卡机柜' THEN 3 WHEN '16卡机柜' THEN 4 ELSE 99 END
            """
        ).fetchall()

    breakdown_by_location: dict[str, list[dict]] = {}
    for row in breakdown_rows:
        breakdown_by_location.setdefault(row["location"], []).append(
            {
                "card_type": row["card_type"],
                "cabinet_type": row["cabinet_type"],
                "capacity_cards": row["capacity_cards"],
                "total_cabinets": row["total_cabinets"],
                "available_cabinets": row["available_cabinets"],
                "rented_cabinets": row["rented_cabinets"],
                "offline_cabinets": row["offline_cabinets"],
            }
        )

    items = []
    for row in location_rows:
        if row["available_cabinets"] > 0:
            node_status = "available"
        elif row["rented_cabinets"] > 0:
            node_status = "rented"
        else:
            node_status = "offline"
        layout = LOCATION_LAYOUTS.get(row["location"], {"x_ratio": 0.5, "y_ratio": 0.5})
        items.append(
            {
                "location": row["location"],
                "label": row["location"],
                "total_cabinets": row["total_cabinets"],
                "available_cabinets": row["available_cabinets"],
                "rented_cabinets": row["rented_cabinets"],
                "offline_cabinets": row["offline_cabinets"],
                "node_status": node_status,
                "x_ratio": layout["x_ratio"],
                "y_ratio": layout["y_ratio"],
                "cabinet_breakdown": breakdown_by_location.get(row["location"], []),
            }
        )
    return {"items": items, "edges": LOCATION_EDGES}

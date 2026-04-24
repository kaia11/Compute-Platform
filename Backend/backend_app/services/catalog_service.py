from __future__ import annotations

from ..db import connection_scope


def get_cards() -> dict:
    with connection_scope() as conn:
        items = conn.execute(
            """
            SELECT card_type, title, cabinet_desc, vram, cpu, memory, display_price
            FROM card_products
            ORDER BY CASE card_type WHEN '4090' THEN 1 WHEN '910B' THEN 2 WHEN '910C' THEN 3 ELSE 99 END
            """
        ).fetchall()
        return {"items": items}

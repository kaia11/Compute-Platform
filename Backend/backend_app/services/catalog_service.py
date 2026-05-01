from __future__ import annotations

from ..db import connection_scope
from ..seed import get_pricing_preview


def get_cards() -> dict:
    with connection_scope() as conn:
        items = conn.execute(
            """
            SELECT card_type, title, cabinet_desc, vram, cpu, memory, display_price
            FROM card_products
            ORDER BY CASE card_type WHEN '4090' THEN 1 WHEN '910B' THEN 2 WHEN '910C' THEN 3 ELSE 99 END
            """
        ).fetchall()
        result = []
        for item in items:
            if item["card_type"] == "4090":
                pricing_options = [
                    {"cabinet_type": "单卡机柜", "pricing_preview": get_pricing_preview("4090", "单卡机柜")},
                    {"cabinet_type": "双卡机柜", "pricing_preview": get_pricing_preview("4090", "双卡机柜")},
                ]
            else:
                pricing_options = [
                    {"cabinet_type": item["cabinet_desc"], "pricing_preview": get_pricing_preview(item["card_type"], item["cabinet_desc"])}
                ]
            result.append(
                {
                    **item,
                    "pricing_options": pricing_options,
                }
            )
        return {"items": result}

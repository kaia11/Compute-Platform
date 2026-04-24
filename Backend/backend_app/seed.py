from __future__ import annotations

from dataclasses import dataclass


LOCATION_LAYOUTS = {
    "位置1": {"x_ratio": 0.18, "y_ratio": 0.22},
    "位置2": {"x_ratio": 0.42, "y_ratio": 0.16},
    "位置3": {"x_ratio": 0.68, "y_ratio": 0.58},
    "位置4": {"x_ratio": 0.84, "y_ratio": 0.34},
}

LOCATION_EDGES = [
    {"from": "位置1", "to": "位置2"},
    {"from": "位置2", "to": "位置3"},
    {"from": "位置1", "to": "位置3"},
    {"from": "位置3", "to": "位置4"},
]

CARD_PRODUCTS = [
    {
        "card_type": "4090",
        "title": "4090",
        "cabinet_desc": "需选择单卡机柜或双卡机柜",
        "vram": "24G",
        "cpu": "16核",
        "memory": "64G",
        "display_price": "4.2元/小时起",
    },
    {
        "card_type": "910B",
        "title": "910B",
        "cabinet_desc": "8卡机柜",
        "vram": "32G",
        "cpu": "64核",
        "memory": "256G",
        "display_price": "21.6元/小时起",
    },
    {
        "card_type": "910C",
        "title": "910C",
        "cabinet_desc": "16卡机柜",
        "vram": "64G",
        "cpu": "128核",
        "memory": "512G",
        "display_price": "24.9元/小时起",
    },
]

USER_PRICE_CONFIGS = [
    {"card_type": "4090", "cabinet_type": "单卡机柜", "hourly_user_price": 12.0, "enabled": 1},
    {"card_type": "4090", "cabinet_type": "双卡机柜", "hourly_user_price": 22.0, "enabled": 1},
    {"card_type": "910B", "cabinet_type": "8卡机柜", "hourly_user_price": 48.0, "enabled": 1},
    {"card_type": "910C", "cabinet_type": "16卡机柜", "hourly_user_price": 66.0, "enabled": 1},
]

DEFAULT_USERS = [
    {
        "username": "gpu_user_001",
        "password_hash": "seeded-user-001:b605a16b1b2db6b1d53ddd872561dded825ffde7d5de9532146d5cbf2b638bd8",
        "phone": "15800000746",
        "nickname": "GPU User",
        "avatar_url": None,
        "balance": 286.40,
        "status": "active",
    }
]

DEFAULT_HISTORY_RENTALS = [
    {
        "card_type": "910C",
        "cabinet_type": "16卡机柜",
        "cabinet_count": 1,
        "timeslot": "day",
        "started_at": "2026-04-20T10:00:00+08:00",
        "ended_at": "2026-04-20T12:00:00+08:00",
        "duration_seconds": 7200,
        "hourly_user_price_total": 66.0,
        "hourly_power_cost_total": 29.8,
        "user_total_amount": 132.0,
        "power_cost_total": 59.6,
        "status": "cancelled",
        "ip": "192.168.0.100",
        "password": "123456",
    },
    {
        "card_type": "4090",
        "cabinet_type": "双卡机柜",
        "cabinet_count": 1,
        "timeslot": "night",
        "started_at": "2026-04-18T09:00:00+08:00",
        "ended_at": "2026-04-18T15:00:00+08:00",
        "duration_seconds": 21600,
        "hourly_user_price_total": 22.0,
        "hourly_power_cost_total": 8.4,
        "user_total_amount": 132.0,
        "power_cost_total": 50.4,
        "status": "cancelled",
        "ip": "192.168.0.100",
        "password": "123456",
    },
]


@dataclass(frozen=True)
class CabinetTemplate:
    location: str
    card_type: str
    cabinet_type: str
    capacity_cards: int
    quantity: int
    day_hourly_power_cost: float
    night_hourly_power_cost: float
    code_prefix: str


TEMPLATES = [
    CabinetTemplate("位置1", "4090", "单卡机柜", 1, 4, 5.0, 4.8, "P1-4090-S"),
    CabinetTemplate("位置1", "4090", "双卡机柜", 2, 3, 9.4, 9.0, "P1-4090-D"),
    CabinetTemplate("位置1", "910B", "8卡机柜", 8, 5, 24.0, 22.8, "P1-910B"),
    CabinetTemplate("位置1", "910C", "16卡机柜", 16, 2, 28.0, 26.0, "P1-910C"),
    CabinetTemplate("位置2", "4090", "单卡机柜", 1, 2, 5.4, 4.4, "P2-4090-S"),
    CabinetTemplate("位置2", "4090", "双卡机柜", 2, 5, 9.8, 8.6, "P2-4090-D"),
    CabinetTemplate("位置2", "910B", "8卡机柜", 8, 4, 25.2, 21.6, "P2-910B"),
    CabinetTemplate("位置2", "910C", "16卡机柜", 16, 3, 29.2, 24.9, "P2-910C"),
    CabinetTemplate("位置3", "4090", "单卡机柜", 1, 6, 4.9, 4.2, "P3-4090-S"),
    CabinetTemplate("位置3", "4090", "双卡机柜", 2, 2, 9.1, 8.4, "P3-4090-D"),
    CabinetTemplate("位置3", "910B", "8卡机柜", 8, 3, 24.6, 22.1, "P3-910B"),
    CabinetTemplate("位置3", "910C", "16卡机柜", 16, 4, 28.7, 25.4, "P3-910C"),
    CabinetTemplate("位置4", "4090", "单卡机柜", 1, 3, 5.7, 4.9, "P4-4090-S"),
    CabinetTemplate("位置4", "4090", "双卡机柜", 2, 4, 10.1, 8.8, "P4-4090-D"),
    CabinetTemplate("位置4", "910B", "8卡机柜", 8, 2, 25.6, 22.4, "P4-910B"),
    CabinetTemplate("位置4", "910C", "16卡机柜", 16, 5, 29.8, 25.2, "P4-910C"),
]

LOCATION_STATUS_PLANS = {
    "位置1": ["available"] * 7 + ["rented"] * 5 + ["offline"] * 2,
    "位置2": ["rented"] * 11 + ["offline"] * 3,
    "位置3": ["available"] * 5 + ["rented"] * 6 + ["offline"] * 4,
    "位置4": ["offline"] * 14,
}

STATUS_OVERRIDES = {
    "P1-910C-002": "available",
    "P3-910C-001": "available",
}


def build_cabinets() -> list[dict]:
    grouped: dict[str, list[dict]] = {location: [] for location in LOCATION_STATUS_PLANS}

    for template in TEMPLATES:
        for index in range(1, template.quantity + 1):
            grouped[template.location].append(
                {
                    "cabinet_code": f"{template.code_prefix}-{index:03d}",
                    "location": template.location,
                    "card_type": template.card_type,
                    "cabinet_type": template.cabinet_type,
                    "capacity_cards": template.capacity_cards,
                    "day_hourly_power_cost": template.day_hourly_power_cost,
                    "night_hourly_power_cost": template.night_hourly_power_cost,
                }
            )

    cabinets: list[dict] = []
    for location, items in grouped.items():
        statuses = LOCATION_STATUS_PLANS[location]
        if len(items) != len(statuses):
            raise ValueError(f"status plan mismatch for {location}")
        items.sort(key=lambda item: item["cabinet_code"])
        for item, status in zip(items, statuses, strict=True):
            cabinets.append({**item, "status": status})

    cabinets_by_code = {cabinet["cabinet_code"]: cabinet for cabinet in cabinets}
    for cabinet_code, forced_status in STATUS_OVERRIDES.items():
        current = cabinets_by_code[cabinet_code]
        if current["status"] == forced_status:
            continue
        swap_target = next(
            cabinet
            for cabinet in cabinets
            if cabinet["location"] == current["location"]
            and cabinet["status"] == forced_status
            and cabinet["cabinet_code"] not in STATUS_OVERRIDES
        )
        swap_target["status"], current["status"] = current["status"], forced_status
    return cabinets

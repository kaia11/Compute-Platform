from __future__ import annotations

from backend_app.db import connection_scope


def login_headers(client) -> dict:
    response = client.post(
        "/api/auth/login",
        json={"username": "gpu_user_001", "password": "123456"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_sample_rental(client, headers: dict) -> dict:
    response = client.post(
        "/api/rentals",
        headers=headers,
        json={
            "card_type": "4090",
            "cabinet_type": "单卡机柜",
            "cabinet_count": 2,
            "timeslot": "night",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    return data


def test_create_rental_requires_login(client):
    response = client.post(
        "/api/rentals",
        json={
            "card_type": "4090",
            "cabinet_type": "单卡机柜",
            "cabinet_count": 1,
            "timeslot": "night",
        },
    )

    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_create_rental_success(client):
    headers = login_headers(client)
    data = create_sample_rental(client, headers)

    assert data["status"] == "active"
    assert data["hourly_user_price_total"] == 24.0
    assert data["hourly_power_cost_total"] == 8.4
    assert len(data["allocations"]) == 2
    assert [item["cabinet_code"] for item in data["allocations"]] == [
        "P3-4090-S-001",
        "P3-4090-S-002",
    ]

    with connection_scope() as conn:
        rental = conn.execute("SELECT user_id FROM rentals WHERE id = ?", (data["rental_id"],)).fetchone()
        rented_count = conn.execute(
            "SELECT COUNT(*) AS count FROM cabinets WHERE status = 'rented'"
        ).fetchone()["count"]
    assert rental["user_id"] == 1
    assert rented_count >= 2


def test_get_rental_detail(client):
    headers = login_headers(client)
    created = create_sample_rental(client, headers)
    rental_id = created["rental_id"]

    response = client.get(f"/api/rentals/{rental_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["rental_id"] == rental_id
    assert data["status"] == "active"
    assert len(data["allocations"]) == 2


def test_create_rental_no_available_cabinets_returns_unified_error(client):
    headers = login_headers(client)
    response = client.post(
        "/api/rentals",
        headers=headers,
        json={
            "card_type": "910C",
            "cabinet_type": "16卡机柜",
            "cabinet_count": 3,
            "timeslot": "day",
        },
    )

    assert response.status_code == 409
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "NO_AVAILABLE_CABINETS"


def test_get_missing_rental_returns_unified_404(client):
    headers = login_headers(client)
    response = client.get("/api/rentals/99999", headers=headers)

    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RENTAL_NOT_FOUND"


def test_cancel_rental_releases_cabinets_and_computes_totals(client):
    headers = login_headers(client)
    created = create_sample_rental(client, headers)
    rental_id = created["rental_id"]
    codes = [item["cabinet_code"] for item in created["allocations"]]

    response = client.post(f"/api/rentals/{rental_id}/cancel", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "cancelled"
    assert data["duration_seconds"] >= 0
    assert data["hourly_user_price_total"] == 24.0
    assert data["hourly_power_cost_total"] == 8.4

    placeholders = ",".join("?" for _ in codes)
    with connection_scope() as conn:
        rows = conn.execute(
            f"SELECT cabinet_code, status FROM cabinets WHERE cabinet_code IN ({placeholders}) ORDER BY cabinet_code",
            codes,
        ).fetchall()
    assert [row["status"] for row in rows] == ["available", "available"]


def test_cancel_rental_is_idempotent(client):
    headers = login_headers(client)
    created = create_sample_rental(client, headers)
    rental_id = created["rental_id"]

    first = client.post(f"/api/rentals/{rental_id}/cancel", headers=headers)
    second = client.post(f"/api/rentals/{rental_id}/cancel", headers=headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "cancelled"
    assert second.json()["status"] == "cancelled"


def test_validation_error_uses_unified_shape(client):
    headers = login_headers(client)
    response = client.post(
        "/api/rentals",
        headers=headers,
        json={
            "card_type": "4090",
            "cabinet_type": "单卡机柜",
            "cabinet_count": 0,
            "timeslot": "night",
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"

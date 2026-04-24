from __future__ import annotations


def test_cards_returns_expected_items(client):
    response = client.get("/api/cards")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 3

    card_types = [item["card_type"] for item in data["items"]]
    assert card_types == ["4090", "910B", "910C"]

    first = data["items"][0]
    assert first["title"] == "4090"
    assert "display_price" in first

from fastapi import HTTPException

from src.services.dhl import DHLService


def test_root(client, clean_test_db):
    response = client.get("/")

    assert response.status_code == 200
    assert "service" in response.json()


def test_get_status_returns_normalized_status_and_persists(client, db_connection, clean_test_db, monkeypatch):
    tracking_id = "7777777770"
    dhl_payload = {
        "shipments": [
            {
                "status": {
                    "status": "TRANSIT",
                    "description": "The shipment is in transit",
                }
            }
        ]
    }

    async def fake_buscar_en_dhl(_: str):
        return dhl_payload

    monkeypatch.setattr(DHLService, "buscar_en_dhl", fake_buscar_en_dhl)

    response = client.get(f"/status/{tracking_id}")

    assert response.status_code == 200
    assert response.json() == {
        "tracking_id": tracking_id,
        "status": "TRANSIT",
        "description": "The shipment is in transit",
    }

    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_status, current_description FROM shipments WHERE tracking_id = %s",
            (tracking_id,),
        )
        row = cursor.fetchone()

    assert row is not None
    assert row["current_status"] == "TRANSIT"
    assert row["current_description"] == "The shipment is in transit"


def test_get_location_returns_normalized_location_and_persists(client, db_connection, clean_test_db, monkeypatch):
    tracking_id = "7777777770"
    dhl_payload = {
        "shipments": [
            {
                "status": {
                    "timestamp": "2024-04-16T09:30:00Z",
                    "location": {
                        "address": {
                            "addressLocality": "Madrid - Spain",
                            "countryCode": "ES",
                        }
                    },
                }
            }
        ]
    }

    async def fake_buscar_en_dhl(_: str):
        return dhl_payload

    monkeypatch.setattr(DHLService, "buscar_en_dhl", fake_buscar_en_dhl)

    response = client.get(f"/location/{tracking_id}")

    assert response.status_code == 200
    assert response.json() == {
        "tracking_id": tracking_id,
        "location": "Spain",
        "city": "Madrid",
        "timestamp": "2024-04-16T09:30:00Z",
    }

    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT location, city, timestamp FROM shipments WHERE tracking_id = %s",
            (tracking_id,),
        )
        row = cursor.fetchone()

    assert row is not None
    assert row["location"] == "Spain"
    assert row["city"] == "Madrid"
    assert row["timestamp"] == "2024-04-16T09:30:00Z"

def test_get_history_returns_normalized_history_and_persists(client, db_connection, clean_test_db, monkeypatch):
    tracking_id = "7777777770"
    dhl_payload = {
        "shipments": [
            {
                "events": [
                    {
                        "timestamp": "2024-04-15T08:00:00Z",
                        "status": {
                            "status": "PICKUP",
                            "description": "Shipment picked up",
                        },
                    },
                    {
                        "timestamp": "2024-04-16T09:30:00Z",
                        "status": {
                            "status": "TRANSIT",
                            "description": "The shipment is in transit",
                        },
                    },
                ]
            }
        ]
    }

    async def fake_buscar_en_dhl(_: str):
        return dhl_payload

    monkeypatch.setattr(DHLService, "buscar_en_dhl", fake_buscar_en_dhl)

    response = client.get(f"/history/{tracking_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["tracking_id"] == tracking_id
    assert len(data["events"]) == 2 

    with db_connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_status, current_description FROM shipments WHERE tracking_id = %s",
            (tracking_id,),
        )
        row = cursor.fetchone()

    assert row is not None
    assert row["current_status"] == "PICKUP"


def test_get_status_propagates_not_found(client, clean_test_db, monkeypatch):
    async def fake_buscar_en_dhl(_: str):
        raise HTTPException(status_code=404, detail="Guía no encontrada.")

    monkeypatch.setattr(DHLService, "buscar_en_dhl", fake_buscar_en_dhl)

    response = client.get("/status/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Guía no encontrada."}


def test_get_location_returns_422_for_invalid_dhl_structure(client, clean_test_db, monkeypatch):
    async def fake_buscar_en_dhl(_: str):
        return {"shipments": []}

    monkeypatch.setattr(DHLService, "buscar_en_dhl", fake_buscar_en_dhl)

    response = client.get("/location/7777777770")

    assert response.status_code == 422
    assert response.json() == {"detail": "Estructura de DHL inválida."}

def test_get_history_propagates_not_found(client, clean_test_db, monkeypatch):
    async def fake_buscar_en_dhl(_: str):
        raise HTTPException(status_code=404, detail="Guía no encontrada.")

    monkeypatch.setattr(DHLService, "buscar_en_dhl", fake_buscar_en_dhl)

    response = client.get("/history/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"detail": "Guía no encontrada."}
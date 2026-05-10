from fastapi import HTTPException

from src.services.dhl import DHLService


def test_root(client, clean_test_db):
    response = client.get("/")

    assert response.status_code == 200
    assert "service" in response.json()


def test_get_shipment_returns_normalized_status_and_persists(client, db_connection, clean_test_db, monkeypatch):
    with db_connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO users (id_user, email, hashed_password) VALUES (%s, %s, %s)",
            (1, "test@example.com", "fakehash")
        )
        cursor.execute(
            "INSERT INTO locations (id_location, country_code, city, latitude, longitude) "
            "VALUES (%s, %s, %s, %s, %s)",
            (1, "ES", "Madrid", 40.4167, -3.7033)
        )
        cursor.execute(
            "INSERT INTO locations (id_location, country_code, city, latitude, longitude) "
            "VALUES (%s, %s, %s, %s, %s)",
            (2, "ES", "Barcelona", 41.3851, 2.1734)
        )
    db_connection.commit()

    tracking_id = "7777777770"
    user_id = 1
    
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

    response = client.get(f"/status/{tracking_id}", params={"user_id": user_id})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "TRANSIT"

    with db_connection.cursor() as cursor:
        cursor.execute("SELECT dhl_id, status FROM shipments WHERE dhl_id = %s", (tracking_id,))
        result = cursor.fetchone()
        assert result is not None
        assert result["status"] == "TRANSIT"


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

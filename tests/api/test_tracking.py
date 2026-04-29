import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

# MOCKS DE RESPUESTA
MOCK_DHL_SUCCESS = {
    "shipments": [
        {
            "status": {
                "status": "DELIVERED",
                "description": "Shipment has been delivered"
            }
        }
    ]
}

def test_root(client):
    """Prueba que el root funcione."""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()

@patch("src.api.routes.tracking.DHLService.buscar_en_dhl", new_callable=AsyncMock)
def test_get_status_success(mock_buscar, client):
    """Prueba el éxito (200) simulando el servicio de DHL"""
    mock_buscar.return_value = MOCK_DHL_SUCCESS
    
    tracking_id = "7777777770"
    response = client.get(f"/status/{tracking_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["tracking_id"] == tracking_id
    assert data["status"] == "DELIVERED"
    assert data["description"] == "Shipment has been delivered"

@patch("src.api.routes.tracking.DHLService.buscar_en_dhl", new_callable=AsyncMock)
def test_get_status_unprocessable_entity(mock_buscar, client):
    """Prueba el error 422 cuando la estructura de datos es inválida"""
    mock_buscar.return_value = {"shipments": []}
    
    response = client.get("/status/12345")
    
    assert response.status_code == 422
    assert "Estructura de DHL inválida" in response.json()["detail"]


@patch("src.api.routes.tracking.DHLService.buscar_en_dhl", new_callable=AsyncMock)
def test_get_status_persists_shipment_status(mock_buscar, client, db_connection):
    """Guarda el estado normalizado del envío tras consultar DHL."""
    mock_buscar.return_value = MOCK_DHL_SUCCESS

    tracking_id = "7777777770"
    response = client.get(f"/status/{tracking_id}")

    assert response.status_code == 200

    row = db_connection.execute(
        """
        SELECT tracking_id, carrier, current_status, current_description
        FROM shipments
        WHERE tracking_id = ?
        """,
        (tracking_id,),
    ).fetchone()

    assert row is not None
    assert row["tracking_id"] == tracking_id
    assert row["carrier"] == "DHL"
    assert row["current_status"] == "DELIVERED"
    assert row["current_description"] == "Shipment has been delivered"


@patch("src.api.routes.tracking.DHLService.buscar_en_dhl", new_callable=AsyncMock)
def test_get_status_updates_existing_shipment(mock_buscar, client, db_connection):
    """Actualiza el mismo envío en lugar de duplicarlo."""
    tracking_id = "7777777770"
    mock_buscar.side_effect = [
        MOCK_DHL_SUCCESS,
        {
            "shipments": [
                {
                    "status": {
                        "status": "TRANSIT",
                        "description": "Shipment is moving again",
                    }
                }
            ]
        },
    ]

    first_response = client.get(f"/status/{tracking_id}")
    second_response = client.get(f"/status/{tracking_id}")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["status"] == "TRANSIT"

    count_row = db_connection.execute(
        "SELECT COUNT(*) AS total FROM shipments WHERE tracking_id = ?",
        (tracking_id,),
    ).fetchone()
    shipment_row = db_connection.execute(
        """
        SELECT current_status, current_description
        FROM shipments
        WHERE tracking_id = ?
        """,
        (tracking_id,),
    ).fetchone()

    assert count_row["total"] == 1
    assert shipment_row["current_status"] == "TRANSIT"
    assert shipment_row["current_description"] == "Shipment is moving again"

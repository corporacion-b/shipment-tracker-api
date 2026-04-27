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

@patch("src.api.routes.tracking.DHLService.buscar_en_dhl", new_callable=AsyncMock)
def test_get_status_unprocessable_entity(mock_buscar, client):
    """Prueba el error 422 cuando la estructura de datos es inválida"""
    mock_buscar.return_value = {"shipments": []}
    
    response = client.get("/status/12345")
    
    assert response.status_code == 422
    assert "Estructura de DHL inválida" in response.json()["detail"]
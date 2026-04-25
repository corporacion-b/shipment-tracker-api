import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import src 

client = TestClient(src)

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

MOCK_DHL_BAD_STRUCTURE = {"shipments": []}

# PRUEBAS
def test_root():
    """Prueba que el root funcione y detecte la carga de la API KEY"""
    response = client.get("/")
    assert response.status_code == 200
    assert "service" in response.json()

@patch("src.main.buscar_en_dhl", new_callable=AsyncMock)
def test_get_status_success(mock_buscar):
    """Prueba el éxito (200) simulando una respuesta de DHL"""
    mock_buscar.return_value = MOCK_DHL_SUCCESS
    
    tracking_id = "7777777770"
    response = client.get(f"/status/{tracking_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["tracking_id"] == tracking_id
    assert data["status"] == "DELIVERED"
    assert data["description"] == "Shipment has been delivered"

@patch("src.main.buscar_en_dhl", new_callable=AsyncMock)
def test_get_status_not_found(mock_buscar):
    """Prueba el error 404 cuando el paquete no existe"""
    from fastapi import HTTPException
    
    mock_buscar.side_effect = HTTPException(status_code=404, detail="No existe en DHL")
    
    response = client.get("/status/0000000000")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "No existe en DHL"

@patch("src.main.buscar_en_dhl", new_callable=AsyncMock)
def test_get_status_unprocessable_entity(mock_buscar):
    """Prueba el error 422 cuando DHL responde algo inesperado"""
    mock_buscar.return_value = MOCK_DHL_BAD_STRUCTURE
    
    response = client.get("/status/12345")
    
    assert response.status_code == 422
    assert "estructura de envío esperada" in response.json()["detail"]
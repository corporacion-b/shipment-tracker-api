import pytest
from fastapi.testclient import TestClient
from src.main import src

client = TestClient(src)
    
## 1. Prueba del Endpoint Raíz
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API de Rastreo con DB simulada."}

## 2. Prueba de Rastreo Exitoso (Caso Existente)
def test_get_status_success():
    tracking_id = "DHL-123"
    response = client.get(f"/status/{tracking_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["tracking_id"] == tracking_id
    assert data["status"] == "In Transit"
    assert "location" in data

## 3. Prueba de Error (ID no encontrado)
def test_get_status_not_found():
    tracking_id = "NON-EXISTENT-999"
    response = client.get(f"/status/{tracking_id}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Envío no encontrado en el sistema"

## 4. Prueba de Validación de Tipos (Opcional pero recomendada)
def test_get_status_data_types():
    response = client.get("/status/DHL-456")
    data = response.json()
    
    assert isinstance(data["days_stationary"], int)
    assert isinstance(data["status"], str)
import pytest
import httpx
from unittest.mock import patch
from src.services.dhl import DHLService
from fastapi import HTTPException

@pytest.mark.anyio
async def test_buscar_en_dhl_real_connection():
    """Usa la API real de DHL."""
    tracking_id = "1234567891" 
    try:
        resultado = await DHLService.buscar_en_dhl(tracking_id)
        assert "shipments" in resultado
    except HTTPException as e:
        pytest.fail(f"La conexión real falló (Revisa tus llaves en .env): {e.detail}")

@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
async def test_buscar_en_dhl_timeout_mock(mock_get):
    mock_get.side_effect = httpx.TimeoutException("Timeout")
    
    with pytest.raises(HTTPException) as excinfo:
        await DHLService.buscar_en_dhl("any_id")
    
    assert excinfo.value.status_code == 504

@pytest.mark.anyio
async def test_buscar_en_dhl_invalid_id_real():
    """Usa la API real con un ID falso."""
    tracking_id = "1234567892" 
    with pytest.raises(HTTPException) as excinfo:
        await DHLService.buscar_en_dhl(tracking_id)

    assert excinfo.value.status_code == 404
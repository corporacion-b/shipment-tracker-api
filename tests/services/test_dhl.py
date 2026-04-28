import pytest
import httpx
from unittest.mock import AsyncMock, patch
from src.services.dhl import DHLService
from fastapi import HTTPException

@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
async def test_buscar_en_dhl_timeout(mock_get):
    """Prueba que el servicio maneje correctamente un Timeout de la red."""
    mock_get.side_effect = httpx.TimeoutException("Timeout")
    
    with pytest.raises(HTTPException) as excinfo:
        await DHLService.buscar_en_dhl("12345")
    
    assert excinfo.value.status_code == 504
    assert "tardó demasiado" in excinfo.value.detail

@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
async def test_buscar_en_dhl_not_found(mock_get):
    """Prueba que el servicio maneje un 404 real de la API de DHL."""
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    with pytest.raises(HTTPException) as excinfo:
        await DHLService.buscar_en_dhl("000000")
        
    assert excinfo.value.status_code == 404
    assert "no existe" in excinfo.value.detail
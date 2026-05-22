from unittest.mock import Mock, patch

import httpx
import pytest
from fastapi import HTTPException

from src.services.dhl import DHLService


pytestmark = pytest.mark.unit


@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
async def test_buscar_en_dhl_timeout_returns_504(mock_get):
    mock_get.side_effect = httpx.TimeoutException("Timeout")

    with pytest.raises(HTTPException) as excinfo:
        await DHLService.buscar_en_dhl("any-id")

    assert excinfo.value.status_code == 504


@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
async def test_buscar_en_dhl_maps_404(mock_get):
    request = httpx.Request("GET", "https://api-eu.dhl.com/track/shipments")
    response = httpx.Response(404, request=request)
    mock_get.side_effect = httpx.HTTPStatusError(
        "Not found",
        request=request,
        response=response,
    )

    with pytest.raises(HTTPException) as excinfo:
        await DHLService.buscar_en_dhl("missing-id")

    assert excinfo.value.status_code == 404
    assert "missing-id" in excinfo.value.detail


@pytest.mark.anyio
@patch("httpx.AsyncClient.get")
async def test_buscar_en_dhl_returns_payload(mock_get):
    mock_response = Mock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"shipments": [{"id": "abc"}]}
    mock_get.return_value = mock_response

    result = await DHLService.buscar_en_dhl("abc")

    assert result == {"shipments": [{"id": "abc"}]}

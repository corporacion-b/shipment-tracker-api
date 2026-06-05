"""
Tests de contrato contra el mock DHL en Railway.

Validan que el mock responde con la estructura correcta que nuestra
API espera consumir. Se ejecutan con --run-external.

NOTA sobre el allowlist de IPs:
    El mock de Railway solo acepta peticiones desde IPs registradas.
    Desde GitHub Actions (IPs dinámicas) los tests harán SKIP automáticamente.
    Eso es comportamiento correcto — el CI no falla por esto.
    Para correrlos localmente necesitas tener tu IP registrada en el mock.
"""

import json
import os
import re

import httpx
import pytest


def _get_base_url() -> str:
    return os.environ.get(
        "DHL_BASE_URL",
        "https://shipment-tracker-mock-api-production.up.railway.app/track/shipments",
    )


def _get_api_key() -> str:
    key = os.environ.get("DHL_API_KEY", "")
    if re.fullmatch(r"[A-Za-z0-9]{32,}", key):
        return key
    return "1234567890ABCDEF1234567890ABCDEF"


def _get_tracking_ids() -> list[str]:
    """
    Lee los tracking IDs desde la variable de entorno DHL_MOCK_TRACKING_IDS.
    En GitHub Actions viene del secret DHL_TRACKING_IDS_OK.
    Acepta JSON array o lista separada por comas.
    Si no está definida, usa los IDs conocidos del mock.
    """
    raw = os.environ.get("DHL_MOCK_TRACKING_IDS", "")
    if raw:
        raw = raw.strip()
        try:
            ids = json.loads(raw)
            if isinstance(ids, list) and ids:
                return ids
        except json.JSONDecodeError:
            pass
        ids = [i.strip() for i in raw.split(",") if i.strip()]
        if ids:
            return ids

    # Fallback: IDs que sabemos que existen en el mock
    return [
        "7KQ4M9X2LA", "P8R3T6Z1BN", "H5W9C2V7QM", "L2N8Y4D6KP", "A9F3J7M1TX",
        "C6V2Q8R5ZS", "N4X7B1K9YD", "T1M5P8W3QJ", "Z7D2L6C9RV", "R4H8N1S5XB",
        "Q9Y3V7A2LM", "B5K1T6P8NC", "M8C4R2Z7QW", "D3P9X5H1VK", "Y6L2N8M4SA",
        "W1Z7Q3C6PT", "K8S4B9D2LX", "V5A1M7R3QN", "X2T6H8Y4BC", "S9Q5L1P7DZ",
    ]


def _call_mock(tracking_id: str) -> httpx.Response:
    """Llama al mock y maneja el rechazo por IP antes de cualquier assert."""
    response = httpx.get(
        _get_base_url(),
        params={"trackingNumber": tracking_id},
        headers={"DHL-API-Key": _get_api_key()},
        timeout=10.0,
    )

    if response.text.strip() == "Host not in allowlist":
        pytest.skip(
            "La IP de este runner no está en el allowlist del mock de Railway. "
            "Los tests de contrato se omiten automáticamente en este entorno. "
            "Para ejecutarlos, registra la IP en el mock o corre desde Railway."
        )

    if response.status_code == 404:
        try:
            if response.json().get("message") == "Application not found":
                pytest.skip("El mock de Railway no está disponible en este momento.")
        except Exception:
            pass

    if response.status_code == 403:
        pytest.skip("El mock de Railway rechazó esta IP/API key (403).")

    return response


def require_dict(value, field_name):
    assert isinstance(value, dict), f"{field_name} debe ser un objeto, got: {type(value)}"
    return value


def require_non_empty_list(value, field_name):
    assert isinstance(value, list), f"{field_name} debe ser una lista, got: {type(value)}"
    assert value, f"{field_name} no debe estar vacía"
    return value


@pytest.mark.contract
@pytest.mark.external
@pytest.mark.parametrize("tracking_id", _get_tracking_ids())
def test_dhl_mock_shipment_contract(tracking_id):
    """El mock debe devolver un shipment válido para cada tracking ID conocido."""
    response = _call_mock(tracking_id)

    assert response.status_code == 200, (
        f"Esperado 200, obtenido {response.status_code}. Body: {response.text[:300]}"
    )

    payload = response.json()
    shipments = require_non_empty_list(payload.get("shipments"), "shipments")
    shipment = require_dict(shipments[0], "shipments[0]")

    assert shipment.get("id") == tracking_id, (
        f"El ID del shipment '{shipment.get('id')}' no coincide con '{tracking_id}'"
    )

    origin = require_dict(shipment.get("origin"), "origin")
    destination = require_dict(shipment.get("destination"), "destination")
    status = require_dict(shipment.get("status"), "status")
    details = require_dict(shipment.get("details"), "details")
    events = require_non_empty_list(shipment.get("events"), "events")

    origin_addr = require_dict(origin.get("address"), "origin.address")
    dest_addr = require_dict(destination.get("address"), "destination.address")
    status_loc = require_dict(status.get("location"), "status.location")
    status_addr = require_dict(status_loc.get("address"), "status.location.address")
    weight = require_dict(details.get("weight"), "details.weight")

    assert origin_addr.get("addressLocality"), "origin.address.addressLocality vacío"
    assert origin_addr.get("countryCode"), "origin.address.countryCode vacío"
    assert dest_addr.get("addressLocality"), "destination.address.addressLocality vacío"
    assert dest_addr.get("countryCode"), "destination.address.countryCode vacío"
    assert status.get("timestamp"), "status.timestamp vacío"
    assert status.get("status"), "status.status vacío"
    assert status_addr.get("addressLocality"), "status.location.address.addressLocality vacío"
    assert status_addr.get("countryCode"), "status.location.address.countryCode vacío"
    assert isinstance(weight.get("value"), int | float), "details.weight.value debe ser numérico"

    first_event = require_dict(events[0], "events[0]")
    assert first_event.get("timestamp"), "events[0].timestamp vacío"
    assert first_event.get("status"), "events[0].status vacío"


@pytest.mark.contract
@pytest.mark.external
def test_dhl_mock_returns_404_for_unknown_id():
    """El mock debe devolver 404 para un tracking ID que no existe."""
    response = httpx.get(
        _get_base_url(),
        params={"trackingNumber": "ID_QUE_NO_EXISTE_XYZ"},
        headers={"DHL-API-Key": _get_api_key()},
        timeout=10.0,
    )

    if response.text.strip() == "Host not in allowlist":
        pytest.skip("IP no registrada en el allowlist del mock.")

    assert response.status_code == 404, (
        f"Se esperaba 404 para ID inexistente, se obtuvo {response.status_code}"
    )

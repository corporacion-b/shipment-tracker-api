import os
import re

import httpx
import pytest


DHL_MOCK_URL = "https://shipment-tracker-mock-api-production.up.railway.app/track/shipments"
DHL_MOCK_TRACKING_IDS = [
    "7KQ4M9X2LA",
    "P8R3T6Z1BN",
    "H5W9C2V7QM",
    "L2N8Y4D6KP",
    "A9F3J7M1TX",
    "C6V2Q8R5ZS",
    "N4X7B1K9YD",
    "T1M5P8W3QJ",
    "Z7D2L6C9RV",
    "R4H8N1S5XB",
    "Q9Y3V7A2LM",
    "B5K1T6P8NC",
    "M8C4R2Z7QW",
    "D3P9X5H1VK",
    "Y6L2N8M4SA",
    "W1Z7Q3C6PT",
    "K8S4B9D2LX",
    "V5A1M7R3QN",
    "X2T6H8Y4BC",
    "S9Q5L1P7DZ",
]


def require_dict(value, field_name):
    assert isinstance(value, dict), f"{field_name} must be an object"
    return value


def require_non_empty_list(value, field_name):
    assert isinstance(value, list), f"{field_name} must be a list"
    assert value, f"{field_name} must not be empty"
    return value


@pytest.mark.contract
@pytest.mark.external
@pytest.mark.parametrize("tracking_id", DHL_MOCK_TRACKING_IDS)
def test_dhl_mock_shipment_contract(tracking_id):
    api_key = os.getenv("DHL_API_KEY", "1234567890ABCDEF1234567890ABCDEF")
    if not re.fullmatch(r"[A-Za-z0-9]{32}", api_key):
        api_key = "1234567890ABCDEF1234567890ABCDEF"

    response = httpx.get(
        DHL_MOCK_URL,
        params={"trackingNumber": tracking_id},
        headers={"DHL-API-Key": api_key},
        timeout=10.0,
    )
    assert response.status_code == 200

    payload = response.json()
    shipments = require_non_empty_list(payload.get("shipments"), "shipments")
    shipment = require_dict(shipments[0], "shipments[0]")
    assert shipment["id"] == tracking_id

    origin = require_dict(shipment.get("origin"), "origin")
    destination = require_dict(shipment.get("destination"), "destination")
    status = require_dict(shipment.get("status"), "status")
    details = require_dict(shipment.get("details"), "details")
    events = require_non_empty_list(shipment.get("events"), "events")

    origin_address = require_dict(origin.get("address"), "origin.address")
    destination_address = require_dict(destination.get("address"), "destination.address")
    status_location = require_dict(status.get("location"), "status.location")
    status_address = require_dict(status_location.get("address"), "status.location.address")
    weight = require_dict(details.get("weight"), "details.weight")

    assert origin_address.get("addressLocality")
    assert origin_address.get("countryCode")
    assert destination_address.get("addressLocality")
    assert destination_address.get("countryCode")
    assert status.get("timestamp")
    assert status.get("status")
    assert status_address.get("addressLocality")
    assert status_address.get("countryCode")
    assert isinstance(weight.get("value"), int | float)

    first_event = require_dict(events[0], "events[0]")
    assert first_event.get("timestamp")
    assert first_event.get("status")

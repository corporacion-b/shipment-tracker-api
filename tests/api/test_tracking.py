import uuid

import pytest


def unique_tracking_id(prefix="TEST"):
    return f"{prefix}{uuid.uuid4().hex[:10].upper()}"


@pytest.mark.integration
def test_full_tracking_returns_raw_dhl_payload(client, mock_dhl_service):
    response = client.get("/full-tracking/7KQ4M9X2LA")

    assert response.status_code == 200
    assert response.json() == mock_dhl_service


@pytest.mark.integration
def test_protected_tracking_routes_require_token(client):
    tracking_id = "7KQ4M9X2LA"

    protected_routes = [
        ("GET", f"/status/{tracking_id}"),
        ("GET", f"/location/{tracking_id}"),
        ("GET", f"/dwell-time/{tracking_id}"),
        ("GET", f"/history/{tracking_id}"),
        ("GET", "/shipments"),
        ("GET", f"/shipments/{tracking_id}"),
        ("POST", f"/shipments/{tracking_id}/refresh"),
    ]

    for method, path in protected_routes:
        response = client.request(method, path)
        assert response.status_code == 401


@pytest.mark.integration
def test_status_endpoint_normalizes_dhl_payload(client, auth_headers, mock_dhl_service):
    tracking_id = unique_tracking_id("STS")

    response = client.get(f"/status/{tracking_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "tracking_id": tracking_id,
        "status": "Shipment information received",
        "weight": 0.65,
    }


@pytest.mark.integration
def test_location_endpoint_normalizes_current_location(client, auth_headers, mock_dhl_service):
    tracking_id = unique_tracking_id("LOC")

    response = client.get(f"/location/{tracking_id}", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {
        "tracking_id": tracking_id,
        "country_code": "MX",
        "city": "Saltillo",
        "timestamp": "2026-05-01T08:45:00Z",
    }


@pytest.mark.integration
def test_dwell_time_endpoint_returns_elapsed_time(client, auth_headers, mock_dhl_service):
    tracking_id = unique_tracking_id("DWL")

    response = client.get(f"/dwell-time/{tracking_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["tracking_id"] == tracking_id
    assert data["status"] == "SHIPMENT INFORMATION RECEIVED"
    assert data["country_code"] == "MX"
    assert data["city"] == "Saltillo"
    assert data["current_status_timestamp"] == "2026-05-01T08:45:00Z"
    assert data["dwell_time_hours"] >= 0
    assert data["dwell_time_days"] >= 0


@pytest.mark.integration
def test_history_endpoint_returns_timeline_events(client, auth_headers, mock_dhl_service):
    tracking_id = unique_tracking_id("HIS")

    response = client.get(f"/history/{tracking_id}", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["tracking_id"] == tracking_id
    assert len(data["history"]) == 3
    assert data["history"][0] == {
        "event_timestamp": "2026-05-01 08:45:00",
        "status": "Shipment information received",
        "description": "Shipment data has been received",
        "city": "Saltillo",
        "country_code": "MX",
    }


@pytest.mark.integration
def test_refresh_persists_shipment_and_detail_can_be_read(
    client,
    auth_headers,
    mock_dhl_service,
):
    tracking_id = unique_tracking_id("REF")

    refresh_response = client.post(
        f"/shipments/{tracking_id}/refresh",
        headers=auth_headers,
    )
    assert refresh_response.status_code == 200

    detail_response = client.get(
        f"/shipments/{tracking_id}",
        headers=auth_headers,
    )
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["tracking_id"] == tracking_id
    assert detail["status"] == "Shipment information received"
    assert detail["weight"] == 0.65
    assert detail["initial_location"]["city"] == "Aguascalientes"
    assert detail["end_location"]["city"] == "Guadalajara"
    assert detail["current_location"]["city"] == "Saltillo"


@pytest.mark.integration
def test_shipments_list_supports_search_and_pagination(
    client,
    auth_headers,
    mock_dhl_service,
):
    tracking_id = unique_tracking_id("LST")
    client.post(f"/shipments/{tracking_id}/refresh", headers=auth_headers)

    response = client.get(
        "/shipments",
        params={"q": tracking_id, "page": 1, "page_size": 10},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["items"][0]["tracking_id"] == tracking_id

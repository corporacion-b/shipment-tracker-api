import os
import uuid
from urllib.parse import urlparse

import pymysql
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DHL_API_KEY", "1234567890ABCDEF1234567890ABCDEF")
os.environ.setdefault("JWT_SECRET_KEY", "test_secret_key")

from src.core.config import settings
from src.db.connection import init_db
from src.main import src as fastapi_app


def pytest_addoption(parser):
    parser.addoption(
        "--run-external",
        action="store_true",
        default=False,
        help="Run tests that call external services such as the DHL mock API.",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-external"):
        return

    skip_external = pytest.mark.skip(reason="requires --run-external")
    for item in items:
        if "external" in item.keywords:
            item.add_marker(skip_external)


@pytest.fixture
def db_connection():
    """Provides a pymysql connection based on the active test config."""
    init_db()
    url = urlparse(settings.DATABASE_URL)
    connection = pymysql.connect(
        host=url.hostname or "localhost",
        port=url.port or 3306,
        user=url.username,
        password=url.password,
        database=url.path.lstrip("/"),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )
    yield connection
    connection.rollback()
    connection.close()


@pytest.fixture
def client():
    """FastAPI test client for endpoint tests."""
    with TestClient(fastapi_app) as test_client:
        yield test_client


@pytest.fixture
def unique_email():
    return f"tester_{uuid.uuid4().hex}@example.com"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def auth_headers(client, unique_email):
    password = "password123"
    register_response = client.post(
        "/auth/register",
        json={"email": unique_email, "password": password},
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/auth/login",
        data={"username": unique_email, "password": password},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def dhl_shipment_payload():
    return {
        "shipments": [
            {
                "id": "7KQ4M9X2LA",
                "service": "parcel-mx",
                "division": "ecommerce",
                "origin": {
                    "address": {
                        "addressLocality": "Aguascalientes",
                        "countryCode": "MX",
                    }
                },
                "destination": {
                    "address": {
                        "addressLocality": "Guadalajara",
                        "countryCode": "MX",
                    }
                },
                "status": {
                    "timestamp": "2026-05-01T08:45:00Z",
                    "statusCode": "pre-transit",
                    "status": "Shipment information received",
                    "description": "Shipment data has been received",
                    "remark": "Shipment created in DHL systems",
                    "location": {
                        "address": {
                            "addressLocality": "Saltillo - Mexico",
                            "addressLocalityServicing": "Saltillo",
                            "countryCode": "MX",
                        }
                    },
                },
                "estimatedTimeOfDelivery": "2026-05-03T23:59:00Z",
                "serviceUrl": "https://mock-dhl.local/track/7KQ4M9X2LA",
                "returnFlag": False,
                "details": {
                    "product": {"productName": "DHL Parcel Mexico"},
                    "proofOfDelivery": {},
                    "proofOfDeliverySignedAvailable": False,
                    "totalNumberOfPieces": 1,
                    "weight": {"unitText": "kg", "value": 0.65},
                    "volume": {"unitText": "cm3", "value": 0},
                    "dimensions": {
                        "height": {"unitText": "cm", "value": 8},
                        "length": {"unitText": "cm", "value": 20},
                        "width": {"unitText": "cm", "value": 12},
                    },
                },
                "events": [
                    {
                        "timestamp": "2026-05-01T08:45:00Z",
                        "location": {
                            "address": {
                                "addressLocality": "Saltillo",
                                "addressLocalityServicing": "Saltillo",
                                "countryCode": "MX",
                            }
                        },
                        "statusCode": "pre-transit",
                        "status": "Shipment information received",
                        "description": "Shipment data has been received",
                    },
                    {
                        "timestamp": "2026-05-01T16:20:00Z",
                        "location": {
                            "address": {
                                "addressLocality": "Aguascalientes",
                                "addressLocalityServicing": "Aguascalientes",
                                "countryCode": "MX",
                            }
                        },
                        "statusCode": "transit",
                        "status": "Processed at facility",
                        "description": "Shipment processed at origin facility",
                    },
                    {
                        "timestamp": "2026-05-01T09:05:00Z",
                        "location": {
                            "address": {
                                "addressLocality": "Aguascalientes",
                                "addressLocalityServicing": "Aguascalientes",
                                "countryCode": "MX",
                            }
                        },
                        "statusCode": "pre-transit",
                        "status": "Shipment information received",
                        "description": "Shipment data has been received",
                    },
                ],
            }
        ]
    }


@pytest.fixture
def mock_dhl_service(monkeypatch, dhl_shipment_payload):
    async def fake_buscar_en_dhl(*args, **kwargs):
        return dhl_shipment_payload

    monkeypatch.setattr(
        "src.services.dhl.DHLService.buscar_en_dhl",
        fake_buscar_en_dhl,
    )
    return dhl_shipment_payload

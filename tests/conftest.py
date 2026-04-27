import pytest
from fastapi.testclient import TestClient
from src.main import src

@pytest.fixture
def client():
    """Fixture que provee un cliente de pruebas para la app."""
    return TestClient(src)